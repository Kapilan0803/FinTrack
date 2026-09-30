from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import Company, User
from members.models import Member
from loans.models import Loan, LoanPlan


class MemberModelAndViewsTests(TestCase):
    def setUp(self):
        self.company = Company.objects.create(
            name="Lakshmi Chits & Finance",
            phone="9842100000",
            email="lakshmi@finance.com",
            subscription_status="ACTIVE"
        )
        self.owner = User.objects.create_user(
            username="test_owner",
            password="password123",
            company=self.company,
            role="OWNER"
        )
        self.agent = User.objects.create_user(
            username="test_agent",
            password="password123",
            company=self.company,
            role="AGENT",
            is_active_agent=True
        )
        self.client = Client()
        self.client.login(username="test_owner", password="password123")

    def test_member_code_auto_generation(self):
        member1 = Member.objects.create(
            company=self.company,
            name="Ramesh Kumar",
            phone="9876500001",
            address="12 Main St"
        )
        self.assertEqual(member1.member_code, "MBR-0001")

        member2 = Member.objects.create(
            company=self.company,
            name="Suresh Babu",
            phone="9876500002",
            address="14 Main St"
        )
        self.assertEqual(member2.member_code, "MBR-0002")

    def test_member_properties(self):
        member = Member.objects.create(
            company=self.company,
            name="Ganesh Textiles",
            phone="9876500003",
            address="Bazaar St"
        )
        plan = LoanPlan.objects.create(
            company=self.company,
            name="Daily Plan",
            loan_type="DAILY",
            default_duration_units=10
        )
        Loan.objects.create(
            company=self.company,
            member=member,
            loan_plan=plan,
            loan_type="DAILY",
            principal_amount=Decimal('10000.00'),
            interest_rate_percent=Decimal('10.00'),
            interest_amount=Decimal('1000.00'),
            total_amount=Decimal('11000.00'),
            disbursed_amount=Decimal('10000.00'),
            installment_amount=Decimal('1100.00'),
            outstanding_balance=Decimal('8000.00'),
            total_paid=Decimal('3000.00'),
            number_of_installments=10,
            start_date="2026-09-01",
            end_date="2026-09-10",
            status="ACTIVE"
        )

        self.assertEqual(member.total_borrowed, Decimal('10000.00'))
        self.assertEqual(member.total_outstanding, Decimal('8000.00'))
        self.assertEqual(member.total_paid, Decimal('3000.00'))

    def test_member_list_filtering(self):
        Member.objects.create(
            company=self.company,
            name="Anand Kumar",
            phone="9876511111",
            address="North Street",
            area_or_route="Route North",
            assigned_agent=self.agent
        )
        Member.objects.create(
            company=self.company,
            name="Bala Murugan",
            phone="9876522222",
            address="South Street",
            area_or_route="Route South"
        )

        # Search by name
        res = self.client.get(reverse('members:member_list') + '?q=Anand')
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Anand Kumar")
        self.assertNotContains(res, "Bala Murugan")

        # Filter by route
        res2 = self.client.get(reverse('members:member_list') + '?route=Route+South')
        self.assertEqual(res2.status_code, 200)
        self.assertContains(res2, "Bala Murugan")
        self.assertNotContains(res2, "Anand Kumar")

        # HTMX partial table request
        res3 = self.client.get(reverse('members:member_list'), HTTP_HX_REQUEST='true')
        self.assertEqual(res3.status_code, 200)

    def test_member_create_and_update_views(self):
        # Create member
        post_data = {
            'name': 'Priya Sundar',
            'phone': '9842155555',
            'address': '45 Cross Cut Road',
            'area_or_route': 'Main Market',
            'visit_order': 1,
            'id_proof_type': 'AADHAAR',
            'id_proof_number': '123456789012',
            'guarantor_name': 'Sundar',
            'guarantor_phone': '9842155556',
            'guarantor_relation': 'Spouse'
        }
        res = self.client.post(reverse('members:member_create'), post_data)
        self.assertEqual(res.status_code, 302)
        new_member = Member.objects.get(name='Priya Sundar')
        self.assertEqual(new_member.company, self.company)
        self.assertEqual(new_member.area_or_route, 'Main Market')

        # Update member
        update_data = post_data.copy()
        update_data['address'] = '46 Cross Cut Road'
        res_update = self.client.post(reverse('members:member_edit', kwargs={'pk': new_member.pk}), update_data)
        self.assertEqual(res_update.status_code, 302)
        new_member.refresh_from_db()
        self.assertEqual(new_member.address, '46 Cross Cut Road')

        # Detail view
        res_detail = self.client.get(reverse('members:member_detail', kwargs={'pk': new_member.pk}))
        self.assertEqual(res_detail.status_code, 200)
        self.assertContains(res_detail, 'Priya Sundar')

    def test_group_list_view(self):
        Member.objects.create(
            company=self.company,
            name="Trader Raman",
            phone="9876543210",
            address="Shop 5",
            area_or_route="Bazaar Route"
        )
        res = self.client.get(reverse('members:group_list'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Groups & Collection Routes')
        self.assertContains(res, 'Bazaar Route')

