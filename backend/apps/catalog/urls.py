from django.urls import path
from .views import (
    CategoryListCreateView, CategoryArchiveView, CategoryRestoreView, CategoryDetailView, ProductRestoreView, ProductAssignmentView, SellerMyProductsView, CustomerStoreProductsView, CustomerStoreProductDetailView, CustomerStoreProductImageView, BrandView, TagView, DiscountCodeView, PromotionalCampaignView, PromotionalCampaignDetailView,
    ProductListCreateView, ProductDetailView, ProductVariantCreateView,
)

app_name = "catalog"

urlpatterns = [
    path("categories/", CategoryListCreateView.as_view(), name="category-list"),
    path("categories/<uuid:category_id>/", CategoryDetailView.as_view(), name="category-detail"),
    path("categories/<uuid:category_id>/archive/", CategoryArchiveView.as_view(), name="category-archive"),
    path("categories/<uuid:category_id>/restore/", CategoryRestoreView.as_view(), name="category-restore"),
    path("brands/", BrandView.as_view(), name="brand-list"),
    path("tags/", TagView.as_view(), name="tag-list"),
    path("discount-codes/", DiscountCodeView.as_view(), name="discount-code-list"),
    path("campaigns/", PromotionalCampaignView.as_view(), name="campaign-list"),
    path("campaigns/<uuid:id>/", PromotionalCampaignDetailView.as_view(), name="campaign-detail"),
    path("products/", ProductListCreateView.as_view(), name="product-list"),
    path("products/<uuid:id>/", ProductDetailView.as_view(), name="product-detail"),
    path("products/mine/", SellerMyProductsView.as_view(), name="seller-products"),
    path("store/products/", CustomerStoreProductsView.as_view(), name="customer-store-products"),
    path("store/products/<uuid:product_id>/", CustomerStoreProductDetailView.as_view(), name="customer-store-product-detail"),
    path("store/products/<uuid:product_id>/images/", CustomerStoreProductImageView.as_view(), name="customer-store-product-image"),
    path("products/<uuid:product_id>/restore/", ProductRestoreView.as_view(), name="product-restore"),
    path("products/<uuid:product_id>/sellers/", ProductAssignmentView.as_view(), name="product-assignment"),
    path("products/<uuid:product_id>/variants/", ProductVariantCreateView.as_view(), name="variant-create"),
]
