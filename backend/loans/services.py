from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP
from dateutil.relativedelta import relativedelta
from .models import Installment


def generate_loan_schedule(loan):
    """
    Generates a mathematically exact repayment schedule for the loan.
    Guarantees that sum(installments.expected_amount) == loan.total_amount down to 0 paise.
    """
    # Delete any existing installments for this loan
    loan.installments.all().delete()

    n = loan.number_of_installments
    if n <= 0:
        return []

    loan_type = loan.loan_type
    company = loan.company
    skip_sundays = company.skip_sundays_in_daily if company else True

    installments_data = []
    current_date = loan.start_date

    if loan_type in ['MONTHLY_INTEREST', 'WEEKLY_INTEREST']:
        # Interest paid periodically; principal repaid on final maturity date
        interest_per_period = (loan.interest_amount / Decimal(str(n))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        for i in range(1, n + 1):
            # Calculate due date
            if loan_type == 'MONTHLY_INTEREST':
                if i > 1:
                    current_date = loan.start_date + relativedelta(months=+(i - 1))
            else: # WEEKLY_INTEREST
                if i > 1:
                    current_date = loan.start_date + timedelta(weeks=(i - 1))

            if i == n:
                # Last installment carries principal + remaining interest to equal total_amount exactly
                sum_previous_expected = sum(inst['expected_amount'] for inst in installments_data)
                expected_amt = loan.total_amount - sum_previous_expected
            else:
                expected_amt = interest_per_period

            installments_data.append({
                'installment_number': i,
                'due_date': current_date,
                'expected_amount': expected_amt,
                'pending_amount': expected_amt,
                'paid_amount': Decimal('0.00'),
                'status': 'PENDING'
            })

    else:
        # Standard amortized / equal installment (DAILY, WEEKLY, MONTHLY_EMI)
        base_emi = (loan.total_amount / Decimal(str(n))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        sum_allocated = Decimal('0.00')

        for i in range(1, n + 1):
            if i == 1:
                due_date = current_date
            else:
                if loan_type == 'DAILY':
                    current_date = current_date + timedelta(days=1)
                    if skip_sundays:
                        while current_date.weekday() == 6: # Sunday
                            current_date = current_date + timedelta(days=1)
                    due_date = current_date
                elif loan_type == 'WEEKLY':
                    current_date = current_date + timedelta(weeks=1)
                    due_date = current_date
                else: # MONTHLY_EMI
                    due_date = loan.start_date + relativedelta(months=+(i - 1))
                    current_date = due_date

            if i == n:
                # The final installment absorbs any 1-2 paise rounding discrepancy
                expected_amt = loan.total_amount - sum_allocated
            else:
                expected_amt = base_emi
                sum_allocated += expected_amt

            installments_data.append({
                'installment_number': i,
                'due_date': due_date,
                'expected_amount': expected_amt,
                'pending_amount': expected_amt,
                'paid_amount': Decimal('0.00'),
                'status': 'PENDING'
            })

    # Bulk create installments
    created_instances = [
        Installment(
            loan=loan,
            installment_number=item['installment_number'],
            due_date=item['due_date'],
            expected_amount=item['expected_amount'],
            pending_amount=item['pending_amount'],
            paid_amount=item['paid_amount'],
            status=item['status']
        )
        for item in installments_data
    ]
    Installment.objects.bulk_create(created_instances)

    # Update loan maturity end_date based on actual final installment date
    if installments_data:
        loan.end_date = installments_data[-1]['due_date']
        loan.save(update_fields=['end_date'])

    return created_instances
