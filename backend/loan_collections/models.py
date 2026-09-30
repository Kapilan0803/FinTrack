import uuid
from decimal import Decimal
from django.db import models
from django.utils import timezone
from accounts.models import Company, User
from loans.models import Loan, Installment


class Payment(models.Model):
    PAYMENT_MODE_CHOICES = [
        ('CASH', 'Cash'),
        ('UPI', 'UPI / QR Code'),
        ('BANK_TRANSFER', 'Bank Transfer / NEFT'),
        ('CHEQUE', 'Cheque'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='payments')
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='payments')
    installment = models.ForeignKey(Installment, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    receipt_number = models.CharField(max_length=60, unique=True, db_index=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Amount Collected (₹)")
    payment_mode = models.CharField(max_length=20, choices=PAYMENT_MODE_CHOICES, default='CASH')
    reference_number = models.CharField(max_length=100, blank=True, verbose_name="UPI Ref / Cheque No.")
    collected_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='collections_recorded')
    payment_date = models.DateTimeField(default=timezone.now, db_index=True)
    is_advance = models.BooleanField(default=False)

    # Late Payment Penalty Tracking
    penalty_collected = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Penalty Collected (₹)")
    penalty_waived = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Penalty Waived (₹)")
    waiver_reason = models.CharField(max_length=200, blank=True, verbose_name="Penalty Waiver Reason")

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Payment / Collection"
        verbose_name_plural = "Payments / Collections"
        ordering = ['-payment_date']

    def __str__(self):
        return f"{self.receipt_number} - ₹{self.amount} for {self.loan.loan_account_no}"

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            date_str = timezone.now().strftime('%Y%m%d')
            rand_suffix = uuid.uuid4().hex[:6].upper()
            self.receipt_number = f"RCP-{date_str}-{rand_suffix}"
        super().save(*args, **kwargs)


class CollectionAttempt(models.Model):
    """
    Tracks missed visit attempts and field visit outcome reasons
    (Shop Closed, Out of Station, Promised Later, Dispute).
    """
    REASON_CHOICES = [
        ('SHOP_CLOSED', 'Shop / Stall Closed'),
        ('NOT_AVAILABLE', 'Customer Not Available / Out of Station'),
        ('PROMISED_LATER', 'Promised to Pay Later'),
        ('DISPUTE', 'Dispute / Refused to Pay'),
        ('INSUFFICIENT_FUNDS', 'Cash Shortage / Arranging Funds'),
        ('OTHER', 'Other Reason'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='collection_attempts')
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='collection_attempts')
    installment = models.ForeignKey(Installment, on_delete=models.SET_NULL, null=True, blank=True, related_name='collection_attempts')
    attempted_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='collection_attempts_logged')
    attempt_date = models.DateTimeField(default=timezone.now, db_index=True)
    reason = models.CharField(max_length=30, choices=REASON_CHOICES, default='PROMISED_LATER')
    promised_date = models.DateField(null=True, blank=True, verbose_name="Promised Payment Date")
    notes = models.TextField(blank=True, verbose_name="Agent Visit Remarks")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Collection / Visit Attempt"
        verbose_name_plural = "Collection / Visit Attempts"
        ordering = ['-attempt_date']

    def __str__(self):
        return f"{self.loan.loan_account_no} - {self.get_reason_display()} on {self.attempt_date.strftime('%Y-%m-%d')}"


class DailyCashClosing(models.Model):
    """
    Day-End Cash Denomination Reconciliation & Handover for field agents.
    Validates physical currency note counts against system collections.
    """
    STATUS_CHOICES = [
        ('SUBMITTED', 'Submitted by Agent'),
        ('VERIFIED', 'Verified & Accepted by Manager'),
        ('DISCREPANCY', 'Discrepancy / Shortage Reported'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='cash_closings')
    agent = models.ForeignKey(User, on_delete=models.PROTECT, related_name='cash_closings_submitted')
    closing_date = models.DateField(default=timezone.now, db_index=True)

    count_500 = models.PositiveIntegerField(default=0, verbose_name="₹500 Notes")
    count_200 = models.PositiveIntegerField(default=0, verbose_name="₹200 Notes")
    count_100 = models.PositiveIntegerField(default=0, verbose_name="₹100 Notes")
    count_50 = models.PositiveIntegerField(default=0, verbose_name="₹50 Notes")
    count_20 = models.PositiveIntegerField(default=0, verbose_name="₹20 Notes")
    count_10 = models.PositiveIntegerField(default=0, verbose_name="₹10 Notes")
    count_coins = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'), verbose_name="Coins Total (₹)")

    total_physical_cash = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name="Total Counted Cash (₹)")
    system_cash_collected = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name="System Cash Collected (₹)")
    variance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name="Variance / Difference (₹)")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SUBMITTED')
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='cash_closings_verified')
    remarks = models.TextField(blank=True, verbose_name="Closing Remarks / Handover Notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Daily Cash Closing"
        verbose_name_plural = "Daily Cash Closings"
        unique_together = ('company', 'agent', 'closing_date')
        ordering = ['-closing_date', '-created_at']

    def __str__(self):
        return f"{self.agent.username} - {self.closing_date} (Counted: ₹{self.total_physical_cash}, System: ₹{self.system_cash_collected})"

    def calculate_physical_total(self):
        return (
            Decimal(str(self.count_500 * 500)) +
            Decimal(str(self.count_200 * 200)) +
            Decimal(str(self.count_100 * 100)) +
            Decimal(str(self.count_50 * 50)) +
            Decimal(str(self.count_20 * 20)) +
            Decimal(str(self.count_10 * 10)) +
            Decimal(str(self.count_coins))
        )

    def save(self, *args, **kwargs):
        self.total_physical_cash = self.calculate_physical_total()
        self.variance = self.total_physical_cash - self.system_cash_collected
        super().save(*args, **kwargs)
