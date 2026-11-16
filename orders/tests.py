import base64
from datetime import timedelta
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Order


class OrderApiTests(APITestCase):
    def setUp(self):
        self.customer = get_user_model().objects.create_user(
            username='customer',
            email='ada@example.com',
            password='strong-test-password',
        )
        token = Token.objects.create(user=self.customer)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
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

        self.client.credentials()
        detail = self.client.get(
            reverse('order-detail', args=(response.data['id'],)),
            {'email': 'ADA@example.com'},
        )
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        self.assertEqual(detail.data['items'][0]['name'], 'Strawberry Cake')

    def test_order_lookup_requires_the_matching_email(self):
        created = self.create_order().data
        self.client.credentials()

        response = self.client.get(
            reverse('order-detail', args=(created['id'],)),
            {'email': 'somebody-else@example.com'},
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_local_frontend_origin_is_allowed_by_cors(self):
        self.client.credentials()
        response = self.client.options(
            reverse('order-create'),
            HTTP_ORIGIN='http://localhost:5173',
            HTTP_ACCESS_CONTROL_REQUEST_METHOD='POST',
        )

        self.assertEqual(response['access-control-allow-origin'], 'http://localhost:5173')

    def test_guest_can_place_an_order(self):
        self.client.credentials()

        response = self.create_order()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['email'], self.payload['email'])
        self.assertEqual(Order.objects.count(), 1)

    def test_authenticated_user_email_is_used_for_new_order(self):
        self.payload['email'] = 'somebody-else@example.com'

        response = self.create_order()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['email'], self.customer.email)

    def test_notification_changes_require_matching_authenticated_account(self):
        created = self.create_order().data
        response = self.client.patch(
            reverse('order-notification', args=(created['id'],)),
            {'notification_email': 'notify@example.com'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        other = get_user_model().objects.create_user(
            username='other',
            email='other@example.com',
            password='strong-test-password',
        )
        other_token = Token.objects.create(user=other)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {other_token.key}')
        forbidden = self.client.patch(
            reverse('order-notification', args=(created['id'],)),
            {'notification_email': 'other@example.com'},
            format='json',
        )
        self.assertEqual(forbidden.status_code, status.HTTP_404_NOT_FOUND)

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


class ApiContractTests(APITestCase):
    """Delete support and the shared error shape documented in backend/API.md."""

    def setUp(self):
        User = get_user_model()
        User.objects.create_user(username='baker', password='strong-test-password', is_staff=True)
        self.customer = User.objects.create_user(
            username='customer', email='ada@example.com', password='strong-test-password',
        )
        self.staff_auth = 'Basic ' + base64.b64encode(b'baker:strong-test-password').decode('ascii')
        self.customer_auth = f'Token {Token.objects.create(user=self.customer).key}'
        self.payload = {
            'name': 'Ada Baker',
            'email': 'ada@example.com',
            'pickup_at': (timezone.now() + timedelta(days=1)).isoformat(),
            'payment': 'cash',
            'items': [{'product_id': 'croissant', 'detail': 'Plain', 'quantity': 1}],
        }

    def place_order(self):
        return self.client.post(reverse('order-create'), self.payload, format='json').data['id']

    def test_validation_errors_use_the_shared_shape(self):
        response = self.client.post(reverse('order-create'), {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIsInstance(response.data['detail'], str)
        self.assertIn('email', response.data['errors'])

    def test_not_found_uses_the_shared_shape(self):
        response = self.client.get(reverse('order-detail', args=('CK-000000',)), {'email': 'a@b.com'})

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['errors'], {})
        self.assertIsInstance(response.data['detail'], str)

    def test_missing_email_on_lookup_is_a_validation_error(self):
        response = self.client.get(reverse('order-detail', args=('CK-000000',)))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data['errors'])

    def test_invalid_notification_email_is_rejected(self):
        order_id = self.place_order()
        self.client.credentials(HTTP_AUTHORIZATION=self.customer_auth)

        response = self.client.patch(
            reverse('order-notification', args=(order_id,)), {'notification_email': 'nope'}, format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('notification_email', response.data['errors'])

    def test_staff_can_read_then_delete_an_order(self):
        order_id = self.place_order()
        self.client.credentials(HTTP_AUTHORIZATION=self.staff_auth)
        url = reverse('staff-order-detail', args=(order_id,))

        self.assertEqual(self.client.get(url).data['id'], order_id)
        self.assertEqual(self.client.delete(url).status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(self.client.get(url).status_code, status.HTTP_404_NOT_FOUND)

    def test_only_staff_can_delete_orders(self):
        order_id = self.place_order()
        url = reverse('staff-order-detail', args=(order_id,))

        self.assertEqual(self.client.delete(url).status_code, status.HTTP_401_UNAUTHORIZED)
        self.client.credentials(HTTP_AUTHORIZATION=self.customer_auth)
        self.assertEqual(self.client.delete(url).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Order.objects.count(), 1)

    def test_status_cannot_skip_a_step(self):
        order_id = self.place_order()
        self.client.credentials(HTTP_AUTHORIZATION=self.staff_auth)

        response = self.client.patch(
            reverse('staff-order-status', args=(order_id,)), {'status': 'ready'}, format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('status', response.data['errors'])
        self.assertEqual(Order.objects.get().status, 'placed')


@override_settings(DEBUG=True)
class SeedDataCommandTests(TestCase):
    def run_seed(self, *args):
        output = StringIO()
        call_command('seed_dev_data', *args, stdout=output)
        return output.getvalue()

    def test_seed_data_is_representative_idempotent_and_related(self):
        first_output = self.run_seed()
        second_output = self.run_seed()

        self.assertIn('5 new orders', first_output)
        self.assertIn('0 new orders', second_output)
        self.assertEqual(Order.objects.filter(public_id__in=[f'CK-90000{i}' for i in range(1, 6)]).count(), 5)
        self.assertSetEqual(
            set(Order.objects.values_list('status', flat=True)),
            {Order.Status.PLACED, Order.Status.BAKING, Order.Status.READY, Order.Status.DONE},
        )

        baking = Order.objects.get(public_id='CK-900002')
        self.assertEqual(baking.items.count(), 2)
        self.assertEqual(
            set(baking.items.values_list('detail', flat=True)),
            {'Box of 6', 'Butter'},
        )
        self.assertLess(baking.placed_at, baking.started_at)
        self.assertLess(baking.started_at, baking.pickup_at)

        customer = get_user_model().objects.get(username='demo_customer')
        self.assertFalse(customer.has_usable_password())
        self.assertTrue(Order.objects.filter(email__iexact=customer.email).exists())

    def test_reset_does_not_delete_normal_orders_with_similar_ids(self):
        self.run_seed()
        normal_order = Order.objects.create(
            public_id='CK-999999',
            customer_name='Real Customer',
            email='real.customer@example.com',
            pickup_at=timezone.now() + timedelta(days=1),
            subtotal='10.00',
            tax='0.95',
            total='10.95',
        )

        self.run_seed('--reset')

        self.assertTrue(Order.objects.filter(pk=normal_order.pk).exists())
        self.assertEqual(Order.objects.filter(public_id__in=[f'CK-90000{i}' for i in range(1, 6)]).count(), 5)

    def test_reset_refuses_to_delete_an_order_that_collides_with_a_seed_id(self):
        normal_order = Order.objects.create(
            public_id='CK-900001',
            customer_name='Real Customer',
            email='real.customer@example.com',
            pickup_at=timezone.now() + timedelta(days=1),
            subtotal='10.00',
            tax='0.95',
            total='10.95',
        )

        with self.assertRaises(CommandError):
            self.run_seed('--reset')

        self.assertTrue(Order.objects.filter(pk=normal_order.pk).exists())

    @override_settings(DEBUG=False)
    def test_seed_requires_explicit_acknowledgement_when_debug_is_off(self):
        with self.assertRaises(CommandError):
            self.run_seed()
