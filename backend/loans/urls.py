from django.urls import path
from . import views

app_name = 'loans'

urlpatterns = [
    path('', views.loan_list_view, name='loan_list'),
    path('create/', views.loan_create_view, name='loan_create'),
    path('<int:pk>/', views.loan_detail_view, name='loan_detail'),
    path('<int:pk>/close/', views.loan_close_view, name='loan_close'),
    path('plans/', views.loan_plan_list_view, name='plan_list'),
    path('plans/add/', views.loan_plan_create_view, name='plan_create'),
]
