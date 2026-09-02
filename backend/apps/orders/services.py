from django.db import transaction

from apps.shared.exceptions import DomainError
from apps.cart.models import Cart
from apps.cart.services import CartService
from apps.inventory.services import InventoryService
from apps.inventory.models import StockAdjustment
from .models import Order, OrderItem
from apps.catalog.models import DiscountCode
from django.utils import timezone
from decimal import Decimal


class OrderService:
    @staticmethod
    def _selected_items(cart: Cart, cart_item_ids, lock=False):
        selected_ids = set(cart_item_ids)
        if not selected_ids:
            raise DomainError("Please select at least one product.")
        queryset = cart.items.select_related("variant", "variant__product").filter(id__in=selected_ids)
        if lock:
            queryset = queryset.select_for_update()
        items = list(queryset)
        if len(items) != len(selected_ids):
            raise DomainError("One or more selected cart items are no longer available.")
        return items

    @staticmethod
    def _quote(cart: Cart, cart_item_ids, discount_code: str = "", lock=False):
        items = OrderService._selected_items(cart, cart_item_ids, lock=lock)
        subtotal = Decimal("0")
        for cart_item in items:
            variant = cart_item.variant
            if variant.is_deleted or variant.product.is_deleted or variant.product.status != "ACTIVE":
                raise DomainError(f"Product '{variant.product.name}' is no longer available.")
            if variant.stock_quantity < cart_item.quantity:
                raise DomainError(f"'{variant.sku}' is out of stock or has insufficient quantity.")
            if not variant.product.seller_assignments.filter(is_active=True).exists():
                raise DomainError(f"Product '{variant.product.name}' has no active seller.")
            subtotal += variant.effective_price * cart_item.quantity

        discount = None
        discount_amount = Decimal("0")
        if discount_code:
            try:
                discount = DiscountCode.objects.get(code__iexact=discount_code.strip(), is_active=True)
            except DiscountCode.DoesNotExist:
                raise DomainError("Discount code is invalid or inactive.")
            now = timezone.now()
            if not (discount.starts_at <= now <= discount.ends_at):
                raise DomainError("Discount code has expired or is not active yet.")
            if discount.discount_type == DiscountCode.Type.PERCENTAGE:
                discount_amount = (subtotal * discount.value / Decimal("100")).quantize(Decimal("0.01"))
            else:
                discount_amount = discount.value
            discount_amount = min(discount_amount, subtotal)
        return items, subtotal, discount, discount_amount

    @staticmethod
    def preview(cart: Cart, cart_item_ids, discount_code: str = ""):
        _, subtotal, discount, discount_amount = OrderService._quote(cart, cart_item_ids, discount_code)
        return {
            "subtotal": str(subtotal),
            "discount_amount": str(discount_amount),
            "total": str(subtotal - discount_amount),
            "discount_code": discount.code if discount else None,
        }

    @staticmethod
    @transaction.atomic
    def checkout(cart: Cart, shipping_address: str, cart_item_ids, discount_code: str = "") -> Order:
        """
        Centralized order total calculation (spec section 8). Validates
        stock availability, decrements inventory, and snapshots pricing.
        """
        items, subtotal, discount, discount_amount = OrderService._quote(cart, cart_item_ids, discount_code, lock=True)

        order = Order.objects.create(
            customer=cart.customer,
            shipping_address=shipping_address,
            status=Order.Status.PENDING,
        )

        for cart_item in items:
            variant = cart_item.variant
            assignment = variant.product.seller_assignments.filter(is_active=True).order_by("-role").first()
            unit_price = variant.effective_price
            OrderItem.objects.create(
                order=order, variant=variant, seller=assignment.seller,
                quantity=cart_item.quantity, unit_price=unit_price,
            )
            InventoryService.adjust_stock(variant.id, -cart_item.quantity, StockAdjustment.Reason.SALE)
        order.subtotal = subtotal
        order.discount_code = discount
        order.discount_amount = discount_amount
        order.total = subtotal - discount_amount
        order.save(update_fields=["subtotal", "discount_code", "discount_amount", "total"])

        CartService.remove_items(cart, [item.id for item in items])
        return order

    @staticmethod
    def transition_status(order: Order, new_status: str) -> Order:
        if not order.can_transition_to(new_status):
            raise DomainError(f"Cannot transition order from {order.status} to {new_status}.")
        order.status = new_status
        order.save(update_fields=["status"])
        return order

    @staticmethod
    def cancel(order: Order) -> Order:
        return OrderService.transition_status(order, Order.Status.CANCELLED)
