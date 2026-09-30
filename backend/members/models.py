from decimal import Decimal
from django.db import models
from django.db.models import Sum
from accounts.models import Company, User


class Member(models.Model):
    ID_TYPE_CHOICES = [
        ('AADHAAR', 'Aadhaar Card'),
        ('PAN', 'PAN Card'),
        ('VOTER_ID', 'Voter ID'),
        ('RATION_CARD', 'Ration Card'),
        ('DRIVING_LICENSE', 'Driving License'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='members')
    member_code = models.CharField(max_length=30, db_index=True, verbose_name="Member / Customer ID")
    name = models.CharField(max_length=150, verbose_name="Full Name")
    phone = models.CharField(max_length=20, db_index=True, verbose_name="Mobile Number")
    email = models.EmailField(blank=True, verbose_name="Email Address")
    address = models.TextField(verbose_name="Residential Address")
    city = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=10, blank=True)
    area_or_route = models.CharField(
        max_length=120,
        blank=True,
        verbose_name="Route / Area Name",
        help_text="Helpful for grouping collections by route or locality"
    )
    visit_order = models.PositiveIntegerField(
        default=0,
        db_index=True,
        verbose_name="Walk / Visit Order",
        help_text="Sequence number for the agent walking route (e.g. 1, 2, 3...)"
    )
    landmark = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Nearby Landmark",
        help_text="e.g. Opp. Murugan Temple, Behind Bus Stand"
    )
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name="GPS Latitude"
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name="GPS Longitude"
    )

    # KYC Verification
    id_proof_type = models.CharField(max_length=30, choices=ID_TYPE_CHOICES, default='AADHAAR')
    id_proof_number = models.CharField(max_length=50, blank=True, verbose_name="ID Number")
    id_proof_file = models.FileField(upload_to='kyc_docs/', blank=True, null=True, verbose_name="KYC Document")
    photo = models.ImageField(upload_to='member_photos/', blank=True, null=True, verbose_name="Customer Photo")

    # Guarantor
    guarantor_name = models.CharField(max_length=150, blank=True, verbose_name="Guarantor Name")
    guarantor_phone = models.CharField(max_length=20, blank=True, verbose_name="Guarantor Phone")
    guarantor_relation = models.CharField(max_length=50, blank=True, verbose_name="Relationship with Borrower")

    # Field Operations
    assigned_agent = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_members',
        verbose_name="Assigned Collection Agent"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Member"
        verbose_name_plural = "Members"
        unique_together = ('company', 'member_code')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.member_code}) - {self.phone}"

    def save(self, *args, **kwargs):
        if not self.member_code and self.company_id:
            count = Member.objects.filter(company=self.company).count() + 1
            self.member_code = f"MBR-{count:04d}"
        super().save(*args, **kwargs)

    @property
    def total_borrowed(self):
        aggregate = self.loans.aggregate(total=Sum('principal_amount'))
        return aggregate['total'] or Decimal('0.00')

    @property
    def total_outstanding(self):
        aggregate = self.loans.filter(status='ACTIVE').aggregate(total=Sum('outstanding_balance'))
        return aggregate['total'] or Decimal('0.00')

    @property
    def total_paid(self):
        aggregate = self.loans.aggregate(total=Sum('total_paid'))
        return aggregate['total'] or Decimal('0.00')
