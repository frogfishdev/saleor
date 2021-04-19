from django.db import models
from django.utils.timezone import now

from ..order.models import Order, OrderLine
from ..product.models import ProductVariant

class ReturnHeader(models.Model):
    order = models.ForeignKey(
        Order,
        related_name="return_order",
        on_delete=models.CASCADE
    )
    misc_refund_amount = 0
    date_submitted = models.DateTimeField(default=now, editable=False)
    date_received_in_wharehouse = models.DateTimeField(null=True, blank=True)
    comment = models.TextField()

class ReturnLine(models.Model):
    return_header = models.ForeignKey(
        ReturnHeader,
        on_delete=models.CASCADE
    )
    return_reason = models.CharField(max_length=255)
    order_line = models.ForeignKey(
        OrderLine,
        related_name="order_line",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    quantity_returned = models.IntegerField(default=0)
    RETURN_CHOICES = (
        ('EXCHANGE', 'EXCHANGE'),
        ('REFUND', 'REFUND'),
    )
    return_type = models.CharField(
        choices=RETURN_CHOICES, 
        default='REFUND', 
        max_length=255
    )
    return_variant = models.ForeignKey(
        ProductVariant,
        related_name="return_variant",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    return_sku = models.CharField(max_length=255)
    exchange_variant = models.ForeignKey(
        ProductVariant,
        related_name="exchange_variant",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    exchange_sku = models.CharField(max_length=255, null=True, blank=True)
    returned_to_stock = models.BooleanField(default=False)
    accepted = models.BooleanField(default=False)
    accepted_quantity = models.IntegerField(default=0) 
    rejected_reason = models.CharField(max_length=255, null=True, blank=True)
    processed_by = models.CharField(max_length=255, null=True, blank=True)
    date_processed = models.DateTimeField(null=True, blank=True)
