from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('daily/', views.daily_report_view, name='daily_report'),
    path('agents/', views.agent_performance_view, name='agent_performance'),
    path('defaulters/', views.defaulters_report_view, name='defaulters_report'),
]
