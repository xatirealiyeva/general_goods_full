from rest_framework import serializers
from .models import Review


class ReviewDTO(serializers.ModelSerializer):
    customer_name = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ["id", "product", "customer", "customer_name", "rating", "comment", "image", "moderation_status", "created_at"]
        read_only_fields = ["id", "customer", "customer_name", "moderation_status", "created_at"]

    def get_customer_name(self, obj):
        return f"{obj.customer.first_name} {obj.customer.last_name[:1]}."


class SubmitProductReviewRequest(serializers.Serializer):
    product = serializers.UUIDField()
    rating = serializers.IntegerField(min_value=1, max_value=5)
    comment = serializers.CharField(required=False, allow_blank=True)
    image = serializers.ImageField(required=False, allow_null=True)


class ModerateReviewRequest(serializers.Serializer):
    moderation_status = serializers.ChoiceField(choices=Review.ModerationStatus.choices)
