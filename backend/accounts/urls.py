from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('team/', views.team_list_view, name='team_list'),
    path('team/add/', views.staff_create_view, name='staff_create'),
    path('team/<int:user_id>/toggle/', views.staff_toggle_status_view, name='staff_toggle_status'),
    path('settings/', views.company_settings_view, name='company_settings'),
]
