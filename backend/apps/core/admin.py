"""Admin configuration for Core models."""
from django.contrib import admin
from .models import TimeBlock, TaskType, Building, Zone, RoomType, Room, DayOfWeek


@admin.register(TimeBlock)
class TimeBlockAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'start_time', 'end_time', 'min_staff', 'helps_other_shift_hours', 'order', 'is_active']
    list_editable = ['start_time', 'end_time', 'min_staff', 'helps_other_shift_hours', 'order', 'is_active']
    search_fields = ['code', 'name']
    ordering = ['order']


@admin.register(TaskType)
class TaskTypeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'base_minutes', 'persons_required', 'earliest_start_time', 'latest_end_time', 'priority', 'is_active']
    list_editable = ['base_minutes', 'persons_required', 'earliest_start_time', 'latest_end_time', 'priority', 'is_active']
    list_filter = ['allowed_blocks', 'is_active']
    filter_horizontal = ['allowed_blocks']
    search_fields = ['code', 'name']


@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'is_active']
    list_editable = ['is_active']


@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'building', 'floor_number', 'priority_order', 'room_count', 'is_active']
    list_editable = ['floor_number', 'priority_order', 'is_active']
    list_filter = ['building', 'is_active']
    search_fields = ['code', 'name']

    def room_count(self, obj):
        return obj.rooms.count()
    room_count.short_description = 'Habitaciones'


@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'time_multiplier', 'is_active']
    list_editable = ['time_multiplier', 'is_active']


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['number', 'zone', 'room_type', 'order_in_zone', 'corridor_side', 'is_active']
    list_editable = ['order_in_zone', 'corridor_side', 'is_active']
    list_filter = ['zone', 'room_type', 'corridor_side', 'is_active']
    search_fields = ['number']
    ordering = ['zone', 'order_in_zone']


@admin.register(DayOfWeek)
class DayOfWeekAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'iso_weekday']
    ordering = ['iso_weekday']
