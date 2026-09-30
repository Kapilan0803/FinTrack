from django.urls import path
from . import views

app_name = 'members'

urlpatterns = [
    path('', views.member_list_view, name='member_list'),
    path('groups/', views.group_list_view, name='group_list'),
    path('add/', views.member_create_view, name='member_create'),
    path('<int:pk>/', views.member_detail_view, name='member_detail'),
    path('<int:pk>/edit/', views.member_update_view, name='member_edit'),
]
