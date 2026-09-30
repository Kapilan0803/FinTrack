from datetime import timedelta
from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum
from django.http import HttpResponse

from accounts.models import User
from members.models import Member
from loans.models import Loan, Installment
from loan_collections.models import Payment
from .services.excel_exporter import export_daily_collections_excel
from .services.pdf_exporter import render_to_pdf


@login_required
def dashboard_view(request):
    company = request.company
    today = timezone.now().date()

    # Base querysets
    loans_qs = Loan.objects.filter(company=company)
    active_loans = loans_qs.filter(status='ACTIVE')
    installments_qs = Installment.objects.filter(loan__company=company, loan__status='ACTIVE')
    payments_qs = Payment.objects.filter(company=company)

    # Agent role scoping
    if request.user.is_agent and not request.user.can_manage_company:
        active_loans = active_loans.filter(assigned_agent=request.user)
        installments_qs = installments_qs.filter(loan__assigned_agent=request.user)
        payments_qs = payments_qs.filter(collected_by=request.user)

    # 1. Today's KPIs
    today_payments = payments_qs.filter(payment_date__date=today)
    today_collected = today_payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    today_cash = today_payments.filter(payment_mode='CASH').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    today_upi = today_payments.filter(payment_mode='UPI').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    today_due_installments = installments_qs.filter(due_date=today)
    today_expected = today_due_installments.aggregate(total=Sum('expected_amount'))['total'] or Decimal('0.00')
    today_pending = max(Decimal('0.00'), today_expected - today_collected)

    # 2. Portfolio KPIs
    total_outstanding = active_loans.aggregate(total=Sum('outstanding_balance'))['total'] or Decimal('0.00')
    total_active_loans_count = active_loans.count()
    total_members_count = Member.objects.filter(company=company, is_active=True).count()

    # 3. Overdue KPIs
    overdue_installments = installments_qs.filter(status='OVERDUE')
    overdue_count = overdue_installments.count()
    overdue_amount = overdue_installments.aggregate(total=Sum('pending_amount'))['total'] or Decimal('0.00')

    # 4. 7-Day Collection Trend
    trend_labels = []
    trend_values = []
    max_val = 1
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_amt = payments_qs.filter(payment_date__date=day).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        trend_labels.append(day.strftime('%a (%d)'))
        trend_values.append(float(day_amt))
        if float(day_amt) > max_val:
            max_val = float(day_amt)

    # Compute bar height percentages for chart
    trend_data = []
    for lbl, val in zip(trend_labels, trend_values):
        pct = int((val / max_val) * 100) if max_val > 0 else 10
        trend_data.append({'label': lbl, 'amount': val, 'height_pct': max(12, pct)})

    # 5. Recent Collections
    recent_payments = payments_qs.select_related('loan__member', 'collected_by')[:6]

    # 6. Critical Overdue Customers
    urgent_overdues = overdue_installments.select_related('loan__member', 'loan__assigned_agent').order_by('due_date')[:6]

    active_agents_count = User.objects.filter(company=company, is_active_agent=True, role='AGENT').count()

    return render(request, 'reports/dashboard.html', {
        'today': today,
        'today_collected': today_collected,
        'today_cash': today_cash,
        'today_upi': today_upi,
        'today_expected': today_expected,
        'today_pending': today_pending,
        'total_outstanding': total_outstanding,
        'total_active_loans_count': total_active_loans_count,
        'total_members_count': total_members_count,
        'overdue_count': overdue_count,
        'overdue_amount': overdue_amount,
        'trend_data': trend_data,
        'recent_payments': recent_payments,
        'urgent_overdues': urgent_overdues,
        'active_agents_count': active_agents_count,
    })


@login_required
def daily_report_view(request):
    company = request.company
    today = timezone.now().date()

    date_str = request.GET.get('date', '')
    if date_str:
        try:
            target_date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            target_date = today
    else:
        target_date = today

    agent_id = request.GET.get('agent', '')
    mode = request.GET.get('mode', '')

    payments = Payment.objects.filter(
        company=company,
        payment_date__date=target_date
    ).select_related('loan', 'loan__member', 'collected_by').order_by('-payment_date')

    if request.user.is_agent and not request.user.can_manage_company:
        payments = payments.filter(collected_by=request.user)
    elif agent_id:
        payments = payments.filter(collected_by_id=agent_id)

    if mode:
        payments = payments.filter(payment_mode=mode)

    total_collected = payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    cash_total = payments.filter(payment_mode='CASH').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    upi_total = payments.filter(payment_mode='UPI').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    # Check for Excel export
    if request.GET.get('export') == 'excel':
        excel_data = export_daily_collections_excel(company, payments, target_date)
        response = HttpResponse(
            excel_data,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="Daily_Collections_{target_date}.xlsx"'
        return response

    # Check for PDF export
    if request.GET.get('export') == 'pdf':
        pdf_bytes = render_to_pdf('reports/pdf/daily_collection_pdf.html', {
            'company': company,
            'payments': payments,
            'target_date': target_date,
            'total_collected': total_collected,
            'cash_total': cash_total,
            'upi_total': upi_total,
        })
        if pdf_bytes:
            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="Daily_Collections_{target_date}.pdf"'
            return response
        else:
            messages.error(request, "Error generating PDF report.")

    agents = User.objects.filter(company=company, is_active_agent=True)

    return render(request, 'reports/daily_report.html', {
        'payments': payments,
        'target_date': target_date,
        'selected_agent': agent_id,
        'selected_mode': mode,
        'total_collected': total_collected,
        'cash_total': cash_total,
        'upi_total': upi_total,
        'agents': agents,
    })


@login_required
def agent_performance_view(request):
    company = request.company
    if not request.user.can_manage_company:
        messages.error(request, "Permission denied.")
        return redirect('reports:dashboard')

    today = timezone.now().date()
    agents = User.objects.filter(company=company, is_active_agent=True)

    agent_stats = []
    for agent in agents:
        today_col = Payment.objects.filter(company=company, collected_by=agent, payment_date__date=today)
        collected_today = today_col.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        cash_in_hand = today_col.filter(payment_mode='CASH').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        target = agent.daily_collection_target
        perf_pct = int((collected_today / target) * 100) if target > Decimal('0.00') else 0

        total_all_time = Payment.objects.filter(company=company, collected_by=agent).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        active_members_count = Member.objects.filter(company=company, assigned_agent=agent, is_active=True).count()

        agent_stats.append({
            'agent': agent,
            'target': target,
            'collected_today': collected_today,
            'cash_in_hand': cash_in_hand,
            'perf_pct': min(100, perf_pct),
            'total_all_time': total_all_time,
            'active_members_count': active_members_count,
        })

    return render(request, 'reports/agent_performance.html', {'agent_stats': agent_stats})


@login_required
def defaulters_report_view(request):
    company = request.company
    today = timezone.now().date()

    overdue_installments = Installment.objects.filter(
        loan__company=company,
        loan__status='ACTIVE',
        status='OVERDUE'
    ).select_related('loan', 'loan__member', 'loan__assigned_agent').order_by('due_date')

    if request.user.is_agent and not request.user.can_manage_company:
        overdue_installments = overdue_installments.filter(loan__assigned_agent=request.user)

    # Classify into aging brackets: 1-7 days, 8-30 days, 30+ days
    bracket_1_7 = []
    bracket_8_30 = []
    bracket_30_plus = []

    for inst in overdue_installments:
        days = (today - inst.due_date).days
        inst.days_overdue = days
        if days <= 7:
            bracket_1_7.append(inst)
        elif days <= 30:
            bracket_8_30.append(inst)
        else:
            bracket_30_plus.append(inst)

    total_overdue = sum(i.pending_amount for i in overdue_installments)

    return render(request, 'reports/defaulters_report.html', {
        'total_overdue': total_overdue,
        'overdue_count': overdue_installments.count(),
        'bracket_1_7': bracket_1_7,
        'bracket_8_30': bracket_8_30,
        'bracket_30_plus': bracket_30_plus,
    })
