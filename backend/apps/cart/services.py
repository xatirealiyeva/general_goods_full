from django.core.cache import cache
from django.db import transaction

from apps.shared.exceptions import DomainError
from apps.catalog.models import ProductVariant
from .models import Cart, CartItem

CART_CACHE_KEY = "cart:{customer_id}"
CART_CACHE_TTL = 60 * 30  # 30 minutes


class CartCacheService:
    """
    Redis is used as a fast read cache for cart contents (spec: 'Cart
    storage' under REDIS REQUIREMENTS). Postgres remains the source of
    truth so carts survive cache eviction/restarts.
    """

    @staticmethod
    def invalidate(customer_id):
        cache.delete(CART_CACHE_KEY.format(customer_id=customer_id))

    @staticmethod
    def get(customer_id):
        return cache.get(CART_CACHE_KEY.format(customer_id=customer_id))

    @staticmethod
    def set(customer_id, data):
        cache.set(CART_CACHE_KEY.format(customer_id=customer_id), data, CART_CACHE_TTL)


class CartService:
    @staticmethod
    def get_or_create_cart(customer) -> Cart:
        cart, _ = Cart.objects.get_or_create(customer=customer)
        return cart

    @staticmethod
    @transaction.atomic
    def add_item(cart: Cart, variant, quantity: int) -> CartItem:
        variant_id = variant
        try:
            variant = ProductVariant.objects.select_for_update().get(id=variant_id, is_deleted=False)
        except ProductVariant.DoesNotExist:
            raise DomainError("Product variant not found.", code="not_found", http_status=404)
        if variant.stock_quantity < quantity:
            raise DomainError("Cannot add more items than are in stock.")
        item, created = CartItem.objects.get_or_create(cart=cart, variant=variant, defaults={"quantity": quantity})
        if not created:
            item.quantity += quantity
            item.save(update_fields=["quantity"])
        CartCacheService.invalidate(cart.customer_id)
        return item

    @staticmethod
    def update_item(cart: Cart, item_id, quantity: int) -> CartItem:
        try:
            item = CartItem.objects.select_related("variant").get(id=item_id, cart=cart)
        except CartItem.DoesNotExist:
            raise DomainError("Cart item not found.", code="not_found", http_status=404)
        if item.variant.stock_quantity < quantity:
            raise DomainError("Cannot set quantity above available stock.")
        item.quantity = quantity
        item.save(update_fields=["quantity"])
        CartCacheService.invalidate(cart.customer_id)
        return item

    @staticmethod
    def remove_item(cart: Cart, item_id):
        deleted, _ = CartItem.objects.filter(id=item_id, cart=cart).delete()
        if not deleted:
            raise DomainError("Cart item not found.", code="not_found", http_status=404)
        CartCacheService.invalidate(cart.customer_id)

    @staticmethod
    def clear(cart: Cart):
        cart.items.all().delete()
        CartCacheService.invalidate(cart.customer_id)

    @staticmethod
    def remove_items(cart: Cart, item_ids):
        """Remove only successfully checked-out rows from this customer's cart."""
        CartItem.objects.filter(cart=cart, id__in=item_ids).delete()
        CartCacheService.invalidate(cart.customer_id)
