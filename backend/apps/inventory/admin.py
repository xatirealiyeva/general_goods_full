from django.contrib import admin
from .models import StockAdjustment


@admin.register(StockAdjustment)
class StockAdjustmentAdmin(admin.ModelAdmin):
    list_display = ["variant", "delta", "reason", "created_at"]
    list_filter = ["reason"]
