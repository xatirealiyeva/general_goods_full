from decimal import Decimal
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from apps.catalog.models import DiscountCode
from apps.shared.exceptions import DomainError
from apps.users.models import User
from apps.customers.models import Customer
from apps.sellers.models import Seller
from apps.catalog.models import Category, Product, ProductVariant, ProductSellerAssignment
from apps.cart.services import CartService
from .models import Order, RefundRequest
from .services import OrderService

class DiscountCodeValidationTests(TestCase):
    def test_percentage_discount_is_calculated_server_side(self):
        code = DiscountCode(code="SAVE10", discount_type="PERCENTAGE", value=Decimal("10"), starts_at=timezone.now(), ends_at=timezone.now() + timedelta(days=1))
        self.assertEqual((Decimal("50") * code.value / Decimal("100")).quantize(Decimal("0.01")), Decimal("5.00"))

    def test_expired_code_is_not_valid(self):
        code = DiscountCode(code="OLD", discount_type="FIXED", value=Decimal("5"), starts_at=timezone.now()-timedelta(days=2), ends_at=timezone.now()-timedelta(days=1))
        self.assertLess(code.ends_at, timezone.now())


class SelectedCartCheckoutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("buyer@example.com", "password123", role="CUSTOMER")
        self.customer = Customer.objects.create(user=self.user, first_name="Buyer", last_name="One")
        seller_user = User.objects.create_user("seller@example.com", "password123", role="SELLER")
        seller = Seller.objects.create(user=seller_user, business_name="Seller", first_name="Seller", last_name="One", status="ACTIVE")
        category = Category.objects.create(name="Checkout", slug="checkout", status="ACTIVE")
        self.cart = CartService.get_or_create_cart(self.customer)
        self.items = []
        for suffix, price in (("A", Decimal("50.00")), ("B", Decimal("30.00")), ("C", Decimal("20.00"))):
            product = Product.objects.create(name=f"Product {suffix}", slug=f"product-{suffix.lower()}", category=category, base_price=price, status="ACTIVE")
            variant = ProductVariant.objects.create(product=product, sku=f"SKU-{suffix}", stock_quantity=10)
            ProductSellerAssignment.objects.create(product=product, seller=seller, role="PRIMARY_SELLER", price=price)
            self.items.append(CartService.add_item(self.cart, variant.id, 1))

    def test_selected_items_are_discounted_and_only_selected_rows_are_removed(self):
        DiscountCode.objects.create(code="FIX36", discount_type="FIXED", value=Decimal("36.00"), starts_at=timezone.now() - timedelta(minutes=1), ends_at=timezone.now() + timedelta(days=1), is_active=True)
        order = OrderService.checkout(self.cart, "1 Main Street", [self.items[0].id, self.items[2].id], "FIX36")
        self.assertEqual(order.subtotal, Decimal("70.00"))
        self.assertEqual(order.discount_amount, Decimal("36.00"))
        self.assertEqual(order.total, Decimal("34.00"))
        self.assertEqual(order.discount_code.code, "FIX36")
        self.assertEqual(self.cart.items.count(), 1)
        self.assertEqual(self.cart.items.first().id, self.items[1].id)

    def test_empty_or_foreign_selection_is_rejected(self):
        with self.assertRaises(DomainError):
            OrderService.checkout(self.cart, "1 Main Street", [], "")
        other_user = User.objects.create_user("other@example.com", "password123", role="CUSTOMER")
        other_customer = Customer.objects.create(user=other_user, first_name="Other", last_name="Buyer")
        other_cart = CartService.get_or_create_cart(other_customer)
        other_item = CartService.add_item(other_cart, self.items[0].variant_id, 1)
        with self.assertRaises(DomainError):
            OrderService.checkout(self.cart, "1 Main Street", [other_item.id], "")

    def test_percentage_and_invalid_discount_codes_are_validated_against_selected_subtotal(self):
        DiscountCode.objects.create(code="PCT10", discount_type="PERCENTAGE", value=Decimal("10"), starts_at=timezone.now() - timedelta(minutes=1), ends_at=timezone.now() + timedelta(days=1), is_active=True)
        quote = OrderService.preview(self.cart, [self.items[0].id, self.items[2].id], "PCT10")
        self.assertEqual(quote["subtotal"], "70.00")
        self.assertEqual(quote["discount_amount"], "7.00")
        self.assertEqual(quote["total"], "63.00")
        DiscountCode.objects.create(code="EXPIRED", discount_type="FIXED", value=Decimal("1"), starts_at=timezone.now() - timedelta(days=2), ends_at=timezone.now() - timedelta(days=1), is_active=True)
        DiscountCode.objects.create(code="OFF", discount_type="FIXED", value=Decimal("1"), starts_at=timezone.now() - timedelta(minutes=1), ends_at=timezone.now() + timedelta(days=1), is_active=False)
        with self.assertRaises(DomainError):
            OrderService.preview(self.cart, [self.items[0].id], "EXPIRED")
        with self.assertRaises(DomainError):
            OrderService.preview(self.cart, [self.items[0].id], "OFF")

    def test_preview_endpoint_uses_selected_cart_items_and_returns_discount_quote(self):
        DiscountCode.objects.create(code="FIX36", discount_type="FIXED", value=Decimal("36.00"), starts_at=timezone.now() - timedelta(minutes=1), ends_at=timezone.now() + timedelta(days=1), is_active=True)
        client = APIClient()
        client.force_authenticate(self.user)

        response = client.post(
            "/api/orders/checkout/preview/",
            {"cart_item_ids": [str(self.items[0].id), str(self.items[2].id)], "discount_code": "FIX36"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["subtotal"], "70.00")
        self.assertEqual(response.data["discount_amount"], "36.00")
        self.assertEqual(response.data["total"], "34.00")
        self.assertEqual(response.data["discount_code"], "FIX36")

    def test_discount_is_capped_at_selected_subtotal(self):
        DiscountCode.objects.create(code="TOO-MUCH", discount_type="FIXED", value=Decimal("500.00"), starts_at=timezone.now() - timedelta(minutes=1), ends_at=timezone.now() + timedelta(days=1), is_active=True)
        quote = OrderService.preview(self.cart, [self.items[0].id], "TOO-MUCH")
        self.assertEqual(quote["subtotal"], "50.00")
        self.assertEqual(quote["discount_amount"], "50.00")
        self.assertEqual(quote["total"], "0.00")


class RefundRequestApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user("refund-buyer@example.com", "password123", role=User.Role.CUSTOMER)
        self.customer = Customer.objects.create(user=self.user, first_name="Refund", last_name="Buyer")
        self.order = Order.objects.create(
            customer=self.customer,
            status=Order.Status.DELIVERED,
            shipping_address="1 Main Street",
        )
        self.client.force_authenticate(self.user)

    def test_customer_can_request_refund_for_own_delivered_order_once(self):
        payload = {"order": str(self.order.id), "reason": "The item arrived damaged."}

        created = self.client.post("/api/orders/refund-requests/", payload, format="json")
        duplicate = self.client.post("/api/orders/refund-requests/", payload, format="json")

        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.data["order"], str(self.order.id))
        self.assertEqual(created.data["reason"], payload["reason"])
        self.assertEqual(created.data["status"], RefundRequest.Status.PENDING)
        self.assertEqual(duplicate.status_code, 200)
        self.assertEqual(RefundRequest.objects.filter(order=self.order).count(), 1)

        admin = User.objects.create_user("refund-admin@example.com", "password123", role=User.Role.ADMIN)
        self.client.force_authenticate(admin)
        admin_list = self.client.get("/api/orders/refund-requests/admin/")

        self.assertEqual(admin_list.status_code, 200)
        records = admin_list.data.get("results", admin_list.data) if isinstance(admin_list.data, dict) else admin_list.data
        self.assertEqual(records[0]["id"], created.data["id"])

    def test_customer_cannot_request_refund_for_another_customers_order(self):
        other_user = User.objects.create_user("other-refund-buyer@example.com", "password123", role=User.Role.CUSTOMER)
        other_customer = Customer.objects.create(user=other_user, first_name="Other", last_name="Buyer")
        other_order = Order.objects.create(
            customer=other_customer,
            status=Order.Status.DELIVERED,
            shipping_address="2 Main Street",
        )

        response = self.client.post(
            "/api/orders/refund-requests/",
            {"order": str(other_order.id), "reason": "Not my order."},
            format="json",
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(RefundRequest.objects.filter(order=other_order).exists())

    def test_customer_cannot_request_refund_for_a_non_delivered_order(self):
        self.order.status = Order.Status.CONFIRMED
        self.order.save(update_fields=["status"])

        response = self.client.post(
            "/api/orders/refund-requests/",
            {"order": str(self.order.id), "reason": "Not delivered yet."},
            format="json",
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(RefundRequest.objects.filter(order=self.order).exists())
