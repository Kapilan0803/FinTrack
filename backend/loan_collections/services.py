from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.db.models import Sum, F

from .models import Payment, CollectionAttempt, DailyCashClosing


def calculate_installment_penalty(installment, as_of_date=None):
    """
    Calculates dynamic late payment penalty fees based on days overdue
    and the loan plan penalty settings.
    """
    if installment.status == 'PAID' or installment.pending_amount <= Decimal('0.00'):
        return Decimal('0.00')

    if as_of_date is None:
        as_of_date = timezone.now().date()

    if installment.due_date >= as_of_date:
        return Decimal('0.00')

    days_overdue = (as_of_date - installment.due_date).days
    if days_overdue <= 0:
        return Decimal('0.00')

    # Grace period: 1 day free
    if days_overdue <= 1:
        return Decimal('0.00')

    chargeable_days = days_overdue - 1
    penalty_rate = Decimal('1.00')
    if installment.loan.loan_plan and installment.loan.loan_plan.penalty_rate_percent:
        penalty_rate = installment.loan.loan_plan.penalty_rate_percent

    # Formula: ₹2/day * penalty_rate multiplier, capped at pending installment amount
    raw_penalty = Decimal(str(chargeable_days)) * penalty_rate * Decimal('2.00')
    penalty = min(installment.pending_amount, round(raw_penalty, 2))

    if installment.penalty_amount != penalty:
        installment.penalty_amount = penalty
        installment.save(update_fields=['penalty_amount'])

    return penalty


@transaction.atomic
def record_collection(
    loan,
    amount,
    collected_by,
    payment_mode='CASH',
    reference_number='',
    notes='',
    installment=None,
    penalty_collected=Decimal('0.00'),
    penalty_waived=Decimal('0.00'),
    waiver_reason='',
    is_principal_payoff=False
):
    """
    Records a payment against a loan, applies penalty collections or waivers,
    handles interest-only principal payoffs, and cascades payments through installments.
    """
    amount = Decimal(str(amount))
    penalty_collected = Decimal(str(penalty_collected or '0.00'))
    penalty_waived = Decimal(str(penalty_waived or '0.00'))

    total_transaction_amount = amount + penalty_collected
    if total_transaction_amount <= Decimal('0.00'):
        raise ValueError("Collection amount must be greater than zero.")

    company = loan.company

    payment = Payment.objects.create(
        company=company,
        loan=loan,
        installment=installment,
        amount=total_transaction_amount,
        payment_mode=payment_mode,
        reference_number=reference_number,
        collected_by=collected_by,
        penalty_collected=penalty_collected,
        penalty_waived=penalty_waived,
        waiver_reason=waiver_reason,
        notes=notes,
        payment_date=timezone.now()
    )

    # 1. Update installment penalty status if applicable
    if installment:
        if penalty_collected > Decimal('0.00') or penalty_waived > Decimal('0.00'):
            cleared_penalty = penalty_collected + penalty_waived
            installment.penalty_amount = max(Decimal('0.00'), installment.penalty_amount - cleared_penalty)
            installment.save(update_fields=['penalty_amount'])

    # 2. Handle Principal Payoff for Interest-Only Loans (Monthly / Weekly Interest)
    if is_principal_payoff and loan.loan_type in ['MONTHLY_INTEREST', 'WEEKLY_INTEREST']:
        # Mark all pending installments paid
        loan.installments.filter(status__in=['PENDING', 'OVERDUE', 'PARTIALLY_PAID']).update(
            status='PAID',
            paid_amount=F('expected_amount'),
            pending_amount=Decimal('0.00'),
            paid_date=timezone.now().date()
        )
        loan.total_paid += amount
        loan.outstanding_balance = Decimal('0.00')
        loan.status = 'CLOSED'
        loan.closure_reason = 'COMPLETED'
        loan.save()
        return payment

    # 3. Standard EMI / Installment Allocation
    remaining_payment = amount

    if installment:
        allocated = min(remaining_payment, installment.pending_amount)
        installment.paid_amount += allocated
        installment.pending_amount = max(Decimal('0.00'), installment.expected_amount - installment.paid_amount)

        if installment.pending_amount == Decimal('0.00'):
            installment.status = 'PAID'
            installment.paid_date = timezone.now().date()
        else:
            installment.status = 'PARTIALLY_PAID'
            installment.paid_date = timezone.now().date()

        installment.save()
        remaining_payment -= allocated

    # Cascade remaining payment through unpaid installments
    if remaining_payment > Decimal('0.00'):
        unpaid_installments = loan.installments.filter(
            status__in=['OVERDUE', 'PENDING', 'PARTIALLY_PAID']
        ).exclude(id=installment.id if installment else None).order_by('due_date')

        for inst in unpaid_installments:
            if remaining_payment <= Decimal('0.00'):
                break
            needed = inst.pending_amount
            allocate = min(remaining_payment, needed)
            inst.paid_amount += allocate
            inst.pending_amount = max(Decimal('0.00'), inst.expected_amount - inst.paid_amount)
            if inst.pending_amount == Decimal('0.00'):
                inst.status = 'PAID'
                inst.paid_date = timezone.now().date()
            else:
                inst.status = 'PARTIALLY_PAID'
                inst.paid_date = timezone.now().date()
            inst.save()
            remaining_payment -= allocate

        if remaining_payment > Decimal('0.00'):
            payment.is_advance = True
            payment.save(update_fields=['is_advance'])

    # Update loan totals
    loan.total_paid += amount
    loan.outstanding_balance = max(Decimal('0.00'), loan.total_amount - loan.total_paid)
    if loan.outstanding_balance == Decimal('0.00'):
        loan.status = 'CLOSED'
        if not loan.closure_reason:
            loan.closure_reason = 'COMPLETED'
    loan.save()

    return payment


def record_missed_visit(loan, installment, agent, reason, promised_date=None, notes=''):
    """
    Logs an agent field visit attempt when the customer cannot pay.
    """
    attempt = CollectionAttempt.objects.create(
        company=loan.company,
        loan=loan,
        installment=installment,
        attempted_by=agent,
        attempt_date=timezone.now(),
        reason=reason,
        promised_date=promised_date,
        notes=notes
    )
    return attempt


@transaction.atomic
def submit_cash_closing(agent, closing_date, counts_dict, remarks=''):
    """
    Performs physical cash tally vs system cash collection calculation for agent handover.
    """
    company = agent.company
    system_cash = Payment.objects.filter(
        company=company,
        collected_by=agent,
        payment_date__date=closing_date,
        payment_mode='CASH'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    closing, _ = DailyCashClosing.objects.get_or_create(
        company=company,
        agent=agent,
        closing_date=closing_date
    )

    closing.count_500 = int(counts_dict.get('count_500', 0) or 0)
    closing.count_200 = int(counts_dict.get('count_200', 0) or 0)
    closing.count_100 = int(counts_dict.get('count_100', 0) or 0)
    closing.count_50 = int(counts_dict.get('count_50', 0) or 0)
    closing.count_20 = int(counts_dict.get('count_20', 0) or 0)
    closing.count_10 = int(counts_dict.get('count_10', 0) or 0)
    closing.count_coins = Decimal(str(counts_dict.get('count_coins', '0.00') or '0.00'))

    closing.system_cash_collected = system_cash
    closing.remarks = remarks

    # calculate physical cash and variance in save()
    closing.total_physical_cash = closing.calculate_physical_total()
    closing.variance = closing.total_physical_cash - closing.system_cash_collected

    if closing.variance == Decimal('0.00'):
        closing.status = 'SUBMITTED'
    else:
        closing.status = 'DISCREPANCY'

    closing.save()
    return closing
