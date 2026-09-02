from django.core.cache import cache
from django.db import transaction

from apps.shared.exceptions import DomainError
from apps.sellers.models import Seller
from .models import Category, Product, ProductVariant, ProductSellerAssignment

PRODUCT_LIST_CACHE_KEY = "catalog:product_list:{params_hash}"
PRODUCT_LIST_CACHE_TTL = 60 * 5  # 5 minutes


class CatalogCacheService:
    """Redis-backed caching for product listings (spec: REDIS REQUIREMENTS)."""

    @staticmethod
    def get_cached_list(params_hash: str):
        return cache.get(PRODUCT_LIST_CACHE_KEY.format(params_hash=params_hash))

    @staticmethod
    def set_cached_list(params_hash: str, data):
        cache.set(PRODUCT_LIST_CACHE_KEY.format(params_hash=params_hash), data, PRODUCT_LIST_CACHE_TTL)

    @staticmethod
    def invalidate_product_lists():
        # django-redis supports pattern deletion; fall back to a version bump otherwise.
        try:
            cache.delete_pattern("catalog:product_list:*")
        except AttributeError:
            cache.clear()


class CategoryService:
    @staticmethod
    def create_category(data: dict) -> Category:
        return Category.objects.create(**data)

    @staticmethod
    def archive_category(category: Category):
        category.status = Category.Status.ARCHIVED
        category.save(update_fields=["status"])
        category.archive()

    @staticmethod
    def restore_category(category: Category):
        category.status = Category.Status.ACTIVE
        category.save(update_fields=["status"])
        category.restore()


class ProductService:
    @staticmethod
    @transaction.atomic
    def create_product(data: dict, seller: Seller | None = None) -> Product:
        product = Product.objects.create(**data)
        if seller is not None:
            ProductSellerAssignment.objects.create(
                product=product,
                seller=seller,
                role=ProductSellerAssignment.Role.PRIMARY_SELLER,
                price=product.base_price,
            )
        CatalogCacheService.invalidate_product_lists()
        return product

    @staticmethod
    def update_product(product: Product, data: dict) -> Product:
        for field, value in data.items():
            setattr(product, field, value)
        product.save()
        CatalogCacheService.invalidate_product_lists()
        return product

    @staticmethod
    def archive_product(product: Product):
        product.status = Product.Status.ARCHIVED
        product.save(update_fields=["status"])
        CatalogCacheService.invalidate_product_lists()

    @staticmethod
    def restore_product(product: Product):
        product.status = Product.Status.ACTIVE
        product.restore()
        product.save(update_fields=["status"])
        CatalogCacheService.invalidate_product_lists()

    @staticmethod
    def add_variant(product: Product, data: dict) -> ProductVariant:
        variant = ProductVariant.objects.create(product=product, **data)
        CatalogCacheService.invalidate_product_lists()
        return variant

    @staticmethod
    def assign_seller(product: Product, seller: Seller, role: str, price) -> ProductSellerAssignment:
        if ProductSellerAssignment.objects.filter(product=product, seller=seller).exists():
            raise DomainError("This seller is already assigned to the product.")
        return ProductSellerAssignment.objects.create(product=product, seller=seller, role=role, price=price)
