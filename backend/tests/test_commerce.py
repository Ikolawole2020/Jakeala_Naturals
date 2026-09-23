"""Commerce tests: cart isolation, checkout pricing, order privacy.

Run with:  python manage.py test tests
"""

from decimal import Decimal
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from catalog.models import Category, Product
from commerce.models import Cart, Order

User = get_user_model()


class CommerceBase(TestCase):
    """Shared catalogue fixture.

    Throttle counters live in a file-based cache that is shared between tests
    (unlike the database), so each test starts by clearing it.
    """

    def setUp(self):
        cache.clear()
        self.client = APIClient()

        self.category = Category.objects.create(name="Skin & Body", slug="skin-body")
        self.product = Product.objects.create(
            category=self.category,
            name="Shea Body Butter",
            slug="shea-body-butter",
            short_benefit="Deep moisture.",
            description="Whipped shea.",
            price=Decimal("8500.00"),
            sku="JN-SHEA-01",
            image="https://example.com/shea.jpg",
        )

    def add_to_cart(self, session=None, quantity=1, **extra):
        payload = {"product_id": self.product.id, "quantity": quantity, **extra}
        if session is not None:
            payload["session"] = session
        return self.client.post("/api/cart/add/", payload, format="json")

    def get_cart(self, session=None):
        url = "/api/cart/" if session is None else f"/api/cart/?session={session}"
        return self.client.get(url)


class CartIsolationTests(CommerceBase):
    """The old code fell back to the literal key ``"guest"``, so every anonymous
    visitor shared one basket - and any visitor could read or edit someone else's
    cart by passing their key."""

    def test_missing_session_gets_a_generated_key(self):
        response = self.get_cart()
        self.assertEqual(response.status_code, 200)

        key = response.data["session_key"]
        self.assertGreaterEqual(len(key), 16)
        self.assertTrue(key.startswith("g_"))

    def test_two_guests_never_share_a_basket(self):
        first = self.get_cart().data["session_key"]
        second = APIClient().get("/api/cart/").data["session_key"]
        self.assertNotEqual(first, second)

    def test_short_or_malformed_key_is_replaced(self):
        response = self.get_cart(session="guest")
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.data["session_key"], "guest")

    def test_add_returns_the_key_the_browser_must_store(self):
        response = self.add_to_cart(quantity=2)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["session_key"].startswith("g_"))
        self.assertEqual(response.data["item_count"], 2)

    def test_cannot_touch_another_carts_item(self):
        key = self.add_to_cart().data["session_key"]
        item_id = self.get_cart(key).data["items"][0]["id"]

        stranger = APIClient()
        response = stranger.post(
            "/api/cart/update_item/",
            {"session": "g_" + "x" * 30, "item_id": item_id, "quantity": 99},
            format="json",
        )
        self.assertEqual(response.status_code, 404)

    def test_quantity_is_capped(self):
        key = self.add_to_cart().data["session_key"]
        self.assertEqual(self.add_to_cart(session=key, quantity=10_000).status_code, 400)

    def test_negative_quantity_is_rejected_rather_than_added(self):
        key = self.add_to_cart().data["session_key"]
        response = self.add_to_cart(session=key, quantity=-999)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.get_cart(key).data["items"][0]["quantity"], 1)


    def test_out_of_stock_product_cannot_be_added(self):
        self.product.in_stock = False
        self.product.save(update_fields=["in_stock"])
        self.assertEqual(self.add_to_cart().status_code, 409)

    def test_zero_quantity_removes_the_line(self):
        key = self.add_to_cart().data["session_key"]
        item_id = self.get_cart(key).data["items"][0]["id"]

        response = self.client.post(
            "/api/cart/update_item/",
            {"session": key, "item_id": item_id, "quantity": 0},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["items"], [])

    def test_signed_in_shopper_gets_an_account_key(self):
        user = User.objects.create_user(username="ada", password="Sunflower-Ritual-2026")
        token = Token.objects.create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        response = self.get_cart(session="g_" + "y" * 30)
        self.assertEqual(response.data["session_key"], f"user:{user.pk}")

    def test_guest_basket_merges_into_the_account_basket(self):
        guest_key = self.add_to_cart(quantity=3).data["session_key"]

        user = User.objects.create_user(username="ada", password="Sunflower-Ritual-2026")
        token = Token.objects.create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        response = self.client.post("/api/cart/merge/", {"session": guest_key}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["item_count"], 3)
        self.assertFalse(Cart.objects.filter(session_key=guest_key).exists())

    def test_merge_requires_a_signed_in_user(self):
        response = self.client.post(
            "/api/cart/merge/", {"session": "g_" + "z" * 30}, format="json"
        )
        self.assertEqual(response.status_code, 401)


class CheckoutTests(CommerceBase):
    """Checkout used to mark orders ``paid`` with no money taken, take prices from
    the request, and ignore stock entirely."""

    ADDRESS = {
        "email": "ada@example.com",
        "full_name": "Ada Obi",
        "address": "12 Marina Road",
        "city": "Lagos",
        "state": "Lagos",
    }

    def checkout(self, session=None, **overrides):
        key = session or self.add_to_cart(quantity=1).data["session_key"]
        payload = {**self.ADDRESS, "session_key": key, **overrides}
        return self.client.post("/api/checkout/", payload, format="json"), key

    def test_empty_basket_cannot_check_out(self):
        response, _ = self.checkout(session="g_" + "e" * 30)
        self.assertEqual(response.status_code, 409)

    def test_order_starts_pending_not_paid(self):
        response, _ = self.checkout()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["order"]["status"], "pending")

        order = Order.objects.get()
        self.assertEqual(order.status, Order.PENDING)
        self.assertIsNone(order.paid_at)

    def test_order_carries_a_public_token(self):
        response, _ = self.checkout()
        self.assertTrue(response.data["order"]["public_token"])
        self.assertIsNotNone(Order.objects.get().public_token)

    def test_prices_come_from_the_catalogue_not_the_request(self):
        key = self.add_to_cart(quantity=2).data["session_key"]
        self.client.post(
            "/api/checkout/",
            {
                **self.ADDRESS,
                "session_key": key,
                # A tampered payload: the server must ignore every one of these.
                "total": "1.00",
                "subtotal": "1.00",
                "shipping": "0.00",
            },
            format="json",
        )

        order = Order.objects.get()
        self.assertEqual(order.subtotal, Decimal("17000.00"))
        # 17,000 is over the 15,000 free-shipping threshold.
        self.assertEqual(order.shipping, Decimal("0.00"))
        self.assertEqual(order.total, Decimal("17000.00"))

    def test_shipping_is_charged_below_the_threshold(self):
        self.checkout()
        self.assertEqual(Order.objects.get().shipping, Decimal("2500.00"))
        self.assertEqual(Order.objects.get().total, Decimal("11000.00"))

    def test_subscription_line_gets_the_discount(self):
        key = self.add_to_cart(quantity=1, subscribe=True).data["session_key"]
        self.checkout(session=key)
        self.assertEqual(Order.objects.get().subtotal, Decimal("7650.00"))

    def test_tracked_stock_is_enforced(self):
        self.product.stock_quantity = 1
        self.product.save(update_fields=["stock_quantity"])

        key = self.add_to_cart(quantity=3).data["session_key"]
        response, _ = self.checkout(session=key)

        self.assertEqual(response.status_code, 409)
        self.assertFalse(Order.objects.exists())

    def test_pressing_place_order_twice_reuses_the_pending_order(self):
        first, key = self.checkout()
        second, _ = self.checkout(session=key)

        self.assertEqual(first.data["order"]["id"], second.data["order"]["id"])
        self.assertEqual(Order.objects.count(), 1)

    def test_order_is_linked_to_the_matching_account(self):
        user = User.objects.create_user(
            username="ada", email="ada@example.com", password="Sunflower-Ritual-2026"
        )
        self.checkout()
        self.assertEqual(Order.objects.get().user_id, user.pk)

    def test_guest_order_has_no_account(self):
        self.checkout()
        self.assertIsNone(Order.objects.get().user_id)

    def test_basket_is_kept_until_payment_succeeds(self):
        _, key = self.checkout()
        self.assertEqual(self.get_cart(key).data["item_count"], 1)


class OrderPrivacyTests(CommerceBase):
    """The old ``/api/orders/`` was public and filterable by ``?email=``, so anyone
    could read a stranger's full name, phone number and delivery address."""

    def setUp(self):
        super().setUp()
        self.ada = User.objects.create_user(
            username="ada", email="ada@example.com", password="Sunflower-Ritual-2026"
        )
        self.ben = User.objects.create_user(
            username="ben", email="ben@example.com", password="Sunflower-Ritual-2026"
        )

        self.ada_order = Order.objects.create(
            user=self.ada,
            email="ada@example.com",
            full_name="Ada Obi",
            phone="08030000000",
            address="12 Marina Road",
            city="Lagos",
            state="Lagos",
            subtotal=Decimal("8500.00"),
            total=Decimal("11000.00"),
        )
        self.ben_order = Order.objects.create(
            user=self.ben,
            email="ben@example.com",
            full_name="Ben Adeyemi",
            phone="08040000000",
            address="5 Broad Street",
            city="Abuja",
            state="FCT",
            subtotal=Decimal("8500.00"),
            total=Decimal("11000.00"),
        )

    def sign_in(self, user):
        token = Token.objects.create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        return token

    def test_order_list_requires_a_token(self):
        """Anonymous access is refused. DRF answers 403 rather than 401 here
        because SessionAuthentication is listed first and offers no challenge."""
        self.assertEqual(self.client.get("/api/orders/").status_code, 403)

    def test_list_only_returns_the_callers_orders(self):
        self.sign_in(self.ada)
        response = self.client.get("/api/orders/")

        self.assertEqual(response.status_code, 200)
        ids = [row["id"] for row in response.data["results"]]
        self.assertEqual(ids, [self.ada_order.id])

    def test_email_filter_cannot_reach_another_customer(self):
        """``?email=`` must not widen the result set, so a stranger's order can
        never come back even though the parameter is still accepted."""
        self.sign_in(self.ada)
        response = self.client.get("/api/orders/?email=ben@example.com")

        returned = [row["id"] for row in response.data["results"]]
        self.assertEqual(returned, [self.ada_order.id])
        self.assertNotIn(self.ben_order.id, returned)


    def test_status_filter_stays_within_the_callers_orders(self):
        self.sign_in(self.ada)
        response = self.client.get("/api/orders/?status=pending")

        ids = [row["id"] for row in response.data["results"]]
        self.assertEqual(ids, [self.ada_order.id])

    def test_retrieve_without_credentials_is_a_404(self):
        response = self.client.get(f"/api/orders/{self.ada_order.id}/")
        self.assertEqual(response.status_code, 404)

    def test_retrieve_with_a_wrong_token_is_a_404(self):
        response = self.client.get(f"/api/orders/{self.ada_order.id}/?token={uuid4()}")
        self.assertEqual(response.status_code, 404)

    def test_guest_with_the_public_token_sees_a_reduced_record(self):
        response = self.client.get(
            f"/api/orders/{self.ada_order.id}/?token={self.ada_order.public_token}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("address", response.data, "a token holder must not get the address")
        self.assertNotIn("phone", response.data)
        self.assertNotIn("payment_reference", response.data)
        self.assertIn("*", response.data["email_masked"])
        self.assertNotIn("ada@example.com", response.data["email_masked"])

    def test_owner_sees_full_detail(self):
        self.sign_in(self.ada)
        response = self.client.get(f"/api/orders/{self.ada_order.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["address"], "12 Marina Road")
        self.assertEqual(response.data["phone"], "08030000000")

    def test_an_authenticated_stranger_still_cannot_read_it(self):
        self.sign_in(self.ben)
        response = self.client.get(f"/api/orders/{self.ada_order.id}/")
        self.assertEqual(response.status_code, 404)

    def test_owner_can_read_their_own_full_record(self):
        self.sign_in(self.ben)
        response = self.client.get(f"/api/orders/{self.ben_order.id}/")
        self.assertEqual(response.data["address"], "5 Broad Street")


