from django.contrib import admin
from .models import LoanPlan, Loan, Installment


@admin.register(LoanPlan)
class LoanPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'loan_type', 'default_interest_rate_percent', 'default_duration_units', 'company', 'is_active')
    list_filter = ('company', 'loan_type', 'is_active')


class InstallmentInline(admin.TabularInline):
    model = Installment
    extra = 0
    readonly_fields = ('installment_number', 'due_date', 'expected_amount', 'paid_amount', 'pending_amount', 'status')


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ('loan_account_no', 'member', 'loan_type', 'principal_amount', 'total_amount', 'total_paid', 'outstanding_balance', 'status', 'start_date', 'end_date')
    search_fields = ('loan_account_no', 'member__name', 'member__phone')
    list_filter = ('company', 'status', 'loan_type')
    inlines = [InstallmentInline]


@admin.register(Installment)
class InstallmentAdmin(admin.ModelAdmin):
    list_display = ('loan', 'installment_number', 'due_date', 'expected_amount', 'paid_amount', 'pending_amount', 'status')
    search_fields = ('loan__loan_account_no', 'loan__member__name')
    list_filter = ('status', 'due_date')
