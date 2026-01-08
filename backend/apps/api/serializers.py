"""
API Serializers.
"""
from rest_framework import serializers
from apps.core.models import TimeBlock, TaskType, Zone, Room, RoomType, Building, DayOfWeek
from apps.staff.models import Role, Employee, Team, EmployeeUnavailability
from apps.shifts.models import ShiftTemplate, ShiftSubBlock
from apps.rooms.models import RoomDailyState, RoomDailyTask, ProtelImportLog
from apps.rules.models import TaskTimeRule, ZoneAssignmentRule, ElasticityRule, PlanningParameter
from apps.planning.models import (
    WeekPlan, ShiftAssignment, DailyPlan, TaskAssignment,
    DailyLoadSummary, PlanningAlert
)


# === CORE ===

class TimeBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeBlock
        fields = '__all__'


class TaskTypeSerializer(serializers.ModelSerializer):
    allowed_blocks = TimeBlockSerializer(many=True, read_only=True)
    allowed_block_ids = serializers.PrimaryKeyRelatedField(
        queryset=TimeBlock.objects.all(),
        many=True,
        write_only=True,
        source='allowed_blocks'
    )

    class Meta:
        model = TaskType
        fields = '__all__'


class BuildingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Building
        fields = '__all__'


class ZoneSerializer(serializers.ModelSerializer):
    building_name = serializers.CharField(source='building.name', read_only=True)
    room_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Zone
        fields = '__all__'

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['room_count'] = instance.rooms.count()
        return data


class RoomTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomType
        fields = '__all__'


class RoomSerializer(serializers.ModelSerializer):
    zone_name = serializers.CharField(source='zone.name', read_only=True)
    room_type_name = serializers.CharField(source='room_type.name', read_only=True)

    class Meta:
        model = Room
        fields = '__all__'


class DayOfWeekSerializer(serializers.ModelSerializer):
    class Meta:
        model = DayOfWeek
        fields = '__all__'


# === STAFF ===

class RoleSerializer(serializers.ModelSerializer):
    allowed_blocks = TimeBlockSerializer(many=True, read_only=True)
    employee_count = serializers.SerializerMethodField()

    class Meta:
        model = Role
        fields = '__all__'

    def get_employee_count(self, obj):
        return obj.employees.filter(is_active=True).count()


class EmployeeSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source='role.name', read_only=True)
    full_name = serializers.CharField(read_only=True)
    allowed_blocks = TimeBlockSerializer(many=True, read_only=True)
    eligible_tasks = TaskTypeSerializer(many=True, read_only=True)
    fixed_days_off = DayOfWeekSerializer(many=True, read_only=True)

    class Meta:
        model = Employee
        fields = '__all__'


class EmployeeCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = '__all__'


class TeamSerializer(serializers.ModelSerializer):
    members = EmployeeSerializer(many=True, read_only=True)
    member_ids = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.all(),
        many=True,
        write_only=True,
        source='members'
    )
    member_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Team
        fields = '__all__'

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['member_count'] = instance.members.count()
        return data


class EmployeeUnavailabilitySerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)

    class Meta:
        model = EmployeeUnavailability
        fields = '__all__'


# === SHIFTS ===

class ShiftSubBlockSerializer(serializers.ModelSerializer):
    duration_minutes = serializers.IntegerField(read_only=True)

    class Meta:
        model = ShiftSubBlock
        fields = '__all__'


class ShiftTemplateSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source='role.name', read_only=True)
    time_block_code = serializers.CharField(source='time_block.code', read_only=True)
    sub_blocks = ShiftSubBlockSerializer(many=True, read_only=True)
    total_hours = serializers.DecimalField(max_digits=4, decimal_places=2, read_only=True)

    class Meta:
        model = ShiftTemplate
        fields = '__all__'


# === ROOMS ===

class RoomDailyTaskSerializer(serializers.ModelSerializer):
    task_type_code = serializers.CharField(source='task_type.code', read_only=True)
    task_type_name = serializers.CharField(source='task_type.name', read_only=True)
    time_block_code = serializers.CharField(source='time_block.code', read_only=True)

    class Meta:
        model = RoomDailyTask
        fields = '__all__'


class RoomDailyStateSerializer(serializers.ModelSerializer):
    room_number = serializers.CharField(source='room.number', read_only=True)
    zone_code = serializers.CharField(source='room.zone.code', read_only=True)
    zone_name = serializers.CharField(source='room.zone.name', read_only=True)
    tasks = RoomDailyTaskSerializer(many=True, read_only=True)

    class Meta:
        model = RoomDailyState
        fields = '__all__'


class ProtelImportLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProtelImportLog
        fields = '__all__'
        read_only_fields = ['imported_at', 'rows_processed', 'rows_success', 'rows_error', 'status']


# === RULES ===

class TaskTimeRuleSerializer(serializers.ModelSerializer):
    task_type_code = serializers.CharField(source='task_type.code', read_only=True)

    class Meta:
        model = TaskTimeRule
        fields = '__all__'


class ZoneAssignmentRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ZoneAssignmentRule
        fields = '__all__'


class ElasticityRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ElasticityRule
        fields = '__all__'


class PlanningParameterSerializer(serializers.ModelSerializer):
    typed_value = serializers.SerializerMethodField()

    class Meta:
        model = PlanningParameter
        fields = '__all__'

    def get_typed_value(self, obj):
        return obj.get_typed_value()


# === PLANNING ===

class ShiftAssignmentSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    team_name = serializers.SerializerMethodField()
    shift_template_code = serializers.CharField(source='shift_template.code', read_only=True)
    time_block_code = serializers.CharField(source='shift_template.time_block.code', read_only=True)

    class Meta:
        model = ShiftAssignment
        fields = '__all__'

    def get_team_name(self, obj):
        return str(obj.team) if obj.team else None


class WeekPlanSerializer(serializers.ModelSerializer):
    shift_assignments = ShiftAssignmentSerializer(many=True, read_only=True)
    week_end_date = serializers.DateField(read_only=True)
    total_assigned_hours = serializers.SerializerMethodField()

    class Meta:
        model = WeekPlan
        fields = '__all__'

    def get_total_assigned_hours(self, obj):
        return float(obj.get_total_assigned_hours())


class WeekPlanListSerializer(serializers.ModelSerializer):
    """Serializer ligero para listados."""
    week_end_date = serializers.DateField(read_only=True)
    assignment_count = serializers.SerializerMethodField()

    class Meta:
        model = WeekPlan
        fields = ['id', 'week_start_date', 'week_end_date', 'name', 'status',
                  'created_at', 'published_at', 'assignment_count']

    def get_assignment_count(self, obj):
        return obj.shift_assignments.count()


class TaskAssignmentSerializer(serializers.ModelSerializer):
    room_number = serializers.CharField(source='room_task.room_daily_state.room.number', read_only=True)
    task_type_code = serializers.CharField(source='room_task.task_type.code', read_only=True)
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    team_name = serializers.SerializerMethodField()
    zone_code = serializers.CharField(source='zone.code', read_only=True)
    zone_name = serializers.CharField(source='zone.name', read_only=True)
    estimated_minutes = serializers.IntegerField(source='room_task.estimated_minutes', read_only=True)

    class Meta:
        model = TaskAssignment
        fields = '__all__'

    def get_team_name(self, obj):
        return str(obj.team) if obj.team else None


class DailyPlanSerializer(serializers.ModelSerializer):
    task_assignments = TaskAssignmentSerializer(many=True, read_only=True)
    total_tasks = serializers.SerializerMethodField()
    completed_tasks = serializers.SerializerMethodField()

    class Meta:
        model = DailyPlan
        fields = '__all__'

    def get_total_tasks(self, obj):
        return obj.get_total_tasks()

    def get_completed_tasks(self, obj):
        return obj.get_completed_tasks()


class DailyPlanListSerializer(serializers.ModelSerializer):
    """Serializer ligero para listados."""
    total_tasks = serializers.SerializerMethodField()
    completed_tasks = serializers.SerializerMethodField()

    class Meta:
        model = DailyPlan
        fields = ['id', 'date', 'status', 'total_tasks', 'completed_tasks', 'created_at']

    def get_total_tasks(self, obj):
        return obj.get_total_tasks()

    def get_completed_tasks(self, obj):
        return obj.get_completed_tasks()


class DailyLoadSummarySerializer(serializers.ModelSerializer):
    time_block_code = serializers.CharField(source='time_block.code', read_only=True)
    load_percentage = serializers.FloatField(read_only=True)
    balance_minutes = serializers.IntegerField(read_only=True)
    is_overloaded = serializers.BooleanField(read_only=True)

    class Meta:
        model = DailyLoadSummary
        fields = '__all__'


class PlanningAlertSerializer(serializers.ModelSerializer):
    time_block_code = serializers.CharField(source='time_block.code', read_only=True)

    class Meta:
        model = PlanningAlert
        fields = '__all__'


# === SPECIAL SERIALIZERS ===

class CSVImportSerializer(serializers.Serializer):
    """Serializer para importación de CSV."""
    file = serializers.FileField()
    filename = serializers.CharField(required=False)


class GenerateWeekPlanSerializer(serializers.Serializer):
    """Serializer para generar plan semanal."""
    week_start_date = serializers.DateField()


class GenerateDailyPlanSerializer(serializers.Serializer):
    """Serializer para generar plan diario."""
    date = serializers.DateField()
    week_plan_id = serializers.IntegerField(required=False)


class LoadSummarySerializer(serializers.Serializer):
    """Serializer para resumen de carga."""
    date = serializers.DateField()
    blocks = serializers.DictField()
    total_minutes = serializers.IntegerField()
    total_tasks = serializers.IntegerField()
    by_zone = serializers.DictField()
    hard_rooms = serializers.ListField()


class CapacitySummarySerializer(serializers.Serializer):
    """Serializer para resumen de capacidad."""
    date = serializers.DateField()
    blocks = serializers.DictField()
    total_minutes = serializers.IntegerField()
    total_employees = serializers.IntegerField()
