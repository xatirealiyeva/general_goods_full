from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.shared.permissions import IsAdmin
from apps.shared.pagination import DefaultPagination
from .models import User
from .serializers import UserDTO, AdminUpdateUserStatusRequest
from .services import UserService


class UserListView(generics.ListAPIView):
    """Admin: list/search all user accounts."""
    serializer_class = UserDTO
    permission_classes = [IsAdmin]
    pagination_class = DefaultPagination
    queryset = User.objects.all().order_by("-created_at")
    filterset_fields = ["role", "account_status"]


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserDTO(request.user).data)


class AdminUpdateUserStatusView(APIView):
    permission_classes = [IsAdmin]

    def patch(self, request, user_id):
        serializer = AdminUpdateUserStatusRequest(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = UserService.update_user(user_id, serializer.validated_data)
        return Response(UserDTO(user).data)
