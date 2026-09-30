from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Company, User
from .forms import CompanyRegistrationForm, UserLoginForm, StaffCreateForm, CompanySettingsForm


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('reports:dashboard')

    if request.method == 'POST':
        form = CompanyRegistrationForm(request.POST)
        if form.is_valid():
            company = Company.objects.create(
                name=form.cleaned_data['company_name'],
                phone=form.cleaned_data['business_phone'],
                email=form.cleaned_data['business_email'],
                trial_starts_at=timezone.now(),
                trial_ends_at=timezone.now() + timedelta(days=30),
                subscription_status='TRIALING'
            )

            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['business_email'],
                password=form.cleaned_data['password'],
                first_name=form.cleaned_data['full_name'],
                company=company,
                role='OWNER',
                phone_number=form.cleaned_data['business_phone']
            )

            login(request, user)
            messages.success(
                request,
                f"Welcome to FinTrack! Your 30-day free trial has been activated for {company.name}."
            )
            return redirect('reports:dashboard')
    else:
        form = CompanyRegistrationForm()

    return render(request, 'accounts/signup.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('reports:dashboard')

    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.first_name or user.username}!")
                next_url = request.GET.get('next', 'reports:dashboard')
                return redirect(next_url)
            else:
                messages.error(request, "Invalid username or password. Please try again.")
    else:
        form = UserLoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out securely.")
    return redirect('website:home')


@login_required
def profile_view(request):
    user = request.user
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone = request.POST.get('phone_number')
        email = request.POST.get('email')

        user.first_name = first_name
        user.last_name = last_name
        user.phone_number = phone
        user.email = email
        user.save()
        messages.success(request, "Your profile has been updated successfully.")
        return redirect('accounts:profile')

    return render(request, 'accounts/profile.html', {'user_obj': user})


@login_required
def team_list_view(request):
    company = request.company
    if not request.user.can_manage_company:
        messages.error(request, "You do not have permission to manage team members.")
        return redirect('reports:dashboard')

    staff_members = User.objects.filter(company=company).exclude(id=request.user.id)
    return render(request, 'accounts/team_list.html', {
        'staff_members': staff_members,
        'company': company
    })


@login_required
def staff_create_view(request):
    company = request.company
    if not request.user.can_manage_company:
        messages.error(request, "Permission denied.")
        return redirect('reports:dashboard')

    if request.method == 'POST':
        form = StaffCreateForm(request.POST)
        if form.is_valid():
            staff = form.save(commit=False)
            staff.company = company
            staff.set_password(form.cleaned_data['password'])
            staff.save()
            messages.success(request, f"Team member {staff.username} created successfully!")
            return redirect('accounts:team_list')
    else:
        form = StaffCreateForm(initial={'role': 'AGENT'})

    return render(request, 'accounts/staff_form.html', {'form': form, 'title': 'Add Team Member'})


@login_required
def staff_toggle_status_view(request, user_id):
    if not request.user.can_manage_company:
        messages.error(request, "Permission denied.")
        return redirect('reports:dashboard')

    staff = get_object_or_404(User, id=user_id, company=request.company)
    staff.is_active_agent = not staff.is_active_agent
    staff.save()
    status_label = "activated" if staff.is_active_agent else "deactivated"
    messages.info(request, f"Agent {staff.get_full_name() or staff.username} has been {status_label}.")
    return redirect('accounts:team_list')


@login_required
def company_settings_view(request):
    company = request.company
    if not request.user.is_owner:
        messages.error(request, "Only the company owner can modify company settings.")
        return redirect('reports:dashboard')

    if request.method == 'POST':
        form = CompanySettingsForm(request.POST, instance=company)
        if form.is_valid():
            form.save()
            messages.success(request, "Company settings saved successfully.")
            return redirect('accounts:company_settings')
    else:
        form = CompanySettingsForm(instance=company)

    return render(request, 'accounts/company_settings.html', {'form': form, 'company': company})
