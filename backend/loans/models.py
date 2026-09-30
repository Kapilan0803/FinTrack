from decimal import Decimal
from django.db import models
from accounts.models import Company, User
from members.models import Member


class LoanPlan(models.Model):
    LOAN_TYPE_CHOICES = [
        ('DAILY', 'Daily Collection'),
        ('WEEKLY', 'Weekly Collection'),
        ('MONTHLY_EMI', 'Monthly EMI (Principal + Interest)'),
        ('MONTHLY_INTEREST', 'Monthly Interest Only (Bullet Principal at End)'),
        ('WEEKLY_INTEREST', 'Weekly Interest Only (Bullet Principal at End)'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='loan_plans')
    name = models.CharField(max_length=150, verbose_name="Plan Name")
    loan_type = models.CharField(max_length=25, choices=LOAN_TYPE_CHOICES, default='DAILY')
    default_interest_rate_percent = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal('10.00'),
        verbose_name="Interest Rate (%)"
    )
    default_duration_units = models.PositiveIntegerField(
        default=100,
        verbose_name="Duration (Days / Weeks / Months)"
    )
    processing_fee_percent = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal('2.00'),
        verbose_name="Processing Fee (%)"
    )
    penalty_rate_percent = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal('1.00'),
        verbose_name="Late Penalty Fee (% or ₹/day)"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Loan Plan"
        verbose_name_plural = "Loan Plans"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_loan_type_display()})"


class Loan(models.Model):
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('CLOSED', 'Closed / Paid Off'),
        ('DEFAULTED', 'Defaulted / NPA'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='loans')
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='loans')
    loan_plan = models.ForeignKey(LoanPlan, on_delete=models.SET_NULL, null=True, blank=True, related_name='loans')
    loan_account_no = models.CharField(max_length=50, db_index=True, verbose_name="Loan Account No.")
    loan_type = models.CharField(max_length=25, choices=LoanPlan.LOAN_TYPE_CHOICES, default='DAILY')

    # Financial Amounts (Strict Decimal Precision)
    principal_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Loan Principal (₹)")
    interest_rate_percent = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="Interest Rate (%)")
    interest_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Interest Amount (₹)")
    processing_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Processing Fee (₹)")
    disbursed_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Disbursed Amount (₹)")
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Total Repayable (₹)")

    start_date = models.DateField(verbose_name="Start / First EMI Date")
    end_date = models.DateField(verbose_name="Maturity Date")
    number_of_installments = models.PositiveIntegerField(verbose_name="No. of Installments")
    installment_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="EMI / Installment (₹)")

    # Real-Time Ledger Tracking
    total_paid = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    outstanding_balance = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')

    CLOSURE_REASON_CHOICES = [
        ('COMPLETED', 'Completed / Fully Paid'),
        ('SETTLED', 'Settled / Compromise'),
        ('BAD_DEBT', 'Bad Debt / Default Write-off'),
        ('DECEASED', 'Deceased Borrower'),
        ('ABSCONDED', 'Absconded / Untraceable'),
        ('LEGAL_ACTION', 'Legal Action Initiated'),
    ]

    route_sequence = models.PositiveIntegerField(
        default=0,
        db_index=True,
        verbose_name="Route Sequence",
        help_text="Custom order along the collection route"
    )
    closure_reason = models.CharField(
        max_length=30,
        choices=CLOSURE_REASON_CHOICES,
        blank=True,
        verbose_name="Loan Closure Reason"
    )

    assigned_agent = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_loans',
        verbose_name="Collection Agent"
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Loan"
        verbose_name_plural = "Loans"
        unique_together = ('company', 'loan_account_no')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.loan_account_no} - {self.member.name} (₹{self.principal_amount})"

    def save(self, *args, **kwargs):
        if not self.loan_account_no and self.company_id:
            count = Loan.objects.filter(company=self.company).count() + 1
            self.loan_account_no = f"LN-{count:05d}"
        if self.outstanding_balance is None:
            self.outstanding_balance = self.total_amount
        super().save(*args, **kwargs)

    @property
    def progress_percentage(self):
        if not self.total_amount or self.total_amount <= 0:
            return 0
        pct = (self.total_paid / self.total_amount) * 100
        return min(100, int(round(pct)))

    @property
    def is_interest_only(self):
        return self.loan_type in ['MONTHLY_INTEREST', 'WEEKLY_INTEREST']

    @property
    def navigation_url(self):
        if self.member.latitude and self.member.longitude:
            return f"https://www.google.com/maps/dir/?api=1&destination={self.member.latitude},{self.member.longitude}"
        elif self.member.address:
            import urllib.parse
            query = f"{self.member.address}, {self.member.city}".strip(', ')
            return f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(query)}"
        return ""


class Installment(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PARTIALLY_PAID', 'Partially Paid'),
        ('PAID', 'Paid'),
        ('OVERDUE', 'Overdue'),
    ]

    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='installments')
    installment_number = models.PositiveIntegerField()
    due_date = models.DateField(db_index=True)
    expected_amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    pending_amount = models.DecimalField(max_digits=10, decimal_places=2)
    penalty_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', db_index=True)
    paid_date = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "Installment"
        verbose_name_plural = "Installments"
        ordering = ['loan', 'installment_number']
        unique_together = ('loan', 'installment_number')

    def __str__(self):
        return f"{self.loan.loan_account_no} - Inst #{self.installment_number} (₹{self.expected_amount} on {self.due_date})"
