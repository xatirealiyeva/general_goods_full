from rest_framework import serializers
from .models import Cart, CartItem


class CartItemDTO(serializers.ModelSerializer):
    sku = serializers.CharField(source="variant.sku", read_only=True)
    product_name = serializers.CharField(source="variant.product.name", read_only=True)
    unit_price = serializers.DecimalField(source="variant.effective_price", max_digits=12, decimal_places=2, read_only=True)
    line_total = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ["id", "variant", "sku", "product_name", "unit_price", "quantity", "line_total"]
        read_only_fields = ["id", "sku", "product_name", "unit_price", "line_total"]

    def get_line_total(self, obj):
        return str(obj.variant.effective_price * obj.quantity)


class CartDTO(serializers.ModelSerializer):
    items = CartItemDTO(many=True, read_only=True)
    total = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ["id", "items", "total", "updated_at"]

    def get_total(self, obj):
        return str(sum((item.variant.effective_price * item.quantity for item in obj.items.all()), start=0))


class CreateCartItemRequest(serializers.Serializer):
    variant = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1, default=1)


class UpdateCartItemRequest(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)
