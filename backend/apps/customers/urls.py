from django.urls import path
from .views import RegisterCustomerView, CustomerListView, AdminCreateCustomerView, MyCustomerProfileView, WishlistView, WishlistDeleteView, MyStoreView, StoreDashboardView, AdminStoreListView, AdminStoreDetailView, PublicStoreView

app_name = "customers"

urlpatterns = [
    path("register/", RegisterCustomerView.as_view(), name="register"),
    path("", CustomerListView.as_view(), name="list"),
    path("create/", AdminCreateCustomerView.as_view(), name="create"),
    path("me/", MyCustomerProfileView.as_view(), name="me"),
    path("wishlist/", WishlistView.as_view(), name="wishlist"),
    path("wishlist/<uuid:product_id>/", WishlistDeleteView.as_view(), name="wishlist-delete"),
    path("store/", MyStoreView.as_view(), name="my-store"),
    path("store/dashboard/", StoreDashboardView.as_view(), name="store-dashboard"),
    path("stores/admin/", AdminStoreListView.as_view(), name="admin-store-list"),
    path("stores/admin/<uuid:store_id>/", AdminStoreDetailView.as_view(), name="admin-store-detail"),
    path("stores/<uuid:store_id>/", PublicStoreView.as_view(), name="public-store"),
]
