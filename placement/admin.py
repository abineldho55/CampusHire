from django.contrib import admin
from .models import UserProfile, StudentProfile, CompanyProfile, jobPost, Application


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'phone')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__email', 'phone')


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'roll_number', 'branch', 'cgpa', 'backlogs', 'is_placed')
    list_filter = ('branch', 'is_placed', 'graduation_year')
    search_fields = ('full_name', 'roll_number', 'user__username', 'skills')


@admin.register(CompanyProfile)
class CompanyProfileAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'contact_email', 'contact_phone', 'website', 'is_verified', 'verification_status')
    list_filter = ('is_verified', 'verification_status')
    search_fields = ('company_name', 'contact_email')


@admin.register(jobPost)
class JobPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'job_type', 'package_lpa', 'deadline', 'is_active')
    list_filter = ('job_type', 'is_active', 'deadline')
    search_fields = ('title', 'company__company_name', 'required_skills', 'location')


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('student', 'job', 'status', 'interview_date', 'applied_at')
    list_filter = ('status', 'applied_at')
    search_fields = ('student__full_name', 'job__title', 'job__company__company_name')
