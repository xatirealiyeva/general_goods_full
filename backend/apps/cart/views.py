from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.shared.permissions import IsCustomer
from .serializers import CartDTO, CreateCartItemRequest, UpdateCartItemRequest
from .services import CartService


class CartView(APIView):
    """Customer's own cart (spec 4.3: add to cart)."""
    permission_classes = [IsCustomer]

    def get(self, request):
        cart = CartService.get_or_create_cart(request.user.customer_profile)
        return Response(CartDTO(cart).data)

    def delete(self, request):
        cart = CartService.get_or_create_cart(request.user.customer_profile)
        CartService.clear(cart)
        return Response(status=204)


class CartItemView(APIView):
    permission_classes = [IsCustomer]

    def post(self, request):
        serializer = CreateCartItemRequest(data=request.data)
        serializer.is_valid(raise_exception=True)
        cart = CartService.get_or_create_cart(request.user.customer_profile)
        CartService.add_item(cart, **serializer.validated_data)
        return Response(CartDTO(cart).data, status=201)

    def patch(self, request, item_id):
        serializer = UpdateCartItemRequest(data=request.data)
        serializer.is_valid(raise_exception=True)
        cart = CartService.get_or_create_cart(request.user.customer_profile)
        CartService.update_item(cart, item_id, serializer.validated_data["quantity"])
        return Response(CartDTO(cart).data)

    def delete(self, request, item_id):
        cart = CartService.get_or_create_cart(request.user.customer_profile)
        CartService.remove_item(cart, item_id)
        return Response(CartDTO(cart).data)
