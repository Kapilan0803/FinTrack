from datetime import timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import Company, User
from members.models import Member
from loans.models import LoanPlan, Loan, Installment
from loans.services import generate_loan_schedule
from loan_collections.models import Payment, CollectionAttempt
from loan_collections.services import record_collection


class Command(BaseCommand):
    help = 'Seeds realistic demo data for FinTrack with company, staff, borrowers, loans, and collections.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding demo data for FinTrack...")

        # 1. Company
        company, _ = Company.objects.get_or_create(
            name="Sri Lakshmi Finance",
            defaults={
                'phone': "9842100000",
                'email': "contact@srilakshmifinance.com",
                'address': "142 Cross Cut Road, Gandhipuram, Coimbatore, Tamil Nadu 641012",
                'skip_sundays_in_daily': True,
                'subscription_status': 'TRIALING',
                'trial_starts_at': timezone.now() - timedelta(days=2),
                'trial_ends_at': timezone.now() + timedelta(days=28),
                'currency_symbol': '₹'
            }
        )

        # 2. Users
        owner = User.objects.filter(username="owner").first()
        if not owner:
            owner = User.objects.create_user(
                username="owner",
                email="owner@srilakshmifinance.com",
                password="password123",
                first_name="Kannan",
                last_name="Sundaram",
                company=company,
                role='OWNER',
                phone_number="9842100000",
                is_staff=True,
                is_superuser=True
            )

        agent1 = User.objects.filter(username="agent_kannan").first()
        if not agent1:
            agent1 = User.objects.create_user(
                username="agent_kannan",
                email="murugan@srilakshmifinance.com",
                password="password123",
                first_name="Murugan",
                last_name="K",
                company=company,
                role='AGENT',
                phone_number="9842199991",
                daily_collection_target=Decimal('50000.00'),
                is_active_agent=True
            )

        agent2 = User.objects.filter(username="agent_rajesh").first()
        if not agent2:
            agent2 = User.objects.create_user(
                username="agent_rajesh",
                email="rajesh@srilakshmifinance.com",
                password="password123",
                first_name="Rajesh",
                last_name="Kumar",
                company=company,
                role='AGENT',
                phone_number="9842199992",
                daily_collection_target=Decimal('40000.00'),
                is_active_agent=True
            )

        # 3. Loan Plans
        daily_plan, _ = LoanPlan.objects.get_or_create(
            company=company,
            name="Daily 100 Days Market Plan",
            defaults={
                'loan_type': 'DAILY',
                'default_interest_rate_percent': Decimal('10.00'),
                'default_duration_units': 100,
                'processing_fee_percent': Decimal('2.00'),
                'penalty_rate_percent': Decimal('1.00')
            }
        )

        weekly_plan, _ = LoanPlan.objects.get_or_create(
            company=company,
            name="Weekly 15 Weeks Micro Plan",
            defaults={
                'loan_type': 'WEEKLY',
                'default_interest_rate_percent': Decimal('12.00'),
                'default_duration_units': 15,
                'processing_fee_percent': Decimal('2.00'),
                'penalty_rate_percent': Decimal('1.50')
            }
        )

        monthly_interest_plan, _ = LoanPlan.objects.get_or_create(
            company=company,
            name="Monthly Interest Only (Gold/Business)",
            defaults={
                'loan_type': 'MONTHLY_INTEREST',
                'default_interest_rate_percent': Decimal('2.00'),
                'default_duration_units': 12,
                'processing_fee_percent': Decimal('1.00'),
                'penalty_rate_percent': Decimal('2.00')
            }
        )

        # 4. Members with Door-to-Door Walk Order & GPS Coordinates
        members_data = [
            ("Meena Ramesh", "9842111111", "Flower Market Route", "Coimbatore", "AADHAAR", "2345 6789 0123", agent1, 1, "Shop #14, Flower Market", Decimal('11.016844'), Decimal('76.955832')),
            ("Karthik S.", "9786522222", "Town Hall Route", "Coimbatore", "PAN", "ABCDE1234F", agent1, 2, "Opp. Clock Tower", Decimal('11.005550'), Decimal('76.966120')),
            ("Lakshmi V.", "9003133333", "Gandhipuram Market", "Coimbatore", "VOTER_ID", "VTR1234567", agent1, 3, "Near Cross Cut Signal", Decimal('11.018300'), Decimal('76.965400')),
            ("Suresh Babu", "9843244444", "RS Puram", "Coimbatore", "AADHAAR", "9876 5432 1098", agent2, 4, "DB Road, Near Post Office", Decimal('11.010200'), Decimal('76.948200')),
            ("Kavitha M.", "9443355555", "North Bus Stand", "Coimbatore", "AADHAAR", "3456 7890 1234", agent1, 5, "Stall #7, Bus Stand Complex", Decimal('11.025000'), Decimal('76.950000')),
            ("Dinesh Kumar", "9159966666", "Peelamedu", "Coimbatore", "PAN", "XYZPK9876Q", agent2, 6, "Avinashi Road, Near PSG", Decimal('11.028000'), Decimal('77.001000')),
            ("Murugan Textiles", "9842177777", "Flower Market Route", "Coimbatore", "PAN", "TEX9876543", agent1, 7, "Shop #28, Market Lane", Decimal('11.017500'), Decimal('76.956200')),
        ]

        created_members = []
        for name, phone, route, city, id_type, id_no, agent, walk_order, landmark, lat, lng in members_data:
            m, created = Member.objects.get_or_create(
                company=company,
                phone=phone,
                defaults={
                    'name': name,
                    'address': f"{route}, {city}",
                    'city': city,
                    'area_or_route': route,
                    'id_proof_type': id_type,
                    'id_proof_number': id_no,
                    'assigned_agent': agent,
                    'visit_order': walk_order,
                    'landmark': landmark,
                    'latitude': lat,
                    'longitude': lng,
                    'is_active': True
                }
            )
            if not created:
                m.visit_order = walk_order
                m.landmark = landmark
                m.latitude = lat
                m.longitude = lng
                m.area_or_route = route
                m.save()
            created_members.append(m)

        # 5. Loans
        today = timezone.now().date()
        loan_configs = [
            (created_members[0], daily_plan, Decimal('10000.00'), Decimal('10.00'), 100, today - timedelta(days=12), agent1, 1),
            (created_members[1], daily_plan, Decimal('20000.00'), Decimal('10.00'), 100, today - timedelta(days=8), agent1, 2),
            (created_members[2], daily_plan, Decimal('15000.00'), Decimal('10.00'), 100, today - timedelta(days=5), agent1, 3),
            (created_members[3], weekly_plan, Decimal('30000.00'), Decimal('12.00'), 15, today - timedelta(weeks=4), agent2, 4),
            (created_members[4], daily_plan, Decimal('5000.00'), Decimal('10.00'), 50, today - timedelta(days=20), agent1, 5),
            (created_members[5], daily_plan, Decimal('25000.00'), Decimal('10.00'), 100, today, agent2, 6),
            (created_members[6], monthly_interest_plan, Decimal('50000.00'), Decimal('2.00'), 12, today - timedelta(days=35), agent1, 7),
        ]

        for mem, plan, principal, rate, num_inst, start_dt, agent, r_seq in loan_configs:
            loan = Loan.objects.filter(company=company, member=mem).first()
            if not loan:
                if plan.loan_type == 'MONTHLY_INTEREST':
                    # Interest is monthly rate * principal
                    monthly_interest = (principal * (rate / Decimal('100.00'))).quantize(Decimal('0.01'))
                    interest = monthly_interest * Decimal(str(num_inst))
                    total = principal + interest
                    inst_amt = monthly_interest
                else:
                    interest = (principal * (rate / Decimal('100.00'))).quantize(Decimal('0.01'))
                    total = principal + interest
                    inst_amt = (total / Decimal(str(num_inst))).quantize(Decimal('0.01'))

                proc_fee = (principal * (plan.processing_fee_percent / Decimal('100.00'))).quantize(Decimal('0.01'))
                disbursed = principal - proc_fee

                loan = Loan.objects.create(
                    company=company,
                    member=mem,
                    loan_plan=plan,
                    loan_type=plan.loan_type,
                    principal_amount=principal,
                    interest_rate_percent=rate,
                    interest_amount=interest,
                    processing_fee=proc_fee,
                    disbursed_amount=disbursed,
                    total_amount=total,
                    start_date=start_dt,
                    end_date=start_dt + timedelta(days=num_inst if plan.loan_type == 'DAILY' else num_inst * 30),
                    number_of_installments=num_inst,
                    installment_amount=inst_amt,
                    outstanding_balance=total,
                    total_paid=Decimal('0.00'),
                    status='ACTIVE',
                    assigned_agent=agent,
                    route_sequence=r_seq
                )
                generate_loan_schedule(loan)

                # Record past collections
                past_insts = loan.installments.filter(due_date__lt=today).order_by('due_date')
                for idx, inst in enumerate(past_insts):
                    if mem.name == "Kavitha M." and idx > len(past_insts) - 3:
                        inst.status = 'OVERDUE'
                        inst.penalty_amount = Decimal('30.00')
                        inst.save()
                    else:
                        record_collection(
                            loan=loan,
                            amount=inst.pending_amount,
                            collected_by=agent,
                            payment_mode='CASH' if idx % 2 == 0 else 'UPI',
                            installment=inst
                        )

                # Collect on first member to demonstrate a Paid card today
                today_inst = loan.installments.filter(due_date=today).first()
                if today_inst and mem.name == "Meena Ramesh":
                    record_collection(
                        loan=loan,
                        amount=today_inst.pending_amount,
                        collected_by=agent,
                        payment_mode='CASH',
                        installment=today_inst
                    )

        # 6. Add a sample CollectionAttempt for Karthik S. (Missed Visit - Shop Closed)
        karthik_inst = Installment.objects.filter(loan__member__name="Karthik S.", due_date=today).first()
        if karthik_inst:
            CollectionAttempt.objects.get_or_create(
                company=company,
                loan=karthik_inst.loan,
                installment=karthik_inst,
                defaults={
                    'attempted_by': agent1,
                    'reason': 'SHOP_CLOSED',
                    'promised_date': today + timedelta(days=1),
                    'notes': "Owner was attending vegetable wholesale market auction, will pay tomorrow."
                }
            )

        # 7. Add sample past payments for 7-day trend chart
        sample_loan = Loan.objects.filter(company=company).first()
        if sample_loan:
            for day_offset in range(1, 7):
                past_date = timezone.now() - timedelta(days=day_offset)
                Payment.objects.get_or_create(
                    company=company,
                    loan=sample_loan,
                    receipt_number=f"RCP-HIST-{day_offset}",
                    defaults={
                        'amount': Decimal('4200.00') + Decimal(str(day_offset * 600)),
                        'payment_mode': 'CASH' if day_offset % 2 == 0 else 'UPI',
                        'collected_by': agent1,
                        'payment_date': past_date
                    }
                )

        self.stdout.write(self.style.SUCCESS("Demo data seeded successfully with RupeeCollect features!"))
        self.stdout.write(self.style.SUCCESS("Credentials: Owner: 'owner' / 'password123' | Agent: 'agent_kannan' / 'password123'"))
