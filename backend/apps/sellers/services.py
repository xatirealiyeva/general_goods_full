from django.db import transaction
from apps.users.models import User
from .models import Seller


class SellerService:
    @staticmethod
    @transaction.atomic
    def create_seller(data: dict) -> Seller:
        user = User.objects.create_user(
            email=data["email"], password=data["password"], role=User.Role.SELLER
        )
        seller = Seller.objects.create(
            user=user,
            business_name=data["business_name"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            date_of_birth=data.get("date_of_birth"),
            phone_number=data.get("phone_number", ""),
            shipping_address=data.get("shipping_address", ""),
            billing_address=data.get("billing_address", ""),
        )
        return seller

    @staticmethod
    def set_status(seller: Seller, status: str) -> Seller:
        seller.status = status
        seller.user.is_active = status == Seller.Status.ACTIVE
        seller.user.save(update_fields=["is_active"])
        seller.save(update_fields=["status"])
        return seller
