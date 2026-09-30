from django.urls import path
from . import views

app_name = 'collections'

urlpatterns = [
    path('today/', views.today_collection_view, name='today'),
    path('quick-pay/<int:installment_id>/', views.quick_pay_htmx_view, name='quick_pay'),
    path('custom-pay/<int:loan_id>/', views.custom_pay_view, name='custom_pay'),
    path('mark-missed/<int:installment_id>/', views.mark_missed_htmx_view, name='mark_missed'),
    path('settle-principal/<int:loan_id>/', views.settle_principal_view, name='settle_principal'),
    path('cash-closing/', views.cash_closing_view, name='cash_closing'),
    path('receipt/<str:receipt_number>/', views.receipt_view, name='receipt'),
]
