"""Admin configuration for Rules models."""
from django.contrib import admin
from .models import TaskTimeRule, ZoneAssignmentRule, ElasticityRule, PlanningParameter


@admin.register(TaskTimeRule)
class TaskTimeRuleAdmin(admin.ModelAdmin):
    list_display = [
        'task_type', 'condition', 'room_type',
        'base_minutes', 'time_multiplier', 'priority', 'is_active'
    ]
    list_filter = ['task_type', 'condition', 'room_type', 'is_active']
    list_editable = ['base_minutes', 'time_multiplier', 'priority', 'is_active']
    search_fields = ['task_type__code', 'description']
    ordering = ['task_type', '-priority']

    fieldsets = (
        ('Tarea', {
            'fields': ('task_type',)
        }),
        ('Condición', {
            'fields': ('condition', 'room_type')
        }),
        ('Tiempo', {
            'fields': ('base_minutes', 'time_multiplier', 'priority')
        }),
        ('Descripción', {
            'fields': ('description', 'is_active'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ZoneAssignmentRule)
class ZoneAssignmentRuleAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'value_boolean', 'value_integer', 'value_text', 'is_active']
    list_editable = ['value_boolean', 'value_integer', 'value_text', 'is_active']
    search_fields = ['code', 'name']


@admin.register(ElasticityRule)
class ElasticityRuleAdmin(admin.ModelAdmin):
    list_display = [
        'elasticity_level', 'max_extra_hours_week',
        'max_extra_hours_day', 'assignment_priority'
    ]
    list_editable = ['max_extra_hours_week', 'max_extra_hours_day', 'assignment_priority']


@admin.register(PlanningParameter)
class PlanningParameterAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'value_type', 'value', 'category']
    list_filter = ['category', 'value_type']
    list_editable = ['value']
    search_fields = ['code', 'name']
    ordering = ['category', 'code']
