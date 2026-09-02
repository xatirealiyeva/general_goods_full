from django.db import transaction

from apps.shared.exceptions import DomainError
from apps.orders.models import Order
from apps.orders.services import OrderService
from apps.sellers.models import Seller
from .models import Shipment


class ShipmentService:
    @staticmethod
    @transaction.atomic
    def create_shipment(seller: Seller, order, carrier: str, tracking_number: str, estimated_arrival=None) -> Shipment:
        order_id = order
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            raise DomainError("Order not found.", code="not_found", http_status=404)
        if not order.items.filter(seller=seller).exists():
            raise DomainError("This order does not contain any of your products.", http_status=403)
        shipment = Shipment.objects.create(
            order=order, seller=seller, carrier=carrier,
            tracking_number=tracking_number, estimated_arrival=estimated_arrival,
        )
        if order.status == Order.Status.CONFIRMED:
            OrderService.transition_status(order, Order.Status.SHIPPED)
        return shipment

    @staticmethod
    def update_status(shipment: Shipment, status: str) -> Shipment:
        shipment.status = status
        shipment.save(update_fields=["status"])
        if status == Shipment.Status.DELIVERED and shipment.order.status == Order.Status.SHIPPED:
            OrderService.transition_status(shipment.order, Order.Status.DELIVERED)
        return shipment
