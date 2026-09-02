from rest_framework import serializers
from django.utils import timezone
from apps.users.models import User
from .models import Seller


class SellerDTO(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Seller
        fields = [
            "id", "seller_registration_number", "email", "business_name",
            "first_name", "last_name", "date_of_birth", "phone_number",
            "shipping_address", "billing_address", "status", "created_at",
        ]
        read_only_fields = ["id", "seller_registration_number", "email", "status", "created_at"]


class CreateSellerRequest(serializers.Serializer):
    """Admin-only: create a seller account."""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    business_name = serializers.CharField(max_length=200)
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    phone_number = serializers.CharField(max_length=32, required=False, allow_blank=True)
    shipping_address = serializers.CharField(required=False, allow_blank=True)
    billing_address = serializers.CharField(required=False, allow_blank=True)

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_date_of_birth(self, value):
        if value and value >= timezone.now().date():
            raise serializers.ValidationError("Date of birth must be in the past.")
        return value


class UpdateSellerStatusRequest(serializers.Serializer):
    status = serializers.ChoiceField(choices=Seller.Status.choices)
