from django.contrib import admin
from .models import Customer, Store


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ["customer_number", "first_name", "last_name", "user"]
    search_fields = ["customer_number", "first_name", "last_name", "user__email"]


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ["name", "owner", "status", "created_at"]
    list_filter = ["status"]
    search_fields = ["name", "owner__user__email", "owner__first_name", "owner__last_name"]
