from django.contrib import admin
from .models import Shipment


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ["tracking_number", "order", "seller", "status", "estimated_arrival"]
    list_filter = ["status"]
