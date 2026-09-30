from decimal import Decimal
from django import forms
from django.utils import timezone
from .models import Loan, LoanPlan
from members.models import Member
from accounts.models import User


class LoanCreateForm(forms.ModelForm):
    class Meta:
        model = Loan
        fields = [
            'member', 'loan_plan', 'loan_type', 'principal_amount',
            'interest_rate_percent', 'number_of_installments', 'processing_fee',
            'start_date', 'assigned_agent', 'notes'
        ]
        widgets = {
            'member': forms.Select(attrs={'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-emerald-500 focus:outline-none'}),
            'loan_plan': forms.Select(attrs={'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-emerald-500 focus:outline-none'}),
            'loan_type': forms.Select(attrs={'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-emerald-500 focus:outline-none'}),
            'principal_amount': forms.NumberInput(attrs={'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-emerald-500 focus:outline-none', 'placeholder': 'e.g. 10000'}),
            'interest_rate_percent': forms.NumberInput(attrs={'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-emerald-500 focus:outline-none', 'placeholder': 'e.g. 10.00'}),
            'number_of_installments': forms.NumberInput(attrs={'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-emerald-500 focus:outline-none', 'placeholder': 'e.g. 100 for daily, 12 for monthly'}),
            'processing_fee': forms.NumberInput(attrs={'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-emerald-500 focus:outline-none', 'placeholder': '0.00'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-emerald-500 focus:outline-none'}),
            'assigned_agent': forms.Select(attrs={'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-emerald-500 focus:outline-none'}),
            'notes': forms.Textarea(attrs={'rows': 2, 'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-emerald-500 focus:outline-none'}),
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        if company:
            self.fields['member'].queryset = Member.objects.filter(company=company, is_active=True)
            self.fields['loan_plan'].queryset = LoanPlan.objects.filter(company=company, is_active=True)
            self.fields['assigned_agent'].queryset = User.objects.filter(company=company, is_active_agent=True)
        self.fields['start_date'].initial = timezone.now().date()
        self.fields['processing_fee'].initial = Decimal('0.00')


class LoanPlanForm(forms.ModelForm):
    class Meta:
        model = LoanPlan
        fields = ['name', 'loan_type', 'default_interest_rate_percent', 'default_duration_units', 'processing_fee_percent', 'penalty_rate_percent', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-emerald-500 focus:outline-none'}),
            'loan_type': forms.Select(attrs={'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-emerald-500 focus:outline-none'}),
            'default_interest_rate_percent': forms.NumberInput(attrs={'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-emerald-500 focus:outline-none'}),
            'default_duration_units': forms.NumberInput(attrs={'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-emerald-500 focus:outline-none'}),
            'processing_fee_percent': forms.NumberInput(attrs={'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-emerald-500 focus:outline-none'}),
            'penalty_rate_percent': forms.NumberInput(attrs={'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-emerald-500 focus:outline-none'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'w-4 h-4 text-emerald-600 rounded focus:ring-emerald-500'}),
        }
