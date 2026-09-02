from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    JWT login using email + password (spec: 'Email is the main login
    identifier'). Also embeds role/account_status claims so the frontend can
    route users without an extra /me call.
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["account_status"] = user.account_status
        token["email"] = user.email
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["role"] = self.user.role
        data["account_status"] = self.user.account_status
        data["email"] = self.user.email
        data["has_seller_access"] = hasattr(self.user, "seller_profile")
        return data
