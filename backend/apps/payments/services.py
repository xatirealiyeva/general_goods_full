from django.db import transaction

from apps.shared.exceptions import DomainError
from apps.orders.models import Order
from apps.orders.services import OrderService
from .models import Payment


class PaymentGatewayClient:
    """
    Thin abstraction over Stripe/PayPal. In real deployments this calls out
    to the provider SDK; here it simulates a successful charge confirmation
    so the module is runnable without live credentials.
    """

    @staticmethod
    def confirm_charge(provider: str, provider_reference: str, amount) -> bool:
        return bool(provider_reference)


class PaymentService:
    @staticmethod
    @transaction.atomic
    def process_payment(order, provider: str, provider_reference: str) -> Payment:
        order_id = order
        try:
            order = Order.objects.select_for_update().get(id=order_id)
        except Order.DoesNotExist:
            raise DomainError("Order not found.", code="not_found", http_status=404)

        if order.status != Order.Status.PENDING:
            raise DomainError("Payment can only be processed for orders in PENDING status.")

        confirmed = PaymentGatewayClient.confirm_charge(provider, provider_reference, order.total)
        payment = Payment.objects.create(
            order=order, provider=provider, provider_reference=provider_reference,
            amount=order.total, status=Payment.Status.SUCCEEDED if confirmed else Payment.Status.FAILED,
        )
        if confirmed:
            OrderService.transition_status(order, Order.Status.CONFIRMED)
        return payment

    @staticmethod
    @transaction.atomic
    def refund(payment: Payment) -> Payment:
        payment.status = Payment.Status.REFUNDED
        payment.save(update_fields=["status"])
        OrderService.transition_status(payment.order, Order.Status.REFUNDED)
        return payment
