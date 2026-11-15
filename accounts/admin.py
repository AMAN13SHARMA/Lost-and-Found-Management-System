"""
Django Admin registration for the Administrator proxy (FR-34, FR-35).

Regular User management is provided by Django's built-in UserAdmin.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Administrator


@admin.register(Administrator)
class AdministratorAdmin(UserAdmin):
    list_display = ("username", "email", "is_staff", "is_superuser", "is_active", "last_login")
    list_filter = ("is_staff", "is_superuser", "is_active")
