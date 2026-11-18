from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class FretFlowUserAdmin(UserAdmin):
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Contact details', {'fields': ('email', 'first_name', 'last_name')}),
    )
    fieldsets = UserAdmin.fieldsets + (
        ('Practice preferences', {
            'fields': ('contact_number', 'preferred_accidentals', 'default_bpm'),
        }),
    )
