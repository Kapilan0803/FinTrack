def tenant_context(request):
    """
    Exposes current company and user role details to all templates.
    """
    company = getattr(request, 'company', None)
    return {
        'current_company': company,
        'user_role': getattr(request.user, 'role', None) if request.user.is_authenticated else None,
        'is_owner': getattr(request.user, 'is_owner', False) if request.user.is_authenticated else False,
        'is_manager': getattr(request.user, 'is_manager', False) if request.user.is_authenticated else False,
        'is_agent': getattr(request.user, 'is_agent', False) if request.user.is_authenticated else False,
        'can_manage': getattr(request.user, 'can_manage_company', False) if request.user.is_authenticated else False,
    }
