from django.urls import path
from .views import UserListView, MeView, AdminUpdateUserStatusView

app_name = "users"

urlpatterns = [
    path("", UserListView.as_view(), name="list"),
    path("me/", MeView.as_view(), name="me"),
    path("<int:user_id>/status/", AdminUpdateUserStatusView.as_view(), name="update-status"),
]
