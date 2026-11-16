from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from orders.models import Order, OrderItem
from orders.serializers import CATALOG, TAX_RATE

SEED_PREFIX = 'CK-9'  # every seeded order id starts with CK-9 so it is easy to find and remove

CUSTOMERS = [
    ('demo_customer', 'demo.customer@example.com'),
    ('demo_customer2', 'demo.customer2@example.com'),
]

# (public_id, customer name, email, status, hours from now for pickup, [(product_id, detail, qty, note)])
ORDERS = [
    ('CK-900001', 'Demo Customer', 'demo.customer@example.com', 'placed', 26, [('strawberry', 'Medium', 1, 'Happy birthday, Sam')]),
    ('CK-900002', 'Demo Customer', 'demo.customer@example.com', 'baking', 5, [('cupcake', 'Box of 6', 2, ''), ('croissant', '', 3, '')]),
    ('CK-900003', 'Demo Customer Two', 'demo.customer2@example.com', 'ready', 2, [('chocolate', 'Large', 1, 'No nuts')]),
    ('CK-900004', 'Demo Customer Two', 'demo.customer2@example.com', 'done', -20, [('redvelvet', 'Small', 1, '')]),
    ('CK-900005', 'Guest Buyer', 'guest.buyer@example.com', 'placed', 48, [('cupcake', 'Box of 12', 1, ''), ('croissant', '', 6, '')]),
]


class Command(BaseCommand):
    help = 'Create (or reset) representative development data: demo customers and orders in every status.'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true', help='Delete previously seeded orders and demo customers first.')

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()
        if options['reset']:
            Order.objects.filter(public_id__startswith=SEED_PREFIX).delete()
            User.objects.filter(username__in=[u for u, _ in CUSTOMERS]).delete()

        for username, email in CUSTOMERS:
            user, created = User.objects.get_or_create(username=username, defaults={'email': email})
            if created:
                user.set_password('DemoPass-12345')
                user.save()

        now = timezone.now()
        made = 0
        for public_id, name, email, status, hours, items in ORDERS:
            if Order.objects.filter(public_id=public_id).exists():
                continue
            lines = []
            for product_id, detail, qty, note in items:
                product = CATALOG[product_id]
                price = Decimal(str(product['options'][detail] if 'options' in product else product['price']))
                lines.append((product_id, product['name'], detail, qty, price, note))
            subtotal = sum((p * q for _, _, _, q, p, _ in lines), start=Decimal('0.00'))
            tax = (subtotal * TAX_RATE).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            order = Order.objects.create(
                public_id=public_id, customer_name=name, email=email, status=status,
                pickup_at=now + timedelta(hours=hours), subtotal=subtotal, tax=tax, total=subtotal + tax,
                started_at=now - timedelta(hours=2) if status in ('baking', 'ready', 'done') else None,
                ready_at=now - timedelta(hours=1) if status in ('ready', 'done') else None,
            )
            for product_id, pname, detail, qty, price, note in lines:
                OrderItem.objects.create(order=order, product_id=product_id, name=pname, detail=detail,
                                         quantity=qty, unit_price=price, note=note)
            made += 1

        self.stdout.write(self.style.SUCCESS(
            f'Seed complete: {made} new orders, {Order.objects.filter(public_id__startswith=SEED_PREFIX).count()} seeded orders in total.'))
