from django.urls import path
from . import views

app_name = 'website'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('request-demo/', views.demo_request_view, name='demo_request'),
    path('privacy/', views.privacy_policy_view, name='privacy'),
    path('terms/', views.terms_of_service_view, name='terms'),
]
