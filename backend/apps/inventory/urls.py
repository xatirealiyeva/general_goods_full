from django.urls import path
from .views import AdminInventoryListView, StockAdjustmentView, LowStockAlertView, SellerStockAdjustmentView, SellerLowStockView

app_name = "inventory"

urlpatterns = [
    path("", AdminInventoryListView.as_view(), name="admin-inventory-list"),
    path("adjustments/", StockAdjustmentView.as_view(), name="adjustments"),
    path("low-stock/", LowStockAlertView.as_view(), name="low-stock"),
    path("seller/", SellerStockAdjustmentView.as_view(), name="seller-inventory"),
    path("seller/low-stock/", SellerLowStockView.as_view(), name="seller-low-stock"),
]
