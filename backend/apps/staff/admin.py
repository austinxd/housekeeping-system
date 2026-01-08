"""Admin configuration for Staff models."""
from django.contrib import admin
from .models import Role, Employee, Team, EmployeeUnavailability


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'display_order', 'employee_count', 'is_active']
    list_editable = ['display_order', 'is_active']
    filter_horizontal = ['allowed_blocks']
    search_fields = ['code', 'name']

    def employee_count(self, obj):
        return obj.employees.filter(is_active=True).count()
    employee_count.short_description = 'Empleados activos'


class UnavailabilityInline(admin.TabularInline):
    model = EmployeeUnavailability
    extra = 0
    fields = ['date_start', 'date_end', 'reason', 'notes']


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = [
        'employee_code', 'full_name', 'role', 'weekly_hours_target',
        'elasticity', 'can_work_night', 'is_active'
    ]
    list_filter = ['role', 'elasticity', 'can_work_night', 'is_active', 'allowed_blocks']
    list_editable = ['weekly_hours_target', 'elasticity', 'is_active']
    search_fields = ['employee_code', 'first_name', 'last_name']
    filter_horizontal = ['allowed_blocks', 'fixed_days_off', 'eligible_tasks']
    inlines = [UnavailabilityInline]

    fieldsets = (
        ('Identificación', {
            'fields': ('employee_code', 'first_name', 'last_name', 'role')
        }),
        ('Horario', {
            'fields': ('weekly_hours_target', 'elasticity', 'allowed_blocks', 'fixed_days_off')
        }),
        ('Capacidades', {
            'fields': ('eligible_tasks', 'can_work_night')
        }),
        ('Estado', {
            'fields': ('is_active', 'hire_date', 'notes')
        }),
    )

    def full_name(self, obj):
        return obj.full_name
    full_name.short_description = 'Nombre completo'


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'team_type', 'member_count', 'get_members_display', 'is_active']
    list_filter = ['team_type', 'is_active']
    filter_horizontal = ['members']
    search_fields = ['name', 'members__first_name', 'members__last_name']

    def get_members_display(self, obj):
        return ', '.join([m.first_name for m in obj.members.all()[:5]])
    get_members_display.short_description = 'Miembros'

    def member_count(self, obj):
        return obj.members.count()
    member_count.short_description = 'Nº miembros'


@admin.register(EmployeeUnavailability)
class EmployeeUnavailabilityAdmin(admin.ModelAdmin):
    list_display = ['employee', 'date_start', 'date_end', 'reason']
    list_filter = ['reason', 'date_start']
    search_fields = ['employee__first_name', 'employee__last_name']
    date_hierarchy = 'date_start'
