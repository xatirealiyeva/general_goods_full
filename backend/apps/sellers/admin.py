from django.contrib import admin
from .models import Seller


@admin.register(Seller)
class SellerAdmin(admin.ModelAdmin):
    list_display = ["seller_registration_number", "business_name", "status", "user"]
    search_fields = ["seller_registration_number", "business_name", "user__email"]
