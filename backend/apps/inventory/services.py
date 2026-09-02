from django.db import transaction
from apps.shared.exceptions import DomainError
from apps.catalog.models import ProductVariant
from .models import StockAdjustment, LOW_STOCK_THRESHOLD, LowStockAlert
from django.core.mail import mail_admins
import logging
logger = logging.getLogger(__name__)


class InventoryService:
    @staticmethod
    @transaction.atomic
    def adjust_stock(variant, delta: int, reason: str, note: str = "") -> StockAdjustment:
        variant_id = variant
        variant = ProductVariant.objects.select_for_update().get(id=variant_id)
        new_quantity = variant.stock_quantity + delta
        if new_quantity < 0:
            raise DomainError("Stock adjustment would result in negative inventory.")
        variant.stock_quantity = new_quantity
        variant.save(update_fields=["stock_quantity"])
        if new_quantity < LOW_STOCK_THRESHOLD:
            alert, created = LowStockAlert.objects.get_or_create(variant=variant, acknowledged=False, defaults={"quantity": new_quantity})
            if created:
                try:
                    mail_admins("Low stock alert", f"SKU {variant.sku} is now at {new_quantity} units.", fail_silently=False)
                except Exception:
                    logger.exception("Low-stock notification delivery failed for %s", variant.sku)
        return StockAdjustment.objects.create(variant=variant, delta=delta, reason=reason, note=note)

    @staticmethod
    def low_stock_variants():
        return ProductVariant.objects.filter(stock_quantity__lte=LOW_STOCK_THRESHOLD, is_deleted=False)
