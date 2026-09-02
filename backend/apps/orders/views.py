from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.shared.permissions import IsAdmin, IsCustomer, IsSeller
from apps.shared.pagination import DefaultPagination
from apps.cart.services import CartService
from .models import Order, RefundRequest, Dispute
from .serializers import CheckoutSelectionRequest, OrderDTO, CreateOrderRequest, UpdateOrderStatusRequest, RefundRequestDTO, DisputeDTO, CreateRefundRequest, CreateDisputeRequest, ResolveDisputeRequest, ReviewRefundRequest
from django.db.models import Sum, F, DecimalField, ExpressionWrapper
from .services import OrderService


class CheckoutView(APIView):
    """Customer: place an order from their current cart (spec 4.3)."""
    permission_classes = [IsCustomer]

    def post(self, request):
        serializer = CreateOrderRequest(data=request.data)
        serializer.is_valid(raise_exception=True)
        cart = CartService.get_or_create_cart(request.user.customer_profile)
        order = OrderService.checkout(cart, serializer.validated_data["shipping_address"], serializer.validated_data["cart_item_ids"], serializer.validated_data.get("discount_code", ""))
        return Response(OrderDTO(order).data, status=201)


class CheckoutPreviewView(APIView):
    """Server-calculated selection total and discount before order creation."""
    permission_classes = [IsCustomer]

    def post(self, request):
        serializer = CheckoutSelectionRequest(data=request.data)
        serializer.is_valid(raise_exception=True)
        cart = CartService.get_or_create_cart(request.user.customer_profile)
        return Response(OrderService.preview(cart, serializer.validated_data["cart_item_ids"], serializer.validated_data.get("discount_code", "")))


class MyOrdersView(generics.ListAPIView):
    """Customer: own order history (spec 4.3)."""
    serializer_class = OrderDTO
    permission_classes = [IsCustomer]
    pagination_class = DefaultPagination

    def get_queryset(self):
        return Order.objects.filter(customer=self.request.user.customer_profile).select_related("customer").prefetch_related("items__variant__product", "items__seller")


class SellerOrdersView(generics.ListAPIView):
    """Seller: own order queue — orders containing at least one of their items (spec 4.2)."""
    serializer_class = OrderDTO
    permission_classes = [IsSeller]
    pagination_class = DefaultPagination

    def get_queryset(self):
        seller = self.request.user.seller_profile
        return Order.objects.filter(items__seller=seller).distinct().select_related("customer").prefetch_related("items__variant__product", "items__seller")


class AdminOrdersView(generics.ListAPIView):
    """Admin: review all orders (spec 4.1)."""
    serializer_class = OrderDTO
    permission_classes = [IsAdmin]
    pagination_class = DefaultPagination
    queryset = Order.objects.all().select_related("customer").prefetch_related("items__variant__product", "items__seller")
    filterset_fields = ["status"]


class OrderDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, order_id):
        order = get_object_or_404(Order.objects.select_related("customer").prefetch_related("items__variant__product", "items__seller"), id=order_id)
        user = request.user
        if user.role == "CUSTOMER" and order.customer_id != getattr(user.customer_profile, "id", None):
            return Response({"error": {"message": "Not permitted."}}, status=403)
        if user.role == "SELLER":
            seller = getattr(user, "seller_profile", None)
            if not seller or not order.items.filter(seller=seller).exists():
                return Response({"error": {"message": "Not permitted."}}, status=403)
        return Response(OrderDTO(order).data)


class OrderStatusUpdateView(APIView):
    """Admin: transition order status (confirm, ship, cancel, refund)."""
    permission_classes = [IsAdmin]

    def patch(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)
        serializer = UpdateOrderStatusRequest(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = OrderService.transition_status(order, serializer.validated_data["status"])
        return Response(OrderDTO(order).data)


class OrderCancelView(APIView):
    """Customer: cancel their own pending order."""
    permission_classes = [IsCustomer]

    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id, customer=request.user.customer_profile)
        order = OrderService.cancel(order)
        return Response(OrderDTO(order).data)

class RefundRequestView(APIView):
    permission_classes = [IsCustomer]
    def post(self, request):
        s = CreateRefundRequest(data=request.data); s.is_valid(raise_exception=True)
        order = get_object_or_404(Order, id=s.validated_data["order"], customer=request.user.customer_profile, status=Order.Status.DELIVERED)
        refund, created = RefundRequest.objects.get_or_create(order=order, defaults={"reason": s.validated_data["reason"]})
        return Response(RefundRequestDTO(refund).data, status=201 if created else 200)

class AdminRefundRequestsView(generics.ListAPIView):
    permission_classes=[IsAdmin]; serializer_class=RefundRequestDTO; queryset=RefundRequest.objects.all()

class AdminRefundRequestDetailView(APIView):
    permission_classes = [IsAdmin]
    def patch(self, request, refund_id):
        refund = get_object_or_404(RefundRequest, id=refund_id)
        serializer = ReviewRefundRequest(data=request.data); serializer.is_valid(raise_exception=True)
        if refund.status != RefundRequest.Status.PENDING:
            return Response({"error": {"message": "Only pending refund requests can be reviewed."}}, status=400)
        status = serializer.validated_data["status"]
        if status == RefundRequest.Status.APPROVED:
            if refund.order.status != Order.Status.DELIVERED:
                return Response({"error": {"message": "Only delivered orders can be approved for refund."}}, status=400)
            OrderService.transition_status(refund.order, Order.Status.REFUNDED)
        refund.status = status; refund.reviewed_by = request.user; refund.save(update_fields=["status", "reviewed_by"])
        return Response(RefundRequestDTO(refund).data)

class DisputeView(APIView):
    permission_classes=[IsCustomer]
    def post(self, request):
        s=CreateDisputeRequest(data=request.data); s.is_valid(raise_exception=True)
        order=get_object_or_404(Order,id=s.validated_data["order"],customer=request.user.customer_profile)
        dispute=Dispute.objects.create(order=order,customer=request.user.customer_profile,subject=s.validated_data["subject"],description=s.validated_data["description"])
        return Response(DisputeDTO(dispute).data,status=201)

class AdminDisputeView(APIView):
    permission_classes=[IsAdmin]
    def get(self,request): return Response(DisputeDTO(Dispute.objects.all(),many=True).data)
    def patch(self,request,dispute_id):
        s=ResolveDisputeRequest(data=request.data); s.is_valid(raise_exception=True); dispute=get_object_or_404(Dispute,id=dispute_id)
        dispute.status=s.validated_data["status"]; dispute.resolution=s.validated_data["resolution"]; dispute.save(update_fields=["status","resolution"]); return Response(DisputeDTO(dispute).data)

class SellerAnalyticsView(APIView):
    permission_classes=[IsSeller]
    def get(self,request):
        seller=request.user.seller_profile; items=Order.objects.filter(items__seller=seller).exclude(status=Order.Status.CANCELLED)
        revenue=items.aggregate(value=Sum(ExpressionWrapper(F("items__unit_price") * F("items__quantity"), output_field=DecimalField(max_digits=12, decimal_places=2))))["value"] or 0
        customers=items.values("customer").distinct().count()
        return Response({"orders": items.distinct().count(), "customers": customers, "revenue": revenue})

class SellerCustomersView(APIView):
    permission_classes=[IsSeller]
    def get(self,request):
        customers=__import__('apps.customers.models',fromlist=['Customer']).Customer.objects.filter(orders__items__seller=request.user.seller_profile).distinct()
        from apps.customers.serializers import CustomerDTO
        return Response(CustomerDTO(customers,many=True).data)
