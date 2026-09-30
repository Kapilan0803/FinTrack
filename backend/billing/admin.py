from django.contrib import admin
from .models import SubscriptionPlan, RazorpayOrder, Invoice


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'price', 'tax_percent', 'duration_days', 'is_active')


@admin.register(RazorpayOrder)
class RazorpayOrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'company', 'amount', 'currency', 'status', 'created_at')
    search_fields = ('order_id', 'payment_id', 'company__name')
    list_filter = ('status', 'created_at')


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'company', 'amount', 'tax_amount', 'total_amount', 'status', 'billing_date')
    search_fields = ('invoice_number', 'company__name', 'razorpay_payment_id')
    list_filter = ('status', 'billing_date')
