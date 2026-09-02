from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.shared.permissions import IsAdmin, IsCustomer
from apps.shared.pagination import DefaultPagination
from .models import Review
from .serializers import ReviewDTO, SubmitProductReviewRequest, ModerateReviewRequest
from .services import ReviewService


class ProductReviewListView(generics.ListAPIView):
    """Public: approved reviews for a product."""
    serializer_class = ReviewDTO
    pagination_class = DefaultPagination
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        # Rejected reviews are retained for admin audit purposes but are no
        # longer shown publicly.  Newly submitted reviews are APPROVED.
        return Review.objects.filter(
            product_id=self.kwargs["product_id"],
            moderation_status=Review.ModerationStatus.APPROVED,
        ).select_related("customer")


class SubmitReviewView(APIView):
    permission_classes = [IsCustomer]

    def post(self, request):
        serializer = SubmitProductReviewRequest(data=request.data)
        serializer.is_valid(raise_exception=True)
        review = ReviewService.submit_review(request.user.customer_profile, **serializer.validated_data)
        return Response(ReviewDTO(review).data, status=201)


class AdminModerateReviewView(APIView):
    """Admin: retain control to manage or remove published reviews."""
    permission_classes = [IsAdmin]

    def patch(self, request, review_id):
        review = get_object_or_404(Review, id=review_id)
        serializer = ModerateReviewRequest(data=request.data)
        serializer.is_valid(raise_exception=True)
        review = ReviewService.moderate(review, serializer.validated_data["moderation_status"])
        return Response(ReviewDTO(review).data)

    def delete(self, request, review_id):
        review = get_object_or_404(Review, id=review_id)
        # Soft moderation removal preserves the audit record and prevents public display.
        review.moderation_status = Review.ModerationStatus.REJECTED
        review.save(update_fields=["moderation_status"])
        return Response(status=204)


class AdminReviewListView(generics.ListAPIView):
    serializer_class = ReviewDTO
    permission_classes = [IsAdmin]
    pagination_class = DefaultPagination
    queryset = Review.objects.all()
    filterset_fields = ["moderation_status"]
