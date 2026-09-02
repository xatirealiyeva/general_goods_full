from django.urls import path
from .views import SellerCreateShipmentView, SellerShipmentStatusView, OrderShipmentsView, ShippingZoneView

app_name = "shipments"

urlpatterns = [
    path("", SellerCreateShipmentView.as_view(), name="create"),
    path("<uuid:shipment_id>/status/", SellerShipmentStatusView.as_view(), name="status"),
    path("order/<uuid:order_id>/", OrderShipmentsView.as_view(), name="by-order"),
    path("zones/", ShippingZoneView.as_view(), name="zones"),
]
