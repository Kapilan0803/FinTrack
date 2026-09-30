from django.contrib import admin
from .models import Member


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('member_code', 'name', 'phone', 'area_or_route', 'company', 'assigned_agent', 'is_active', 'created_at')
    search_fields = ('name', 'member_code', 'phone', 'id_proof_number')
    list_filter = ('company', 'is_active', 'id_proof_type')
