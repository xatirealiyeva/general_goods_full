from rest_framework import serializers
from .models import Order, OrderItem, RefundRequest, Dispute


class OrderItemDTO(serializers.ModelSerializer):
    sku = serializers.CharField(source="variant.sku", read_only=True)
    product_name = serializers.CharField(source="variant.product.name", read_only=True)
    seller_name = serializers.CharField(source="seller.business_name", read_only=True)
    line_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "variant", "sku", "product_name", "seller", "seller_name", "quantity", "unit_price", "line_total"]
        read_only_fields = fields


class OrderDTO(serializers.ModelSerializer):
    items = OrderItemDTO(many=True, read_only=True)
    customer_name = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id", "order_number", "customer", "customer_name", "status",
            "subtotal", "total", "shipping_address", "items", "created_at",
            "discount_amount", "discount_code",
        ]
        read_only_fields = ["id", "order_number", "customer", "status", "subtotal", "total", "created_at"]

    def get_customer_name(self, obj):
        return f"{obj.customer.first_name} {obj.customer.last_name}"


class CheckoutSelectionRequest(serializers.Serializer):
    """A customer-owned subset of cart rows; prices remain server calculated."""
    cart_item_ids = serializers.ListField(child=serializers.UUIDField(), min_length=1)
    discount_code = serializers.CharField(max_length=50, required=False, allow_blank=True)

    def validate_cart_item_ids(self, value):
        if len(value) != len(set(value)):
            raise serializers.ValidationError("Each cart item may be selected only once.")
        return value


class CreateOrderRequest(CheckoutSelectionRequest):
    """Checkout: convert selected items from the customer's cart into an order."""
    shipping_address = serializers.CharField()


class UpdateOrderStatusRequest(serializers.Serializer):
    status = serializers.ChoiceField(choices=Order.Status.choices)

class RefundRequestDTO(serializers.ModelSerializer):
    class Meta: model = RefundRequest; fields = ["id", "order", "reason", "status", "reviewed_by", "created_at"]

class DisputeDTO(serializers.ModelSerializer):
    class Meta: model = Dispute; fields = ["id", "order", "customer", "subject", "description", "status", "resolution", "created_at"]

class CreateRefundRequest(serializers.Serializer):
    order = serializers.UUIDField(); reason = serializers.CharField()
class CreateDisputeRequest(serializers.Serializer):
    order = serializers.UUIDField(); subject = serializers.CharField(max_length=200); description = serializers.CharField()
class ResolveDisputeRequest(serializers.Serializer):
    status = serializers.ChoiceField(choices=[Dispute.Status.RESOLVED, Dispute.Status.REJECTED]); resolution = serializers.CharField()

class ReviewRefundRequest(serializers.Serializer):
    status = serializers.ChoiceField(choices=[RefundRequest.Status.APPROVED, RefundRequest.Status.REJECTED])
