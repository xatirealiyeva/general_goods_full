from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.shared.permissions import IsAdmin
from apps.shared.pagination import DefaultPagination
from .models import Customer, WishlistItem, Store
from .serializers import CustomerDTO, CreateCustomerRequest, UpdateCustomerRequest, WishlistItemDTO, StoreDTO, StoreRequest
from apps.shared.permissions import IsCustomer
from apps.catalog.models import Product
from apps.catalog.services import ProductService
from apps.catalog.serializers import ProductListDTO
from django.shortcuts import get_object_or_404
from django.db.models import Sum, F, DecimalField, ExpressionWrapper, Count
from .services import CustomerService


class RegisterCustomerView(APIView):
    """Public self-registration endpoint (spec: Auth -> optional customer registration)."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = CreateCustomerRequest(data=request.data)
        serializer.is_valid(raise_exception=True)
        customer = CustomerService.register_customer(serializer.validated_data)
        return Response(CustomerDTO(customer).data, status=201)


class CustomerListView(generics.ListAPIView):
    """Admin: list all customers."""
    serializer_class = CustomerDTO
    permission_classes = [IsAdmin]
    pagination_class = DefaultPagination
    queryset = Customer.objects.select_related("user").order_by("-created_at")


class AdminCreateCustomerView(APIView):
    """Admin account creation uses the same validated service as registration."""
    permission_classes = [IsAdmin]

    def post(self, request):
        serializer = CreateCustomerRequest(data=request.data)
        serializer.is_valid(raise_exception=True)
        customer = CustomerService.register_customer(serializer.validated_data)
        return Response(CustomerDTO(customer).data, status=201)


class AdminStoreListView(generics.ListAPIView):
    serializer_class = StoreDTO
    permission_classes = [IsAdmin]
    pagination_class = DefaultPagination
    queryset = Store.objects.select_related("owner__user").annotate(product_count=Count("products")).order_by("-created_at")


class AdminStoreDetailView(APIView):
    permission_classes = [IsAdmin]

    def delete(self, request, store_id):
        store = get_object_or_404(Store.objects.select_related("owner"), id=store_id)
        # Preserve order/payment history: listings are archived, not deleted.
        for product in store.products.all():
            ProductService.archive_product(product)
        store.status = Store.Status.ARCHIVED
        store.save(update_fields=["status"])
        return Response(status=204)


class PublicStoreView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, store_id):
        store = get_object_or_404(Store.objects.select_related("owner"), id=store_id)
        if store.status == Store.Status.ARCHIVED:
            return Response({"error": {"message": "Store not found."}}, status=404)
        products = Product.objects.filter(store=store, status=Product.Status.ACTIVE).select_related("category", "store").prefetch_related("images", "variants")
        return Response({"store": StoreDTO(store).data, "products": ProductListDTO(products, many=True).data})


class MyCustomerProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile = getattr(request.user, "customer_profile", None)
        if profile is None:
            return Response({"error": {"message": "No customer profile for this account."}}, status=404)
        return Response(CustomerDTO(profile).data)


class WishlistView(generics.ListCreateAPIView):
    permission_classes = [IsCustomer]
    serializer_class = WishlistItemDTO
    def get_queryset(self): return WishlistItem.objects.filter(customer=self.request.user.customer_profile).select_related("product", "product__category").order_by("-created_at", "-id")
    def post(self, request, *args, **kwargs):
        product = get_object_or_404(Product, id=request.data.get("product"), status=Product.Status.ACTIVE)
        item, created = WishlistItem.objects.get_or_create(customer=request.user.customer_profile, product=product)
        return Response(WishlistItemDTO(item).data, status=201 if created else 200)


class WishlistDeleteView(APIView):
    permission_classes = [IsCustomer]
    def delete(self, request, product_id):
        WishlistItem.objects.filter(customer=request.user.customer_profile, product_id=product_id).delete()
        return Response(status=204)


class MyStoreView(APIView):
    permission_classes = [IsCustomer]

    def get(self, request):
        store = getattr(request.user.customer_profile, "store", None)
        if store is None:
            return Response({"error": {"message": "Create a store to manage products."}}, status=404)
        return Response(StoreDTO(store).data)

    def post(self, request):
        if hasattr(request.user.customer_profile, "store"):
            return Response({"error": {"message": "You already have a store."}}, status=400)
        serializer = StoreRequest(data=request.data)
        serializer.is_valid(raise_exception=True)
        from apps.sellers.models import Seller
        customer = request.user.customer_profile
        seller = getattr(request.user, "seller_profile", None)
        # A customer-owned store still needs a seller record for fulfilment.
        # Create that internal profile atomically from the authenticated owner,
        # rather than forcing the browser to fabricate a second account.
        if seller is None:
            seller = Seller.objects.create(
                user=request.user,
                business_name=serializer.validated_data["name"],
                first_name=customer.first_name,
                last_name=customer.last_name,
                phone_number=customer.phone_number,
                shipping_address=customer.shipping_address,
                billing_address=customer.billing_address,
                status=Seller.Status.ACTIVE,
            )
        store = Store.objects.create(owner=customer, seller=seller, **serializer.validated_data)
        return Response(StoreDTO(store).data, status=201)

    def patch(self, request):
        store = get_object_or_404(Store, owner=request.user.customer_profile)
        serializer = StoreRequest(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        for field, value in serializer.validated_data.items():
            setattr(store, field, value)
        store.save()
        return Response(StoreDTO(store).data)


class StoreDashboardView(APIView):
    """Customer-only sales data derived from their store's actual order items."""
    permission_classes = [IsCustomer]

    def get(self, request):
        store = get_object_or_404(Store, owner=request.user.customer_profile)
        from apps.orders.models import Order, OrderItem

        successful_statuses = [Order.Status.CONFIRMED, Order.Status.SHIPPED, Order.Status.DELIVERED]
        items = OrderItem.objects.filter(seller=store.seller, order__status__in=successful_statuses).select_related("order", "variant__product")
        revenue_expression = ExpressionWrapper(F("unit_price") * F("quantity"), output_field=DecimalField(max_digits=12, decimal_places=2))
        aggregate = items.aggregate(total_items_sold=Sum("quantity"), total_revenue=Sum(revenue_expression))
        product_sales = []
        for product in store.products.all().prefetch_related("variants"):
            product_items = items.filter(variant__product=product)
            totals = product_items.aggregate(sold=Sum("quantity"), revenue=Sum(revenue_expression))
            product_sales.append({
                "id": str(product.id), "name": product.name, "price": str(product.base_price), "status": product.status,
                "stock_quantity": sum(variant.stock_quantity for variant in product.variants.all()),
                "sold": totals["sold"] or 0, "revenue": str(totals["revenue"] or 0),
            })
        sales = [{
            "order_id": str(item.order_id), "order_number": item.order.order_number, "product": item.variant.product.name,
            "quantity": item.quantity, "unit_price": str(item.unit_price), "total": str(item.line_total),
            "status": item.order.status, "created_at": item.order.created_at,
        } for item in items.order_by("-order__created_at")]
        return Response({
            "store": StoreDTO(store).data,
            "products": product_sales,
            "sales_summary": {"total_orders": items.values("order_id").distinct().count(), "total_items_sold": aggregate["total_items_sold"] or 0, "total_revenue": str(aggregate["total_revenue"] or 0)},
            "sales": sales,
        })

    def patch(self, request):
        profile = getattr(request.user, "customer_profile", None)
        if profile is None:
            return Response({"error": {"message": "No customer profile for this account."}}, status=404)
        serializer = UpdateCustomerRequest(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        profile = CustomerService.update_customer(profile, serializer.validated_data)
        return Response(CustomerDTO(profile).data)
