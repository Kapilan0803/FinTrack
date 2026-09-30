import logging
from decimal import Decimal
from celery import shared_task
from django.utils import timezone
from loans.models import Installment
from accounts.models import Company
from loan_collections.models import Payment

logger = logging.getLogger(__name__)


@shared_task
def mark_overdue_installments():
    """
    Automated daily job:
    1. Identifies installments due before today that are not fully paid.
    2. Marks them as OVERDUE.
    3. Calculates and applies late penalty fees if configured in the Loan Plan.
    """
    today = timezone.now().date()
    past_due_installments = Installment.objects.filter(
        due_date__lt=today,
        status__in=['PENDING', 'PARTIALLY_PAID'],
        loan__status='ACTIVE'
    ).select_related('loan', 'loan__loan_plan')

    updated_count = 0
    for inst in past_due_installments:
        inst.status = 'OVERDUE'
        
        # Apply late penalty if loan plan specifies
        plan = inst.loan.loan_plan
        if plan and plan.penalty_rate_percent > Decimal('0.00'):
            days_overdue = (today - inst.due_date).days
            # Calculate penalty = (penalty_rate_percent / 100) * pending_amount
            daily_penalty = (inst.pending_amount * (plan.penalty_rate_percent / Decimal('100.00'))).quantize(Decimal('0.01'))
            inst.penalty_amount = daily_penalty * Decimal(str(days_overdue))
        
        inst.save(update_fields=['status', 'penalty_amount'])
        updated_count += 1

    return f"Marked {updated_count} installments as overdue on {today}."


@shared_task
def send_daily_owner_summary():
    """
    Aggregates day's collection performance and compiles summary digest for company owners.
    """
    today = timezone.now().date()
    active_companies = Company.objects.filter(is_active=True)

    summaries = []
    for company in active_companies:
        payments_today = Payment.objects.filter(company=company, payment_date__date=today)
        total_collected = sum(p.amount for p in payments_today)
        cash_collected = sum(p.amount for p in payments_today if p.payment_mode == 'CASH')
        upi_collected = sum(p.amount for p in payments_today if p.payment_mode == 'UPI')

        expected_today = sum(
            inst.expected_amount for inst in Installment.objects.filter(
                loan__company=company,
                loan__status='ACTIVE',
                due_date=today
            )
        )
        
        overdue_total = sum(
            inst.pending_amount for inst in Installment.objects.filter(
                loan__company=company,
                loan__status='ACTIVE',
                status='OVERDUE'
            )
        )

        summary_msg = (
            f"[{company.name}] Daily Digest for {today}:\n"
            f"Collected: Rs. {total_collected} (Cash: Rs. {cash_collected}, UPI: Rs. {upi_collected})\n"
            f"Expected: Rs. {expected_today}\n"
            f"Total Overdue in Portfolio: Rs. {overdue_total}"
        )
        logger.info(summary_msg)
        summaries.append(summary_msg)

    return f"Dispatched {len(summaries)} owner summaries."
