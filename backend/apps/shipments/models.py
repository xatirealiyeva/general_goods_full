import uuid
from django.db import models
from apps.shared.models import TimeStampedModel
from apps.orders.models import Order
from apps.sellers.models import Seller


class Shipment(TimeStampedModel):
    """Delivery record tracking the physical dispatch of an order (spec section 5)."""

    class Status(models.TextChoices):
        PREPARING = "PREPARING", "Preparing"
        DISPATCHED = "DISPATCHED", "Dispatched"
        IN_TRANSIT = "IN_TRANSIT", "In transit"
        DELIVERED = "DELIVERED", "Delivered"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="shipments")
    seller = models.ForeignKey(Seller, on_delete=models.PROTECT, related_name="shipments")
    carrier = models.CharField(max_length=100)
    tracking_number = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PREPARING)
    estimated_arrival = models.DateField(null=True, blank=True)
    shipping_zone = models.ForeignKey("ShippingZone", null=True, blank=True, on_delete=models.SET_NULL, related_name="shipments")

    class Meta:
        db_table = "shipments"
        ordering = ["-created_at"]

class ShippingZone(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    regions = models.JSONField(default=list, help_text="Cities or regions served by this zone.")
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2)
    estimated_days = models.PositiveIntegerField(default=3)
    is_active = models.BooleanField(default=True)
    class Meta: db_table = "shipping_zones"
