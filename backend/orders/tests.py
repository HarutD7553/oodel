import base64
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Order


class OrderApiTests(APITestCase):
    def setUp(self):
        self.payload = {
            'name': 'Ada Baker',
            'email': 'ada@example.com',
            'phone': '(818) 555-0100',
            'pickup_at': (timezone.now() + timedelta(days=1)).isoformat(),
            'payment': 'cash',
            'items': [
                {
                    'product_id': 'strawberry',
                    'detail': 'Medium · Strawberry',
                    'quantity': 2,
                    'note': 'Happy birthday',
                }
            ],
        }

    def create_order(self):
        return self.client.post(reverse('order-create'), self.payload, format='json')

    def test_customer_can_create_and_retrieve_an_order(self):
        response = self.create_order()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertRegex(response.data['id'], r'^CK-\d{6}$')
        self.assertEqual(response.data['totals'], {'sub': 48.0, 'tax': 4.56, 'total': 52.56})
        self.assertEqual(Order.objects.count(), 1)

        detail = self.client.get(
            reverse('order-detail', args=(response.data['id'],)),
            {'email': 'ADA@example.com'},
        )
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        self.assertEqual(detail.data['items'][0]['name'], 'Strawberry Cake')

    def test_order_lookup_requires_the_matching_email(self):
        created = self.create_order().data

        response = self.client.get(
            reverse('order-detail', args=(created['id'],)),
            {'email': 'somebody-else@example.com'},
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_local_frontend_origin_is_allowed_by_cors(self):
        response = self.client.options(
            reverse('order-create'),
            HTTP_ORIGIN='http://localhost:5173',
            HTTP_ACCESS_CONTROL_REQUEST_METHOD='POST',
        )

        self.assertEqual(response['access-control-allow-origin'], 'http://localhost:5173')

    def test_server_rejects_client_supplied_prices_and_unknown_options(self):
        self.payload['items'][0]['detail'] = 'Gigantic · Strawberry'

        response = self.create_order()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Order.objects.count(), 0)

    def test_staff_can_log_in_list_orders_and_advance_status(self):
        created = self.create_order().data
        user = get_user_model().objects.create_user(
            username='baker',
            password='strong-test-password',
            is_staff=True,
        )
        encoded = base64.b64encode(b'baker:strong-test-password').decode('ascii')
        self.client.credentials(HTTP_AUTHORIZATION=f'Basic {encoded}')

        login = self.client.post(reverse('staff-login'))
        listing = self.client.get(reverse('staff-orders'))
        updated = self.client.patch(
            reverse('staff-order-status', args=(created['id'],)),
            {'status': 'baking'},
            format='json',
        )

        self.assertEqual(login.status_code, status.HTTP_200_OK)
        self.assertEqual(login.data['username'], user.username)
        self.assertEqual(listing.status_code, status.HTTP_200_OK)
        self.assertEqual(len(listing.data), 1)
        self.assertEqual(updated.status_code, status.HTTP_200_OK)
        self.assertEqual(updated.data['status'], 'baking')
        self.assertTrue(Order.objects.get().started_at)
