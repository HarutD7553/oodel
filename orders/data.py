"""Data access for orders.

This is the only module that talks to the database for orders. Views and
serializers call these functions instead of using the ORM directly.
All queries go through the Django ORM, which parameterizes them for us.
"""
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import Order, OrderItem


# ---- Create ----

@transaction.atomic
def create_order(*, name, email, phone, pickup_at, payment, items, subtotal, tax):
    """Save an order and its items together (all or nothing)."""
    order = Order.objects.create(
        customer_name=name,
        email=email,
        phone=phone,
        pickup_at=pickup_at,
        payment=payment,
        subtotal=subtotal,
        tax=tax,
        total=subtotal + tax,
    )
    OrderItem.objects.bulk_create(
        OrderItem(
            order=order,
            product_id=item['product_id'],
            name=item['name'],
            detail=item['detail'],
            quantity=item['quantity'],
            unit_price=item['unit_price'],
            note=item.get('note', ''),
        )
        for item in items
    )
    return order


# ---- Read ----

def get_order(public_id, email=None):
    """Return one order, or raise 404. Pass email to also require a match."""
    orders = Order.objects.prefetch_related('items')
    if email is not None:
        orders = orders.filter(email__iexact=email)
    return get_object_or_404(orders, public_id=public_id)


def list_active_orders():
    """Every order that has not been picked up yet."""
    return Order.objects.exclude(status=Order.Status.DONE).prefetch_related('items')


# ---- Update ----

def set_status(order, new_status):
    """Move an order to a new status and stamp the matching time."""
    fields = ['status']
    order.status = new_status
    if new_status == Order.Status.BAKING:
        order.started_at = timezone.now()
        fields.append('started_at')
    elif new_status == Order.Status.READY:
        order.ready_at = timezone.now()
        fields.append('ready_at')
    order.save(update_fields=fields)
    return order


def set_notification_email(order, notification_email):
    order.notification_email = notification_email
    order.save(update_fields=['notification_email'])
    return order


# ---- Delete ----

def delete_order(order):
    """Delete an order. Its items are removed with it (CASCADE)."""
    order.delete()
