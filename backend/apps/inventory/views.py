from rest_framework.response import Response
from rest_framework.views import APIView

from apps.shared.permissions import IsAdmin, IsSeller
from apps.catalog.models import ProductVariant
from apps.catalog.serializers import ProductVariantDTO
from .serializers import AdminInventoryDTO, StockAdjustmentDTO, CreateStockAdjustmentRequest
from .services import InventoryService


class StockAdjustmentView(APIView):
    """Admin/seller: record a stock adjustment (restock, correction, etc.)."""
    permission_classes = [IsAdmin]

    def post(self, request):
        serializer = CreateStockAdjustmentRequest(data=request.data)
        serializer.is_valid(raise_exception=True)
        adjustment = InventoryService.adjust_stock(**serializer.validated_data)
        return Response(StockAdjustmentDTO(adjustment).data, status=201)


class AdminInventoryListView(APIView):
    """Admin-only complete variant inventory with product context."""
    permission_classes = [IsAdmin]

    def get(self, request):
        variants = ProductVariant.objects.select_related("product").order_by("product__name", "sku")
        return Response(AdminInventoryDTO(variants, many=True).data)


class SellerStockAdjustmentView(APIView):
    """Sellers can adjust variants only for products assigned to them."""
    permission_classes = [IsSeller]

    def get(self, request):
        variants = ProductVariant.objects.filter(product__seller_assignments__seller=request.user.seller_profile, product__seller_assignments__is_active=True, is_deleted=False).distinct().select_related("product")
        return Response(ProductVariantDTO(variants, many=True).data)

    def post(self, request):
        serializer = CreateStockAdjustmentRequest(data=request.data)
        serializer.is_valid(raise_exception=True)
        variant = ProductVariant.objects.filter(id=serializer.validated_data["variant"], product__seller_assignments__seller=request.user.seller_profile, product__seller_assignments__is_active=True).first()
        if variant is None:
            return Response({"error": {"message": "You do not own this inventory item."}}, status=403)
        adjustment = InventoryService.adjust_stock(**serializer.validated_data)
        return Response(StockAdjustmentDTO(adjustment).data, status=201)


class SellerLowStockView(APIView):
    permission_classes = [IsSeller]

    def get(self, request):
        variants = InventoryService.low_stock_variants().filter(product__seller_assignments__seller=request.user.seller_profile, product__seller_assignments__is_active=True).distinct()
        return Response(ProductVariantDTO(variants, many=True).data)


class LowStockAlertView(APIView):
    """Admin: low-stock alerts (spec 4.1)."""
    permission_classes = [IsAdmin]

    def get(self, request):
        variants = InventoryService.low_stock_variants()
        return Response(ProductVariantDTO(variants, many=True).data)
