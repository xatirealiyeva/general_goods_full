from rest_framework import serializers
from .models import StockAdjustment
from apps.catalog.models import ProductVariant


class StockAdjustmentDTO(serializers.ModelSerializer):
    class Meta:
        model = StockAdjustment
        fields = ["id", "variant", "delta", "reason", "note", "created_at"]
        read_only_fields = ["id", "created_at"]


class CreateStockAdjustmentRequest(serializers.Serializer):
    variant = serializers.UUIDField()
    delta = serializers.IntegerField()
    reason = serializers.ChoiceField(choices=StockAdjustment.Reason.choices)
    note = serializers.CharField(required=False, allow_blank=True, max_length=255)


class AdminInventoryDTO(serializers.ModelSerializer):
    product_id = serializers.UUIDField(source="product.id", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_status = serializers.CharField(source="product.status", read_only=True)
    effective_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    in_stock = serializers.BooleanField(read_only=True)
    low_stock = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        fields = ["id", "product_id", "product_name", "product_status", "sku", "attributes", "stock_quantity", "effective_price", "in_stock", "low_stock"]

    def get_low_stock(self, obj):
        from .models import LOW_STOCK_THRESHOLD
        return obj.stock_quantity <= LOW_STOCK_THRESHOLD
