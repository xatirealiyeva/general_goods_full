from datetime import timedelta
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from apps.users.models import User
from apps.customers.models import Customer
from apps.sellers.models import Seller
from .models import Category, Product, ProductSellerAssignment, Brand, Tag, DiscountCode

class CatalogReviewTests(TestCase):
    def setUp(self):
        self.client=APIClient(); self.admin=User.objects.create_user("admin@test.dev","password123",role="ADMIN"); self.customer=User.objects.create_user("customer@test.dev","password123",role="CUSTOMER"); Customer.objects.create(user=self.customer,first_name="C",last_name="User")
        self.seller_user=User.objects.create_user("seller@test.dev","password123",role="SELLER"); self.seller=Seller.objects.create(user=self.seller_user,business_name="Shop",first_name="S",last_name="User")
        self.category=Category.objects.create(name="Cat",slug="cat",status="ACTIVE"); self.product=Product.objects.create(name="Product",slug="product",category=self.category,base_price=10,status="DRAFT")
    def auth(self,user): self.client.force_authenticate(user)
    def test_category_archive_restore_and_customer_denial(self):
        self.auth(self.customer); self.assertEqual(self.client.post(f"/api/catalog/categories/{self.category.id}/archive/").status_code,403)
        self.auth(self.admin); self.assertEqual(self.client.post(f"/api/catalog/categories/{self.category.id}/archive/").status_code,204); self.assertEqual(self.client.post(f"/api/catalog/categories/{self.category.id}/restore/").status_code,200)
    def test_brand_tag_admin_only_and_product_relationships(self):
        self.auth(self.customer); self.assertEqual(self.client.post("/api/catalog/brands/",{"name":"B","slug":"b"},format="json").status_code,403)
        self.auth(self.admin); brand=Brand.objects.create(name="B",slug="b"); tag=Tag.objects.create(name="T",slug="t"); self.product.brand=brand; self.product.save(); self.product.tags.add(tag); self.assertEqual(self.product.tags.count(),1)
    def test_seller_assignment_and_my_listings(self):
        self.auth(self.admin); self.assertEqual(self.client.post(f"/api/catalog/products/{self.product.id}/sellers/",{"seller":str(self.seller.id),"role":"ALTERNATIVE_SELLER","price":"9.00"},format="json").status_code,201)
        self.auth(self.seller_user); response=self.client.get("/api/catalog/products/mine/"); self.assertEqual(response.status_code,200); self.assertIn(str(self.product.id),str(response.data))
    def test_discount_dates_and_types(self):
        now=timezone.now(); pct=DiscountCode.objects.create(code="P10",discount_type="PERCENTAGE",value=Decimal("10"),starts_at=now-timedelta(days=1),ends_at=now+timedelta(days=1)); self.assertEqual((Decimal("50")*pct.value/100).quantize(Decimal(".01")),Decimal("5.00")); self.assertTrue(pct.is_active)
