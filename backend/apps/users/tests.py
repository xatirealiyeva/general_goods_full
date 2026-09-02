from django.test import TestCase
from rest_framework.test import APIClient

from apps.customers.models import Customer
from apps.sellers.models import Seller
from .models import User


class CustomerPromotionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user("admin@example.com", "AdminPass123!", role=User.Role.ADMIN)
        self.customer = User.objects.create_user("customer@example.com", "CustomerPass123!", role=User.Role.CUSTOMER)
        Customer.objects.create(user=self.customer, first_name="Customer", last_name="Example")

    def test_admin_promotion_creates_one_seller_profile_and_seller_analytics_loads(self):
        self.client.force_authenticate(self.admin)
        response = self.client.patch(
            f"/api/users/{self.customer.id}/status/", {"role": User.Role.SELLER}, format="json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Seller.objects.filter(user=self.customer).count(), 1)

        self.customer.refresh_from_db()
        self.client.force_authenticate(self.customer)
        analytics = self.client.get("/api/orders/seller/analytics/")

        self.assertEqual(analytics.status_code, 200)
        self.assertEqual(analytics.data, {"orders": 0, "customers": 0, "revenue": 0})

    def test_promoting_an_account_with_a_seller_profile_does_not_create_a_duplicate(self):
        Seller.objects.create(user=self.customer, business_name="Existing Store", first_name="Customer", last_name="Example")
        self.client.force_authenticate(self.admin)

        response = self.client.patch(
            f"/api/users/{self.customer.id}/status/", {"role": User.Role.SELLER}, format="json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Seller.objects.filter(user=self.customer).count(), 1)

    def test_existing_seller_analytics_remain_available(self):
        seller_user = User.objects.create_user("seller@example.com", "SellerPass123!", role=User.Role.SELLER)
        Seller.objects.create(user=seller_user, business_name="Existing Seller", first_name="Seller", last_name="Example")
        self.client.force_authenticate(seller_user)

        response = self.client.get("/api/orders/seller/analytics/")

        self.assertEqual(response.status_code, 200)
