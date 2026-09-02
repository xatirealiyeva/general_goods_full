from django.urls import path
from .views import AdminCreateSellerView, SellerListView, AdminUpdateSellerStatusView, MySellerProfileView

app_name = "sellers"

urlpatterns = [
    path("", SellerListView.as_view(), name="list"),
    path("create/", AdminCreateSellerView.as_view(), name="create"),
    path("me/", MySellerProfileView.as_view(), name="me"),
    path("<uuid:seller_id>/status/", AdminUpdateSellerStatusView.as_view(), name="update-status"),
]
