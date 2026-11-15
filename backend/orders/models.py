import secrets

from django.db import models


def generate_order_id():
    return f'CK-{secrets.randbelow(900_000) + 100_000}'


class Order(models.Model):
    class Status(models.TextChoices):
        PLACED = 'placed', 'Placed'
        BAKING = 'baking', 'Baking'
        READY = 'ready', 'Ready for pickup'
        DONE = 'done', 'Picked up'

    class Payment(models.TextChoices):
        CASH = 'cash', 'Cash on pickup'
        PAID = 'paid', 'Paid online'

    public_id = models.CharField(max_length=16, unique=True, default=generate_order_id, editable=False)
    customer_name = models.CharField(max_length=120)
    email = models.EmailField(db_index=True)
    phone = models.CharField(max_length=30, blank=True)
    status = models.CharField(max_length=12, choices=Status, default=Status.PLACED, db_index=True)
    payment = models.CharField(max_length=12, choices=Payment, default=Payment.CASH)
    pickup_at = models.DateTimeField(db_index=True)
    placed_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ready_at = models.DateTimeField(null=True, blank=True)
    notification_email = models.EmailField(blank=True)
    subtotal = models.DecimalField(max_digits=9, decimal_places=2)
    tax = models.DecimalField(max_digits=9, decimal_places=2)
    total = models.DecimalField(max_digits=9, decimal_places=2)

    class Meta:
        ordering = ('pickup_at', 'placed_at')

    def __str__(self):
        return f'{self.public_id} - {self.customer_name}'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product_id = models.CharField(max_length=32)
    name = models.CharField(max_length=120)
    detail = models.CharField(max_length=160)
    quantity = models.PositiveSmallIntegerField()
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)
    note = models.CharField(max_length=240, blank=True)

    def __str__(self):
        return f'{self.quantity}x {self.name}'
