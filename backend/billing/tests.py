from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import Company, User
from billing.models import SubscriptionPlan, Invoice, RazorpayOrder
from billing.services import verify_razorpay_signature


class BillingTests(TestCase):
    def setUp(self):
        self.company = Company.objects.create(
            name="Apex Capital",
            phone="9842100000",
            email="apex@test.com",
            subscription_status="TRIALING"
        )
        self.user = User.objects.create_user(
            username="apex_admin",
            password="password123",
            company=self.company,
            role="OWNER"
        )
        self.client = Client()
        self.client.login(username="apex_admin", password="password123")

    def test_pricing_page_renders_annual_plan(self):
        """Pricing page displays the ₹1,000 annual plan and trial banner."""
        response = self.client.get(reverse('billing:pricing'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "1000")
        self.assertContains(response, "Annual")
        plan = SubscriptionPlan.objects.get(code="ANNUAL_1000")
        self.assertEqual(plan.price, Decimal('1000.00'))
        self.assertTrue(verify_razorpay_signature('order_mock_test', 'pay_123', 'sig_123'))

    def test_verify_payment_success_activates_subscription(self):
        """Successful payment verification marks company ACTIVE and creates an invoice."""
        order = RazorpayOrder.objects.create(
            company=self.company,
            order_id="order_mock_test12345",
            amount=Decimal('1180.00'),
            currency="INR"
        )

        response = self.client.post(reverse('billing:verify_payment'), {
            'razorpay_order_id': order.order_id,
            'razorpay_payment_id': 'pay_mock_123',
            'razorpay_signature': 'sig_mock_123'
        })

        self.assertEqual(response.status_code, 302)

        self.company.refresh_from_db()
        self.assertEqual(self.company.subscription_status, 'ACTIVE')
        self.assertTrue(self.company.is_subscription_active())

        # Verify Invoice generated
        invoice = Invoice.objects.filter(company=self.company).first()
        self.assertIsNotNone(invoice)
        self.assertEqual(invoice.status, 'PAID')
        self.assertEqual(invoice.total_amount, Decimal('1180.00'))
