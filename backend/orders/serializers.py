from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from .models import Order, OrderItem


CATALOG = {
    'strawberry': {'name': 'Strawberry Cake', 'options': {'Small': 18, 'Medium': 24, 'Large': 32}},
    'chocolate': {'name': 'Chocolate Cake', 'options': {'Small': 16, 'Medium': 22, 'Large': 28}},
    'redvelvet': {'name': 'Red Velvet Cake', 'options': {'Small': 20, 'Medium': 26, 'Large': 34}},
    'cupcake': {'name': 'Vanilla Cupcake', 'options': {'Box of 4': 14, 'Box of 6': 20, 'Box of 12': 36}},
    'croissant': {'name': 'Croissant', 'price': 6},
}
TAX_RATE = Decimal('0.095')


class OrderItemInputSerializer(serializers.Serializer):
    product_id = serializers.CharField(max_length=32)
    detail = serializers.CharField(max_length=160)
    quantity = serializers.IntegerField(min_value=1, max_value=20)
    note = serializers.CharField(max_length=240, allow_blank=True, required=False, default='')

    def validate(self, attrs):
        product = CATALOG.get(attrs['product_id'])
        if not product:
            raise serializers.ValidationError({'product_id': 'Unknown menu item.'})

        option = attrs['detail'].split(' · ', 1)[0]
        if 'options' in product:
            price = product['options'].get(option)
            if price is None:
                raise serializers.ValidationError({'detail': 'Unknown size or box option.'})
        else:
            price = product['price']

        attrs['name'] = product['name']
        attrs['unit_price'] = Decimal(str(price))
        return attrs


class OrderCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=120)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=30, allow_blank=True, required=False, default='')
    pickup_at = serializers.DateTimeField()
    payment = serializers.ChoiceField(choices=(Order.Payment.CASH,))
    items = OrderItemInputSerializer(many=True, allow_empty=False)

    def validate_pickup_at(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError('Pickup time must be in the future.')
        return value

    @transaction.atomic
    def create(self, validated_data):
        items = validated_data.pop('items')
        subtotal = sum(
            (item['unit_price'] * item['quantity'] for item in items),
            start=Decimal('0.00'),
        )
        tax = (subtotal * TAX_RATE).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        order = Order.objects.create(
            customer_name=validated_data['name'],
            email=validated_data['email'],
            phone=validated_data.get('phone', ''),
            pickup_at=validated_data['pickup_at'],
            payment=validated_data['payment'],
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
