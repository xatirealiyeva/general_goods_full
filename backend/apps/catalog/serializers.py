from decimal import Decimal
from rest_framework import serializers
from .models import Category, Product, ProductVariant, ProductImage, ProductSellerAssignment, Brand, Tag, DiscountCode, PromotionalCampaign


class CategoryDTO(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description", "parent", "status", "created_at"]
        read_only_fields = ["id", "created_at"]


class CreateProductCategoryRequest(serializers.Serializer):
    name = serializers.CharField(max_length=150)
    slug = serializers.SlugField(max_length=170)
    description = serializers.CharField(required=False, allow_blank=True)
    parent = serializers.UUIDField(required=False, allow_null=True)

    def validate_name(self, value):
        if Category.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError("A category with this name already exists.")
        return value


class UpdateProductCategoryRequest(serializers.Serializer):
    """Admin DTO for changing a category without creating a duplicate."""
    name = serializers.CharField(max_length=150, required=False)
    slug = serializers.SlugField(max_length=170, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    parent = serializers.UUIDField(required=False, allow_null=True)
    status = serializers.ChoiceField(choices=Category.Status.choices, required=False)

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError("Provide at least one category field to update.")
        category = self.context["category"]
        if "name" in attrs and Category.all_objects.filter(name__iexact=attrs["name"]).exclude(id=category.id).exists():
            raise serializers.ValidationError({"name": "A category with this name already exists."})
        if "slug" in attrs and Category.all_objects.filter(slug=attrs["slug"]).exclude(id=category.id).exists():
            raise serializers.ValidationError({"slug": "A category with this slug already exists."})
        if attrs.get("parent") == category.id:
            raise serializers.ValidationError({"parent": "A category cannot be its own parent."})
        if "parent" in attrs and attrs["parent"] and not Category.objects.filter(id=attrs["parent"], is_deleted=False).exists():
            raise serializers.ValidationError({"parent": "Parent category does not exist."})
        return attrs


class ProductVariantDTO(serializers.ModelSerializer):
    effective_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    in_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = ProductVariant
        fields = ["id", "sku", "attributes", "price_override", "effective_price", "stock_quantity", "in_stock"]
        read_only_fields = ["id"]


class CreateProductVariantRequest(serializers.Serializer):
    sku = serializers.CharField(max_length=64)
    attributes = serializers.JSONField(required=False)
    price_override = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)
    stock_quantity = serializers.IntegerField(min_value=0, default=0)

    def validate_sku(self, value):
        if ProductVariant.objects.filter(sku=value).exists():
            raise serializers.ValidationError("A variant with this SKU already exists.")
        return value


class ProductImageDTO(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = ["id", "image", "is_primary"]
        read_only_fields = ["id"]

    def get_image(self, obj):
        """Do not advertise media rows whose file has been removed."""
        if not obj.image:
            return None
        try:
            return obj.image.url if obj.image.storage.exists(obj.image.name) else None
        except OSError:
            return None


class ProductSellerAssignmentDTO(serializers.ModelSerializer):
    seller_name = serializers.CharField(source="seller.business_name", read_only=True)

    class Meta:
        model = ProductSellerAssignment
        fields = ["id", "seller", "seller_name", "role", "price", "is_active"]
        read_only_fields = ["id", "seller_name"]


class AssignSellerRequest(serializers.Serializer):
    seller = serializers.UUIDField()
    role = serializers.ChoiceField(choices=ProductSellerAssignment.Role.choices, default=ProductSellerAssignment.Role.ALTERNATIVE_SELLER)
    price = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0"))


class BrandDTO(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ["id", "name", "slug"]


class TagDTO(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "slug"]

class DiscountCodeDTO(serializers.ModelSerializer):
    usage_count = serializers.SerializerMethodField()

    class Meta:
        model = DiscountCode
        fields = ["id", "code", "discount_type", "value", "starts_at", "ends_at", "is_active", "usage_count"]

    def get_usage_count(self, obj):
        return getattr(obj, "usage_count", obj.orders.count())
class PromotionalCampaignDTO(serializers.ModelSerializer):
    class Meta:
        model=PromotionalCampaign
        fields=["id","name","description","discount_type","value","starts_at","ends_at","is_active","products","categories"]
    def validate(self, attrs):
        start=attrs.get("starts_at",getattr(self.instance,"starts_at",None)); end=attrs.get("ends_at",getattr(self.instance,"ends_at",None))
        if start and end and end<=start: raise serializers.ValidationError({"ends_at":"End date must be after start date."})
        return attrs


class ProductListDTO(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    store_name = serializers.CharField(source="store.name", read_only=True, default=None)
    store_id = serializers.UUIDField(source="store.id", read_only=True, allow_null=True)
    min_price = serializers.SerializerMethodField()
    primary_image = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ["id", "name", "slug", "category", "category_name", "status", "base_price", "min_price", "primary_image", "store_id", "store_name", "rating"]

    def get_min_price(self, obj):
        # Use the view's prefetched collection; filtering the related manager
        # here would issue two extra queries for every product in a list.
        variants = [v for v in obj.variants.all() if not v.is_deleted]
        variant = min(variants, key=lambda v: v.effective_price, default=None)
        return str(variant.effective_price) if variant else str(obj.base_price)

    def get_primary_image(self, obj):
        images = list(obj.images.all())
        img = next((image for image in images if image.is_primary), None) or (images[0] if images else None)
        if not img or not img.image:
            return None
        try:
            return img.image.url if img.image.storage.exists(img.image.name) else None
        except OSError:
            return None

    def get_rating(self, obj):
        from django.db.models import Avg
        value = getattr(obj, "approved_rating", None)
        if value is None:
            value = obj.reviews.filter(moderation_status="APPROVED").aggregate(value=Avg("rating"))["value"]
        return round(float(value), 1) if value is not None else None


class ProductDetailDTO(serializers.ModelSerializer):
    variants = ProductVariantDTO(many=True, read_only=True)
    images = ProductImageDTO(many=True, read_only=True)
    seller_assignments = ProductSellerAssignmentDTO(many=True, read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)
    store_id = serializers.UUIDField(source="store.id", read_only=True, allow_null=True)
    store_name = serializers.CharField(source="store.name", read_only=True, default=None)
    store_description = serializers.CharField(source="store.description", read_only=True, default=None)
    store_owner_name = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id", "name", "slug", "description", "category", "category_name",
            "status", "base_price", "store_id", "store_name", "store_description", "store_owner_name", "rating", "review_count", "variants", "images", "seller_assignments", "created_at",
        ]

    def get_rating(self, obj):
        return ProductListDTO.get_rating(self, obj)

    def get_review_count(self, obj):
        from django.db.models import Count
        return getattr(obj, "approved_review_count", None) or obj.reviews.filter(moderation_status="APPROVED").aggregate(value=Count("id"))["value"]

    def get_store_owner_name(self, obj):
        if not obj.store_id:
            return None
        owner = obj.store.owner
        return f"{owner.first_name} {owner.last_name}".strip()


class CreateProductRequest(serializers.Serializer):
    """DTO used by Admin or the PRIMARY_SELLER to create a product listing."""
    name = serializers.CharField(max_length=200)
    slug = serializers.SlugField(max_length=220)
    description = serializers.CharField(required=False, allow_blank=True)
    category = serializers.UUIDField()
    base_price = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0"))
    status = serializers.ChoiceField(choices=Product.Status.choices, default=Product.Status.DRAFT)

    def validate_category(self, value):
        if not Category.objects.filter(id=value, is_deleted=False).exists():
            raise serializers.ValidationError("Product must belong to an existing category.")
        return value

    def validate_slug(self, value):
        if Product.objects.filter(slug=value).exists():
            raise serializers.ValidationError("A product with this slug already exists.")
        return value


class UpdateProductRequest(serializers.Serializer):
    name = serializers.CharField(max_length=200, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    category = serializers.UUIDField(required=False)
    base_price = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0"), required=False)
    status = serializers.ChoiceField(choices=Product.Status.choices, required=False)
