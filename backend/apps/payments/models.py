import uuid
from django.db import models
from apps.shared.models import TimeStampedModel
from apps.orders.models import Order


class Payment(TimeStampedModel):
    """
    Payment can be processed only for orders in PENDING status (spec section
    8/11). Only a payment gateway reference token is stored — never raw card
    data (spec section 10).
    """

    class Provider(models.TextChoices):
        STRIPE = "STRIPE", "Stripe"
        PAYPAL = "PAYPAL", "PayPal"

    class Status(models.TextChoices):
        INITIATED = "INITIATED", "Initiated"
        SUCCEEDED = "SUCCEEDED", "Succeeded"
        FAILED = "FAILED", "Failed"
        REFUNDED = "REFUNDED", "Refunded"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.OneToOneField(Order, on_delete=models.PROTECT, related_name="payment")
    provider = models.CharField(max_length=16, choices=Provider.choices)
    provider_reference = models.CharField(max_length=255, help_text="Opaque gateway token/charge id — never a raw card number.")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.INITIATED)

    class Meta:
        db_table = "payments"
