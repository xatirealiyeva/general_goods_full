from django.urls import path
from .views import CartView, CartItemView

app_name = "cart"

urlpatterns = [
    path("", CartView.as_view(), name="detail"),
    path("items/", CartItemView.as_view(), name="add-item"),
    path("items/<uuid:item_id>/", CartItemView.as_view(), name="item-detail"),
]
