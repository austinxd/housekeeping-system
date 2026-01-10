"""
API Views.
"""
import math
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
from apps.planning.services.forecast_loader import ForecastLoader
from apps.planning.services.forecast_pdf_parser import ForecastPDFParser

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
    authentication_classes = []
    permission_classes = []

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
        from datetime import timedelta
        from collections import OrderedDict

        week_plan = self.get_object()

        assignments = week_plan.shift_assignments.select_related(
            'employee', 'employee__role', 'team', 'shift_template'
        ).order_by('date')

        # Obtener parejas/equipos para ordenar
        teams = Team.objects.filter(is_active=True).prefetch_related('members')
        employee_team_order = {}  # employee_id -> (team_order, member_order)
        team_counter = 0
        for team in teams:
            members = list(team.members.all())
            for idx, member in enumerate(members):
                employee_team_order[member.id] = (team_counter, idx)
            team_counter += 1

        # Agrupar por empleado/equipo
        by_assignee = {}
        for assignment in assignments:
            if assignment.employee:
                key = f"emp_{assignment.employee.id}"
                name = assignment.employee.full_name
                role = assignment.employee.role.name if assignment.employee.role else None
                emp_id = assignment.employee.id
                # Orden: primero parejas, luego individuales
                sort_key = employee_team_order.get(emp_id, (999, emp_id))
            else:
                key = f"team_{assignment.team.id}"
                name = str(assignment.team)
                role = None
                sort_key = (998, 0)

            if key not in by_assignee:
                by_assignee[key] = {
                    'name': name,
                    'role': role,
                    'type': 'employee' if assignment.employee else 'team',
                    'sort_key': sort_key,
                    'shifts': []
                }

            # Calcular hora de salida
            start_time = None
            end_time = None
            if assignment.shift_template and assignment.shift_template.start_time:
                start_time = assignment.shift_template.start_time.strftime('%H:%M')
                # Calcular salida: entrada + horas asignadas
                start_dt = datetime.combine(assignment.date, assignment.shift_template.start_time)
                end_dt = start_dt + timedelta(hours=float(assignment.assigned_hours))
                end_time = end_dt.strftime('%H:%M')

            by_assignee[key]['shifts'].append({
                'date': assignment.date,
                'shift': assignment.shift_template.code if assignment.shift_template else None,
                'shift_name': assignment.shift_template.name if assignment.shift_template else None,
                'hours': float(assignment.assigned_hours),
                'start_time': start_time,
                'end_time': end_time,
                'is_day_off': assignment.is_day_off
            })

        # Ordenar por parejas (sort_key)
        sorted_assignees = OrderedDict(
            sorted(by_assignee.items(), key=lambda x: x[1]['sort_key'])
        )

        # Eliminar sort_key del resultado
        for key in sorted_assignees:
            del sorted_assignees[key]['sort_key']

        return Response(sorted_assignees)

    @action(detail=True, methods=['get'])
    def load_explanation(self, request, pk=None):
        """
        Devuelve la explicación de por qué se eligió cada horario.
        Incluye datos del forecast, cálculo de carga, y distribución de tareas.
        """
        from datetime import timedelta

        week_plan = self.get_object()

        forecast_data = week_plan.forecast_data or []
        load_calculation = week_plan.load_calculation or {}

        # Obtener configuración de turnos desde BD
        day_block = TimeBlock.objects.filter(code='DAY').first()
        evening_block = TimeBlock.objects.filter(code='EVENING').first()

        day_start = day_block.start_time.strftime('%H:%M') if day_block and day_block.start_time else '09:00'
        day_end = day_block.end_time.strftime('%H:%M') if day_block and day_block.end_time else '17:00'
        evening_start = evening_block.start_time.strftime('%H:%M') if evening_block and evening_block.start_time else '13:30'
        evening_end = evening_block.end_time.strftime('%H:%M') if evening_block and evening_block.end_time else '21:30'
        evening_helps_hours = float(evening_block.helps_other_shift_hours) if evening_block else 4.5

        # Obtener tiempos de tareas desde BD
        task_times = {}
        task_persons = {}
        for task in TaskType.objects.all():
            task_times[task.code] = task.base_minutes
            task_persons[task.code] = task.persons_required

        depart_time = task_times.get('DEPART', 50)
        recouch_time = task_times.get('RECOUCH', 20)
        couverture_time = task_times.get('COUVERTURE', 20)
        depart_pers = task_persons.get('DEPART', 2)
        recouch_pers = task_persons.get('RECOUCH', 2)
        couverture_pers = task_persons.get('COUVERTURE', 1)

        # Construir explicación por día
        explanation = {
            'week_start': week_plan.week_start_date.isoformat(),
            'totals': load_calculation.get('totals', {}),
            'shift_config': {
                'day': {'start': day_start, 'end': day_end},
                'evening': {'start': evening_start, 'end': evening_end, 'helps_day_hours': evening_helps_hours},
            },
            'task_config': {
                'depart': {'minutes': depart_time, 'persons': depart_pers},
                'recouch': {'minutes': recouch_time, 'persons': recouch_pers},
                'couverture': {'minutes': couverture_time, 'persons': couverture_pers},
            },
            'days': [],
        }

        week_days = [week_plan.week_start_date + timedelta(days=i) for i in range(7)]
        day_names_es = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

        # Obtener asignaciones por día con horarios
        assignments = week_plan.shift_assignments.select_related(
            'employee', 'shift_template', 'shift_template__time_block'
        ).order_by('date')

        assignments_by_day = {}
        for assignment in assignments:
            day_key = assignment.date.isoformat()
            if day_key not in assignments_by_day:
                assignments_by_day[day_key] = {'DAY': [], 'EVENING': []}

            if assignment.shift_template and assignment.shift_template.time_block:
                block_code = assignment.shift_template.time_block.code
                start_time = assignment.shift_template.start_time
                if block_code in assignments_by_day[day_key]:
                    # Calcular hora de salida
                    end_time = None
                    if start_time:
                        from datetime import datetime
                        start_dt = datetime.combine(assignment.date, start_time)
                        end_dt = start_dt + timedelta(hours=float(assignment.assigned_hours))
                        end_time = end_dt.strftime('%H:%M')

                    assignments_by_day[day_key][block_code].append({
                        'employee': assignment.employee.full_name if assignment.employee else None,
                        'employee_short': assignment.employee.first_name if assignment.employee else None,
                        'hours': float(assignment.assigned_hours),
                        'start_time': start_time.strftime('%H:%M') if start_time else None,
                        'end_time': end_time,
                    })

        for i, day_date in enumerate(week_days):
            day_key = day_date.isoformat()
            day_load = load_calculation.get('by_day', {}).get(day_key, {})

            # Buscar forecast del día
            forecast_day = None
            for fc in forecast_data:
                if fc.get('date') == day_key:
                    forecast_day = fc
                    break

            fc = forecast_day or {'departures': 0, 'arrivals': 0, 'occupied': 0}
            departures = fc.get('departures', 0)
            arrivals = fc.get('arrivals', 0)
            occupied = fc.get('occupied', 0)
            stays = max(0, occupied - arrivals)

            assigned_day = assignments_by_day.get(day_key, {}).get('DAY', [])
            assigned_evening = assignments_by_day.get(day_key, {}).get('EVENING', [])

            # Calcular distribución de tareas por persona
            total_day_workers = len(assigned_day) + len(assigned_evening)  # EVENING ayuda con DAY
            total_evening_workers = len(assigned_evening)

            # Distribución de DEPART y RECOUCH (tareas DAY)
            day_task_distribution = []
            if total_day_workers > 0:
                departs_per_person = departures / total_day_workers
                recouch_per_person = stays / total_day_workers

                for emp in assigned_day:
                    day_task_distribution.append({
                        'employee': emp['employee_short'],
                        'shift': 'MAÑANA',
                        'schedule': f"{emp['start_time']}-{emp['end_time']}" if emp['start_time'] else f"{day_start}-{day_end}",
                        'departs': round(departs_per_person, 1),
                        'recouch': round(recouch_per_person, 1),
                        'couvertures': 0,
                    })

                for emp in assigned_evening:
                    day_task_distribution.append({
                        'employee': emp['employee_short'],
                        'shift': 'TARDE (ayuda)',
                        'schedule': f"{emp['start_time']}-18:30" if emp['start_time'] else f"{evening_start}-18:30",
                        'departs': round(departs_per_person, 1),
                        'recouch': round(recouch_per_person, 1),
                        'couvertures': 0,
                    })

            # Distribución de COUVERTURE (tareas EVENING)
            evening_task_distribution = []
            if total_evening_workers > 0:
                couvertures_per_person = occupied / total_evening_workers

                for emp in assigned_evening:
                    evening_task_distribution.append({
                        'employee': emp['employee_short'],
                        'shift': 'TARDE',
                        'schedule': f"19:00-{emp['end_time']}" if emp['end_time'] else f"19:00-{evening_end}",
                        'couvertures': round(couvertures_per_person, 1),
                    })

            day_hours = day_load.get('shifts', {}).get('DAY', {}).get('hours', 0)
            evening_hours = day_load.get('shifts', {}).get('EVENING', {}).get('hours', 0)
            day_persons = day_load.get('shifts', {}).get('DAY', {}).get('persons_needed', 0)
            evening_persons = day_load.get('shifts', {}).get('EVENING', {}).get('persons_needed', 0)

            day_explanation = {
                'date': day_key,
                'day_name': day_names_es[i],
                'day_short': day_load.get('day_name', day_names_es[i][:3]),
                'forecast': fc,
                'load': {
                    'day_shift': day_load.get('shifts', {}).get('DAY', {}),
                    'evening_shift': day_load.get('shifts', {}).get('EVENING', {}),
                    'total_hours': day_load.get('total_hours', 0),
                },
                'assigned': {
                    'DAY': assigned_day,
                    'EVENING': assigned_evening,
                },
                'task_distribution': {
                    'day_tasks': day_task_distribution,
                    'evening_tasks': evening_task_distribution,
                },
                'explanation_text': '',
            }

            # Calcular distribución de habitaciones por período
            num_day = len(assigned_day)
            num_evening = len(assigned_evening)
            total_workers = num_day + num_evening

            # Distribución de tareas
            total_rooms = departures + stays
            rooms_per_worker = total_rooms / total_workers if total_workers > 0 else 0
            departs_per_worker = departures / total_workers if total_workers > 0 else 0
            recouch_per_worker = stays / total_workers if total_workers > 0 else 0
            couv_per_worker = occupied / num_evening if num_evening > 0 else 0

            # Generar texto explicativo con lógica temporal (incluyendo almuerzo)
            text_parts = []
            text_parts.append(f"{'═' * 55}")
            text_parts.append(f"📊 {departures} salidas | {arrivals} llegadas | {occupied} ocupadas | {stays} estancias")
            text_parts.append(f"{'═' * 55}")

            # PERÍODO 1: Mañana sola antes de almuerzo
            text_parts.append(f"")
            text_parts.append(f"🌅 {day_start} - 12:30  MAÑANA (antes almuerzo)")
            text_parts.append(f"   {num_day} persona(s) inician DEPART + RECOUCH")
            if num_day > 0:
                for emp in assigned_day:
                    text_parts.append(f"      👷 {emp['employee_short']}")

            # ALMUERZO
            text_parts.append(f"")
            text_parts.append(f"🍽️  12:30 - 13:30  ALMUERZO MAÑANA")

            # PERÍODO 2: Solapamiento (13:30 - 17:00)
            text_parts.append(f"")
            text_parts.append(f"🔄 13:30 - {day_end}  MAÑANA + TARDE JUNTOS")
            text_parts.append(f"   {total_workers} persona(s) continúan DEPART + RECOUCH")
            text_parts.append(f"   → {total_rooms} habitaciones ÷ {total_workers} = ~{rooms_per_worker:.0f} hab/persona")
            if num_day > 0:
                text_parts.append(f"   Mañana:")
                for emp in assigned_day:
                    text_parts.append(f"      👷 {emp['employee_short']}: ~{departs_per_worker:.0f} depart + ~{recouch_per_worker:.0f} recouch")
            if num_evening > 0:
                text_parts.append(f"   Tarde (ayuda {evening_helps_hours}h):")
                for emp in assigned_evening:
                    text_parts.append(f"      👷 {emp['employee_short']}: ~{departs_per_worker:.0f} depart + ~{recouch_per_worker:.0f} recouch")

            # PERÍODO 3: Tarde termina (17:00 - 19:00)
            text_parts.append(f"")
            text_parts.append(f"⏰ {day_end} - 19:00  TARDE TERMINA LIMPIEZA")
            text_parts.append(f"   {num_evening} persona(s) finalizan habitaciones pendientes")

            # PERÍODO 4: Couverture (19:00 - 21:30)
            text_parts.append(f"")
            text_parts.append(f"🌙 19:00 - {evening_end}  COUVERTURE")
            text_parts.append(f"   {num_evening} persona(s) → {occupied} couvertures")
            if num_evening > 0:
                text_parts.append(f"   → ~{couv_per_worker:.0f} couvertures/persona")
                for emp in assigned_evening:
                    text_parts.append(f"      👷 {emp['employee_short']}: ~{couv_per_worker:.0f} couvertures")

            # RESUMEN
            text_parts.append(f"")
            text_parts.append(f"{'─' * 55}")
            text_parts.append(f"📋 CARGA: {day_hours:.1f}h limpieza + {evening_hours:.1f}h couverture = {day_hours + evening_hours:.1f}h total")
            text_parts.append(f"{'═' * 55}")

            day_explanation['explanation_text'] = '\n'.join(text_parts)

            explanation['days'].append(day_explanation)

        return Response(explanation)


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


class ForecastWeekPlanView(views.APIView):
    """
    Vista para generar WeekPlan desde datos de forecast.
    Recibe datos de ocupación y genera el plan semanal.
    """
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        """
        Genera WeekPlan desde forecast.

        Espera JSON con formato:
        {
            "week_start": "2026-01-12",
            "forecast": [
                {"date": "2026-01-12", "departures": 3, "arrivals": 3, "occupied": 27},
                {"date": "2026-01-13", "departures": 0, "arrivals": 1, "occupied": 28},
                ...
            ]
        }
        """
        week_start_str = request.data.get('week_start')
        forecast_data = request.data.get('forecast', [])

        if not week_start_str:
            return Response(
                {'error': 'week_start es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not forecast_data or len(forecast_data) != 7:
            return Response(
                {'error': 'forecast debe contener exactamente 7 días'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            week_start = datetime.strptime(week_start_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Formato de fecha inválido (usar YYYY-MM-DD)'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validar que sea lunes
        if week_start.weekday() != 0:
            return Response(
                {'error': 'week_start debe ser un lunes'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Procesar forecast
        processed_forecast = []
        for i, day_data in enumerate(forecast_data):
            try:
                day_date = week_start + timezone.timedelta(days=i)
                processed_forecast.append({
                    'date': day_date,
                    'departures': int(day_data.get('departures', 0)),
                    'arrivals': int(day_data.get('arrivals', 0)),
                    'occupied': int(day_data.get('occupied', 0)),
                })
            except (ValueError, TypeError) as e:
                return Response(
                    {'error': f'Error en datos del día {i+1}: {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Calcular carga
        loader = ForecastLoader()
        week_load = loader.calculate_week_load(processed_forecast)
        requirements = loader.calculate_staffing_requirements(week_load)

        # Preparar forecast_data con fechas serializables para guardar
        forecast_data_to_save = []
        for i, day_data in enumerate(processed_forecast):
            day_date = week_start + timezone.timedelta(days=i)
            forecast_data_to_save.append({
                'date': day_date.isoformat(),
                'departures': day_data['departures'],
                'arrivals': day_data['arrivals'],
                'occupied': day_data['occupied'],
            })

        # Generar WeekPlan
        try:
            week_plan = self._generate_weekplan(week_start, week_load, requirements, forecast_data_to_save)

            # Serializar resultado
            result = {
                'week_plan_id': week_plan.id,
                'week_start': week_start.isoformat(),
                'status': week_plan.status,
                'load_summary': {
                    'total_hours': round(week_load['totals']['total_hours'], 1),
                    'day_shift_hours': round(week_load['totals']['day_minutes'] / 60, 1),
                    'evening_shift_hours': round(week_load['totals']['evening_minutes'] / 60, 1),
                },
                'daily_load': [],
                'assignments': [],
            }

            # Agregar carga diaria
            day_names = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
            for i, (day_key, day_load) in enumerate(week_load['days'].items()):
                req = requirements['by_day'][day_key]
                result['daily_load'].append({
                    'date': day_key,
                    'day_name': day_names[i],
                    'day_shift_hours': round(day_load['shifts']['DAY']['hours'], 1),
                    'evening_shift_hours': round(day_load['shifts']['EVENING']['hours'], 1),
                    'day_persons_needed': req['day_shift']['persons_needed'],
                    'evening_persons_needed': req['evening_shift']['persons_needed'],
                })

            # Agregar asignaciones
            for assignment in week_plan.shift_assignments.select_related('employee', 'shift_template').order_by('employee__last_name', 'date'):
                result['assignments'].append({
                    'employee': assignment.employee.full_name if assignment.employee else None,
                    'date': assignment.date.isoformat(),
                    'shift': assignment.shift_template.code if assignment.shift_template else None,
                    'hours': float(assignment.assigned_hours),
                })

            return Response(result, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'error': f'Error al generar plan: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _generate_weekplan(self, week_start, week_load, requirements, forecast_data=None):
        """Genera el WeekPlan basado en la carga calculada."""
        from datetime import timedelta

        # Preparar datos de carga para guardar
        load_calculation_data = {
            'totals': {
                'total_hours': round(week_load['totals']['total_hours'], 1),
                'day_shift_hours': round(week_load['totals']['day_minutes'] / 60, 1),
                'evening_shift_hours': round(week_load['totals']['evening_minutes'] / 60, 1),
            },
            'by_day': {},
        }

        day_names = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
        for i, (day_key, day_load) in enumerate(week_load['days'].items()):
            req = requirements['by_day'][day_key]
            load_calculation_data['by_day'][day_key] = {
                'day_name': day_names[i],
                'tasks': day_load['tasks'],
                'shifts': {
                    'DAY': {
                        'hours': round(day_load['shifts']['DAY']['hours'], 1),
                        'persons_needed': req['day_shift']['persons_needed'],
                    },
                    'EVENING': {
                        'hours': round(day_load['shifts']['EVENING']['hours'], 1),
                        'persons_needed': req['evening_shift']['persons_needed'],
                    },
                },
                'total_hours': round(day_load['total_hours'], 1),
            }

        # Crear o actualizar WeekPlan
        week_plan, created = WeekPlan.objects.update_or_create(
            week_start_date=week_start,
            defaults={
                'name': f'Semana {week_start.strftime("%d/%m/%Y")}',
                'status': 'DRAFT',
                'forecast_data': forecast_data,
                'load_calculation': load_calculation_data,
            }
        )

        if not created:
            week_plan.shift_assignments.all().delete()

        from apps.staff.models import EmployeeUnavailability
        from apps.core.models import DayOfWeek

        # Obtener empleados activos con roles de limpieza
        housekeeping_employees = Employee.objects.filter(
            role__code__in=['FDC', 'VDC'],
            is_active=True
        ).prefetch_related(
            'allowed_blocks', 'fixed_days_off', 'teams'
        ).order_by('last_name')

        # Obtener equipos/parejas activos
        teams = list(Team.objects.filter(is_active=True).prefetch_related('members'))

        # Obtener indisponibilidades para la semana
        week_end = week_start + timedelta(days=6)
        unavailabilities = EmployeeUnavailability.objects.filter(
            date_start__lte=week_end,
            date_end__gte=week_start
        )
        unavailable_dates = {}
        for u in unavailabilities:
            if u.employee_id not in unavailable_dates:
                unavailable_dates[u.employee_id] = set()
            current = max(u.date_start, week_start)
            while current <= min(u.date_end, week_end):
                unavailable_dates[u.employee_id].add(current)
                current += timedelta(days=1)

        # Obtener plantillas de turno por rol y bloque
        shift_templates = {}
        for st in ShiftTemplate.objects.filter(is_active=True).select_related('role', 'time_block'):
            key = (st.role.code if st.role else None, st.time_block.code if st.time_block else None)
            shift_templates[key] = st

        # Mapeo de día de semana (0=Lunes) a código DayOfWeek (códigos en español)
        weekday_to_code = {0: 'LUN', 1: 'MAR', 2: 'MIE', 3: 'JUE', 4: 'VIE', 5: 'SAB', 6: 'DOM'}

        # Patrones de días libres consecutivos para auto-asignación
        days_off_patterns = [
            (5, 6), (0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (6, 0),
        ]

        # Ordenar días por carga (mayor primero) para evitar días libres en días de alta carga
        day_loads = [(i, day_load['total_hours']) for i, (_, day_load) in enumerate(week_load['days'].items())]
        day_loads.sort(key=lambda x: x[1], reverse=True)
        high_load_days = {day_loads[0][0], day_loads[1][0]} if len(day_loads) >= 2 else set()

        # Calcular días libres por empleado
        employee_days_off = {}
        pattern_idx = 0

        for emp in housekeeping_employees:
            # 1. Verificar si tiene días fijos configurados
            fixed_days = list(emp.fixed_days_off.values_list('code', flat=True))

            if fixed_days:
                # Usar días fijos del empleado (códigos en español)
                code_to_weekday = {'LUN': 0, 'MAR': 1, 'MIE': 2, 'JUE': 3, 'VIE': 4, 'SAB': 5, 'DOM': 6}
                employee_days_off[emp.id] = tuple(code_to_weekday.get(d, 6) for d in fixed_days[:2])
            else:
                # Auto-asignar evitando días de alta carga
                for _ in range(len(days_off_patterns)):
                    pattern = days_off_patterns[pattern_idx % len(days_off_patterns)]
                    if not (pattern[0] in high_load_days and pattern[1] in high_load_days):
                        break
                    pattern_idx += 1
                employee_days_off[emp.id] = days_off_patterns[pattern_idx % len(days_off_patterns)]
                pattern_idx += 1

        # Sincronizar días libres para parejas (si no tienen días fijos)
        for team in teams:
            members = [m for m in team.members.all() if m.id in employee_days_off]
            if len(members) >= 2:
                # Verificar si alguno tiene días fijos
                members_with_fixed = [m for m in members if m.fixed_days_off.exists()]
                if members_with_fixed:
                    # Usar los días del primer miembro con días fijos
                    pattern = employee_days_off[members_with_fixed[0].id]
                else:
                    # Usar el patrón del primer miembro
                    pattern = employee_days_off[members[0].id]
                for member in members:
                    employee_days_off[member.id] = pattern

        # Generar asignaciones
        week_days = [week_start + timedelta(days=i) for i in range(7)]
        day_keys = list(week_load['days'].keys())

        # Preparar necesidades de personal por día y turno
        # NOTA: El turno TARDE también ayuda con tareas DAY, así que:
        # - EVENING persons_needed = personas para COUVERTURE (que también ayudan con DAY)
        # - DAY persons_needed = personas ADICIONALES de mañana (después de la ayuda de TARDE)
        day_needs = {}
        for i, day_key in enumerate(day_keys):
            req = requirements['by_day'][day_key]
            day_needs[i] = {
                'DAY': req['day_shift']['persons_needed'],      # Personas MAÑANA adicionales
                'EVENING': req['evening_shift']['persons_needed'],  # Personas TARDE (hacen couverture + ayudan DAY)
            }

        # === NUEVO MODELO: UNIDADES ASIGNABLES (parejas o individuos) ===
        # Crear unidades asignables - parejas trabajan juntas
        employees_in_pairs = set()
        pair_units = []  # Lista de tuplas (emp1, emp2, team)

        for team in teams:
            members = list(team.members.filter(is_active=True))
            if len(members) >= 2:
                # Tomar los primeros 2 miembros como pareja
                pair_units.append((members[0], members[1], team))
                employees_in_pairs.add(members[0].id)
                employees_in_pairs.add(members[1].id)

        # Empleados individuales (sin pareja)
        individual_employees = [e for e in housekeeping_employees if e.id not in employees_in_pairs]

        # Función para obtener bloques permitidos de una unidad (pareja o individuo)
        def get_unit_allowed_blocks(unit):
            """Retorna bloques que TODOS los miembros de la unidad pueden trabajar."""
            if isinstance(unit, tuple):  # Es una pareja
                emp1, emp2, _ = unit
                blocks1 = set(emp1.allowed_blocks.values_list('code', flat=True)) or {'DAY', 'EVENING'}
                blocks2 = set(emp2.allowed_blocks.values_list('code', flat=True)) or {'DAY', 'EVENING'}
                return blocks1 & blocks2  # Intersección
            else:  # Es un individuo
                blocks = set(unit.allowed_blocks.values_list('code', flat=True))
                return blocks or {'DAY', 'EVENING'}

        # Clasificar unidades por sus bloques permitidos
        day_only_units = []
        evening_only_units = []
        flexible_units = []

        all_units = pair_units + [(e,) for e in individual_employees]  # Tupla de 1 para individuos

        for unit in all_units:
            if isinstance(unit, tuple) and len(unit) == 3:  # Pareja
                allowed = get_unit_allowed_blocks(unit)
            else:  # Individual (tupla de 1)
                allowed = get_unit_allowed_blocks(unit[0])

            can_day = 'DAY' in allowed
            can_evening = 'EVENING' in allowed

            if can_day and not can_evening:
                day_only_units.append(unit)
            elif can_evening and not can_day:
                evening_only_units.append(unit)
            else:
                flexible_units.append(unit)

        # Función para obtener empleados de una unidad
        def get_unit_employees(unit):
            if isinstance(unit, tuple) and len(unit) == 3:  # Pareja (emp1, emp2, team)
                return [unit[0], unit[1]]
            elif isinstance(unit, tuple) and len(unit) == 1:  # Individual
                return [unit[0]]
            else:
                return [unit]

        # Función para asignar una UNIDAD completa a un turno
        def assign_unit_to_shift(unit, shift_block):
            employees = get_unit_employees(unit)
            for emp in employees:
                days_off = employee_days_off.get(emp.id, (5, 6))
                weekly_hours = float(emp.weekly_hours_target)
                hours_assigned = 0

                shift_template = (
                    shift_templates.get((emp.role.code, shift_block)) or
                    shift_templates.get((emp.role.code, 'DAY')) or
                    shift_templates.get((emp.role.code, 'EVENING')) or
                    shift_templates.get((None, shift_block))
                )

                for day_idx, day_date in enumerate(week_days):
                    if day_idx in days_off:
                        continue

                    if emp.id in unavailable_dates and day_date in unavailable_dates[emp.id]:
                        continue

                    if hours_assigned >= weekly_hours:
                        break

                    hours_per_day = min(8, weekly_hours - hours_assigned)

                    ShiftAssignment.objects.create(
                        week_plan=week_plan,
                        date=day_date,
                        employee=emp,
                        shift_template=shift_template,
                        assigned_hours=hours_per_day,
                        is_day_off=False
                    )

                    hours_assigned += hours_per_day

        # === MODELO DE ASIGNACIÓN BALANCEADO ===
        # 1. Primero: Asegurar mínimo de MAÑANA (trabajo en parejas)
        # 2. Luego: Cubrir TARDE para couverture
        # 3. Finalmente: Balancear si hay excesos

        # Mínimos desde BD
        day_block = TimeBlock.objects.filter(code='DAY').first()
        evening_block = TimeBlock.objects.filter(code='EVENING').first()
        min_day_staff = day_block.min_staff if day_block else 2
        min_evening_staff = evening_block.min_staff if evening_block else 2

        # Calcular cobertura por día antes de asignar
        def get_working_days_for_unit(unit):
            """Retorna los días que TODOS los miembros de la unidad pueden trabajar."""
            employees = get_unit_employees(unit)
            if not employees:
                return set()

            # Intersección de días de trabajo de todos los miembros
            working_days = None
            for emp in employees:
                days_off = employee_days_off.get(emp.id, (5, 6))
                emp_working = set(range(7)) - set(days_off)
                # También verificar indisponibilidades
                for i in range(7):
                    day_date = week_days[i]
                    if emp.id in unavailable_dates and day_date in unavailable_dates[emp.id]:
                        emp_working.discard(i)

                if working_days is None:
                    working_days = emp_working
                else:
                    working_days = working_days & emp_working  # Intersección

            return working_days or set()

        def calculate_daily_coverage(assigned_units):
            """Calcula cuántas personas trabajan cada día."""
            coverage = {i: 0 for i in range(7)}
            for unit in assigned_units:
                unit_size = len(get_unit_employees(unit))
                for day in get_working_days_for_unit(unit):
                    coverage[day] += unit_size  # Parejas cuentan como 2
            return coverage

        def find_uncovered_days(coverage, required):
            """Encuentra días donde la cobertura es menor a la requerida."""
            return [day for day in range(7) if coverage[day] < required]

        # Calcular máximo de personas necesarias en la semana
        max_evening_needed = max(day_needs[i]['EVENING'] for i in range(7))
        max_day_needed = max(max(day_needs[i]['DAY'] for i in range(7)), min_day_staff)

        # PASO 1: Asignar UNIDADES al turno MAÑANA primero (para asegurar mínimo)
        # Prioridad: day_only primero, luego flexibles
        day_assigned = []
        available_for_day = day_only_units + flexible_units

        while True:
            coverage = calculate_daily_coverage(day_assigned)
            uncovered = find_uncovered_days(coverage, min_day_staff)  # Asegurar mínimo primero

            if not uncovered:
                break  # Mínimo cubierto todos los días

            best_unit = None
            best_cover_count = 0

            for unit in available_for_day:
                if unit in day_assigned:
                    continue
                working = get_working_days_for_unit(unit)
                covers = len([d for d in uncovered if d in working])
                if covers > best_cover_count:
                    best_cover_count = covers
                    best_unit = unit

            if best_unit is None:
                break

            assign_unit_to_shift(best_unit, 'DAY')
            day_assigned.append(best_unit)

        # PASO 2: Asignar UNIDADES al turno TARDE (para couverture)
        # Solo usar evening_only + flexibles que NO están en DAY
        evening_assigned = []
        available_for_evening = evening_only_units + [u for u in flexible_units if u not in day_assigned]

        while True:
            coverage = calculate_daily_coverage(evening_assigned)
            uncovered = find_uncovered_days(coverage, max_evening_needed)

            if not uncovered:
                break

            best_unit = None
            best_cover_count = 0

            for unit in available_for_evening:
                if unit in evening_assigned:
                    continue
                working = get_working_days_for_unit(unit)
                covers = len([d for d in uncovered if d in working])
                if covers > best_cover_count:
                    best_cover_count = covers
                    best_unit = unit

            if best_unit is None:
                break

            assign_unit_to_shift(best_unit, 'EVENING')
            evening_assigned.append(best_unit)

        # PASO 3: Si DAY necesita más personas (más del mínimo), añadir flexibles disponibles
        available_for_day_extra = [u for u in flexible_units if u not in day_assigned and u not in evening_assigned]

        while True:
            coverage = calculate_daily_coverage(day_assigned)
            uncovered = find_uncovered_days(coverage, max_day_needed)

            if not uncovered:
                break

            best_unit = None
            best_cover_count = 0

            for unit in available_for_day_extra:
                if unit in day_assigned:
                    continue
                working = get_working_days_for_unit(unit)
                covers = len([d for d in uncovered if d in working])
                if covers > best_cover_count:
                    best_cover_count = covers
                    best_unit = unit

            if best_unit is None:
                break

            assign_unit_to_shift(best_unit, 'DAY')
            day_assigned.append(best_unit)

        # PASO 4: Si DAY sigue sin cobertura mínima, mover UNIDADES de EVENING a DAY
        # Permitir que EVENING baje hasta min_evening_staff (no max_evening_needed)
        day_coverage = calculate_daily_coverage(day_assigned)
        evening_coverage = calculate_daily_coverage(evening_assigned)
        uncovered_days = find_uncovered_days(day_coverage, min_day_staff)  # Priorizar mínimo

        if uncovered_days:
            for unit in list(evening_assigned):
                if unit not in flexible_units:
                    continue

                unit_working = get_working_days_for_unit(unit)
                unit_size = len(get_unit_employees(unit))

                helps_day = any(d in unit_working for d in uncovered_days)
                if not helps_day:
                    continue

                # EVENING puede bajar hasta min_evening_staff (no max_evening_needed)
                can_move = True
                for day in unit_working:
                    if evening_coverage[day] - unit_size < min_evening_staff:
                        can_move = False
                        break

                if can_move:
                    evening_assigned.remove(unit)

                    for emp in get_unit_employees(unit):
                        ShiftAssignment.objects.filter(
                            week_plan=week_plan,
                            employee=emp
                        ).delete()

                    assign_unit_to_shift(unit, 'DAY')
                    day_assigned.append(unit)

                    day_coverage = calculate_daily_coverage(day_assigned)
                    evening_coverage = calculate_daily_coverage(evening_assigned)
                    uncovered_days = find_uncovered_days(day_coverage, min_day_staff)

                    if not uncovered_days:
                        break

        return week_plan


class ForecastUploadView(views.APIView):
    """
    Vista para subir PDF de forecast y generar WeekPlan automáticamente.
    """
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        """
        Sube un PDF de forecast, extrae los datos y genera el WeekPlan.
        """
        if 'file' not in request.FILES:
            return Response(
                {'error': 'No se proporcionó archivo'},
                status=status.HTTP_400_BAD_REQUEST
            )

        pdf_file = request.FILES['file']

        # Validar que sea PDF
        if not pdf_file.name.lower().endswith('.pdf'):
            return Response(
                {'error': 'El archivo debe ser un PDF'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Guardar temporalmente
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            for chunk in pdf_file.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name

        try:
            # Parsear PDF
            parser = ForecastPDFParser()
            parsed_data = parser.parse_pdf(tmp_path)

            if 'error' in parsed_data:
                return Response(
                    {'error': parsed_data['error']},
                    status=status.HTTP_400_BAD_REQUEST
                )

            week_start_str = parsed_data.get('week_start')
            forecast_data = parsed_data.get('forecast', [])

            if not week_start_str or len(forecast_data) < 7:
                return Response(
                    {'error': 'No se pudieron extraer suficientes datos del PDF',
                     'parsed': parsed_data},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Usar solo los primeros 7 días
            forecast_data = forecast_data[:7]

            try:
                week_start = datetime.strptime(week_start_str, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {'error': 'Error al parsear fecha de inicio'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Procesar forecast
            processed_forecast = []
            for i, day_data in enumerate(forecast_data):
                day_date = week_start + timezone.timedelta(days=i)
                processed_forecast.append({
                    'date': day_date,
                    'departures': int(day_data.get('departures', 0)),
                    'arrivals': int(day_data.get('arrivals', 0)),
                    'occupied': int(day_data.get('occupied', 0)),
                })

            # Calcular carga
            loader = ForecastLoader()
            week_load = loader.calculate_week_load(processed_forecast)
            requirements = loader.calculate_staffing_requirements(week_load)

            # Preparar forecast_data para guardar
            forecast_data_to_save = [
                {
                    'date': (week_start + timezone.timedelta(days=i)).isoformat(),
                    'departures': d['departures'],
                    'arrivals': d['arrivals'],
                    'occupied': d['occupied'],
                }
                for i, d in enumerate(forecast_data)
            ]

            # Generar WeekPlan (reusar lógica)
            forecast_view = ForecastWeekPlanView()
            week_plan = forecast_view._generate_weekplan(
                week_start, week_load, requirements, forecast_data_to_save
            )

            # Construir respuesta
            result = {
                'week_plan_id': week_plan.id,
                'week_start': week_start.isoformat(),
                'status': week_plan.status,
                'parsed_data': {
                    'forecast': [
                        {
                            'date': (week_start + timezone.timedelta(days=i)).isoformat(),
                            'departures': d['departures'],
                            'arrivals': d['arrivals'],
                            'occupied': d['occupied'],
                        }
                        for i, d in enumerate(forecast_data)
                    ]
                },
                'load_summary': {
                    'total_hours': round(week_load['totals']['total_hours'], 1),
                    'day_shift_hours': round(week_load['totals']['day_minutes'] / 60, 1),
                    'evening_shift_hours': round(week_load['totals']['evening_minutes'] / 60, 1),
                },
                'daily_load': [],
                'assignments': [],
            }

            # Agregar carga diaria
            day_names = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
            for i, (day_key, day_load) in enumerate(week_load['days'].items()):
                req = requirements['by_day'][day_key]
                result['daily_load'].append({
                    'date': day_key,
                    'day_name': day_names[i],
                    'day_shift_hours': round(day_load['shifts']['DAY']['hours'], 1),
                    'evening_shift_hours': round(day_load['shifts']['EVENING']['hours'], 1),
                    'day_persons_needed': req['day_shift']['persons_needed'],
                    'evening_persons_needed': req['evening_shift']['persons_needed'],
                })

            # Agregar asignaciones
            for assignment in week_plan.shift_assignments.select_related('employee', 'shift_template').order_by('employee__last_name', 'date'):
                result['assignments'].append({
                    'employee': assignment.employee.full_name if assignment.employee else None,
                    'date': assignment.date.isoformat(),
                    'shift': assignment.shift_template.code if assignment.shift_template else None,
                    'hours': float(assignment.assigned_hours),
                })

            return Response(result, status=status.HTTP_201_CREATED)

        except Exception as e:
            import traceback
            return Response(
                {'error': f'Error al procesar PDF: {str(e)}',
                 'traceback': traceback.format_exc()},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        finally:
            # Limpiar archivo temporal
            os.unlink(tmp_path)
