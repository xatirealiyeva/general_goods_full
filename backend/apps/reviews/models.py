import uuid
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from apps.shared.models import TimeStampedModel
from apps.customers.models import Customer
from apps.catalog.models import Product


class Review(TimeStampedModel):
    """Product ratings and reviews that are published on submission."""

    class ModerationStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    # Optional customer-supplied photo stored with the persisted review.
    image = models.ImageField(upload_to="reviews/", blank=True)
    moderation_status = models.CharField(max_length=16, choices=ModerationStatus.choices, default=ModerationStatus.APPROVED)

    class Meta:
        db_table = "reviews"
        unique_together = [("product", "customer")]
        ordering = ["-created_at"]
