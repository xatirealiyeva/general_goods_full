from django.db import transaction
from apps.users.models import User
from apps.sellers.models import Seller
from .models import Customer


class CustomerService:
    @staticmethod
    @transaction.atomic
    def register_customer(data: dict) -> Customer:
        user = User.objects.create_user(
            email=data["email"], password=data["password"], role=User.Role.CUSTOMER
        )
        customer = Customer.objects.create(
            user=user,
            first_name=data["first_name"],
            last_name=data["last_name"],
            date_of_birth=data.get("date_of_birth"),
            phone_number=data.get("phone_number", ""),
            shipping_address=data.get("shipping_address", ""),
            billing_address=data.get("billing_address", ""),
        )
        if data.get("seller_access"):
            Seller.objects.create(
                user=user,
                business_name=f"{customer.first_name} {customer.last_name}'s Store",
                first_name=customer.first_name,
                last_name=customer.last_name,
                phone_number=customer.phone_number,
                shipping_address=customer.shipping_address,
                billing_address=customer.billing_address,
                status=Seller.Status.ACTIVE,
            )
        return customer

    @staticmethod
    def update_customer(customer: Customer, data: dict) -> Customer:
        for field, value in data.items():
            setattr(customer, field, value)
        customer.save()
        return customer
