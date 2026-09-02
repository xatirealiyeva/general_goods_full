from django.urls import path
from .views import ProductReviewListView, SubmitReviewView, AdminModerateReviewView, AdminReviewListView

app_name = "reviews"

urlpatterns = [
    path("", SubmitReviewView.as_view(), name="submit"),
    path("admin/", AdminReviewListView.as_view(), name="admin-list"),
    path("product/<uuid:product_id>/", ProductReviewListView.as_view(), name="by-product"),
    path("<uuid:review_id>/moderate/", AdminModerateReviewView.as_view(), name="moderate"),
]
