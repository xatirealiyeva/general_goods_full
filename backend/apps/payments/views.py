from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics

from apps.shared.permissions import IsAdmin, IsCustomer
from .models import Payment
from .serializers import PaymentDTO, CreatePaymentRequest
from .services import PaymentService


class CreatePaymentView(APIView):
    """Customer: pay for a PENDING order (spec 4.3, section 8/11)."""
    permission_classes = [IsCustomer]

    def post(self, request):
        serializer = CreatePaymentRequest(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = get_object_or_404(__import__("apps.orders.models", fromlist=["Order"]).Order, id=serializer.validated_data["order"], customer=request.user.customer_profile)
        payment = PaymentService.process_payment(order=order.id, provider=serializer.validated_data["provider"], provider_reference=serializer.validated_data["provider_reference"])
        return Response(PaymentDTO(payment).data, status=201)


class AdminPaymentListView(generics.ListAPIView):
    permission_classes = [IsAdmin]
    serializer_class = PaymentDTO
    queryset = Payment.objects.select_related("order__customer").order_by("-created_at")


class RefundPaymentView(APIView):
    """Admin: process a refund (spec 4.1: manage refunds)."""
    permission_classes = [IsAdmin]

    def post(self, request, payment_id):
        payment = get_object_or_404(Payment, id=payment_id)
        payment = PaymentService.refund(payment)
        return Response(PaymentDTO(payment).data)
