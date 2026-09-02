from django.contrib import admin
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["product", "customer", "rating", "moderation_status", "created_at"]
    search_fields = ["product__name", "customer__user__email"]
    list_filter = ["moderation_status", "rating"]
