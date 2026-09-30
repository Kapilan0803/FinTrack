from decimal import Decimal
import urllib.parse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Q
from django.http import HttpResponse

from .models import Payment, CollectionAttempt, DailyCashClosing
from .services import (
    record_collection,
    calculate_installment_penalty,
    record_missed_visit,
    submit_cash_closing
)
from loans.models import Loan, Installment
from members.models import Member
from accounts.models import User


@login_required
def today_collection_view(request):
    """
    Field Collection Hub & Register.
    Features:
    - Tabbed sheets by loan type (Daily, Weekly, Monthly EMI, Monthly Interest, Weekly Interest).
    - Route walk-order sequencing (door-to-door visit order).
    - Status filtering (All, Pending, Overdue, Paid, Missed).
    - Accrued penalty fees calculation.
    - Cash closing and denomination summary.
    """
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

    loan_type_filter = request.GET.get('loan_type', 'all').upper()
    sort_filter = request.GET.get('sort', 'walk_order')
    status_filter = request.GET.get('status', 'all')
    route_filter = request.GET.get('route', '').strip()
    agent_id = request.GET.get('agent', '')
    query = request.GET.get('q', '').strip()

    # Base active loan installments
    base_installments = Installment.objects.filter(
        loan__company=company,
        loan__status='ACTIVE'
    ).select_related('loan', 'loan__member', 'loan__assigned_agent', 'loan__loan_plan')

    # Agent role isolation: field agents only see their own assigned customers
    if request.user.is_agent and not request.user.can_manage_company:
        base_installments = base_installments.filter(loan__assigned_agent=request.user)
    elif agent_id:
        base_installments = base_installments.filter(loan__assigned_agent_id=agent_id)

    # Calculate Tab counts for all loan types for target_date + overdue
    tab_query = base_installments.filter(Q(due_date=target_date) | Q(status='OVERDUE'))
    tab_counts = {
        'ALL': tab_query.count(),
        'DAILY': tab_query.filter(loan__loan_type='DAILY').count(),
        'WEEKLY': tab_query.filter(loan__loan_type='WEEKLY').count(),
        'MONTHLY_EMI': tab_query.filter(loan__loan_type='MONTHLY_EMI').count(),
        'MONTHLY_INTEREST': tab_query.filter(loan__loan_type='MONTHLY_INTEREST').count(),
        'WEEKLY_INTEREST': tab_query.filter(loan__loan_type='WEEKLY_INTEREST').count(),
    }

    # Filter by loan type tab
    installments = tab_query
    if loan_type_filter in ['DAILY', 'WEEKLY', 'MONTHLY_EMI', 'MONTHLY_INTEREST', 'WEEKLY_INTEREST']:
        installments = installments.filter(loan__loan_type=loan_type_filter)

    # Status filter
    if status_filter == 'overdue':
        installments = installments.filter(status='OVERDUE')
    elif status_filter == 'paid':
        installments = installments.filter(due_date=target_date, status='PAID')
    elif status_filter == 'pending':
        installments = installments.filter(due_date=target_date, status__in=['PENDING', 'PARTIALLY_PAID'])
    elif status_filter == 'missed':
        missed_loan_ids = CollectionAttempt.objects.filter(
            company=company,
            attempt_date__date=target_date
        ).values_list('loan_id', flat=True)
        installments = installments.filter(loan_id__in=missed_loan_ids)

    # Route filter
    if route_filter:
        installments = installments.filter(loan__member__area_or_route__icontains=route_filter)

    # Search query
    if query:
        installments = installments.filter(
            Q(loan__member__name__icontains=query) |
            Q(loan__member__phone__icontains=query) |
            Q(loan__loan_account_no__icontains=query) |
            Q(loan__member__landmark__icontains=query)
        )

    # Sorting
    if sort_filter == 'due_date':
        installments = installments.order_by('due_date', 'installment_number')
    elif sort_filter == 'amount_desc':
        installments = installments.order_by('-pending_amount', 'due_date')
    elif sort_filter == 'name':
        installments = installments.order_by('loan__member__name')
    else:
        # Default: walk_order (door-to-door physical route sequence)
        installments = installments.order_by(
            'loan__member__visit_order',
            'loan__route_sequence',
            'due_date',
            'installment_number'
        )

    # Evaluate installments and attach penalties & today's visit attempts
    inst_list = list(installments)
    overdue_count = 0
    total_penalties_pending = Decimal('0.00')

    # Fetch attempts made today for instant badge display
    today_attempts_map = {
        att.installment_id: att
        for att in CollectionAttempt.objects.filter(
            company=company,
            attempt_date__date=target_date
        ).select_related('attempted_by')
    }

    for inst in inst_list:
        if inst.status == 'OVERDUE' or inst.due_date < target_date:
            pen = calculate_installment_penalty(inst, as_of_date=target_date)
            total_penalties_pending += pen
            overdue_count += 1
        inst.today_attempt = today_attempts_map.get(inst.id)

    # Summary metrics for target date
    today_collections = Payment.objects.filter(
        company=company,
        payment_date__date=target_date
    )
    if request.user.is_agent and not request.user.can_manage_company:
        today_collections = today_collections.filter(collected_by=request.user)
    elif agent_id:
        today_collections = today_collections.filter(collected_by_id=agent_id)

    total_collected_today = today_collections.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    cash_in_hand = today_collections.filter(payment_mode='CASH').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    upi_collected = today_collections.filter(payment_mode='UPI').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    penalties_collected = today_collections.aggregate(total=Sum('penalty_collected'))['total'] or Decimal('0.00')

    # Target expected for today
    today_inst_query = base_installments.filter(due_date=target_date)
    total_expected_today = today_inst_query.aggregate(total=Sum('expected_amount'))['total'] or Decimal('0.00')

    completion_rate = 0
    if total_expected_today > Decimal('0.00'):
        completion_rate = min(100, int((total_collected_today / total_expected_today) * 100))

    # Existing daily cash closing record (if any)
    agent_for_closing = request.user
    if agent_id and request.user.can_manage_company:
        agent_for_closing = User.objects.filter(id=agent_id, company=company).first() or request.user

    today_closing = DailyCashClosing.objects.filter(
        company=company,
        agent=agent_for_closing,
        closing_date=target_date
    ).first()

    agents = User.objects.filter(company=company, is_active_agent=True)
    routes = Member.objects.filter(company=company).exclude(area_or_route='').values_list('area_or_route', flat=True).distinct()

    context = {
        'installments': inst_list,
        'target_date': target_date,
        'selected_loan_type': loan_type_filter,
        'tab_counts': tab_counts,
        'selected_sort': sort_filter,
        'selected_agent': agent_id,
        'selected_status': status_filter,
        'selected_route': route_filter,
        'query': query,
        'total_expected_today': total_expected_today,
        'total_collected_today': total_collected_today,
        'cash_in_hand': cash_in_hand,
        'upi_collected': upi_collected,
        'penalties_collected': penalties_collected,
        'total_penalties_pending': total_penalties_pending,
        'overdue_count': overdue_count,
        'completion_rate': completion_rate,
        'agents': agents,
        'routes': routes,
        'today_closing': today_closing,
    }

    if request.headers.get('HX-Request') == 'true' and 'only_cards' in request.GET:
        return render(request, 'collections/partials/cards_container.html', context)

    return render(request, 'collections/today.html', context)


@login_required
def quick_pay_htmx_view(request, installment_id):
    """
    1-Tap Quick Pay for field agents via HTMX.
    Marks full remaining pending installment paid immediately.
    Supports optional penalty collection or waiving.
    """
    if request.method != 'POST':
        return HttpResponse("Method not allowed", status=405)

    installment = get_object_or_404(
        Installment.objects.select_related('loan', 'loan__member', 'loan__company', 'loan__loan_plan'),
        id=installment_id,
        loan__company=request.company
    )

    amount = installment.pending_amount
    payment_mode = request.POST.get('payment_mode', 'CASH')
    reference_number = request.POST.get('reference_number', '')

    # Late fee penalty options
    penalty_collected = Decimal('0.00')
    penalty_waived = Decimal('0.00')
    waiver_reason = request.POST.get('waiver_reason', '').strip()

    if request.POST.get('collect_penalty') == '1':
        penalty_collected = installment.penalty_amount
    elif request.POST.get('waive_penalty') == '1':
        penalty_waived = installment.penalty_amount
        if not waiver_reason:
            waiver_reason = "Waived by agent on 1-tap collection"

    payment = record_collection(
        loan=installment.loan,
        amount=amount,
        collected_by=request.user,
        payment_mode=payment_mode,
        reference_number=reference_number,
        installment=installment,
        penalty_collected=penalty_collected,
        penalty_waived=penalty_waived,
        waiver_reason=waiver_reason
    )

    installment.refresh_from_db()

    return render(request, 'collections/partials/collection_card.html', {
        'installment': installment,
        'latest_payment': payment,
        'just_paid': True
    })


@login_required
def custom_pay_view(request, loan_id):
    """
    Drawer / Modal payment for custom, partial, advance amounts or penalty settlement.
    """
    loan = get_object_or_404(Loan, id=loan_id, company=request.company)

    if request.method == 'POST':
        amount_val = request.POST.get('amount')
        payment_mode = request.POST.get('payment_mode', 'CASH')
        ref_no = request.POST.get('reference_number', '').strip()
        notes = request.POST.get('notes', '').strip()
        inst_id = request.POST.get('installment_id')

        # Penalty fields
        penalty_collected_val = request.POST.get('penalty_collected', '0.00')
        penalty_waived_val = request.POST.get('penalty_waived', '0.00')
        waiver_reason = request.POST.get('waiver_reason', '').strip()

        try:
            amount = Decimal(amount_val)
            penalty_collected = Decimal(penalty_collected_val or '0.00')
            penalty_waived = Decimal(penalty_waived_val or '0.00')

            if amount + penalty_collected <= Decimal('0.00'):
                messages.error(request, "Amount must be greater than zero.")
                return redirect('collections:today')

            installment = None
            if inst_id:
                installment = Installment.objects.filter(id=inst_id, loan=loan).first()

            payment = record_collection(
                loan=loan,
                amount=amount,
                collected_by=request.user,
                payment_mode=payment_mode,
                reference_number=ref_no,
                notes=notes,
                installment=installment,
                penalty_collected=penalty_collected,
                penalty_waived=penalty_waived,
                waiver_reason=waiver_reason
            )
            messages.success(request, f"Payment of ₹{payment.amount} recorded! Receipt: {payment.receipt_number}")
            return redirect('collections:receipt', receipt_number=payment.receipt_number)

        except Exception as e:
            messages.error(request, f"Payment error: {str(e)}")
            return redirect('collections:today')

    return redirect('collections:today')


@login_required
def mark_missed_htmx_view(request, installment_id):
    """
    Records a visit attempt when a customer is unable or refuses to pay.
    Updates the card in-place via HTMX.
    """
    if request.method != 'POST':
        return HttpResponse("Method not allowed", status=405)

    installment = get_object_or_404(
        Installment.objects.select_related('loan', 'loan__member', 'loan__company'),
        id=installment_id,
        loan__company=request.company
    )

    reason = request.POST.get('reason', 'PROMISED_LATER')
    promised_date_str = request.POST.get('promised_date', '').strip()
    notes = request.POST.get('notes', '').strip()

    promised_date = None
    if promised_date_str:
        try:
            promised_date = timezone.datetime.strptime(promised_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass

    attempt = record_missed_visit(
        loan=installment.loan,
        installment=installment,
        agent=request.user,
        reason=reason,
        promised_date=promised_date,
        notes=notes
    )

    installment.refresh_from_db()
    installment.today_attempt = attempt

    return render(request, 'collections/partials/collection_card.html', {
        'installment': installment,
        'just_missed': True
    })


@login_required
def settle_principal_view(request, loan_id):
    """
    One-tap bullet principal buyout and loan closure for Monthly / Weekly Interest loans.
    """
    loan = get_object_or_404(Loan, id=loan_id, company=request.company)

    if not loan.is_interest_only:
        messages.error(request, "Principal buyout is only applicable for Monthly or Weekly Interest loans.")
        return redirect('collections:today')

    if request.method == 'POST':
        amount_val = request.POST.get('amount', str(loan.principal_amount))
        payment_mode = request.POST.get('payment_mode', 'CASH')
        ref_no = request.POST.get('reference_number', '').strip()
        notes = request.POST.get('notes', 'Principal Lump Sum Repayment & Loan Closure').strip()

        try:
            amount = Decimal(amount_val)
            payment = record_collection(
                loan=loan,
                amount=amount,
                collected_by=request.user,
                payment_mode=payment_mode,
                reference_number=ref_no,
                notes=notes,
                is_principal_payoff=True
            )
            messages.success(request, f"Principal of ₹{amount} received! Loan {loan.loan_account_no} is now closed.")
            return redirect('collections:receipt', receipt_number=payment.receipt_number)
        except Exception as e:
            messages.error(request, f"Settlement error: {str(e)}")
            return redirect('collections:today')

    return redirect('collections:today')


@login_required
def cash_closing_view(request):
    """
    Agent End-of-Day Cash Denomination Reconciler.
    Compares physical currency note counts with system cash collections.
    """
    today = timezone.now().date()

    if request.method == 'POST':
        closing_date_str = request.POST.get('closing_date', '')
        try:
            closing_date = timezone.datetime.strptime(closing_date_str, '%Y-%m-%d').date()
        except ValueError:
            closing_date = today

        counts = {
            'count_500': request.POST.get('count_500', 0),
            'count_200': request.POST.get('count_200', 0),
            'count_100': request.POST.get('count_100', 0),
            'count_50': request.POST.get('count_50', 0),
            'count_20': request.POST.get('count_20', 0),
            'count_10': request.POST.get('count_10', 0),
            'count_coins': request.POST.get('count_coins', '0.00'),
        }
        remarks = request.POST.get('remarks', '').strip()

        closing = submit_cash_closing(
            agent=request.user,
            closing_date=closing_date,
            counts_dict=counts,
            remarks=remarks
        )

        if closing.variance == Decimal('0.00'):
            messages.success(request, f"Cash Closing for {closing_date} successfully balanced! (Counted: ₹{closing.total_physical_cash})")
        elif closing.variance > Decimal('0.00'):
            messages.warning(request, f"Cash closing submitted with EXCESS of +₹{closing.variance} (Counted: ₹{closing.total_physical_cash}, System: ₹{closing.system_cash_collected})")
        else:
            messages.error(request, f"Cash closing submitted with SHORTAGE of ₹{abs(closing.variance)} (Counted: ₹{closing.total_physical_cash}, System: ₹{closing.system_cash_collected})")

        return redirect(f"/collections/today/?date={closing_date}")

    return redirect('collections:today')


@login_required
def receipt_view(request, receipt_number):
    """
    Thermal Printer (58mm/80mm) & Web printable receipt.
    Includes penalty details and direct WhatsApp receipt share link.
    """
    payment = get_object_or_404(
        Payment.objects.select_related('loan', 'loan__member', 'loan__company', 'collected_by', 'installment'),
        receipt_number=receipt_number,
        company=request.company
    )

    member = payment.loan.member
    company = payment.company
    phone = "".join(filter(str.isdigit, member.phone))
    if len(phone) == 10:
        phone = "91" + phone

    msg_text = (
        f"*{company.name}* - Payment Receipt\n\n"
        f"Dear {member.name},\n"
        f"Received ₹{payment.amount} for Loan *{payment.loan.loan_account_no}*.\n"
        f"• Receipt No: {payment.receipt_number}\n"
        f"• Date: {payment.payment_date.strftime('%d-%b-%Y %I:%M %p')}\n"
        f"• Mode: {payment.get_payment_mode_display()}\n"
    )
    if payment.penalty_collected > Decimal('0.00'):
        msg_text += f"• Penalty Included: ₹{payment.penalty_collected}\n"
    if payment.penalty_waived > Decimal('0.00'):
        msg_text += f"• Late Fee Waived: ₹{payment.penalty_waived}\n"

    msg_text += (
        f"• Remaining Balance: ₹{payment.loan.outstanding_balance}\n"
        f"• Collected By: {payment.collected_by.get_full_name() or payment.collected_by.username}\n\n"
        f"Thank you for banking with {company.name}!"
    )
    whatsapp_url = f"https://api.whatsapp.com/send?phone={phone}&text={urllib.parse.quote(msg_text)}"

    return render(request, 'collections/receipt.html', {
        'payment': payment,
        'whatsapp_url': whatsapp_url,
    })
