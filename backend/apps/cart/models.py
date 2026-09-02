import uuid
from django.conf import settings
from django.db import models
from apps.shared.models import TimeStampedModel
from apps.catalog.models import ProductVariant


class Cart(TimeStampedModel):
    """
    Temporary holding area for items before checkout (spec section 5).
    Persisted in Postgres for durability; hot reads/writes go through the
    Redis cache layer in services.py (spec: 'Cart storage' in Redis).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.OneToOneField("customers.Customer", on_delete=models.CASCADE, related_name="cart")

    class Meta:
        db_table = "carts"


class CartItem(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name="cart_items")
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = "cart_items"
        unique_together = [("cart", "variant")]
