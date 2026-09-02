"""
Central permission classes shared across modules.
Implements role-based access control + ownership validation as required by
the spec (Admin / Seller / Customer roles, ownership checks).
"""
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdmin(BasePermission):
    message = "Only administrators can perform this action."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "ADMIN")


class IsSeller(BasePermission):
    message = "Only sellers can perform this action."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "SELLER")


class IsCustomer(BasePermission):
    message = "Only customers can perform this action."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "CUSTOMER")


class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and request.user.role == "ADMIN")


class IsOwnerSeller(BasePermission):
    """
    Object-level permission: only the seller who owns a resource (or an admin)
    may modify it. Assumes the object exposes a `.seller` or `.seller_id`
    attribute (directly or via a related product).
    """
    message = "You do not have permission to access this seller resource."

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.role == "ADMIN":
            return True
        if user.role != "SELLER":
            return False
        seller_profile = getattr(user, "seller_profile", None)
        if seller_profile is None:
            return False
        owner_id = getattr(obj, "seller_id", None)
        if owner_id is None and hasattr(obj, "product"):
            owner_id = getattr(obj.product, "seller_id", None)
        return owner_id == seller_profile.id


class IsOwnerCustomer(BasePermission):
    """
    Object-level permission: only the customer who owns a resource (or an
    admin) may access/modify it.
    """
    message = "You do not have permission to access this customer resource."

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.role == "ADMIN":
            return True
        if user.role != "CUSTOMER":
            return False
        customer_profile = getattr(user, "customer_profile", None)
        if customer_profile is None:
            return False
        owner_id = getattr(obj, "customer_id", None)
        return owner_id == customer_profile.id
