from datetime import date, timedelta
from decimal import Decimal
from django.test import TestCase
from accounts.models import Company, User
from members.models import Member
from loans.models import Loan, Installment
from loan_collections.models import Payment
from reports.services.excel_exporter import export_daily_collections_excel
from reports.services.pdf_exporter import render_to_pdf
from reports.tasks import mark_overdue_installments, send_daily_owner_summary


class ReportsAndAutomationTests(TestCase):
    def setUp(self):
        self.company = Company.objects.create(
            name="Report Test Corp",
            phone="9842100000",
            email="rtc@test.com"
        )
        self.user = User.objects.create_user(
            username="rep_user",
            password="password123",
            company=self.company,
            role="OWNER"
        )
        self.member = Member.objects.create(
            company=self.company,
            name="Test Customer",
            phone="9842188888",
            address="Market Cross"
        )
        self.loan = Loan.objects.create(
            company=self.company,
            member=self.member,
            loan_type='DAILY',
            principal_amount=Decimal('1000.00'),
            interest_rate_percent=Decimal('10.00'),
            interest_amount=Decimal('100.00'),
            disbursed_amount=Decimal('980.00'),
            total_amount=Decimal('1100.00'),
            start_date=date.today() - timedelta(days=5),
            end_date=date.today() + timedelta(days=5),
            number_of_installments=5,
            installment_amount=Decimal('220.00'),
            outstanding_balance=Decimal('1100.00')
        )

    def test_excel_export_returns_valid_bytes(self):
        """Verify openpyxl exporter returns valid non-empty byte buffer."""
        payment = Payment.objects.create(
            company=self.company,
            loan=self.loan,
            amount=Decimal('220.00'),
            payment_mode='CASH',
            collected_by=self.user
        )
        excel_bytes = export_daily_collections_excel(self.company, [payment], date.today())
        self.assertGreater(len(excel_bytes), 1000)
        # Check ZIP / XLSX signature (first 2 bytes are PK = 0x50, 0x4B)
        self.assertEqual(excel_bytes[:2], b'PK')

    def test_mark_overdue_installments_task(self):
        """Past due installments must be transitioned to OVERDUE by the Celery task."""
        past_inst = Installment.objects.create(
            loan=self.loan,
            installment_number=1,
            due_date=date.today() - timedelta(days=3),
            expected_amount=Decimal('220.00'),
            pending_amount=Decimal('220.00'),
            status='PENDING'
        )

        future_inst = Installment.objects.create(
            loan=self.loan,
            installment_number=2,
            due_date=date.today() + timedelta(days=2),
            expected_amount=Decimal('220.00'),
            pending_amount=Decimal('220.00'),
            status='PENDING'
        )

        mark_overdue_installments()

        past_inst.refresh_from_db()
        future_inst.refresh_from_db()

        self.assertEqual(past_inst.status, 'OVERDUE')
        self.assertEqual(future_inst.status, 'PENDING')

    def test_pdf_export_returns_valid_bytes(self):
        """Verify render_to_pdf creates a non-empty PDF document."""
        payment = Payment.objects.create(
            company=self.company,
            loan=self.loan,
            amount=Decimal('220.00'),
            payment_mode='CASH',
            collected_by=self.user
        )
        pdf_bytes = render_to_pdf('reports/pdf/daily_collection_pdf.html', {
            'company': self.company,
            'payments': [payment],
            'target_date': date.today(),
            'total_collected': Decimal('220.00'),
            'cash_total': Decimal('220.00'),
            'upi_total': Decimal('0.00')
        })
        self.assertIsNotNone(pdf_bytes)
        self.assertGreater(len(pdf_bytes), 100)
        # Check PDF signature (%PDF-)
        self.assertTrue(pdf_bytes.startswith(b'%PDF-'))

    def test_send_daily_owner_summary_task(self):
        """Verify daily owner summary task executes and logs summary without encoding issues."""
        result = send_daily_owner_summary()
        self.assertIn("Dispatched", result)
