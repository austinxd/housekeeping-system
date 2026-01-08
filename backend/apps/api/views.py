"""
API Views.
"""
from datetime import datetime, date
from rest_framework import viewsets, status, views
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.core.models import TimeBlock, TaskType, Zone, Room, RoomType, Building, DayOfWeek
from apps.staff.models import Role, Employee, Team, EmployeeUnavailability
from apps.shifts.models import ShiftTemplate, ShiftSubBlock
from apps.rooms.models import RoomDailyState, RoomDailyTask, ProtelImportLog
from apps.rooms.importers import ProtelCSVImporter
from apps.rules.models import TaskTimeRule, ZoneAssignmentRule, ElasticityRule, PlanningParameter
from apps.planning.models import (
    WeekPlan, ShiftAssignment, DailyPlan, TaskAssignment,
    DailyLoadSummary, PlanningAlert
)
from apps.planning.services import (
    LoadCalculator, CapacityCalculator,
    WeekPlanGenerator, DailyPlanGenerator
)

from . import serializers


# === CORE VIEWSETS ===

class TimeBlockViewSet(viewsets.ModelViewSet):
    queryset = TimeBlock.objects.all()
    serializer_class = serializers.TimeBlockSerializer


class TaskTypeViewSet(viewsets.ModelViewSet):
    queryset = TaskType.objects.all()
    serializer_class = serializers.TaskTypeSerializer


class BuildingViewSet(viewsets.ModelViewSet):
    queryset = Building.objects.all()
    serializer_class = serializers.BuildingSerializer


class ZoneViewSet(viewsets.ModelViewSet):
    queryset = Zone.objects.all()
    serializer_class = serializers.ZoneSerializer

    @action(detail=True, methods=['get'])
    def rooms(self, request, pk=None):
        """Obtiene habitaciones de una zona."""
        zone = self.get_object()
        rooms = zone.rooms.all()
        serializer = serializers.RoomSerializer(rooms, many=True)
        return Response(serializer.data)


class RoomTypeViewSet(viewsets.ModelViewSet):
    queryset = RoomType.objects.all()
    serializer_class = serializers.RoomTypeSerializer


class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.select_related('zone', 'room_type')
    serializer_class = serializers.RoomSerializer
    filterset_fields = ['zone', 'room_type', 'is_active']


class DayOfWeekViewSet(viewsets.ModelViewSet):
    queryset = DayOfWeek.objects.all()
    serializer_class = serializers.DayOfWeekSerializer


# === STAFF VIEWSETS ===

class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = serializers.RoleSerializer


class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.select_related('role').prefetch_related(
        'allowed_blocks', 'eligible_tasks', 'fixed_days_off'
    )
    filterset_fields = ['role', 'is_active', 'elasticity', 'can_work_night']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return serializers.EmployeeCreateUpdateSerializer
        return serializers.EmployeeSerializer

    @action(detail=True, methods=['get'])
    def schedule(self, request, pk=None):
        """Obtiene el horario del empleado para una semana."""
        employee = self.get_object()
        week_start = request.query_params.get('week_start')

        if week_start:
            week_start = datetime.strptime(week_start, '%Y-%m-%d').date()
        else:
            # Usar lunes actual
            today = date.today()
            week_start = today - timezone.timedelta(days=today.weekday())

        assignments = ShiftAssignment.objects.filter(
            employee=employee,
            date__gte=week_start,
            date__lt=week_start + timezone.timedelta(days=7)
        ).select_related('shift_template')

        serializer = serializers.ShiftAssignmentSerializer(assignments, many=True)
        return Response(serializer.data)


class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.prefetch_related('members')
    serializer_class = serializers.TeamSerializer
    filterset_fields = ['team_type', 'is_active']


class EmployeeUnavailabilityViewSet(viewsets.ModelViewSet):
    queryset = EmployeeUnavailability.objects.select_related('employee')
    serializer_class = serializers.EmployeeUnavailabilitySerializer
    filterset_fields = ['employee', 'reason']


# === SHIFTS VIEWSETS ===

class ShiftTemplateViewSet(viewsets.ModelViewSet):
    queryset = ShiftTemplate.objects.select_related('role', 'time_block').prefetch_related('sub_blocks')
    serializer_class = serializers.ShiftTemplateSerializer
    filterset_fields = ['role', 'time_block', 'is_active']


class ShiftSubBlockViewSet(viewsets.ModelViewSet):
    queryset = ShiftSubBlock.objects.select_related('shift_template')
    serializer_class = serializers.ShiftSubBlockSerializer


# === ROOMS VIEWSETS ===

class RoomDailyStateViewSet(viewsets.ModelViewSet):
    queryset = RoomDailyState.objects.select_related('room', 'room__zone').prefetch_related('tasks')
    serializer_class = serializers.RoomDailyStateSerializer
    filterset_fields = ['date', 'occupancy_status', 'day_cleaning_status', 'is_vip']

    def get_queryset(self):
        queryset = super().get_queryset()
        date_param = self.request.query_params.get('date')
        if date_param:
            queryset = queryset.filter(date=date_param)
        return queryset

    @action(detail=True, methods=['post'])
    def update_cleaning_status(self, request, pk=None):
        """Actualiza el estado de limpieza y recalcula dificultad nocturna."""
        state = self.get_object()
        new_status = request.data.get('day_cleaning_status')

        if new_status:
            state.day_cleaning_status = new_status
            state.save()

        serializer = self.get_serializer(state)
        return Response(serializer.data)


class RoomDailyTaskViewSet(viewsets.ModelViewSet):
    queryset = RoomDailyTask.objects.select_related(
        'room_daily_state', 'task_type', 'time_block'
    )
    serializer_class = serializers.RoomDailyTaskSerializer
    filterset_fields = ['time_block', 'status', 'task_type']


class ProtelImportView(views.APIView):
    """Vista para importar CSV de Protel."""

    def post(self, request):
        serializer = serializers.CSVImportSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        uploaded_file = serializer.validated_data['file']
        filename = serializer.validated_data.get('filename', uploaded_file.name)

        try:
            content = uploaded_file.read().decode('utf-8')
        except UnicodeDecodeError:
            try:
                uploaded_file.seek(0)
                content = uploaded_file.read().decode('latin-1')
            except Exception as e:
                return Response(
                    {'error': f'Error al leer el archivo: {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        importer = ProtelCSVImporter()
        try:
            success, import_log = importer.import_csv(
                content,
                filename=filename,
                imported_by=str(request.user) if request.user.is_authenticated else ''
            )

            summary = importer.get_summary()
            log_serializer = serializers.ProtelImportLogSerializer(import_log)

            return Response({
                'success': success,
                'import_log': log_serializer.data,
                'summary': summary
            })

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProtelImportLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ProtelImportLog.objects.all()
    serializer_class = serializers.ProtelImportLogSerializer


# === RULES VIEWSETS ===

class TaskTimeRuleViewSet(viewsets.ModelViewSet):
    queryset = TaskTimeRule.objects.select_related('task_type', 'room_type')
    serializer_class = serializers.TaskTimeRuleSerializer


class ZoneAssignmentRuleViewSet(viewsets.ModelViewSet):
    queryset = ZoneAssignmentRule.objects.all()
    serializer_class = serializers.ZoneAssignmentRuleSerializer


class ElasticityRuleViewSet(viewsets.ModelViewSet):
    queryset = ElasticityRule.objects.all()
    serializer_class = serializers.ElasticityRuleSerializer


class PlanningParameterViewSet(viewsets.ModelViewSet):
    queryset = PlanningParameter.objects.all()
    serializer_class = serializers.PlanningParameterSerializer


# === PLANNING VIEWSETS ===

class WeekPlanViewSet(viewsets.ModelViewSet):
    queryset = WeekPlan.objects.prefetch_related('shift_assignments')
    filterset_fields = ['status']

    def get_serializer_class(self):
        if self.action == 'list':
            return serializers.WeekPlanListSerializer
        return serializers.WeekPlanSerializer

    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Genera un nuevo plan semanal."""
        serializer = serializers.GenerateWeekPlanSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        week_start = serializer.validated_data['week_start_date']

        generator = WeekPlanGenerator()
        try:
            week_plan = generator.generate_week_plan(
                week_start,
                created_by=str(request.user) if request.user.is_authenticated else ''
            )
            result_serializer = serializers.WeekPlanSerializer(week_plan)
            return Response(result_serializer.data, status=status.HTTP_201_CREATED)

        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {'error': f'Error al generar plan: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def regenerate(self, request, pk=None):
        """Regenera un plan semanal existente."""
        week_plan = self.get_object()

        generator = WeekPlanGenerator()
        try:
            new_plan = generator.regenerate_week_plan(week_plan)
            serializer = serializers.WeekPlanSerializer(new_plan)
            return Response(serializer.data)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """Publica un plan semanal."""
        week_plan = self.get_object()

        if week_plan.status == 'PUBLISHED':
            return Response(
                {'error': 'El plan ya está publicado'},
                status=status.HTTP_400_BAD_REQUEST
            )

        week_plan.status = 'PUBLISHED'
        week_plan.published_at = timezone.now()
        week_plan.save()

        serializer = serializers.WeekPlanSerializer(week_plan)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def by_employee(self, request, pk=None):
        """Obtiene el plan organizado por empleado."""
        week_plan = self.get_object()

        assignments = week_plan.shift_assignments.select_related(
            'employee', 'team', 'shift_template'
        ).order_by('date')

        # Agrupar por empleado/equipo
        by_assignee = {}
        for assignment in assignments:
            if assignment.employee:
                key = f"emp_{assignment.employee.id}"
                name = assignment.employee.full_name
            else:
                key = f"team_{assignment.team.id}"
                name = str(assignment.team)

            if key not in by_assignee:
                by_assignee[key] = {
                    'name': name,
                    'type': 'employee' if assignment.employee else 'team',
                    'shifts': []
                }

            by_assignee[key]['shifts'].append({
                'date': assignment.date,
                'shift': assignment.shift_template.code,
                'hours': float(assignment.assigned_hours),
                'is_day_off': assignment.is_day_off
            })

        return Response(by_assignee)


class ShiftAssignmentViewSet(viewsets.ModelViewSet):
    queryset = ShiftAssignment.objects.select_related(
        'employee', 'team', 'shift_template', 'week_plan'
    )
    serializer_class = serializers.ShiftAssignmentSerializer
    filterset_fields = ['date', 'is_day_off', 'week_plan']


class DailyPlanViewSet(viewsets.ModelViewSet):
    queryset = DailyPlan.objects.prefetch_related('task_assignments')
    filterset_fields = ['status', 'date']

    def get_serializer_class(self):
        if self.action == 'list':
            return serializers.DailyPlanListSerializer
        return serializers.DailyPlanSerializer

    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Genera un nuevo plan diario."""
        serializer = serializers.GenerateDailyPlanSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        target_date = serializer.validated_data['date']
        week_plan_id = serializer.validated_data.get('week_plan_id')

        week_plan = None
        if week_plan_id:
            week_plan = get_object_or_404(WeekPlan, id=week_plan_id)

        generator = DailyPlanGenerator()
        try:
            daily_plan = generator.generate_daily_plan(target_date, week_plan)
            result_serializer = serializers.DailyPlanSerializer(daily_plan)
            return Response(result_serializer.data, status=status.HTTP_201_CREATED)

        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def regenerate(self, request, pk=None):
        """Regenera un plan diario existente."""
        daily_plan = self.get_object()

        generator = DailyPlanGenerator()
        try:
            new_plan = generator.regenerate_daily_plan(daily_plan)
            serializer = serializers.DailyPlanSerializer(new_plan)
            return Response(serializer.data)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def summary(self, request, pk=None):
        """Obtiene resumen del plan diario."""
        daily_plan = self.get_object()

        generator = DailyPlanGenerator()
        summary = generator.get_daily_plan_summary(daily_plan)

        return Response(summary)

    @action(detail=True, methods=['get'])
    def by_zone(self, request, pk=None):
        """Obtiene el plan organizado por zona."""
        daily_plan = self.get_object()

        assignments = daily_plan.task_assignments.select_related(
            'room_task', 'room_task__room_daily_state__room',
            'room_task__task_type', 'employee', 'team', 'zone'
        ).order_by('zone__priority_order', 'order_in_assignment')

        by_zone = {}
        for assignment in assignments:
            zone_code = assignment.zone.code

            if zone_code not in by_zone:
                by_zone[zone_code] = {
                    'zone_name': assignment.zone.name,
                    'floor': assignment.zone.floor_number,
                    'tasks': []
                }

            by_zone[zone_code]['tasks'].append({
                'room': assignment.room_task.room_daily_state.room.number,
                'task_type': assignment.room_task.task_type.code,
                'assigned_to': assignment.employee.full_name if assignment.employee else str(assignment.team),
                'estimated_minutes': assignment.room_task.estimated_minutes,
                'status': assignment.status,
                'order': assignment.order_in_assignment
            })

        return Response(by_zone)


class TaskAssignmentViewSet(viewsets.ModelViewSet):
    queryset = TaskAssignment.objects.select_related(
        'room_task', 'employee', 'team', 'zone', 'daily_plan'
    )
    serializer_class = serializers.TaskAssignmentSerializer

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Marca una tarea como completada."""
        assignment = self.get_object()
        assignment.status = 'COMPLETED'
        assignment.completed_at = timezone.now().time()
        assignment.save()

        # Actualizar tarea original
        assignment.room_task.status = 'COMPLETED'
        assignment.room_task.save()

        serializer = self.get_serializer(assignment)
        return Response(serializer.data)


class DailyLoadSummaryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DailyLoadSummary.objects.select_related('time_block')
    serializer_class = serializers.DailyLoadSummarySerializer
    filterset_fields = ['date', 'time_block']


class PlanningAlertViewSet(viewsets.ModelViewSet):
    queryset = PlanningAlert.objects.select_related('time_block')
    serializer_class = serializers.PlanningAlertSerializer
    filterset_fields = ['date', 'alert_type', 'severity', 'is_resolved']

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Marca una alerta como resuelta."""
        alert = self.get_object()
        alert.is_resolved = True
        alert.resolved_at = timezone.now()
        alert.resolved_by = str(request.user) if request.user.is_authenticated else ''
        alert.save()

        serializer = self.get_serializer(alert)
        return Response(serializer.data)


# === CALCULATION VIEWS ===

class LoadCalculationView(views.APIView):
    """Vista para calcular carga de trabajo."""

    def get(self, request):
        date_param = request.query_params.get('date')
        block_code = request.query_params.get('block')

        if not date_param:
            return Response(
                {'error': 'Parámetro date requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            target_date = datetime.strptime(date_param, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Formato de fecha inválido (usar YYYY-MM-DD)'},
                status=status.HTTP_400_BAD_REQUEST
            )

        time_block = None
        if block_code:
            time_block = get_object_or_404(TimeBlock, code=block_code)

        calculator = LoadCalculator()
        load = calculator.compute_load(target_date, time_block)

        return Response(load)


class CapacityCalculationView(views.APIView):
    """Vista para calcular capacidad disponible."""

    def get(self, request):
        date_param = request.query_params.get('date')
        block_code = request.query_params.get('block')

        if not date_param:
            return Response(
                {'error': 'Parámetro date requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            target_date = datetime.strptime(date_param, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Formato de fecha inválido (usar YYYY-MM-DD)'},
                status=status.HTTP_400_BAD_REQUEST
            )

        time_block = None
        if block_code:
            time_block = get_object_or_404(TimeBlock, code=block_code)

        calculator = CapacityCalculator()
        capacity = calculator.compute_capacity(target_date, time_block)

        return Response(capacity)


class DashboardView(views.APIView):
    """Vista para el dashboard de la gouvernante."""

    def get(self, request):
        # Obtener parámetros
        week_start_param = request.query_params.get('week_start')

        if week_start_param:
            try:
                week_start = datetime.strptime(week_start_param, '%Y-%m-%d').date()
            except ValueError:
                week_start = date.today() - timezone.timedelta(days=date.today().weekday())
        else:
            today = date.today()
            week_start = today - timezone.timedelta(days=today.weekday())

        # Calcular datos
        load_calc = LoadCalculator()
        capacity_calc = CapacityCalculator()

        week_load = load_calc.compute_week_load(week_start)
        week_capacity = capacity_calc.compute_week_capacity(week_start)

        # Obtener alertas activas
        alerts = PlanningAlert.objects.filter(
            is_resolved=False,
            date__gte=week_start,
            date__lt=week_start + timezone.timedelta(days=7)
        )

        # Construir respuesta
        dashboard = {
            'week_start': week_start,
            'week_end': week_start + timezone.timedelta(days=6),
            'load': {
                'total_minutes': week_load['totals']['minutes'],
                'total_tasks': week_load['totals']['tasks'],
                'by_block': dict(week_load['by_block']),
            },
            'capacity': {
                'total_minutes': week_capacity['totals']['minutes'],
            },
            'balance': {
                'minutes': week_capacity['totals']['minutes'] - week_load['totals']['minutes'],
                'percentage': round(
                    (week_load['totals']['minutes'] / max(week_capacity['totals']['minutes'], 1)) * 100,
                    1
                )
            },
            'days': [],
            'alerts': serializers.PlanningAlertSerializer(alerts, many=True).data,
        }

        # Datos por día
        for day_offset in range(7):
            current_date = week_start + timezone.timedelta(days=day_offset)
            day_key = current_date.isoformat()

            day_load = week_load['days'].get(day_key, {'total_minutes': 0, 'total_tasks': 0})
            day_capacity = week_capacity['days'].get(day_key, {'total_minutes': 0})

            load_mins = day_load['total_minutes']
            cap_mins = day_capacity['total_minutes']

            dashboard['days'].append({
                'date': current_date,
                'day_name': current_date.strftime('%A'),
                'load_minutes': load_mins,
                'capacity_minutes': cap_mins,
                'load_percentage': round((load_mins / max(cap_mins, 1)) * 100, 1),
                'is_overloaded': load_mins > cap_mins,
            })

        return Response(dashboard)
