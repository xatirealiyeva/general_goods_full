from django.test import TestCase
from rest_framework.test import APIClient
from apps.users.models import User
from .models import Customer, WishlistItem
from apps.catalog.models import Category, Product
class WishlistTests(TestCase):
 def setUp(self):
  self.client=APIClient();self.user=User.objects.create_user("a@a.com","password123",role="CUSTOMER");self.customer=Customer.objects.create(user=self.user,first_name="A",last_name="A");c=Category.objects.create(name="C",slug="c",status="ACTIVE");self.product=Product.objects.create(name="P",slug="p",category=c,base_price=1,status="ACTIVE")
 def test_wishlist_add_duplicate_list_remove(self):
  self.client.force_authenticate(self.user);self.assertEqual(self.client.post("/api/customers/wishlist/",{"product":str(self.product.id)},format="json").status_code,201);self.assertEqual(self.client.post("/api/customers/wishlist/",{"product":str(self.product.id)},format="json").status_code,200);self.assertEqual(WishlistItem.objects.count(),1);self.assertEqual(self.client.delete(f"/api/customers/wishlist/{self.product.id}/").status_code,204)
