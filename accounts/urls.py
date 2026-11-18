from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.SignInView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/member/', views.member_dashboard, name='member_dashboard'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('profile/', views.profile, name='profile'),
]
