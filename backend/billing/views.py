import uuid
from datetime import timedelta
from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

from .models import SubscriptionPlan, RazorpayOrder, Invoice
from .services import create_subscription_order, verify_razorpay_signature


@login_required
def pricing_view(request):
    company = request.company
    plan, _ = SubscriptionPlan.objects.get_or_create(
        code="ANNUAL_1000",
        defaults={
            'name': "Annual Unlimited Plan",
            'price': Decimal('1000.00'),
            'tax_percent': Decimal('18.00'),
            'duration_days': 365,
            'description': "Full access to all features: unlimited members, daily collections, Excel & PDF exports, overdue alerts, and multiple agents."
        }
    )

    days_left = company.days_left_in_trial if company else 0
    is_active = company.is_subscription_active() if company else False

    return render(request, 'billing/pricing.html', {
        'plan': plan,
        'company': company,
        'days_left': days_left,
        'is_active': is_active,
        'razorpay_key': getattr(settings, 'RAZORPAY_KEY_ID', 'rzp_test_sampleKey123')
    })


@login_required
def checkout_view(request):
    company = request.company
    if not request.user.can_manage_company:
        messages.error(request, "Only owners or managers can initiate subscription payments.")
        return redirect('billing:pricing')

    plan = SubscriptionPlan.objects.first()
    if not plan:
        plan = SubscriptionPlan.objects.create(
            name="Annual Unlimited Plan",
            code="ANNUAL_1000",
            price=Decimal('1000.00'),
            tax_percent=Decimal('18.00'),
            duration_days=365
        )

    order, order_id = create_subscription_order(company, plan)

    return render(request, 'billing/checkout.html', {
        'order': order,
        'order_id': order_id,
        'plan': plan,
        'company': company,
        'razorpay_key': getattr(settings, 'RAZORPAY_KEY_ID', 'rzp_test_sampleKey123'),
        'user': request.user
    })


@login_required
def verify_payment_view(request):
    if request.method != 'POST':
        return redirect('billing:pricing')

    order_id = request.POST.get('razorpay_order_id')
    payment_id = request.POST.get('razorpay_payment_id')
    signature = request.POST.get('razorpay_signature')

    company = request.company

    if verify_razorpay_signature(order_id, payment_id, signature):
        order = RazorpayOrder.objects.filter(order_id=order_id, company=company).first()
        if order:
            order.status = "PAID"
            order.payment_id = payment_id
            order.signature = signature
            order.save()

        # Update company subscription
        company.subscription_status = 'ACTIVE'
        # Extend by 365 days from now or current expiry
        base_date = max(timezone.now(), company.trial_ends_at or timezone.now())
        company.trial_ends_at = base_date + timedelta(days=365)
        company.save()

        # Create Invoice
        plan = SubscriptionPlan.objects.first()
        tax_amt = (plan.price * (plan.tax_percent / Decimal('100.00'))).quantize(Decimal('0.01')) if plan else Decimal('180.00')
        tot_amt = plan.total_price if plan else Decimal('1180.00')

        Invoice.objects.create(
            company=company,
            invoice_number=f"INV-{timezone.now().strftime('%Y%m')}-{uuid.uuid4().hex[:6].upper()}",
            amount=plan.price if plan else Decimal('1000.00'),
            tax_amount=tax_amt,
            total_amount=tot_amt,
            status='PAID',
            razorpay_payment_id=payment_id
        )

        messages.success(request, "🎉 Subscription payment successful! Your account is now active for 1 full year.")
        return redirect('billing:invoices')
    else:
        messages.error(request, "Payment signature verification failed. Please contact support.")
        return redirect('billing:pricing')


@login_required
def invoices_view(request):
    invoices = Invoice.objects.filter(company=request.company).order_by('-billing_date')
    return render(request, 'billing/invoices.html', {'invoices': invoices})


@csrf_exempt
def razorpay_webhook(request):
    """
    Asynchronous webhook handler for Razorpay.
    """
    if request.method == 'POST':
        return HttpResponse(status=200)
    return HttpResponse(status=405)
