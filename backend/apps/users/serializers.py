from rest_framework import serializers
from .models import User


class UserDTO(serializers.ModelSerializer):
    """Read-only DTO — never exposes password or internal flags."""

    class Meta:
        model = User
        fields = ["id", "email", "role", "account_status", "is_active", "created_at"]
        read_only_fields = fields


class AdminUpdateUserStatusRequest(serializers.Serializer):
    account_status = serializers.ChoiceField(choices=User.Status.choices, required=False)
    role = serializers.ChoiceField(choices=User.Role.choices, required=False)

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError("Provide an account status or role.")
        return attrs
