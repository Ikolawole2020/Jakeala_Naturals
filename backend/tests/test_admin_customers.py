"""Customer-account management in the staff dashboard.

These cover the destructive paths, because a mistake here loses a customer's
account rather than a product record.
"""

from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import Profile, VerificationCode
from commerce.models import Order


class CustomerAdminTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            "boss", "boss@shop.test", "Str0ng-Pass!99"
        )
        self.customer = User.objects.create_user(
            "jane", email="jane@shop.test", password="Str0ng-Pass!99", first_name="Jane"
        )
        self.customer.profile.email_verified = True
        self.customer.profile.phone = "+234800"
        self.customer.profile.save()
        self.staff = APIClient()
        self.staff.force_authenticate(self.admin)

    def _order(self, email="jane@shop.test"):
        return Order.objects.create(
            email=email,
            full_name="Jane",
            total=Decimal("5000"),
            subtotal=Decimal("5000"),
            shipping=Decimal("0"),
        )

    # ------------------------------------------------------------------ read
    def test_list_requires_staff(self):
        self.assertEqual(APIClient().get("/api/admin/customers/").status_code, 403)

    def test_list_includes_profile_and_orders(self):
        self._order()
        res = self.staff.get("/api/admin/customers/?search=jane")
        self.assertEqual(res.status_code, 200)
        row = res.json()["results"][0]
        self.assertTrue(row["email_verified"])
        self.assertEqual(row["phone"], "+234800")
        # A guest order carries only the email, and must still be attributed.
        self.assertEqual(row["order_count"], 1)

    def test_password_hash_is_never_returned(self):
        res = self.staff.get("/api/admin/customers/")
        self.assertNotIn("password", res.json()["results"][0])

    # ----------------------------------------------------------------- write
    def test_edit_details(self):
        res = self.staff.patch(
            f"/api/admin/customers/{self.customer.id}/",
            {"email": "jane2@shop.test", "first_name": "Janet"},
            format="json",
        )
        self.assertEqual(res.status_code, 200)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.email, "jane2@shop.test")
        self.assertEqual(self.customer.first_name, "Janet")

    def test_blank_fields_do_not_erase_data(self):
        self.staff.patch(
            f"/api/admin/customers/{self.customer.id}/", {"first_name": ""}, format="json"
        )
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.first_name, "Jane")

    def test_admin_can_set_a_new_password(self):
        res = self.staff.patch(
            f"/api/admin/customers/{self.customer.id}/",
            {"password": "Replacement!99"},
            format="json",
        )
        self.assertEqual(res.status_code, 200)
        self.customer.refresh_from_db()
        self.assertTrue(self.customer.check_password("Replacement!99"))

    def test_omitting_password_keeps_the_current_one(self):
        self.staff.patch(
            f"/api/admin/customers/{self.customer.id}/", {"first_name": "Janet"}, format="json"
        )
        self.customer.refresh_from_db()
        self.assertTrue(self.customer.check_password("Str0ng-Pass!99"))

    def test_deactivate_blocks_sign_in(self):
        self.staff.patch(
            f"/api/admin/customers/{self.customer.id}/", {"is_active": False}, format="json"
        )
        res = APIClient().post(
            "/api/auth/login/",
            {"email": "jane@shop.test", "password": "Str0ng-Pass!99"},
            format="json",
        )
        self.assertNotEqual(res.status_code, 200)

    # ---------------------------------------------------------------- delete
    def test_delete_removes_account_and_related_rows(self):
        VerificationCode.issue(self.customer, VerificationCode.SIGNUP)
        self.assertTrue(Profile.objects.filter(user=self.customer).exists())

        res = self.staff.delete(f"/api/admin/customers/{self.customer.id}/")
        self.assertEqual(res.status_code, 204)
        self.assertFalse(User.objects.filter(id=self.customer.id).exists())
        self.assertFalse(Profile.objects.filter(user_id=self.customer.id).exists())
        self.assertFalse(
            VerificationCode.objects.filter(user_id=self.customer.id).exists()
        )

    def test_delete_keeps_orders_for_the_record(self):
        order = self._order()
        self.staff.delete(f"/api/admin/customers/{self.customer.id}/")
        self.assertTrue(Order.objects.filter(id=order.id).exists())

    def test_last_superuser_cannot_be_deleted(self):
        res = self.staff.delete(f"/api/admin/customers/{self.admin.id}/")
        self.assertEqual(res.status_code, 403)
        self.assertTrue(User.objects.filter(id=self.admin.id).exists())

    def test_last_superuser_cannot_be_demoted(self):
        res = self.staff.patch(
            f"/api/admin/customers/{self.admin.id}/", {"is_staff": False}, format="json"
        )
        self.assertEqual(res.status_code, 403)

    def test_second_superuser_allows_deleting_the_first(self):
        User.objects.create_superuser("backup", "b@shop.test", "Str0ng-Pass!99")
        res = self.staff.delete(f"/api/admin/customers/{self.admin.id}/")
        self.assertEqual(res.status_code, 204)
