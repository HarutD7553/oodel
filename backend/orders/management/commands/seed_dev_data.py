import os
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from orders.models import Order, OrderItem
from orders.serializers import CATALOG, TAX_RATE


CUSTOMERS = [
    ('demo_customer', 'demo.customer@example.com'),
    ('demo_customer2', 'demo.customer2@example.com'),
]

ORDERS = [
    {
        'public_id': 'CK-900001',
        'name': 'Demo Customer',
        'email': 'demo.customer@example.com',
        'phone': '(818) 555-0101',
        'status': Order.Status.PLACED,
        'pickup_hours': 26,
        'placed_hours_ago': 1,
        'notification_email': 'demo.customer@example.com',
        'items': [('strawberry', 'Medium · Strawberry', 1, 'Happy birthday, Sam')],
    },
    {
        'public_id': 'CK-900002',
        'name': 'Demo Customer',
        'email': 'demo.customer@example.com',
        'phone': '(818) 555-0101',
        'status': Order.Status.BAKING,
        'pickup_hours': 5,
        'placed_hours_ago': 3,
        'started_hours_ago': 1,
        'items': [('cupcake', 'Box of 6', 2, ''), ('croissant', 'Butter', 3, '')],
    },
    {
        'public_id': 'CK-900003',
        'name': 'Demo Customer Two',
        'email': 'demo.customer2@example.com',
        'phone': '(818) 555-0102',
        'status': Order.Status.READY,
        'pickup_hours': 2,
        'placed_hours_ago': 5,
        'started_hours_ago': 3,
        'ready_hours_ago': 1,
        'items': [('chocolate', 'Large · Chocolate', 1, 'No nuts')],
    },
    {
        'public_id': 'CK-900004',
        'name': 'Demo Customer Two',
        'email': 'demo.customer2@example.com',
        'phone': '(818) 555-0102',
        'status': Order.Status.DONE,
        'pickup_hours': -20,
        'placed_hours_ago': 26,
        'started_hours_ago': 24,
        'ready_hours_ago': 22,
        'items': [('redvelvet', 'Small · Red Velvet', 1, '')],
    },
    {
        'public_id': 'CK-900005',
        'name': 'Guest Buyer',
        'email': 'guest.buyer@example.com',
        'phone': '',
        'status': Order.Status.PLACED,
        'pickup_hours': 48,
        'placed_hours_ago': 1,
        'items': [('cupcake', 'Box of 12', 1, ''), ('croissant', 'Almond', 6, '')],
    },
]

SEED_ORDER_IDS = tuple(order['public_id'] for order in ORDERS)
SEEDS_BY_ID = {order['public_id']: order for order in ORDERS}


def matches_seed(order, seed):
    return order.customer_name == seed['name'] and order.email.casefold() == seed['email'].casefold()


class Command(BaseCommand):
    help = 'Create (or reset) representative development customers and orders.'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true', help='Delete and recreate only the known seed records.')
        parser.add_argument(
            '--allow-production',
            action='store_true',
            help='Acknowledge that seed data is being added while DEBUG is disabled.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG and not options['allow_production']:
            raise CommandError('Refusing to seed while DEBUG is disabled. Use --allow-production only for an intentional demo environment.')

        User = get_user_model()
        if options['reset']:
            for existing in Order.objects.filter(public_id__in=SEED_ORDER_IDS):
                if not matches_seed(existing, SEEDS_BY_ID[existing.public_id]):
                    raise CommandError(f'Order ID {existing.public_id} belongs to a non-seed order and will not be deleted.')
            Order.objects.filter(public_id__in=SEED_ORDER_IDS).delete()
            for username, email in CUSTOMERS:
                User.objects.filter(username=username, email__iexact=email).delete()

        demo_password = os.environ.get('SEED_DEMO_PASSWORD')
        for username, email in CUSTOMERS:
            user = User.objects.filter(username=username).first()
            if user and user.email.casefold() != email.casefold():
                raise CommandError(f'Username {username!r} already belongs to a different email address.')
            if not user:
                user = User(username=username, email=email)
                if demo_password:
                    user.set_password(demo_password)
                else:
                    user.set_unusable_password()
                user.save()

        now = timezone.now()
        made = 0
        for seed in ORDERS:
            existing = Order.objects.filter(public_id=seed['public_id']).first()
            if existing:
                if not matches_seed(existing, seed):
                    raise CommandError(f"Order ID {seed['public_id']} already belongs to a non-seed order.")
                continue

            lines = []
            for product_id, detail, quantity, note in seed['items']:
                product = CATALOG[product_id]
                option = detail.split(' · ', 1)[0]
                price = Decimal(str(product['options'][option] if 'options' in product else product['price']))
                lines.append((product_id, product['name'], detail, quantity, price, note))

            subtotal = sum((price * quantity for _, _, _, quantity, price, _ in lines), start=Decimal('0.00'))
            tax = (subtotal * TAX_RATE).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            order = Order.objects.create(
                public_id=seed['public_id'],
                customer_name=seed['name'],
                email=seed['email'],
                phone=seed['phone'],
                status=seed['status'],
                pickup_at=now + timedelta(hours=seed['pickup_hours']),
                started_at=now - timedelta(hours=seed['started_hours_ago']) if seed.get('started_hours_ago') else None,
                ready_at=now - timedelta(hours=seed['ready_hours_ago']) if seed.get('ready_hours_ago') else None,
                notification_email=seed.get('notification_email', ''),
                subtotal=subtotal,
                tax=tax,
                total=subtotal + tax,
            )
            Order.objects.filter(pk=order.pk).update(placed_at=now - timedelta(hours=seed['placed_hours_ago']))
            OrderItem.objects.bulk_create(
                OrderItem(
                    order=order,
                    product_id=product_id,
                    name=product_name,
                    detail=detail,
                    quantity=quantity,
                    unit_price=price,
                    note=note,
                )
                for product_id, product_name, detail, quantity, price, note in lines
            )
            made += 1

        total = Order.objects.filter(public_id__in=SEED_ORDER_IDS).count()
        self.stdout.write(self.style.SUCCESS(f'Seed complete: {made} new orders, {total} seeded orders in total.'))
