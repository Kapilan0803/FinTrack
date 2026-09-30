from datetime import date
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from accounts.models import Company, User
from members.models import Member
from loans.models import LoanPlan, Loan
from loans.services import generate_loan_schedule
from loan_collections.models import CollectionAttempt
from loan_collections.services import (
    record_collection,
    calculate_installment_penalty,
    submit_cash_closing
)


class CollectionProcessingTests(TestCase):
    def setUp(self):
        self.company = Company.objects.create(
            name="Fast Recoveries",
            phone="9842100000",
            email="fr@test.com",
            subscription_status="ACTIVE"
        )
        self.user = User.objects.create_user(
            username="test_agent",
            password="password123",
            company=self.company,
            role="AGENT"
        )
        self.plan = LoanPlan.objects.create(
            company=self.company,
            name="Standard Daily",
            loan_type='DAILY',
            default_interest_rate_percent=Decimal('10.00'),
            default_duration_units=10,
            penalty_rate_percent=Decimal('2.00')
        )
        self.member1 = Member.objects.create(
            company=self.company,
            name="Senthil M.",
            phone="9842155555",
            address="South Street",
            visit_order=2,
            area_or_route="Route A",
            assigned_agent=self.user
        )
        self.member2 = Member.objects.create(
            company=self.company,
            name="Anand K.",
            phone="9842166666",
            address="North Street",
            visit_order=1,
            area_or_route="Route A",
            assigned_agent=self.user
        )
        self.loan = Loan.objects.create(
            company=self.company,
            member=self.member1,
            loan_plan=self.plan,
            loan_type='DAILY',
            principal_amount=Decimal('1000.00'),
            interest_rate_percent=Decimal('10.00'),
            interest_amount=Decimal('100.00'),
            disbursed_amount=Decimal('980.00'),
            total_amount=Decimal('1100.00'),
            start_date=date(2026, 10, 1),
            end_date=date(2026, 10, 11),
            number_of_installments=10,
            installment_amount=Decimal('110.00'),
            outstanding_balance=Decimal('1100.00'),
            assigned_agent=self.user
        )
        generate_loan_schedule(self.loan)

    def test_record_single_tap_payment(self):
        """Testing payment creation, installment status update, and balance decrease."""
        inst = self.loan.installments.first()
        payment = record_collection(
            loan=self.loan,
            amount=inst.pending_amount,
            collected_by=self.user,
            payment_mode='CASH',
            installment=inst
        )

        inst.refresh_from_db()
        self.assertEqual(inst.status, 'PAID')
        self.assertEqual(inst.pending_amount, Decimal('0.00'))
        self.assertEqual(inst.paid_amount, Decimal('110.00'))

        self.loan.refresh_from_db()
        self.assertEqual(self.loan.total_paid, Decimal('110.00'))
        self.assertEqual(self.loan.outstanding_balance, Decimal('990.00'))
        self.assertTrue(payment.receipt_number.startswith('RCP-'))

    def test_quick_pay_htmx_endpoint(self):
        """Testing the 1-Tap HTMX endpoint directly."""
        client = Client()
        client.login(username="test_agent", password="password123")

        inst = self.loan.installments.first()
        response = client.post(reverse('collections:quick_pay', kwargs={'installment_id': inst.id}), {
            'payment_mode': 'CASH'
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "PAID")
        self.assertContains(response, "Thermal Receipt")

        inst.refresh_from_db()
        self.assertEqual(inst.status, 'PAID')

    def test_penalty_accrual_and_waiver(self):
        """Testing calculation of late penalty and fee waiver."""
        inst = self.loan.installments.first()
        inst.due_date = date(2026, 9, 20)
        inst.status = 'OVERDUE'
        inst.save()

        as_of = date(2026, 9, 25)  # 5 days overdue (4 chargeable days)
        penalty = calculate_installment_penalty(inst, as_of_date=as_of)
        self.assertGreater(penalty, Decimal('0.00'))

        # Test recording payment with penalty waived
        payment = record_collection(
            loan=self.loan,
            amount=inst.pending_amount,
            collected_by=self.user,
            installment=inst,
            penalty_waived=penalty,
            waiver_reason="Customer had family emergency"
        )
        inst.refresh_from_db()
        self.assertEqual(inst.status, 'PAID')
        self.assertEqual(inst.penalty_amount, Decimal('0.00'))
        self.assertEqual(payment.penalty_waived, penalty)
        self.assertEqual(payment.waiver_reason, "Customer had family emergency")

    def test_record_missed_visit(self):
        """Testing missed visit attempt recording."""
        inst = self.loan.installments.first()
        client = Client()
        client.login(username="test_agent", password="password123")

        response = client.post(reverse('collections:mark_missed', kwargs={'installment_id': inst.id}), {
            'reason': 'SHOP_CLOSED',
            'promised_date': '2026-10-05',
            'notes': 'Shop locked, owner at market.'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Shop / Stall Closed")

        attempt = CollectionAttempt.objects.filter(installment=inst).first()
        self.assertIsNotNone(attempt)
        self.assertEqual(attempt.reason, 'SHOP_CLOSED')
        self.assertEqual(attempt.promised_date, date(2026, 10, 5))

    def test_interest_only_principal_buyout(self):
        """Testing bullet principal settlement on interest-only loans."""
        interest_loan = Loan.objects.create(
            company=self.company,
            member=self.member2,
            loan_type='MONTHLY_INTEREST',
            principal_amount=Decimal('50000.00'),
            interest_rate_percent=Decimal('2.00'),
            interest_amount=Decimal('12000.00'),
            disbursed_amount=Decimal('49000.00'),
            total_amount=Decimal('62000.00'),
            start_date=date(2026, 1, 1),
            end_date=date(2027, 1, 1),
            number_of_installments=12,
            installment_amount=Decimal('1000.00'),
            outstanding_balance=Decimal('62000.00'),
            assigned_agent=self.user
        )
        generate_loan_schedule(interest_loan)

        client = Client()
        client.login(username="test_agent", password="password123")

        response = client.post(reverse('collections:settle_principal', kwargs={'loan_id': interest_loan.id}), {
            'amount': '50000.00',
            'payment_mode': 'CASH',
            'notes': 'Customer settled full principal lump sum'
        })
        self.assertEqual(response.status_code, 302)

        interest_loan.refresh_from_db()
        self.assertEqual(interest_loan.status, 'CLOSED')
        self.assertEqual(interest_loan.closure_reason, 'COMPLETED')
        self.assertEqual(interest_loan.outstanding_balance, Decimal('0.00'))

    def test_daily_cash_closing_denomination_reconciler(self):
        """Testing physical cash calculation against system collections."""
        # 1. Record a collection of ₹1700
        inst = self.loan.installments.first()
        record_collection(
            loan=self.loan,
            amount=Decimal('1700.00'),
            collected_by=self.user,
            payment_mode='CASH',
            installment=inst
        )

        today = timezone.now().date()
        # 2. Reconcile with 3x ₹500 + 1x ₹200 = ₹1700
        closing = submit_cash_closing(
            agent=self.user,
            closing_date=today,
            counts_dict={
                'count_500': 3,
                'count_200': 1,
                'count_100': 0,
                'count_coins': '0.00'
            },
            remarks="Exact cash balance"
        )

        self.assertEqual(closing.total_physical_cash, Decimal('1700.00'))
        self.assertEqual(closing.system_cash_collected, Decimal('1700.00'))
        self.assertEqual(closing.variance, Decimal('0.00'))
        self.assertEqual(closing.status, 'SUBMITTED')

    def test_multi_tenant_isolation(self):
        """Ensure other companies cannot see or pay installments."""
        other_company = Company.objects.create(name="Competitor Finance", phone="9999900000", email="comp@test.com")
        User.objects.create_user(username="other_agent", password="password123", company=other_company, role="AGENT")

        client = Client()
        client.login(username="other_agent", password="password123")

        inst = self.loan.installments.first()
        response = client.post(reverse('collections:quick_pay', kwargs={'installment_id': inst.id}), {
            'payment_mode': 'CASH'
        })
        # Should return 404 because company does not match
        self.assertEqual(response.status_code, 404)
