from datetime import timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from accounts.models import Company, User
from members.models import Member


class MultiTenantIsolationTests(TestCase):
    def setUp(self):
        # Company A
        self.company_a = Company.objects.create(
            name="Alpha Finance",
            phone="9876543210",
            email="alpha@test.com",
            subscription_status="ACTIVE"
        )
        self.user_a = User.objects.create_user(
            username="user_alpha",
            password="password123",
            company=self.company_a,
            role="OWNER"
        )
        self.member_a = Member.objects.create(
            company=self.company_a,
            name="Borrower Alpha",
            phone="9999911111",
            address="Street A"
        )

        # Company B
        self.company_b = Company.objects.create(
            name="Beta Finance",
            phone="9876543211",
            email="beta@test.com",
            subscription_status="ACTIVE"
        )
        self.user_b = User.objects.create_user(
            username="user_beta",
            password="password123",
            company=self.company_b,
            role="OWNER"
        )
        self.member_b = Member.objects.create(
            company=self.company_b,
            name="Borrower Beta",
            phone="9999922222",
            address="Street B"
        )

        self.client_a = Client()
        self.client_a.login(username="user_alpha", password="password123")

        self.client_b = Client()
        self.client_b.login(username="user_beta", password="password123")

    def test_member_list_isolation(self):
        """Company A must never see Company B's members in list view."""
        response = self.client_a.get(reverse('members:member_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Borrower Alpha")
        self.assertNotContains(response, "Borrower Beta")

    def test_member_detail_cross_tenant_forbidden(self):
        """User from Company A accessing Member from Company B must receive 404."""
        response = self.client_a.get(reverse('members:member_detail', kwargs={'pk': self.member_b.pk}))
        self.assertEqual(response.status_code, 404)


class SubscriptionLockMiddlewareTests(TestCase):
    def setUp(self):
        self.expired_company = Company.objects.create(
            name="Expired Lending Co",
            phone="9842100000",
            email="exp@test.com",
            subscription_status="EXPIRED",
            trial_ends_at=timezone.now() - timedelta(days=5)
        )
        self.user = User.objects.create_user(
            username="expired_owner",
            password="password123",
            company=self.expired_company,
            role="OWNER"
        )
        self.client = Client()
        self.client.login(username="expired_owner", password="password123")

    def test_locked_access_redirects_to_pricing(self):
        """When company trial has expired, access to dashboard/collections must redirect to pricing."""
        response = self.client.get(reverse('reports:dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(reverse('billing:pricing') in response.url)

    def test_exempt_billing_routes_accessible(self):
        """Billing routes must remain accessible so the user can pay and renew."""
        response = self.client.get(reverse('billing:pricing'))
        self.assertEqual(response.status_code, 200)
