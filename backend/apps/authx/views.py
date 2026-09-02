from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import EmailTokenObtainPairSerializer
from .throttles import RedisLoginRateThrottle


class EmailTokenObtainPairView(TokenObtainPairView):
    """POST /api/auth/login/ — {email, password} -> {access, refresh, role, ...}"""
    serializer_class = EmailTokenObtainPairSerializer
    throttle_classes = [RedisLoginRateThrottle]
