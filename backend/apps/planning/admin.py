"""Admin configuration for Planning models."""
from django.contrib import admin
from .models import (
    WeekPlan, ShiftAssignment, DailyPlan, TaskAssignment,
    DailyLoadSummary, PlanningAlert
)


class ShiftAssignmentInline(admin.TabularInline):
    model = ShiftAssignment
    extra = 0
    fields = ['date', 'employee', 'team', 'shift_template', 'assigned_hours', 'is_day_off']
    raw_id_fields = ['employee', 'team']
    ordering = ['date', 'shift_template__time_block__order']


@admin.register(WeekPlan)
class WeekPlanAdmin(admin.ModelAdmin):
    list_display = [
        'week_start_date', 'week_end_date', 'name', 'status',
        'assignment_count', 'created_at', 'published_at'
    ]
    list_filter = ['status', 'week_start_date']
    search_fields = ['name']
    date_hierarchy = 'week_start_date'
    inlines = [ShiftAssignmentInline]

    fieldsets = (
        ('Identificación', {
            'fields': ('week_start_date', 'name')
        }),
        ('Estado', {
            'fields': ('status', 'published_at')
        }),
        ('Notas', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )

    def assignment_count(self, obj):
        return obj.shift_assignments.count()
    assignment_count.short_description = 'Asignaciones'

    def week_end_date(self, obj):
        return obj.week_end_date
    week_end_date.short_description = 'Fin de semana'

    actions = ['publish_plans', 'archive_plans']

    def publish_plans(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(status__in=['DRAFT', 'REVIEW', 'APPROVED']).update(
            status='PUBLISHED',
            published_at=timezone.now()
        )
        self.message_user(request, f'{updated} planes publicados.')
    publish_plans.short_description = 'Publicar planes seleccionados'

    def archive_plans(self, request, queryset):
        updated = queryset.exclude(status='ARCHIVED').update(status='ARCHIVED')
        self.message_user(request, f'{updated} planes archivados.')
    archive_plans.short_description = 'Archivar planes seleccionados'


@admin.register(ShiftAssignment)
class ShiftAssignmentAdmin(admin.ModelAdmin):
    list_display = [
        'date', 'get_assignee', 'shift_template', 'assigned_hours',
        'is_day_off', 'week_plan'
    ]
    list_filter = ['date', 'shift_template__time_block', 'is_day_off']
    search_fields = ['employee__first_name', 'employee__last_name', 'team__name']
    date_hierarchy = 'date'
    raw_id_fields = ['employee', 'team', 'week_plan']

    def get_assignee(self, obj):
        return obj.get_assignee_name()
    get_assignee.short_description = 'Asignado a'


class TaskAssignmentInline(admin.TabularInline):
    model = TaskAssignment
    extra = 0
    fields = ['room_task', 'employee', 'team', 'zone', 'order_in_assignment', 'status']
    raw_id_fields = ['room_task', 'employee', 'team']
    ordering = ['zone', 'order_in_assignment']


@admin.register(DailyPlan)
class DailyPlanAdmin(admin.ModelAdmin):
    list_display = [
        'date', 'status', 'week_plan', 'get_total_tasks',
        'get_completed_tasks', 'created_at'
    ]
    list_filter = ['status', 'date']
    date_hierarchy = 'date'
    inlines = [TaskAssignmentInline]

    def get_total_tasks(self, obj):
        return obj.get_total_tasks()
    get_total_tasks.short_description = 'Total tareas'

    def get_completed_tasks(self, obj):
        return obj.get_completed_tasks()
    get_completed_tasks.short_description = 'Completadas'


@admin.register(TaskAssignment)
class TaskAssignmentAdmin(admin.ModelAdmin):
    list_display = [
        'daily_plan', 'room_task', 'get_assignee', 'zone',
        'order_in_assignment', 'status'
    ]
    list_filter = ['status', 'zone', 'daily_plan__date']
    search_fields = ['room_task__room_daily_state__room__number']
    raw_id_fields = ['daily_plan', 'room_task', 'employee', 'team']

    def get_assignee(self, obj):
        if obj.employee:
            return obj.employee.full_name
        if obj.team:
            return str(obj.team)
        return "Sin asignar"
    get_assignee.short_description = 'Asignado a'


@admin.register(DailyLoadSummary)
class DailyLoadSummaryAdmin(admin.ModelAdmin):
    list_display = [
        'date', 'time_block', 'total_tasks', 'total_minutes_required',
        'total_minutes_available', 'load_percentage', 'is_overloaded'
    ]
    list_filter = ['time_block', 'date']
    date_hierarchy = 'date'

    def is_overloaded(self, obj):
        return obj.is_overloaded
    is_overloaded.boolean = True
    is_overloaded.short_description = 'Sobrecarga'


@admin.register(PlanningAlert)
class PlanningAlertAdmin(admin.ModelAdmin):
    list_display = [
        'date', 'time_block', 'alert_type', 'severity',
        'title', 'is_resolved', 'created_at'
    ]
    list_filter = ['alert_type', 'severity', 'is_resolved', 'date']
    search_fields = ['title', 'message']
    date_hierarchy = 'date'

    actions = ['mark_resolved']

    def mark_resolved(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(is_resolved=False).update(
            is_resolved=True,
            resolved_at=timezone.now(),
            resolved_by=str(request.user)
        )
        self.message_user(request, f'{updated} alertas marcadas como resueltas.')
    mark_resolved.short_description = 'Marcar como resueltas'
