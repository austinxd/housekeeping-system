"""Admin configuration for Shifts models."""
from django.contrib import admin
from .models import ShiftTemplate, ShiftSubBlock


class SubBlockInline(admin.TabularInline):
    model = ShiftSubBlock
    extra = 0
    fields = ['code', 'name', 'start_time', 'end_time', 'is_break', 'order']
    ordering = ['order', 'start_time']


@admin.register(ShiftTemplate)
class ShiftTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'name', 'role', 'time_block',
        'start_time', 'end_time', 'total_hours', 'is_active'
    ]
    list_filter = ['role', 'time_block', 'is_active']
    list_editable = ['is_active']
    search_fields = ['code', 'name']
    inlines = [SubBlockInline]

    fieldsets = (
        ('Identificación', {
            'fields': ('code', 'name', 'description')
        }),
        ('Clasificación', {
            'fields': ('role', 'time_block')
        }),
        ('Horario', {
            'fields': ('start_time', 'end_time')
        }),
        ('Pausa Principal', {
            'fields': ('break_start', 'break_end', 'break_minutes'),
            'classes': ('collapse',)
        }),
        ('Estado', {
            'fields': ('is_active',)
        }),
    )

    def total_hours(self, obj):
        return f"{obj.total_hours}h"
    total_hours.short_description = 'Horas efectivas'


@admin.register(ShiftSubBlock)
class ShiftSubBlockAdmin(admin.ModelAdmin):
    list_display = [
        'shift_template', 'code', 'name',
        'start_time', 'end_time', 'duration_minutes', 'is_break', 'order'
    ]
    list_filter = ['shift_template', 'is_break']
    list_editable = ['order', 'is_break']
    ordering = ['shift_template', 'order']

    def duration_minutes(self, obj):
        return f"{obj.duration_minutes} min"
    duration_minutes.short_description = 'Duración'
