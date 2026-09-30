from django.db import models


class DemoRequest(models.Model):
    name = models.CharField(max_length=150, verbose_name="Full Name")
    phone = models.CharField(max_length=20, verbose_name="Phone Number")
    email = models.EmailField(verbose_name="Email Address")
    company_name = models.CharField(max_length=200, verbose_name="Finance Company Name")
    city = models.CharField(max_length=100, blank=True, verbose_name="City / State")
    loan_types_interested = models.CharField(max_length=200, blank=True, verbose_name="Loan Types")
    notes = models.TextField(blank=True, verbose_name="Additional Information")
    is_contacted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Demo Request"
        verbose_name_plural = "Demo Requests"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.company_name} ({self.phone})"
