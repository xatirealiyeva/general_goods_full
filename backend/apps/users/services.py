from django.db import transaction

from apps.shared.exceptions import DomainError
from apps.sellers.models import Seller
from .models import User


class UserService:
    @staticmethod
    @transaction.atomic
    def update_user(user_id: str, data: dict) -> User:
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise DomainError("User not found.", code="not_found", http_status=404)
        fields = []
        if "account_status" in data:
            user.account_status = data["account_status"]
            user.is_active = data["account_status"] == User.Status.ACTIVE
            fields.extend(["account_status", "is_active"])
        if "role" in data:
            if data["role"] == User.Role.SELLER and user.role != User.Role.SELLER and not hasattr(user, "seller_profile"):
                customer = getattr(user, "customer_profile", None)
                if customer is None:
                    raise DomainError("A customer profile is required before this account can become a seller.", code="seller_profile_required", http_status=400)
                Seller.objects.create(
                    user=user,
                    business_name=f"{customer.first_name} {customer.last_name}'s Store",
                    first_name=customer.first_name,
                    last_name=customer.last_name,
                    date_of_birth=customer.date_of_birth,
                    phone_number=customer.phone_number,
                    shipping_address=customer.shipping_address,
                    billing_address=customer.billing_address,
                )
            user.role = data["role"]
            fields.append("role")
        user.save(update_fields=fields)
        return user

    @staticmethod
    def set_account_status(user_id: str, new_status: str) -> User:
        return UserService.update_user(user_id, {"account_status": new_status})
