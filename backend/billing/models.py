from decimal import Decimal
from django.db import models
from django.utils import timezone
from accounts.models import Company


class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=100, default="Annual Pro Plan")
    code = models.CharField(max_length=50, default="ANNUAL_1000")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('1000.00'))
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('18.00')) # 18% GST
    duration_days = models.PositiveIntegerField(default=365)
    description = models.TextField(default="Unlimited borrowers, field collections, Excel/PDF exports, and overdue alerts.")
    is_active = models.BooleanField(default=True)

    @property
    def total_price(self):
        tax = (self.price * (self.tax_percent / Decimal('100.00'))).quantize(Decimal('0.01'))
        return self.price + tax

    def __str__(self):
        return f"{self.name} - ₹{self.price}/year"


class RazorpayOrder(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='razorpay_orders')
    order_id = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2) # in Rupees
    currency = models.CharField(max_length=10, default="INR")
    status = models.CharField(max_length=20, default="CREATED")
    payment_id = models.CharField(max_length=100, blank=True)
    signature = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.order_id} - ₹{self.amount} ({self.status})"


class Invoice(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='invoices')
    invoice_number = models.CharField(max_length=50, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    billing_date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=20, default='PAID')
    razorpay_payment_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.invoice_number} - ₹{self.total_amount}"
