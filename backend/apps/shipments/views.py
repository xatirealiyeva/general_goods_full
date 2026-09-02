from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.shared.permissions import IsSeller, IsCustomer, IsAdmin
from apps.shared.pagination import DefaultPagination
from .models import Shipment, ShippingZone
from .serializers import ShipmentDTO, CreateShipmentRequest, UpdateShipmentStatusRequest, ShippingZoneDTO
from .services import ShipmentService


class SellerCreateShipmentView(APIView):
    permission_classes = [IsSeller]

    def post(self, request):
        serializer = CreateShipmentRequest(data=request.data)
        serializer.is_valid(raise_exception=True)
        shipment = ShipmentService.create_shipment(request.user.seller_profile, **serializer.validated_data)
        return Response(ShipmentDTO(shipment).data, status=201)


class SellerShipmentStatusView(APIView):
    permission_classes = [IsSeller]

    def patch(self, request, shipment_id):
        shipment = get_object_or_404(Shipment, id=shipment_id, seller=request.user.seller_profile)
        serializer = UpdateShipmentStatusRequest(data=request.data)
        serializer.is_valid(raise_exception=True)
        shipment = ShipmentService.update_status(shipment, serializer.validated_data["status"])
        return Response(ShipmentDTO(shipment).data)


class OrderShipmentsView(generics.ListAPIView):
    """Customer: track shipments for their own order (spec 4.3)."""
    serializer_class = ShipmentDTO
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = DefaultPagination

    def get_queryset(self):
        order_id = self.kwargs["order_id"]
        user = self.request.user
        qs = Shipment.objects.filter(order_id=order_id)
        if user.role == "CUSTOMER":
            qs = qs.filter(order__customer=user.customer_profile)
        elif user.role == "SELLER":
            qs = qs.filter(seller=user.seller_profile)
        return qs

class ShippingZoneView(generics.ListCreateAPIView):
    serializer_class=ShippingZoneDTO
    def get_permissions(self): return [IsAdmin()] if self.request.method == "POST" else [permissions.AllowAny()]
    queryset=ShippingZone.objects.filter(is_active=True)
