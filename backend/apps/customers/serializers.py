from rest_framework import serializers
from django.utils import timezone
from apps.users.models import User
from apps.users.serializers import UserDTO
from .models import Customer, Store
from .models import WishlistItem
from apps.catalog.serializers import ProductListDTO


class CustomerDTO(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    age = serializers.IntegerField(read_only=True)

    class Meta:
        model = Customer
        fields = [
            "id", "customer_number", "email", "first_name", "last_name",
            "date_of_birth", "age", "phone_number", "shipping_address",
            "billing_address", "emergency_contact_name", "emergency_contact_phone",
            "created_at",
        ]
        read_only_fields = ["id", "customer_number", "email", "age", "created_at"]


class CreateCustomerRequest(serializers.Serializer):
    """DTO for admin- or self-registration of a customer account."""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    phone_number = serializers.CharField(max_length=32, required=False, allow_blank=True)
    shipping_address = serializers.CharField(required=False, allow_blank=True)
    billing_address = serializers.CharField(required=False, allow_blank=True)
    seller_access = serializers.BooleanField(required=False, default=False, write_only=True)

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_date_of_birth(self, value):
        if value and value >= timezone.now().date():
            raise serializers.ValidationError("Date of birth must be in the past.")
        return value


class UpdateCustomerRequest(serializers.Serializer):
    first_name = serializers.CharField(max_length=100, required=False)
    last_name = serializers.CharField(max_length=100, required=False)
    phone_number = serializers.CharField(max_length=32, required=False, allow_blank=True)
    shipping_address = serializers.CharField(required=False, allow_blank=True)
    billing_address = serializers.CharField(required=False, allow_blank=True)
    emergency_contact_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    emergency_contact_phone = serializers.CharField(max_length=32, required=False, allow_blank=True)


class WishlistItemDTO(serializers.ModelSerializer):
    product = ProductListDTO(read_only=True)
    class Meta:
        model = WishlistItem
        fields = ["id", "product", "created_at"]


class StoreDTO(serializers.ModelSerializer):
    owner_name = serializers.SerializerMethodField()
    owner_email = serializers.CharField(source="owner.user.email", read_only=True)
    product_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Store
        fields = ["id", "name", "description", "logo", "status", "owner_name", "owner_email", "product_count", "created_at"]
        read_only_fields = ["id", "created_at"]

    def get_owner_name(self, obj):
        return f"{obj.owner.first_name} {obj.owner.last_name}"


class StoreRequest(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, allow_blank=True)
    logo = serializers.ImageField(required=False)
    status = serializers.ChoiceField(choices=Store.Status.choices, required=False)
