import uuid
from django.conf import settings
from django.db import models
from apps.shared.models import TimeStampedModel
from apps.customers.models import Customer
from apps.catalog.models import ProductVariant


class Order(TimeStampedModel):
    """
    Confirmed purchase containing one or more products. Recorded per
    checkout session, not directly on the cart (spec section 8).
    """

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"
        SHIPPED = "SHIPPED", "Shipped"
        DELIVERED = "DELIVERED", "Delivered"
        CANCELLED = "CANCELLED", "Cancelled"
        REFUNDED = "REFUNDED", "Refunded"

    # Legal status transition graph enforced in services.py
    ALLOWED_TRANSITIONS = {
        Status.PENDING: {Status.CONFIRMED, Status.CANCELLED},
        Status.CONFIRMED: {Status.SHIPPED, Status.CANCELLED},
        Status.SHIPPED: {Status.DELIVERED},
        Status.DELIVERED: {Status.REFUNDED},
        Status.CANCELLED: set(),
        Status.REFUNDED: set(),
    }

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField(max_length=24, unique=True, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="orders")
    checkout_session_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_code = models.ForeignKey("catalog.DiscountCode", null=True, blank=True, on_delete=models.SET_NULL, related_name="orders")
    shipping_address = models.TextField()

    class Meta:
        db_table = "orders"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["customer", "-created_at"], name="orders_customer_created_idx"),
            models.Index(fields=["status", "-created_at"], name="orders_status_created_idx"),
        ]

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f"ORD-{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)

    def can_transition_to(self, new_status: str) -> bool:
        return new_status in self.ALLOWED_TRANSITIONS.get(self.status, set())

    def __str__(self):
        return self.order_number


class OrderItem(TimeStampedModel):
    """Explicit link between an order and a product variant (spec section 5)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT, related_name="order_items")
    seller = models.ForeignKey("sellers.Seller", on_delete=models.PROTECT, related_name="order_items")
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = "order_items"

    @property
    def line_total(self):
        return self.unit_price * self.quantity


class RefundRequest(TimeStampedModel):
    class Status(models.TextChoices): PENDING="PENDING", "Pending"; APPROVED="APPROVED", "Approved"; REJECTED="REJECTED", "Rejected"
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="refund_requests")
    reason = models.TextField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    class Meta: db_table = "refund_requests"


class Dispute(TimeStampedModel):
    class Status(models.TextChoices): OPEN="OPEN", "Open"; RESOLVED="RESOLVED", "Resolved"; REJECTED="REJECTED", "Rejected"
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="disputes")
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="disputes")
    subject = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.OPEN)
    resolution = models.TextField(blank=True)
    class Meta: db_table = "disputes"
