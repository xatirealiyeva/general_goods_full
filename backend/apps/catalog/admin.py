from django.contrib import admin
from .models import Category, Product, ProductVariant, ProductImage, ProductSellerAssignment


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "parent", "is_deleted"]
    search_fields = ["name"]


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0


class ProductSellerAssignmentInline(admin.TabularInline):
    model = ProductSellerAssignment
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "status", "base_price"]
    list_filter = ["status", "category"]
    search_fields = ["name", "slug"]
    inlines = [ProductVariantInline, ProductImageInline, ProductSellerAssignmentInline]
