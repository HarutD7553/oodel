from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from . import data
from .models import Order
from .serializers import NotificationSerializer, OrderCreateSerializer


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
    serializer = OrderCreateSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    order = serializer.save()
    return Response(customer_order(order), status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([AllowAny])
def retrieve_order(request, public_id):
    email = request.query_params.get('email', '').strip()
    if not email:
        raise ValidationError({'email': 'Email is required.'})
    return Response(customer_order(data.get_order(public_id, email=email)))


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_notification(request, public_id):
    serializer = NotificationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    order = data.get_order(public_id, email=request.user.email)
    data.set_notification_email(order, serializer.validated_data['notification_email'])
    return Response({'notification_email': order.notification_email or None})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def staff_login(request):
    if not request.user.is_staff:
        raise PermissionDenied('Staff access is required.')
    return Response({'username': request.user.get_username()})


@api_view(['GET'])
@permission_classes([IsAdminUser])
def staff_orders(request):
    return Response([staff_order(order) for order in data.list_active_orders()])


@api_view(['GET', 'DELETE'])
@permission_classes([IsAdminUser])
def staff_order_detail(request, public_id):
    order = data.get_order(public_id)
    if request.method == 'DELETE':
        data.delete_order(order)
        return Response(status=status.HTTP_204_NO_CONTENT)
    return Response(staff_order(order))


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def update_order_status(request, public_id):
    order = data.get_order(public_id)
    expected = NEXT_STATUS.get(order.status)
    if expected is None:
        raise ValidationError({'status': 'This order has already been picked up.'})
    if request.data.get('status') != expected:
        raise ValidationError({'status': f'Next status must be {expected.value!r}.'})
    return Response(staff_order(data.set_status(order, expected)))
