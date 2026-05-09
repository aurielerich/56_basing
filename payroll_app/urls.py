from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/karyawan/', views.dashboard_karyawan, name='dashboard_karyawan'),
    path('dashboard/hr/', views.dashboard_hr, name='dashboard_hr'),
    path('attendance/record/', views.record_attendance, name='record_attendance'),
    path('payroll/generate/', views.generate_payroll, name='generate_payroll'),
]
