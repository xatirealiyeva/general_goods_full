from rest_framework import serializers
from .models import Payment


class PaymentDTO(serializers.ModelSerializer):
    order_number = serializers.CharField(source="order.order_number", read_only=True)
    buyer = serializers.SerializerMethodField()
    class Meta:
        model = Payment
        fields = ["id", "order", "order_number", "buyer", "provider", "provider_reference", "amount", "status", "created_at"]
        read_only_fields = fields

    def get_buyer(self, obj):
        return f"{obj.order.customer.first_name} {obj.order.customer.last_name}"


class CreatePaymentRequest(serializers.Serializer):
    """
    Client submits a provider + a pre-tokenized reference (obtained from
    Stripe.js/PayPal SDK on the frontend) — raw card data never touches
    this backend, satisfying the 'no raw card storage' requirement.
    """
    order = serializers.UUIDField()
    provider = serializers.ChoiceField(choices=Payment.Provider.choices)
    provider_reference = serializers.CharField(max_length=255)
