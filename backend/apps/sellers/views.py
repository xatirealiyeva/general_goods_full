from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.shared.permissions import IsAdmin
from apps.shared.pagination import DefaultPagination
from .models import Seller
from .serializers import SellerDTO, CreateSellerRequest, UpdateSellerStatusRequest
from .services import SellerService


class AdminCreateSellerView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        serializer = CreateSellerRequest(data=request.data)
        serializer.is_valid(raise_exception=True)
        seller = SellerService.create_seller(serializer.validated_data)
        return Response(SellerDTO(seller).data, status=201)


class SellerListView(generics.ListAPIView):
    serializer_class = SellerDTO
    permission_classes = [permissions.AllowAny]
    pagination_class = DefaultPagination
    def get_queryset(self):
        queryset = Seller.objects.order_by("business_name")
        if self.request.user.is_authenticated and self.request.user.role == "ADMIN":
            return queryset
        return queryset.filter(status=Seller.Status.ACTIVE)


class AdminUpdateSellerStatusView(APIView):
    permission_classes = [IsAdmin]

    def patch(self, request, seller_id):
        seller = get_object_or_404(Seller, id=seller_id)
        serializer = UpdateSellerStatusRequest(data=request.data)
        serializer.is_valid(raise_exception=True)
        seller = SellerService.set_status(seller, serializer.validated_data["status"])
        return Response(SellerDTO(seller).data)


class MySellerProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile = getattr(request.user, "seller_profile", None)
        if profile is None:
            return Response({"error": {"message": "No seller profile for this account."}}, status=404)
        return Response(SellerDTO(profile).data)
