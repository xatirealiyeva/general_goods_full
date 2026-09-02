from django.urls import path
from .views import (
    CheckoutView, CheckoutPreviewView, MyOrdersView, SellerOrdersView, AdminOrdersView,
    OrderDetailView, OrderStatusUpdateView, OrderCancelView, RefundRequestView, AdminRefundRequestsView, AdminRefundRequestDetailView, DisputeView, AdminDisputeView, SellerAnalyticsView, SellerCustomersView,
)

app_name = "orders"

urlpatterns = [
    path("checkout/", CheckoutView.as_view(), name="checkout"),
    path("checkout/preview/", CheckoutPreviewView.as_view(), name="checkout-preview"),
    path("mine/", MyOrdersView.as_view(), name="mine"),
    path("seller/", SellerOrdersView.as_view(), name="seller"),
    path("admin/", AdminOrdersView.as_view(), name="admin"),
    path("<uuid:order_id>/", OrderDetailView.as_view(), name="detail"),
    path("<uuid:order_id>/status/", OrderStatusUpdateView.as_view(), name="status"),
    path("<uuid:order_id>/cancel/", OrderCancelView.as_view(), name="cancel"),
    path("refund-requests/", RefundRequestView.as_view(), name="refund-request"),
    path("refund-requests/admin/", AdminRefundRequestsView.as_view(), name="admin-refunds"),
    path("refund-requests/<uuid:refund_id>/", AdminRefundRequestDetailView.as_view(), name="admin-refund-detail"),
    path("disputes/", DisputeView.as_view(), name="dispute"),
    path("disputes/admin/", AdminDisputeView.as_view(), name="admin-disputes"),
    path("disputes/<uuid:dispute_id>/", AdminDisputeView.as_view(), name="resolve-dispute"),
    path("seller/analytics/", SellerAnalyticsView.as_view(), name="seller-analytics"),
    path("seller/customers/", SellerCustomersView.as_view(), name="seller-customers"),
]
