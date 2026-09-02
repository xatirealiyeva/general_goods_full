from django.db import transaction

from apps.shared.exceptions import DomainError
from apps.catalog.models import Product
from .models import Review


class ReviewService:
    @staticmethod
    @transaction.atomic
    def submit_review(customer, product, rating: int, comment: str = "", image=None) -> Review:
        product_id = product
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            raise DomainError("Product not found.", code="not_found", http_status=404)

        review, _ = Review.objects.update_or_create(
            product=product, customer=customer,
            # Reviews are published as soon as an authenticated customer
            # submits them.  Administrators may still later reject/delete
            # inappropriate reviews through the existing moderation endpoint.
            defaults={"rating": rating, "comment": comment, "image": image, "moderation_status": Review.ModerationStatus.APPROVED},
        )
        return review

    @staticmethod
    def moderate(review: Review, status: str) -> Review:
        review.moderation_status = status
        review.save(update_fields=["moderation_status"])
        return review
