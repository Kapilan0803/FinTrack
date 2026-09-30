from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from .models import DemoRequest


def home_view(request):
    """
    Public marketing landing page for FinTrack.
    """
    return render(request, 'website/home.html')


def demo_request_view(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        company_name = request.POST.get('company_name', '').strip()
        city = request.POST.get('city', '').strip()
        loan_types = request.POST.get('loan_types', '').strip()
        notes = request.POST.get('notes', '').strip()

        if name and phone and company_name:
            DemoRequest.objects.create(
                name=name,
                phone=phone,
                email=email,
                company_name=company_name,
                city=city,
                loan_types_interested=loan_types,
                notes=notes
            )
            if request.headers.get('HX-Request') == 'true':
                return HttpResponse(
                    '<div class="p-6 rounded-2xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-300 dark:border-emerald-800 text-center">'
                    '<p class="text-emerald-700 dark:text-emerald-300 font-bold text-lg mb-1">Thank you for requesting a demo!</p>'
                    '<p class="text-sm text-emerald-600 dark:text-emerald-400">Our product specialist will call you at ' + phone + ' within 2 business hours.</p>'
                    '</div>'
                )
            messages.success(request, "Thank you! Our specialist will reach out shortly for your personalized demo.")
        else:
            messages.error(request, "Please fill in all required fields.")

    return redirect('website:home')


def privacy_policy_view(request):
    """
    DPDP Act 2023 (Digital Personal Data Protection Act) compliant privacy policy.
    """
    return render(request, 'website/privacy.html')


def terms_of_service_view(request):
    """
    Terms of service for lending software.
    """
    return render(request, 'website/terms.html')
