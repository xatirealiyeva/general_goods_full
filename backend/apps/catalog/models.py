import uuid
from decimal import Decimal
from django.db import models
from apps.shared.models import BaseModel, TimeStampedModel
from apps.sellers.models import Seller


class Category(BaseModel):
    """Top-level grouping such as Electronics or Clothing (spec section 5)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(max_length=170, unique=True)
    description = models.TextField(blank=True)
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        ACTIVE = "ACTIVE", "Active"
        ARCHIVED = "ARCHIVED", "Archived"
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="children")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)

    class Meta:
        db_table = "categories"
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Product(BaseModel):
    """Reusable catalog item, e.g. 'Running Shoes Model X' (spec section 5)."""

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        ACTIVE = "ACTIVE", "Active"
        ARCHIVED = "ARCHIVED", "Archived"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
    base_price = models.DecimalField(max_digits=12, decimal_places=2)
    brand = models.ForeignKey("Brand", null=True, blank=True, on_delete=models.SET_NULL, related_name="products")
    tags = models.ManyToManyField("Tag", blank=True, related_name="products")
    store = models.ForeignKey("customers.Store", null=True, blank=True, on_delete=models.PROTECT, related_name="products")

    class Meta:
        db_table = "products"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status"]), models.Index(fields=["category"])]

    def __str__(self):
        return self.name


class ProductSellerAssignment(TimeStampedModel):
    """
    Marketplace model: a product may have several sellers, each with its own
    price/stock. Roles are stored explicitly (spec section 7).
    """

    class Role(models.TextChoices):
        PRIMARY_SELLER = "PRIMARY_SELLER", "Primary seller"
        ALTERNATIVE_SELLER = "ALTERNATIVE_SELLER", "Alternative seller"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="seller_assignments")
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE, related_name="product_assignments")
    role = models.CharField(max_length=24, choices=Role.choices, default=Role.PRIMARY_SELLER)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "product_seller_assignments"
        unique_together = [("product", "seller")]

    def __str__(self):
        return f"{self.product.name} <- {self.seller.business_name} ({self.role})"


class Brand(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)

    class Meta:
        db_table = "brands"


class Tag(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=64, unique=True)
    slug = models.SlugField(max_length=80, unique=True)

    class Meta:
        db_table = "tags"


class DiscountCode(TimeStampedModel):
    class Type(models.TextChoices): PERCENTAGE = "PERCENTAGE", "Percentage"; FIXED = "FIXED", "Fixed"
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=16, choices=Type.choices)
    value = models.DecimalField(max_digits=12, decimal_places=2)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    class Meta: db_table = "discount_codes"

class PromotionalCampaign(TimeStampedModel):
    class Type(models.TextChoices): PERCENTAGE="PERCENTAGE","Percentage"; FIXED="FIXED","Fixed"
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    name=models.CharField(max_length=150,unique=True); description=models.TextField(blank=True)
    discount_type=models.CharField(max_length=16,choices=Type.choices); value=models.DecimalField(max_digits=12,decimal_places=2)
    starts_at=models.DateTimeField(); ends_at=models.DateTimeField(); is_active=models.BooleanField(default=True)
    products=models.ManyToManyField(Product,blank=True,related_name="campaigns"); categories=models.ManyToManyField(Category,blank=True,related_name="campaigns")
    class Meta: db_table="promotional_campaigns"


class ProductVariant(BaseModel):
    """Size/color/configuration-specific version of a product (spec section 5)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    sku = models.CharField(max_length=64, unique=True)
    attributes = models.JSONField(default=dict, blank=True)  # e.g. {"size": "M", "color": "Red"}
    price_override = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    stock_quantity = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "product_variants"

    @property
    def effective_price(self) -> Decimal:
        return self.price_override if self.price_override is not None else self.product.base_price

    @property
    def in_stock(self) -> bool:
        return self.stock_quantity > 0

    def __str__(self):
        return self.sku


class ProductImage(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="products/")
    is_primary = models.BooleanField(default=False)

    class Meta:
        db_table = "product_images"
