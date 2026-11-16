from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class AccountApiTests(APITestCase):
    def registration_payload(self, **overrides):
        payload = {
            'username': 'customer',
            'email': 'customer@example.com',
            'password': 'Fresh-Cake-2026!',
        }
        payload.update(overrides)
        return payload

    def test_user_can_register_and_read_profile(self):
        response = self.client.post(reverse('auth-register'), self.registration_payload(), format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['token'])
        self.assertEqual(response.data['user']['email'], 'customer@example.com')
        self.assertNotIn('password', response.data['user'])

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {response.data['token']}")
        profile = self.client.get(reverse('auth-me'))
        self.assertEqual(profile.status_code, status.HTTP_200_OK)
        self.assertEqual(profile.data['username'], 'customer')

    def test_duplicate_email_is_rejected_case_insensitively(self):
        get_user_model().objects.create_user(
            username='existing',
            email='Customer@Example.com',
            password='Fresh-Cake-2026!',
        )

        response = self.client.post(reverse('auth-register'), self.registration_payload(), format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_weak_password_is_rejected(self):
        response = self.client.post(
            reverse('auth-register'),
            self.registration_payload(password='password'),
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_login_logout_and_invalid_credentials(self):
        user = get_user_model().objects.create_user(**self.registration_payload())

        invalid = self.client.post(
            reverse('auth-login'),
            {'username': user.username, 'password': 'wrong'},
            format='json',
        )
        self.assertEqual(invalid.status_code, status.HTTP_400_BAD_REQUEST)

        login = self.client.post(
            reverse('auth-login'),
            {'username': user.username, 'password': 'Fresh-Cake-2026!'},
            format='json',
        )
        self.assertEqual(login.status_code, status.HTTP_200_OK)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {login.data['token']}")
        logout = self.client.post(reverse('auth-logout'))
        self.assertEqual(logout.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(self.client.get(reverse('auth-me')).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_requires_authentication(self):
        response = self.client.get(reverse('auth-me'))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
