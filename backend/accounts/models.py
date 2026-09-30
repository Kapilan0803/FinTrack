from datetime import timedelta
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.utils.text import slugify


class Company(models.Model):
    SUBSCRIPTION_STATUS_CHOICES = [
        ('TRIALING', 'Trialing (30 Days)'),
        ('ACTIVE', 'Active Subscription'),
        ('EXPIRED', 'Expired / Payment Required'),
        ('CANCELLED', 'Cancelled'),
    ]

    name = models.CharField(max_length=255, verbose_name="Company / Business Name")
    code = models.SlugField(max_length=60, unique=True, db_index=True)
    phone = models.CharField(max_length=20, verbose_name="Business Phone")
    email = models.EmailField(verbose_name="Business Email")
    address = models.TextField(blank=True, verbose_name="Office Address")
    currency_symbol = models.CharField(max_length=5, default="₹")
    skip_sundays_in_daily = models.BooleanField(
        default=True,
        verbose_name="Skip Sundays in Daily Loans",
        help_text="If checked, daily loan repayment schedules will automatically skip Sundays."
    )

    # Subscription & Trial Lifecycle
    trial_starts_at = models.DateTimeField(default=timezone.now)
    trial_ends_at = models.DateTimeField(blank=True, null=True)
    subscription_status = models.CharField(
        max_length=20,
        choices=SUBSCRIPTION_STATUS_CHOICES,
        default='TRIALING'
    )
    razorpay_customer_id = models.CharField(max_length=100, blank=True)
    razorpay_subscription_id = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Company"
        verbose_name_plural = "Companies"
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.code:
            base_slug = slugify(self.name) or "company"
            slug = base_slug
            counter = 1
            while Company.objects.filter(code=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.code = slug
        if not self.trial_ends_at:
            self.trial_ends_at = timezone.now() + timedelta(days=30)
        super().save(*args, **kwargs)

    def is_subscription_active(self):
        """Returns True if company has active paid subscription or unexpired trial."""
        if not self.is_active:
            return False
        if self.subscription_status == 'ACTIVE':
            return True
        if self.subscription_status == 'TRIALING':
            if self.trial_ends_at and timezone.now() <= self.trial_ends_at:
                return True
        return False

    @property
    def days_left_in_trial(self):
        if self.subscription_status != 'TRIALING' or not self.trial_ends_at:
            return 0
        diff = self.trial_ends_at - timezone.now()
        return max(0, diff.days)


class User(AbstractUser):
    ROLE_CHOICES = [
        ('OWNER', 'Company Owner / Admin'),
        ('MANAGER', 'Operations Manager'),
        ('AGENT', 'Field Collection Agent'),
    ]

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='users'
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='OWNER'
    )
    phone_number = models.CharField(max_length=20, blank=True)
    daily_collection_target = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        help_text="Target amount in ₹ expected per day for field collections"
    )
    is_active_agent = models.BooleanField(
        default=True,
        help_text="Designates whether this agent can currently record collections in the field."
    )

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ['role', 'first_name', 'username']

    def __str__(self):
        name = self.get_full_name() or self.username
        role_label = dict(self.ROLE_CHOICES).get(self.role, self.role)
        return f"{name} ({role_label})"

    @property
    def is_owner(self):
        return self.role == 'OWNER'

    @property
    def is_manager(self):
        return self.role == 'MANAGER'

    @property
    def is_agent(self):
        return self.role == 'AGENT'

    @property
    def can_manage_company(self):
        return self.is_superuser or self.role in ['OWNER', 'MANAGER']
