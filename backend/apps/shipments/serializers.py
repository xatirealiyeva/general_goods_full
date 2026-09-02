from rest_framework import serializers
from .models import Shipment, ShippingZone


class ShipmentDTO(serializers.ModelSerializer):
    seller_name = serializers.CharField(source="seller.business_name", read_only=True)

    class Meta:
        model = Shipment
        fields = ["id", "order", "seller", "seller_name", "carrier", "tracking_number", "status", "estimated_arrival", "created_at"]
        read_only_fields = ["id", "seller_name", "created_at"]


class CreateShipmentRequest(serializers.Serializer):
    """Seller: create a shipment record only for orders belonging to their products (spec 4.2)."""
    order = serializers.UUIDField()
    carrier = serializers.CharField(max_length=100)
    tracking_number = serializers.CharField(max_length=100)
    estimated_arrival = serializers.DateField(required=False, allow_null=True)


class UpdateShipmentStatusRequest(serializers.Serializer):
    status = serializers.ChoiceField(choices=Shipment.Status.choices)

class ShippingZoneDTO(serializers.ModelSerializer):
    class Meta: model=ShippingZone; fields=["id","name","regions","delivery_fee","estimated_days","is_active"]
