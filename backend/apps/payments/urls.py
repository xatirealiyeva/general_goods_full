from django.urls import path
from .views import CreatePaymentView, RefundPaymentView, AdminPaymentListView

app_name = "payments"

urlpatterns = [
    path("", CreatePaymentView.as_view(), name="create"),
    path("admin/", AdminPaymentListView.as_view(), name="admin-list"),
    path("<uuid:payment_id>/refund/", RefundPaymentView.as_view(), name="refund"),
]
