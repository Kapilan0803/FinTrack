from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('receipt_number', 'loan', 'amount', 'payment_mode', 'collected_by', 'payment_date', 'is_advance')
    search_fields = ('receipt_number', 'loan__loan_account_no', 'loan__member__name', 'reference_number')
    list_filter = ('company', 'payment_mode', 'is_advance', 'payment_date')
