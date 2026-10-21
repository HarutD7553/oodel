from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from .models import Order
from .serializers import OrderCreateSerializer


STATUS_TO_STAGE = {
    Order.Status.PLACED: 0,
    Order.Status.BAKING: 1,
    Order.Status.READY: 2,
    Order.Status.DONE: 2,
}
NEXT_STATUS = {
    Order.Status.PLACED: Order.Status.BAKING,
    Order.Status.BAKING: Order.Status.READY,
    Order.Status.READY: Order.Status.DONE,
}


def local_time(value, include_date=False):
    value = timezone.localtime(value)
    time_text = value.strftime('%I:%M %p').lstrip('0')
    if not include_date:
        return time_text
    date_text = value.strftime('%b %d').replace(' 0', ' ')
    return f'{date_text} · {time_text}'


def customer_order(order):
    return {
        'id': order.public_id,
        'demo': False,
        'email': order.email,
        'name': order.customer_name,
        'phone': order.phone,
        'pay': order.payment,
        'stage': STATUS_TO_STAGE[order.status],
        'status': order.status,
        'placedAt': local_time(order.placed_at),
        'pickup': local_time(order.pickup_at, include_date=True),
        'notify': order.notification_email or None,
        'items': [
            {
                'id': item.product_id,
                'name': item.name,
                'detail': item.detail,
                'qty': item.quantity,
                'unit': float(item.unit_price),
                'note': item.note,
            }
            for item in order.items.all()
        ],
        'totals': {
            'sub': float(order.subtotal),
            'tax': float(order.tax),
            'total': float(order.total),
        },
    }


def staff_order(order):
    notes = [item.note for item in order.items.all() if item.note]
    data = {
        'id': order.public_id,
        'customer': order.customer_name,
        'phone': order.phone,
        'email': order.email,
        'status': order.status,
        'placedAt': local_time(order.placed_at),
        'pickup': local_time(order.pickup_at, include_date=True),
        'timer': None,
        'items': [
            {'qty': item.quantity, 'name': item.name, 'detail': item.detail}
            for item in order.items.all()
        ],
        'note': '\n'.join(notes),
        'allergens': [],
        'total': float(order.total),
        'pay': order.get_payment_display(),
    }
    if order.started_at:
        data['startedAt'] = local_time(order.started_at)
    if order.ready_at:
        data['readyAt'] = local_time(order.ready_at)
    return data


@api_view(['POST'])
@permission_classes([AllowAny])
def create_order(request):
    serializer = OrderCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    order = serializer.save()
    return Response(customer_order(order), status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([AllowAny])
def retrieve_order(request, public_id):
    email = request.query_params.get('email', '').strip()
    if not email:
        return Response({'detail': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)
    order = get_object_or_404(Order.objects.prefetch_related('items'), public_id=public_id, email__iexact=email)
    return Response(customer_order(order))


@api_view(['PATCH'])
@permission_classes([AllowAny])
def update_notification(request, public_id):
    email = request.data.get('email', '').strip()
    notification_email = request.data.get('notification_email', '').strip()
    order = get_object_or_404(Order, public_id=public_id, email__iexact=email)
    if notification_email:
        try:
            validate_email(notification_email)
        except DjangoValidationError:
            return Response({'notification_email': ['Enter a valid email address.']}, status=status.HTTP_400_BAD_REQUEST)
    order.notification_email = notification_email
    order.save(update_fields=('notification_email',))
    return Response({'notification_email': order.notification_email or None})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def staff_login(request):
    if not request.user.is_staff:
        return Response({'detail': 'Staff access is required.'}, status=status.HTTP_403_FORBIDDEN)
    return Response({'username': request.user.get_username()})


@api_view(['GET'])
@permission_classes([IsAdminUser])
def staff_orders(request):
    orders = Order.objects.exclude(status=Order.Status.DONE).prefetch_related('items')
    return Response([staff_order(order) for order in orders])


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def update_order_status(request, public_id):
    order = get_object_or_404(Order.objects.prefetch_related('items'), public_id=public_id)
    requested = request.data.get('status')
    expected = NEXT_STATUS.get(order.status)
    if not expected or requested != expected:
        return Response(
            {'status': [f'Next status must be {expected!r}.']},
            status=status.HTTP_400_BAD_REQUEST,
        )

    order.status = requested
    now = timezone.now()
    fields = ['status']
    if requested == Order.Status.BAKING:
        order.started_at = now
        fields.append('started_at')
    elif requested == Order.Status.READY:
        order.ready_at = now
        fields.append('ready_at')
    order.save(update_fields=fields)
    return Response(staff_order(order))
