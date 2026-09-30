from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    path('pricing/', views.pricing_view, name='pricing'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('verify/', views.verify_payment_view, name='verify_payment'),
    path('invoices/', views.invoices_view, name='invoices'),
    path('webhook/', views.razorpay_webhook, name='webhook'),
]
