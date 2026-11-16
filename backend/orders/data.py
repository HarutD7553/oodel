"""Database access operations for customer and staff order flows."""

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import Order, OrderItem


@transaction.atomic
def create_order(*, name, email, phone, pickup_at, payment, items, subtotal, tax):
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


def get_order(public_id, email=None):
    orders = Order.objects.prefetch_related('items')
    if email is not None:
        orders = orders.filter(email__iexact=email)
    return get_object_or_404(orders, public_id=public_id)


def list_active_orders():
    return Order.objects.exclude(status=Order.Status.DONE).prefetch_related('items')


def set_status(order, new_status):
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


def delete_order(order):
    order.delete()
