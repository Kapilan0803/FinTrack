from datetime import date, timedelta
from decimal import Decimal
from django.test import TestCase
from accounts.models import Company
from members.models import Member
from loans.models import Loan
from loans.services import generate_loan_schedule


class LoanScheduleEngineTests(TestCase):
    def setUp(self):
        self.company = Company.objects.create(
            name="Precision Finance",
            phone="9842100000",
            email="pf@test.com",
            skip_sundays_in_daily=True
        )
        self.member = Member.objects.create(
            company=self.company,
            name="Ravi Kumar",
            phone="9842177777",
            address="Gandhi Bazaar"
        )

    def test_daily_schedule_exact_paisa_sum(self):
        """
        Verify that in a 100-day loan, sum of all installment amounts
        matches total_amount down to 0 paise.
        """
        loan = Loan.objects.create(
            company=self.company,
            member=self.member,
            loan_type='DAILY',
            principal_amount=Decimal('10000.00'),
            interest_rate_percent=Decimal('10.00'),
            interest_amount=Decimal('1000.00'),
            disbursed_amount=Decimal('9800.00'),
            total_amount=Decimal('11000.00'),
            start_date=date(2026, 10, 1), # Thursday
            end_date=date(2026, 10, 1) + timedelta(days=100),
            number_of_installments=100,
            installment_amount=Decimal('110.00'),
            outstanding_balance=Decimal('11000.00')
        )

        installments = generate_loan_schedule(loan)
        self.assertEqual(len(installments), 100)

        total_scheduled = sum(inst.expected_amount for inst in installments)
        self.assertEqual(total_scheduled, Decimal('11000.00'))

    def test_sunday_skipping_logic(self):
        """
        When skip_sundays_in_daily is True, no installment should fall on a Sunday (weekday 6).
        """
        loan = Loan.objects.create(
            company=self.company,
            member=self.member,
            loan_type='DAILY',
            principal_amount=Decimal('5000.00'),
            interest_rate_percent=Decimal('10.00'),
            interest_amount=Decimal('500.00'),
            disbursed_amount=Decimal('4900.00'),
            total_amount=Decimal('5500.00'),
            start_date=date(2026, 10, 2), # Friday
            end_date=date(2026, 11, 20),
            number_of_installments=30,
            installment_amount=Decimal('183.33'),
            outstanding_balance=Decimal('5500.00')
        )

        installments = generate_loan_schedule(loan)
        for inst in installments:
            self.assertNotEqual(inst.due_date.weekday(), 6, f"Installment {inst.installment_number} fell on Sunday {inst.due_date}")

        total_scheduled = sum(inst.expected_amount for inst in installments)
        self.assertEqual(total_scheduled, Decimal('5500.00'))
