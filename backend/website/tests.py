from django.test import TestCase, Client
from django.urls import reverse
from website.models import DemoRequest


class WebsiteTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_homepage_loads(self):
        """Home page should return 200 and contain branding and loan calculator elements."""
        response = self.client.get(reverse('website:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "FinTrack")
        self.assertContains(response, "calc-principal")
        self.assertContains(response, "Annual Unlimited Plan")

    def test_demo_request_submission(self):
        """Demo request form submission creates a DemoRequest record."""
        response = self.client.post(reverse('website:demo_request'), {
            'name': 'Prakash Narayanan',
            'phone': '9842144444',
            'email': 'prakash@example.com',
            'company_name': 'Kavach Finance',
            'city': 'Madurai',
            'loan_types': 'Daily chit collection'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(DemoRequest.objects.count(), 1)
        demo = DemoRequest.objects.first()
        self.assertEqual(demo.name, 'Prakash Narayanan')
        self.assertEqual(demo.company_name, 'Kavach Finance')

    def test_privacy_and_terms_pages(self):
        """Privacy policy and Terms pages load successfully."""
        p_res = self.client.get(reverse('website:privacy'))
        self.assertEqual(p_res.status_code, 200)
        self.assertContains(p_res, "DPDP Act")

        t_res = self.client.get(reverse('website:terms'))
        self.assertEqual(t_res.status_code, 200)
