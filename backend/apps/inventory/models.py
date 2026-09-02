import uuid
from django.db import models
from apps.shared.models import TimeStampedModel
from apps.catalog.models import ProductVariant


class StockAdjustment(TimeStampedModel):
    """Audit trail of inventory changes (spec 4.1: manage inventory levels)."""

    class Reason(models.TextChoices):
        RESTOCK = "RESTOCK", "Restock"
        SALE = "SALE", "Sale"
        RETURN = "RETURN", "Return"
        DAMAGE = "DAMAGE", "Damage / write-off"
        CORRECTION = "CORRECTION", "Manual correction"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name="stock_adjustments")
    delta = models.IntegerField(help_text="Positive to add stock, negative to remove.")
    reason = models.CharField(max_length=16, choices=Reason.choices)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "stock_adjustments"
        ordering = ["-created_at"]


LOW_STOCK_THRESHOLD = 5

class LowStockAlert(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name="low_stock_alerts")
    quantity = models.PositiveIntegerField()
    acknowledged = models.BooleanField(default=False)
    class Meta: db_table = "low_stock_alerts"
