from decimal import Decimal, ROUND_HALF_UP
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum
from .models import Loan, LoanPlan
from .forms import LoanCreateForm, LoanPlanForm
from .services import generate_loan_schedule


@login_required
def loan_list_view(request):
    company = request.company
    query = request.GET.get('q', '').strip()
    loan_type = request.GET.get('type', '')
    status = request.GET.get('status', '')
    agent_id = request.GET.get('agent', '')

    loans = Loan.objects.filter(company=company).select_related('member', 'assigned_agent')

    if request.user.is_agent and not request.user.can_manage_company:
        loans = loans.filter(assigned_agent=request.user)
    elif agent_id:
        loans = loans.filter(assigned_agent_id=agent_id)

    if loan_type:
        loans = loans.filter(loan_type=loan_type)

    if status:
        loans = loans.filter(status=status)

    if query:
        loans = loans.filter(
            Q(loan_account_no__icontains=query) |
            Q(member__name__icontains=query) |
            Q(member__phone__icontains=query)
        )

    # Aggregates
    total_active_principal = loans.filter(status='ACTIVE').aggregate(total=Sum('principal_amount'))['total'] or Decimal('0.00')
    total_outstanding = loans.filter(status='ACTIVE').aggregate(total=Sum('outstanding_balance'))['total'] or Decimal('0.00')

    context = {
        'loans': loans,
        'query': query,
        'selected_type': loan_type,
        'selected_status': status,
        'selected_agent': agent_id,
        'total_active_principal': total_active_principal,
        'total_outstanding': total_outstanding,
        'loan_types': LoanPlan.LOAN_TYPE_CHOICES,
    }

    if request.headers.get('HX-Request') == 'true':
        return render(request, 'loans/partials/loan_table.html', context)

    return render(request, 'loans/loan_list.html', context)


@login_required
def loan_create_view(request):
    company = request.company
    if not request.user.can_manage_company:
        messages.error(request, "Permission denied.")
        return redirect('loans:loan_list')

    if request.method == 'POST':
        form = LoanCreateForm(request.POST, company=company)
        if form.is_valid():
            loan = form.save(commit=False)
            loan.company = company

            principal = loan.principal_amount
            rate = loan.interest_rate_percent
            # Simple flat interest calculation: interest = principal * (rate / 100)
            interest = (principal * (rate / Decimal('100.00'))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            total = principal + interest
            disbursed = principal - loan.processing_fee

            loan.interest_amount = interest
            loan.total_amount = total
            loan.disbursed_amount = disbursed
            loan.outstanding_balance = total
            loan.total_paid = Decimal('0.00')
            loan.status = 'ACTIVE'

            # Base EMI
            num_inst = loan.number_of_installments
            loan.installment_amount = (total / Decimal(str(num_inst))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
            # Temporary end_date (will be updated by schedule generator)
            loan.end_date = loan.start_date
            loan.save()

            # Automatically generate installment schedule
            generate_loan_schedule(loan)

            messages.success(request, f"Loan {loan.loan_account_no} created with {num_inst} installments!")
            return redirect('loans:loan_detail', pk=loan.pk)
    else:
        initial_member_id = request.GET.get('member')
        initial_data = {}
        if initial_member_id:
            initial_data['member'] = initial_member_id
        form = LoanCreateForm(company=company, initial=initial_data)

    return render(request, 'loans/loan_form.html', {'form': form, 'title': 'Create New Loan'})


@login_required
def loan_detail_view(request, pk):
    loan = get_object_or_404(
        Loan.objects.select_related('member', 'assigned_agent', 'company'),
        pk=pk,
        company=request.company
    )
    installments = loan.installments.all().order_by('installment_number')
    payments = loan.payments.select_related('collected_by', 'installment').order_by('-payment_date')

    overdue_count = installments.filter(status='OVERDUE').count()
    paid_count = installments.filter(status='PAID').count()
    pending_count = installments.filter(status__in=['PENDING', 'PARTIALLY_PAID']).count()

    return render(request, 'loans/loan_detail.html', {
        'loan': loan,
        'installments': installments,
        'payments': payments,
        'overdue_count': overdue_count,
        'paid_count': paid_count,
        'pending_count': pending_count,
    })


@login_required
def loan_close_view(request, pk):
    if not request.user.can_manage_company:
        messages.error(request, "Permission denied.")
        return redirect('loans:loan_list')

    loan = get_object_or_404(Loan, pk=pk, company=request.company)
    loan.status = 'CLOSED'
    loan.outstanding_balance = Decimal('0.00')
    loan.save()
    messages.success(request, f"Loan {loan.loan_account_no} has been closed.")
    return redirect('loans:loan_detail', pk=loan.pk)


@login_required
def loan_plan_list_view(request):
    if not request.user.can_manage_company:
        messages.error(request, "Permission denied.")
        return redirect('loans:loan_list')

    plans = LoanPlan.objects.filter(company=request.company)
    return render(request, 'loans/plan_list.html', {'plans': plans})


@login_required
def loan_plan_create_view(request):
    if not request.user.can_manage_company:
        messages.error(request, "Permission denied.")
        return redirect('loans:loan_list')

    if request.method == 'POST':
        form = LoanPlanForm(request.POST)
        if form.is_valid():
            plan = form.save(commit=False)
            plan.company = request.company
            plan.save()
            messages.success(request, f"Loan Plan '{plan.name}' created!")
            return redirect('loans:plan_list')
    else:
        form = LoanPlanForm()

    return render(request, 'loans/plan_form.html', {'form': form, 'title': 'Create Loan Plan'})
