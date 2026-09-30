from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Sum
from .models import Member
from .forms import MemberForm
from accounts.models import User
from loans.models import Loan, Installment
from loan_collections.models import Payment


@login_required
def member_list_view(request):
    company = request.company
    query = request.GET.get('q', '').strip()
    agent_id = request.GET.get('agent', '')
    route = request.GET.get('route', '').strip()

    members = Member.objects.filter(company=company)

    # If field agent, optionally filter to their own members unless manager/owner
    if request.user.is_agent and not request.user.can_manage_company:
        members = members.filter(assigned_agent=request.user)
    elif agent_id:
        members = members.filter(assigned_agent_id=agent_id)

    if query:
        members = members.filter(
            Q(name__icontains=query) |
            Q(phone__icontains=query) |
            Q(member_code__icontains=query) |
            Q(id_proof_number__icontains=query)
        )

    if route:
        members = members.filter(area_or_route__icontains=route)

    agents = User.objects.filter(company=company, is_active_agent=True)
    routes = Member.objects.filter(company=company).exclude(area_or_route='').values_list('area_or_route', flat=True).distinct()

    context = {
        'members': members,
        'query': query,
        'selected_agent': agent_id,
        'selected_route': route,
        'agents': agents,
        'routes': routes,
    }

    if request.headers.get('HX-Request') == 'true':
        return render(request, 'members/partials/member_table.html', context)

    return render(request, 'members/member_list.html', context)


@login_required
def member_create_view(request):
    company = request.company
    if request.method == 'POST':
        form = MemberForm(request.POST, request.FILES, company=company)
        if form.is_valid():
            member = form.save(commit=False)
            member.company = company
            member.save()
            messages.success(request, f"Customer {member.name} ({member.member_code}) added successfully!")
            return redirect('members:member_detail', pk=member.pk)
    else:
        form = MemberForm(company=company)

    return render(request, 'members/member_form.html', {'form': form, 'title': 'Add New Customer / Member'})


@login_required
def member_update_view(request, pk):
    member = get_object_or_404(Member, pk=pk, company=request.company)
    if request.method == 'POST':
        form = MemberForm(request.POST, request.FILES, instance=member, company=request.company)
        if form.is_valid():
            form.save()
            messages.success(request, f"Customer {member.name} updated successfully.")
            return redirect('members:member_detail', pk=member.pk)
    else:
        form = MemberForm(instance=member, company=request.company)

    return render(request, 'members/member_form.html', {'form': form, 'title': f'Edit Customer - {member.name}'})


@login_required
def member_detail_view(request, pk):
    member = get_object_or_404(Member, pk=pk, company=request.company)
    loans = member.loans.prefetch_related('installments', 'payments').order_by('-created_at')
    
    # Calculate ledger summary
    total_disbursed = sum(l.disbursed_amount for l in loans)
    total_interest = sum(l.interest_amount for l in loans)
    total_repayable = sum(l.total_amount for l in loans)
    total_collected = sum(l.total_paid for l in loans)
    total_balance = sum(l.outstanding_balance for l in loans)

    return render(request, 'members/member_detail.html', {
        'member': member,
        'loans': loans,
        'summary': {
            'total_disbursed': total_disbursed,
            'total_interest': total_interest,
            'total_repayable': total_repayable,
            'total_collected': total_collected,
            'total_balance': total_balance,
        }
    })


@login_required
def group_list_view(request):
    """
    Groups & Collection Routes Management.
    Organizes borrowers, active loan portfolios, and daily collections by Route / Group.
    """
    company = request.company
    today = timezone.now().date()
    query = request.GET.get('q', '').strip()
    agent_id = request.GET.get('agent', '')

    members_qs = Member.objects.filter(company=company)
    if request.user.is_agent and not request.user.can_manage_company:
        members_qs = members_qs.filter(assigned_agent=request.user)
    elif agent_id:
        members_qs = members_qs.filter(assigned_agent_id=agent_id)

    raw_routes = list(members_qs.exclude(area_or_route='').values_list('area_or_route', flat=True).distinct())

    if members_qs.filter(Q(area_or_route='') | Q(area_or_route__isnull=True)).exists():
        raw_routes.append('Unassigned Route')

    groups_data = []
    total_group_members = 0
    total_group_outstanding = Decimal('0.00')
    total_group_loans = 0
    total_today_due = Decimal('0.00')
    total_today_collected = Decimal('0.00')

    for route_name in sorted(raw_routes):
        if query and query.lower() not in route_name.lower():
            continue

        if route_name == 'Unassigned Route':
            m_group = members_qs.filter(Q(area_or_route='') | Q(area_or_route__isnull=True))
        else:
            m_group = members_qs.filter(area_or_route=route_name)

        m_count = m_group.count()
        if m_count == 0:
            continue

        assigned_agents = User.objects.filter(assigned_members__in=m_group).distinct()

        group_loans = Loan.objects.filter(member__in=m_group, status='ACTIVE')
        loans_count = group_loans.count()
        disbursed = group_loans.aggregate(s=Sum('principal_amount'))['s'] or Decimal('0.00')
        outstanding = group_loans.aggregate(s=Sum('outstanding_balance'))['s'] or Decimal('0.00')

        group_insts = Installment.objects.filter(
            loan__member__in=m_group,
            loan__status='ACTIVE'
        )
        today_due = group_insts.filter(Q(due_date=today) | Q(status='OVERDUE')).aggregate(s=Sum('pending_amount'))['s'] or Decimal('0.00')

        today_collected = Payment.objects.filter(
            loan__member__in=m_group,
            payment_date__date=today
        ).aggregate(s=Sum('amount'))['s'] or Decimal('0.00')

        groups_data.append({
            'name': route_name,
            'members_count': m_count,
            'agents': assigned_agents,
            'active_loans_count': loans_count,
            'total_disbursed': disbursed,
            'total_outstanding': outstanding,
            'today_due': today_due,
            'today_collected': today_collected,
        })

        total_group_members += m_count
        total_group_outstanding += outstanding
        total_group_loans += loans_count
        total_today_due += today_due
        total_today_collected += today_collected

    agents = User.objects.filter(company=company, is_active_agent=True)

    context = {
        'groups': groups_data,
        'total_groups': len(groups_data),
        'total_members': total_group_members,
        'total_loans': total_group_loans,
        'total_outstanding': total_group_outstanding,
        'total_today_due': total_today_due,
        'total_today_collected': total_today_collected,
        'query': query,
        'selected_agent': agent_id,
        'agents': agents,
    }
    return render(request, 'members/group_list.html', context)

