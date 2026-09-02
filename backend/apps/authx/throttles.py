from rest_framework.throttling import SimpleRateThrottle


class RedisLoginRateThrottle(SimpleRateThrottle):
    """
    Rate limiting backed by Redis via DRF's cache-based throttle (spec:
    'Rate limiting' under REDIS REQUIREMENTS). Applied to the login view.
    """
    scope = "login"

    def get_cache_key(self, request, view):
        ident = request.data.get("email") or self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}
