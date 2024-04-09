from http import HTTPStatus

from django.test import Client, TestCase


class FrontendAPITestCase(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_web_site_exists(self):
        """Проверка доступности сайта."""
        response = self.guest_client.get('/api/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
