from django.urls import path
from . import views

urlpatterns = [
    # Authentication & Registration URLs
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('register/student/', views.register_student, name='register_student'),
    path('register/company/', views.register_company, name='register_company'),

    # Role-Based Dashboards
    path('dashboard/student/', views.student_dashboard, name='student_dashboard'),
    path('dashboard/company/', views.company_dashboard, name='company_dashboard'),
    path('dashboard/officer/', views.officer_dashboard, name='officer_dashboard'),

    # Company Verification (Office Administrator)
    path('companies/<int:pk>/verify/<str:action>/', views.verify_company, name='verify_company'),

    # Job & Application Management
    path('jobs/', views.job_list, name='job_list'),
    path('jobs/post/', views.post_job, name='post_job'),
    path('jobs/<int:pk>/', views.job_detail, name='job_detail'),
    path('jobs/<int:pk>/apply/', views.apply_for_job, name='apply_for_job'),
    path('jobs/<int:pk>/delete/', views.delete_job, name='delete_job'),
    path('jobs/<int:pk>/toggle-status/', views.toggle_job_active, name='toggle_job_active'),
    path('applications/<int:pk>/update/', views.update_application_status, name='update_application_status'),
    path('applications/<int:pk>/delete/', views.delete_application, name='delete_application'),

    path('', views.index, name='index')
]