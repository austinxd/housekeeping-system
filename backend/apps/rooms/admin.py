"""Admin configuration for Rooms models."""
from django.contrib import admin
from .models import RoomDailyState, RoomDailyTask, ProtelImportLog


class RoomDailyTaskInline(admin.TabularInline):
    model = RoomDailyTask
    extra = 0
    fields = ['task_type', 'time_block', 'estimated_minutes', 'status', 'priority']
    readonly_fields = ['estimated_minutes']


@admin.register(RoomDailyState)
class RoomDailyStateAdmin(admin.ModelAdmin):
    list_display = [
        'date', 'room', 'occupancy_status', 'stay_day_number',
        'day_cleaning_status', 'night_expected_difficulty', 'is_vip', 'task_count'
    ]
    list_filter = [
        'date', 'occupancy_status', 'day_cleaning_status',
        'night_expected_difficulty', 'is_vip', 'room__zone'
    ]
    list_editable = ['day_cleaning_status']
    search_fields = ['room__number']
    date_hierarchy = 'date'
    inlines = [RoomDailyTaskInline]
    raw_id_fields = ['room']

    fieldsets = (
        ('Identificación', {
            'fields': ('date', 'room')
        }),
        ('Estado de Ocupación', {
            'fields': ('occupancy_status', 'stay_day_number', 'is_vip')
        }),
        ('Horarios', {
            'fields': ('expected_checkout_time', 'expected_checkin_time'),
            'classes': ('collapse',)
        }),
        ('Estado de Limpieza', {
            'fields': ('day_cleaning_status', 'night_expected_difficulty')
        }),
        ('Notas', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )

    def task_count(self, obj):
        return obj.tasks.count()
    task_count.short_description = 'Tareas'


@admin.register(RoomDailyTask)
class RoomDailyTaskAdmin(admin.ModelAdmin):
    list_display = [
        'get_date', 'get_room', 'task_type', 'time_block',
        'estimated_minutes', 'status', 'priority'
    ]
    list_filter = ['task_type', 'time_block', 'status', 'room_daily_state__date']
    list_editable = ['status', 'priority']
    search_fields = ['room_daily_state__room__number']
    raw_id_fields = ['room_daily_state']

    def get_date(self, obj):
        return obj.room_daily_state.date
    get_date.short_description = 'Fecha'
    get_date.admin_order_field = 'room_daily_state__date'

    def get_room(self, obj):
        return obj.room_daily_state.room.number
    get_room.short_description = 'Habitación'


@admin.register(ProtelImportLog)
class ProtelImportLogAdmin(admin.ModelAdmin):
    list_display = [
        'filename', 'imported_at', 'imported_by', 'status',
        'rows_processed', 'rows_success', 'rows_error', 'date_from', 'date_to'
    ]
    list_filter = ['status', 'imported_at']
    readonly_fields = [
        'filename', 'imported_at', 'rows_processed', 'rows_success',
        'rows_error', 'date_from', 'date_to', 'errors', 'status'
    ]
    date_hierarchy = 'imported_at'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
