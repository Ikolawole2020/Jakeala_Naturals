"""The signed-in customer dashboard: order history and the address book.

These guard the two things that actually matter here - a customer can only ever
reach their own data, and the order history stays correct for someone who
ordered as a guest before they had an account.
"""

from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import Address
from commerce.models import Order, OrderItem


def make_order(owner, email=None, **kwargs):
    """Create an order. Pass ``user=None`` to model a guest checkout."""
    defaults = {
        "email": email or owner.email,
        "user": owner,
        "full_name": "Ada Lovelace",
        "phone": "+234800",
        "address": "12 Aja Street",
        "city": "Lagos",
        "state": "Lagos",
        "total": Decimal("7500"),
        "subtotal": Decimal("7500"),
        "shipping": Decimal("0"),
    }
    defaults.update(kwargs)
    return Order.objects.create(**defaults)


class MyOrdersTests(TestCase):
    def setUp(self):
        self.me = User.objects.create_user(
            "ada", email="ada@shop.test", password="Str0ng-Pass!99"
        )
        self.stranger = User.objects.create_user(
            "eve", email="eve@shop.test", password="Str0ng-Pass!99"
        )
        self.mine = make_order(self.me)
        OrderItem.objects.create(
            order=self.mine,
            product_name="Cycle Reset Tea",
            sku="TEA-1",
            quantity=2,
            unit_price=Decimal("3750"),
        )
        self.theirs = make_order(self.stranger)
        self.client = APIClient()
        self.client.force_authenticate(self.me)

    def test_requires_sign_in(self):
        self.assertEqual(APIClient().get("/api/auth/me/orders/").status_code, 403)

    def test_lists_only_my_orders(self):
        rows = self.client.get("/api/auth/me/orders/").json()
        self.assertEqual([o["id"] for o in rows], [self.mine.id])

    def test_guest_order_claimed_by_email_is_included(self):
        """Ordering before the account existed must not lose the order."""
        guest = make_order(self.me, user=None, email="ADA@shop.test".upper())
        ids = [o["id"] for o in self.client.get("/api/auth/me/orders/").json()]
        self.assertIn(guest.id, ids)

    def test_list_hides_the_delivery_address(self):
        row = self.client.get("/api/auth/me/orders/").json()[0]
        self.assertNotIn("address", row)
        self.assertEqual(row["city"], "Lagos")

    def test_detail_includes_items_and_address(self):
        data = self.client.get(f"/api/auth/me/orders/{self.mine.id}/").json()
        self.assertEqual(len(data["items"]), 1)
        self.assertEqual(data["items"][0]["product_name"], "Cycle Reset Tea")
        self.assertEqual(data["address"], "12 Aja Street")

    def test_strangers_order_is_404_not_403(self):
        res = self.client.get(f"/api/auth/me/orders/{self.theirs.id}/")
        self.assertEqual(res.status_code, 404)
        self.assertNotIn("address", res.json())


class AddressBookTests(TestCase):
    def setUp(self):
        self.me = User.objects.create_user(
            "ada", email="ada@shop.test", password="Str0ng-Pass!99"
        )
        self.client = APIClient()
        self.client.force_authenticate(self.me)
        self.payload = {
            "label": "work",
            "full_name": "Ada Lovelace",
            "phone": "+234800",
            "line1": "14 Bourdillon Road",
            "city": "Lagos",
            "state": "Lagos",
        }

    def test_requires_sign_in(self):
        self.assertEqual(
            APIClient().get("/api/auth/me/addresses/").status_code, 403
        )

    def test_first_address_becomes_default_and_says_so(self):
        """The API must agree with the row it just promoted."""
        res = self.client.post("/api/auth/me/addresses/", self.payload, format="json")
        self.assertEqual(res.status_code, 201)
        self.assertTrue(res.json()["is_default"])
        self.assertTrue(Address.objects.get(pk=res.json()["id"]).is_default)

    def test_blank_street_is_rejected(self):
        res = self.client.post(
            "/api/auth/me/addresses/", {**self.payload, "line1": "   "}, format="json"
        )
        self.assertEqual(res.status_code, 400)

    def test_only_one_default_survives(self):
        first = self.client.post("/api/auth/me/addresses/", self.payload, format="json")
        second = self.client.post(
            "/api/auth/me/addresses/",
            {**self.payload, "label": "home", "line1": "1 Admiralty Way"},
            format="json",
        )
        self.assertEqual(
            Address.objects.filter(user=self.me, is_default=True).count(), 1
        )
        # Promoting the second must demote the first.
        self.client.patch(
            f"/api/auth/me/addresses/{second.json()['id']}/",
            {"is_default": True},
            format="json",
        )
        self.assertTrue(Address.objects.get(pk=second.json()["id"]).is_default)
        self.assertFalse(Address.objects.get(pk=first.json()["id"]).is_default)

    def test_cannot_edit_or_delete_another_customers_address(self):
        other = User.objects.create_user(
            "eve", email="eve@shop.test", password="Str0ng-Pass!99"
        )
        theirs = Address.objects.create(
            user=other, full_name="Eve", phone="1", line1="9 B St", city="Abuja", state="FCT"
        )
        url = f"/api/auth/me/addresses/{theirs.id}/"
        self.assertEqual(self.client.patch(url, {"city": "Lagos"}, format="json").status_code, 404)
        self.assertEqual(self.client.delete(url).status_code, 404)
        self.assertTrue(Address.objects.filter(pk=theirs.pk).exists())

    def test_deleting_the_default_promotes_another(self):
        self.client.post("/api/auth/me/addresses/", self.payload, format="json")
        second = self.client.post(
            "/api/auth/me/addresses/",
            {**self.payload, "label": "home", "line1": "1 Admiralty Way"},
            format="json",
        ).json()
        self.client.delete(f"/api/auth/me/addresses/{second['id']}/")
        self.assertEqual(
            Address.objects.filter(user=self.me, is_default=True).count(), 1
        )

    def test_cannot_post_an_address_into_another_account(self):
        """The owner comes from the session, never the payload."""
        res = self.client.post(
            "/api/auth/me/addresses/",
            {**self.payload, "user": 999},
            format="json",
        )
        self.assertEqual(res.status_code, 201)
        self.assertEqual(Address.objects.get(pk=res.json()["id"]).user_id, self.me.id)
