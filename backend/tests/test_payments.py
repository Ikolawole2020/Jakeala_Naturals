"""Payment tests: Paystack config, initialise, verify and the signed webhook.

Run with:  python manage.py test tests
"""

import hashlib
import hmac
import json
from decimal import Decimal
from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from catalog.models import Category, Product
from commerce.models import Cart, CartItem, Order, OrderItem

TEST_SECRET = "sk_test_pretend_key"
TEST_PUBLIC = "pk_test_pretend_key"


class PaymentsBase(TestCase):
    """A pending order worth NGN 17,000 with two units of tracked stock."""

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
            stock_quantity=5,
        )

        self.cart_key = "g_" + "a" * 30
        cart = Cart.objects.create(session_key=self.cart_key)
        CartItem.objects.create(cart=cart, product=self.product, quantity=2)

        self.order = Order.objects.create(
            email="ada@example.com",
            full_name="Ada Obi",
            address="12 Marina Road",
            city="Lagos",
            state="Lagos",
            subtotal=Decimal("17000.00"),
            total=Decimal("17000.00"),
            payment_reference="JN1TABCD1234",
            cart_key=self.cart_key,
        )
        OrderItem.objects.create(
            order=self.order,
            product=self.product,
            product_name=self.product.name,
            sku=self.product.sku,
            quantity=2,
            unit_price=Decimal("8500.00"),
        )

    def webhook(self, event="charge.success", reference=None, amount=1_700_000, secret=TEST_SECRET):
        """POST a webhook with a correctly signed body."""
        body = json.dumps(
            {
                "event": event,
                "data": {
                    "reference": reference or self.order.payment_reference,
                    "amount": amount,
                    "currency": "NGN",
                    "status": "success",
                },
            }
        ).encode()
        signature = hmac.new(secret.encode(), body, hashlib.sha512).hexdigest()
        return self.client.post(
            "/api/payments/webhook/",
            data=body,
            content_type="application/json",
            HTTP_X_PAYSTACK_SIGNATURE=signature,
        )


class PaymentsConfigTests(PaymentsBase):
    def test_config_declares_the_provider_and_shipping_rules(self):
        response = self.client.get("/api/payments/config/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["provider"], "paystack")
        self.assertEqual(response.data["currency"], "NGN")
        self.assertEqual(response.data["free_shipping_threshold"], "15000")
        self.assertEqual(response.data["flat_shipping_fee"], "2500")

    @override_settings(PAYSTACK_SECRET_KEY="", PAYSTACK_PUBLIC_KEY="")
    def test_card_payment_reports_itself_disabled_without_keys(self):
        self.assertFalse(self.client.get("/api/payments/config/").data["enabled"])

    @override_settings(PAYSTACK_SECRET_KEY=TEST_SECRET, PAYSTACK_PUBLIC_KEY=TEST_PUBLIC)
    def test_public_key_is_exposed_but_the_secret_never_is(self):
        response = self.client.get("/api/payments/config/")

        self.assertTrue(response.data["enabled"])
        self.assertEqual(response.data["public_key"], TEST_PUBLIC)
        self.assertNotIn(TEST_SECRET, json.dumps(response.data))


class InitializePaymentTests(PaymentsBase):
    def test_unknown_order_is_a_404(self):
        response = self.client.post(
            "/api/payments/initialize/", {"order_id": 999_999, "token": "nope"}, format="json"
        )
        self.assertEqual(response.status_code, 404)

    def test_an_order_id_alone_grants_nothing(self):
        response = self.client.post(
            "/api/payments/initialize/", {"order_id": self.order.id}, format="json"
        )
        self.assertEqual(response.status_code, 404)

    @override_settings(PAYSTACK_SECRET_KEY="", PAYSTACK_PUBLIC_KEY="")
    def test_missing_keys_are_reported_clearly(self):
        response = self.client.post(
            "/api/payments/initialize/",
            {"order_id": self.order.id, "token": str(self.order.public_token)},
            format="json",
        )
        self.assertEqual(response.status_code, 503)
        self.assertIn("PAYSTACK_SECRET_KEY", response.data["detail"])

    @override_settings(PAYSTACK_SECRET_KEY=TEST_SECRET, PAYSTACK_PUBLIC_KEY=TEST_PUBLIC)
    def test_successful_initialisation_returns_a_redirect_url(self):
        fake = {
            "authorization_url": "https://checkout.paystack.com/abc123",
            "access_code": "abc123",
            "reference": "JN1TABCD1234",
        }
        with patch("payments.paystack.initialize_transaction", return_value=fake) as mocked:
            response = self.client.post(
                "/api/payments/initialize/",
                {"order_id": self.order.id, "token": str(self.order.public_token)},
                format="json",
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["authorization_url"], fake["authorization_url"])
        self.assertEqual(response.data["amount_kobo"], 1_700_000)

        # A fresh, unguessable reference is minted on every attempt.
        self.order.refresh_from_db()
        self.assertNotEqual(self.order.payment_reference, "JN1TABCD1234")
        self.assertTrue(self.order.payment_reference.startswith(f"JN{self.order.pk}T"))
        self.assertEqual(mocked.call_args.kwargs["amount"], Decimal("17000.00"))

    @override_settings(PAYSTACK_SECRET_KEY=TEST_SECRET, PAYSTACK_PUBLIC_KEY=TEST_PUBLIC)
    def test_a_paid_order_cannot_be_reinitialised(self):
        self.order.status = Order.PAID
        self.order.save(update_fields=["status"])

        response = self.client.post(
            "/api/payments/initialize/",
            {"order_id": self.order.id, "token": str(self.order.public_token)},
            format="json",
        )
        self.assertEqual(response.status_code, 400)


class VerifyPaymentTests(PaymentsBase):
    def verify(self, reference=None, payload=None):
        with patch("payments.paystack.verify_transaction", return_value=payload or {}):
            return self.client.post(
                "/api/payments/verify/",
                {"reference": reference or self.order.payment_reference},
                format="json",
            )

    def success_payload(self, **overrides):
        return {
            "status": "success",
            "reference": self.order.payment_reference,
            "amount": 1_700_000,
            "currency": "NGN",
            **overrides,
        }

    def test_a_reference_is_required(self):
        self.assertEqual(
            self.client.post("/api/payments/verify/", {}, format="json").status_code, 400
        )

    def test_an_unknown_reference_is_a_404(self):
        response = self.verify(reference="JN999TZZZZZZZZ")
        self.assertEqual(response.status_code, 404)

    def test_successful_verification_settles_the_order(self):
        response = self.verify(payload=self.success_payload())

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["settled"])

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.PAID)
        self.assertIsNotNone(self.order.paid_at)
        self.assertTrue(self.order.stock_reduced)
        self.assertEqual(response.data["order"]["status"], "paid")

    def test_stock_is_decremented_once_on_payment(self):
        self.verify(payload=self.success_payload())

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 3)

    def test_the_basket_is_emptied_on_payment(self):
        self.verify(payload=self.success_payload())
        self.assertFalse(CartItem.objects.filter(cart__session_key=self.cart_key).exists())

    def test_a_short_payment_does_not_settle_the_order(self):
        response = self.verify(payload=self.success_payload(amount=1_000_000))

        self.assertEqual(response.status_code, 409)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.PENDING)
        self.assertIsNone(self.order.paid_at)

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 5, "stock must not move")

    def test_a_failed_payment_status_does_not_settle(self):
        response = self.verify(payload=self.success_payload(status="failed"))

        self.assertEqual(response.status_code, 400)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.PENDING)

    def test_paying_twice_is_idempotent(self):
        self.verify(payload=self.success_payload())
        second = self.verify(payload=self.success_payload())

        self.assertEqual(second.status_code, 200)
        self.assertTrue(second.data["already_paid"])

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 3, "stock must only move once")


@override_settings(PAYSTACK_SECRET_KEY=TEST_SECRET, PAYSTACK_PUBLIC_KEY=TEST_PUBLIC)
class PaystackWebhookTests(PaymentsBase):
    """The webhook is public, so only a correctly signed body may be trusted."""

    def test_a_missing_signature_is_rejected(self):
        response = self.client.post(
            "/api/payments/webhook/", data=b"{}", content_type="application/json"
        )
        self.assertEqual(response.status_code, 401)

    def test_a_wrong_signature_is_rejected(self):
        response = self.webhook(secret="sk_test_someone_elses_key")
        self.assertEqual(response.status_code, 401)

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.PENDING)

    def test_a_valid_charge_success_settles_the_order(self):
        response = self.webhook()

        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.PAID)
        self.assertIsNotNone(self.order.paid_at)

    def test_a_valid_webhook_also_moves_the_stock(self):
        self.webhook()

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 3)

    def test_a_duplicate_webhook_does_not_move_stock_twice(self):
        self.webhook()
        self.webhook()

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 3)
        self.assertEqual(Order.objects.filter(status=Order.PAID).count(), 1)

    def test_an_underpayment_is_ignored(self):
        response = self.webhook(amount=100)

        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.PENDING)

    def test_an_unknown_reference_is_acknowledged_and_ignored(self):
        response = self.webhook(reference="JN999TNOTREAL9")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data.get("ignored"))
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.PENDING)

    def test_other_events_are_acknowledged_without_action(self):
        response = self.webhook(event="charge.failed")

        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.PENDING)

    def test_an_order_with_no_reference_yet_is_not_settled(self):
        self.order.payment_reference = ""
        self.order.save(update_fields=["payment_reference"])

        response = self.webhook(reference="")
        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.PENDING)

    def test_the_webhook_needs_no_api_token(self):
        """Paystack cannot send a DRF token, so this route must be open-but-signed."""
        response = self.webhook()
        self.assertNotEqual(response.status_code, 401)
        self.assertEqual(response.status_code, 200)



