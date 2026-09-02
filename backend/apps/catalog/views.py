import hashlib
import json

from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Avg, Count, Q
from rest_framework.filters import OrderingFilter

from apps.shared.permissions import IsAdmin, IsSeller, IsCustomer
from apps.shared.pagination import DefaultPagination
from apps.shared.exceptions import DomainError
from .models import Category, Product, ProductVariant, ProductImage, Brand, Tag, DiscountCode, PromotionalCampaign, ProductSellerAssignment
from .filters import ProductFilter
from .serializers import (
    CategoryDTO, CreateProductCategoryRequest, UpdateProductCategoryRequest,
    ProductListDTO, ProductDetailDTO, CreateProductRequest, UpdateProductRequest,
    ProductVariantDTO, CreateProductVariantRequest, ProductSellerAssignmentDTO, AssignSellerRequest, BrandDTO, TagDTO, DiscountCodeDTO, PromotionalCampaignDTO,
)
from .services import CategoryService, ProductService, CatalogCacheService


class CategoryListCreateView(generics.ListCreateAPIView):
    """List: public. Create: admin only (spec 4.1)."""
    serializer_class = CategoryDTO
    queryset = Category.objects.all().order_by("name")

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdmin()]
        return [permissions.AllowAny()]

    def post(self, request, *args, **kwargs):
        serializer = CreateProductCategoryRequest(data=request.data)
        serializer.is_valid(raise_exception=True)
        category = CategoryService.create_category(serializer.validated_data)
        return Response(CategoryDTO(category).data, status=201)


class CategoryArchiveView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, category_id):
        category = get_object_or_404(Category, id=category_id)
        CategoryService.archive_category(category)
        return Response(status=204)

    def delete(self, request, category_id):
        return self.post(request, category_id)


class CategoryRestoreView(APIView):
    permission_classes = [IsAdmin]
    def post(self, request, category_id):
        category = get_object_or_404(Category.all_objects, id=category_id)
        CategoryService.restore_category(category)
        return Response(CategoryDTO(category).data)


class CategoryDetailView(APIView):
    """Admin-only category editing; archive/restore retain their explicit actions."""
    permission_classes = [IsAdmin]

    def patch(self, request, category_id):
        category = get_object_or_404(Category.all_objects, id=category_id)
        serializer = UpdateProductCategoryRequest(data=request.data, partial=True, context={"category": category})
        serializer.is_valid(raise_exception=True)
        for field, value in serializer.validated_data.items():
            setattr(category, field, value)
        category.save()
        return Response(CategoryDTO(category).data)


class ProductListCreateView(generics.ListCreateAPIView):
    """
    List: public, cached in Redis (spec: Caching product listings).
    Create: admin or seller (creating seller becomes PRIMARY_SELLER).
    """
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = ProductFilter
    ordering_fields = ["base_price", "created_at", "name"]
    pagination_class = DefaultPagination
    queryset = Product.objects.filter(Q(store__isnull=True) | Q(store__status__in=["ACTIVE", "DRAFT"]), status=Product.Status.ACTIVE).select_related("category", "store").prefetch_related("images", "variants").annotate(approved_rating=Avg("reviews__rating", filter=Q(reviews__moderation_status="APPROVED"))).order_by("-created_at", "-id")

    def get_serializer_class(self):
        return ProductListDTO

    def get_queryset(self):
        if self.request.user.is_authenticated and self.request.user.role == "ADMIN":
            return Product.all_objects.select_related("category", "store").prefetch_related("images", "variants").annotate(approved_rating=Avg("reviews__rating", filter=Q(reviews__moderation_status="APPROVED"))).order_by("-created_at", "-id")
        return super().get_queryset()

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def list(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == "ADMIN":
            return super().list(request, *args, **kwargs)
        params_hash = hashlib.md5(json.dumps(request.query_params.dict(), sort_keys=True).encode()).hexdigest()
        cached = CatalogCacheService.get_cached_list(params_hash)
        if cached is not None:
            return Response(cached)
        response = super().list(request, *args, **kwargs)
        CatalogCacheService.set_cached_list(params_hash, response.data)
        return response

    def post(self, request, *args, **kwargs):
        if request.user.role not in ("ADMIN", "SELLER"):
            return Response({"error": {"message": "Only admins or sellers can create products."}}, status=403)
        serializer = CreateProductRequest(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        data["category"] = get_object_or_404(Category, id=data["category"], is_deleted=False)
        seller = getattr(request.user, "seller_profile", None) if request.user.role == "SELLER" else None
        product = ProductService.create_product(data, seller=seller)
        return Response(ProductDetailDTO(product).data, status=201)


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProductDetailDTO
    queryset = Product.objects.all().select_related("category", "brand", "store").prefetch_related("images", "variants", "seller_assignments__seller", "tags").annotate(approved_rating=Avg("reviews__rating", filter=Q(reviews__moderation_status="APPROVED")), approved_review_count=Count("reviews", filter=Q(reviews__moderation_status="APPROVED")))
    lookup_field = "id"

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.method in permissions.SAFE_METHODS and not (self.request.user.is_authenticated and self.request.user.role == "ADMIN"):
            return queryset.filter(status=Product.Status.ACTIVE)
        return queryset

    def _check_ownership(self, request, product):
        if request.user.role == "ADMIN":
            return True
        if request.user.role == "SELLER":
            seller = getattr(request.user, "seller_profile", None)
            return seller and product.seller_assignments.filter(seller=seller).exists()
        return False

    def patch(self, request, *args, **kwargs):
        product = self.get_object()
        if not self._check_ownership(request, product):
            return Response({"error": {"message": "You do not own this product."}}, status=403)
        serializer = UpdateProductRequest(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        if "category" in data:
            data["category"] = get_object_or_404(Category, id=data["category"])
        product = ProductService.update_product(product, data)
        return Response(ProductDetailDTO(product).data)

    def delete(self, request, *args, **kwargs):
        product = self.get_object()
        if not self._check_ownership(request, product):
            return Response({"error": {"message": "You do not own this product."}}, status=403)
        ProductService.archive_product(product)
        return Response(status=204)


class ProductRestoreView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, product_id):
        product = get_object_or_404(Product.all_objects, id=product_id)
        if not ProductDetailView()._check_ownership(request, product):
            return Response({"error": {"message": "You do not own this product."}}, status=403)
        ProductService.restore_product(product)
        return Response(ProductDetailDTO(product).data)


class ProductAssignmentView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        if request.user.role != "ADMIN" and not ProductDetailView()._check_ownership(request, product):
            return Response({"error": {"message": "Not permitted."}}, status=403)
        serializer = AssignSellerRequest(data=request.data); serializer.is_valid(raise_exception=True)
        from apps.sellers.models import Seller
        assignment = ProductService.assign_seller(product, get_object_or_404(Seller, id=serializer.validated_data["seller"]), serializer.validated_data["role"], serializer.validated_data["price"])
        return Response(ProductSellerAssignmentDTO(assignment).data, status=201)


class SellerMyProductsView(generics.ListAPIView):
    serializer_class = ProductListDTO
    permission_classes = [IsSeller]
    pagination_class = DefaultPagination
    def get_queryset(self):
        return Product.all_objects.filter(seller_assignments__seller=self.request.user.seller_profile).distinct().select_related("category").prefetch_related("images", "variants")


class CustomerStoreProductsView(generics.ListCreateAPIView):
    permission_classes = [IsCustomer]
    pagination_class = DefaultPagination
    serializer_class = ProductDetailDTO

    def get_queryset(self):
        return Product.all_objects.filter(store__owner=self.request.user.customer_profile).select_related("category").prefetch_related("images", "variants")

    def post(self, request, *args, **kwargs):
        from apps.customers.models import Store
        store = get_object_or_404(Store, owner=request.user.customer_profile)
        serializer = CreateProductRequest(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        data["category"] = get_object_or_404(Category, id=data["category"], is_deleted=False)
        stock_quantity = request.data.get("stock_quantity", 0)
        try:
            stock_quantity = int(stock_quantity)
        except (TypeError, ValueError):
            return Response({"error": {"message": "Stock quantity must be a whole number."}}, status=400)
        if stock_quantity < 0:
            return Response({"error": {"message": "Stock quantity cannot be negative."}}, status=400)
        product = ProductService.create_product(data, seller=store.seller)
        product.store = store
        product.save(update_fields=["store"])
        ProductService.add_variant(product, {"sku": f"STORE-{product.id.hex[:12].upper()}", "stock_quantity": stock_quantity})
        return Response(ProductDetailDTO(product).data, status=201)


class CustomerStoreProductDetailView(APIView):
    permission_classes = [IsCustomer]

    def _product(self, request, product_id):
        return get_object_or_404(Product.all_objects, id=product_id, store__owner=request.user.customer_profile)

    def patch(self, request, product_id):
        product = self._product(request, product_id)
        serializer = UpdateProductRequest(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        if "category" in data:
            data["category"] = get_object_or_404(Category, id=data["category"])
        return Response(ProductDetailDTO(ProductService.update_product(product, data)).data)

    def delete(self, request, product_id):
        ProductService.archive_product(self._product(request, product_id))
        return Response(status=204)


class CustomerStoreProductImageView(APIView):
    permission_classes = [IsCustomer]
    def post(self, request, product_id):
        product = get_object_or_404(Product, id=product_id, store__owner=request.user.customer_profile)
        image = request.FILES.get("image")
        if image is None:
            return Response({"error": {"message": "An image file is required."}}, status=400)
        product_image = ProductImage.objects.create(product=product, image=image, is_primary=not product.images.exists())
        CatalogCacheService.invalidate_product_lists()
        return Response(ProductDetailDTO(product).data, status=201)


class BrandTagListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.AllowAny]
    ordering_field = "name"
    def get_queryset(self): return self.model.objects.all().order_by(self.ordering_field)
    def get_serializer_class(self): return self.serializer
    def post(self, request, *args, **kwargs):
        if request.user.role != "ADMIN": return Response({"error": {"message": "Admin only."}}, status=403)
        return super().post(request, *args, **kwargs)

class BrandView(BrandTagListCreateView): model, serializer = Brand, BrandDTO
class TagView(BrandTagListCreateView): model, serializer = Tag, TagDTO
class DiscountCodeView(BrandTagListCreateView):
    model, serializer = DiscountCode, DiscountCodeDTO
    ordering_field = "code"

    def get_queryset(self):
        return DiscountCode.objects.annotate(usage_count=Count("orders")).order_by("code")

class PromotionalCampaignView(generics.ListCreateAPIView):
    serializer_class=PromotionalCampaignDTO
    def get_permissions(self): return [IsAdmin()] if self.request.method=="POST" else [permissions.AllowAny()]
    def get_queryset(self): return PromotionalCampaign.objects.all() if self.request.user.is_authenticated and self.request.user.role=="ADMIN" else PromotionalCampaign.objects.filter(is_active=True)
    def post(self,request,*args,**kwargs): return super().post(request,*args,**kwargs)
class PromotionalCampaignDetailView(generics.RetrieveUpdateAPIView):
    serializer_class=PromotionalCampaignDTO; permission_classes=[IsAdmin]; queryset=PromotionalCampaign.objects.all(); lookup_field="id"


class ProductVariantCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        if request.user.role == "SELLER":
            seller = getattr(request.user, "seller_profile", None)
            if not seller or not product.seller_assignments.filter(seller=seller).exists():
                return Response({"error": {"message": "You do not own this product."}}, status=403)
        elif request.user.role != "ADMIN":
            return Response({"error": {"message": "Not permitted."}}, status=403)
        serializer = CreateProductVariantRequest(data=request.data)
        serializer.is_valid(raise_exception=True)
        variant = ProductService.add_variant(product, serializer.validated_data)
        return Response(ProductVariantDTO(variant).data, status=201)
