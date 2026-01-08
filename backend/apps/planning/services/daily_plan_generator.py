"""
Daily Plan Generator Service.
Genera el plan diario (asignación de tareas específicas).
Implementa asignación zonificada para eficiencia.
"""
from datetime import date
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
from django.db import transaction

from apps.core.models import TimeBlock, Zone, Room
from apps.staff.models import Employee, Team
from apps.rooms.models import RoomDailyTask, RoomDailyState
from apps.planning.models import (
    WeekPlan, ShiftAssignment, DailyPlan, TaskAssignment, PlanningAlert
)
from apps.rules.models import ZoneAssignmentRule
from .load import LoadCalculator
from .time_calculator import TimeCalculator


class DailyPlanGenerator:
    """
    Generador de planes diarios.
    Asigna tareas específicas a empleados/equipos.
    Implementa asignación zonificada para minimizar desplazamientos.
    """

    def __init__(self):
        self.load_calculator = LoadCalculator()
        self.time_calculator = TimeCalculator()
        self.alerts: List[Dict] = []

    def _get_zone_assignment_rules(self) -> Dict[str, Any]:
        """Obtiene reglas de asignación de zonas."""
        rules = {
            'COMPLETE_ZONE_FIRST': ZoneAssignmentRule.get_value('COMPLETE_ZONE_FIRST', True),
            'MAX_ZONES_PER_EMPLOYEE': ZoneAssignmentRule.get_value('MAX_ZONES_PER_EMPLOYEE', 3),
            'ADJACENT_ZONES_PREFERRED': ZoneAssignmentRule.get_value('ADJACENT_ZONES_PREFERRED', True),
            'PAIR_SAME_ZONE': ZoneAssignmentRule.get_value('PAIR_SAME_ZONE', True),
        }
        return rules

    def _get_available_units_for_day(
        self,
        target_date: date,
        time_block: TimeBlock,
        week_plan: Optional[WeekPlan] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtiene las unidades disponibles para un día según el WeekPlan.
        """
        units = []

        if week_plan:
            # Usar asignaciones del WeekPlan
            assignments = ShiftAssignment.objects.filter(
                week_plan=week_plan,
                date=target_date,
                shift_template__time_block=time_block,
                is_day_off=False
            ).select_related('employee', 'team', 'shift_template')

            for assignment in assignments:
                if assignment.employee:
                    units.append({
                        'type': 'employee',
                        'employee': assignment.employee,
                        'employee_id': assignment.employee.id,
                        'name': assignment.employee.full_name,
                        'available_minutes': int(assignment.assigned_hours * 60),
                        'eligible_tasks': list(assignment.employee.eligible_tasks.values_list('code', flat=True)),
                        'assigned_minutes': 0,
                        'assigned_zones': [],
                        'assigned_tasks': [],
                    })
                elif assignment.team:
                    units.append({
                        'type': 'team',
                        'team': assignment.team,
                        'team_id': assignment.team.id,
                        'name': str(assignment.team),
                        'available_minutes': int(assignment.assigned_hours * 60),
                        'eligible_tasks': list(assignment.team.get_common_eligible_tasks().values_list('code', flat=True)),
                        'assigned_minutes': 0,
                        'assigned_zones': [],
                        'assigned_tasks': [],
                    })
        else:
            # Sin WeekPlan, usar todos los disponibles
            from .capacity import CapacityCalculator
            capacity_calc = CapacityCalculator()
            capacity = capacity_calc.compute_capacity(target_date, time_block)

            for unit_data in capacity['blocks'].get(time_block.code, {}).get('units', []):
                units.append({
                    'type': unit_data['type'],
                    'employee': unit_data.get('employee'),
                    'team': unit_data.get('team'),
                    'employee_id': unit_data.get('employee_id'),
                    'team_id': unit_data.get('team_id'),
                    'name': unit_data.get('employee_name') or unit_data.get('team_name'),
                    'available_minutes': unit_data['available_minutes'],
                    'eligible_tasks': unit_data['eligible_tasks'],
                    'assigned_minutes': 0,
                    'assigned_zones': [],
                    'assigned_tasks': [],
                })

        return units

    def _get_tasks_by_zone(
        self,
        target_date: date,
        time_block: TimeBlock
    ) -> Dict[str, List[RoomDailyTask]]:
        """
        Obtiene tareas agrupadas por zona, ordenadas para recorrido eficiente.
        """
        tasks = RoomDailyTask.objects.filter(
            room_daily_state__date=target_date,
            time_block=time_block,
            status='PENDING'
        ).select_related(
            'room_daily_state',
            'room_daily_state__room',
            'room_daily_state__room__zone',
            'task_type'
        ).order_by(
            'room_daily_state__room__zone__priority_order',
            'room_daily_state__room__zone__floor_number',
            'room_daily_state__room__order_in_zone',
            'task_type__priority'
        )

        # Agrupar por zona
        tasks_by_zone = defaultdict(list)
        for task in tasks:
            zone = task.room_daily_state.room.zone
            tasks_by_zone[zone.code].append(task)

        return dict(tasks_by_zone)

    def _calculate_zone_load(
        self,
        tasks: List[RoomDailyTask]
    ) -> int:
        """Calcula la carga total de una zona en minutos."""
        total = 0
        for task in tasks:
            total += self.time_calculator.calculate_task_time(task)
        return total

    def _find_best_unit_for_zone(
        self,
        zone: Zone,
        zone_tasks: List[RoomDailyTask],
        available_units: List[Dict],
        rules: Dict
    ) -> Optional[Dict]:
        """
        Encuentra la mejor unidad para asignar una zona.
        Considera:
        - Elegibilidad de tareas
        - Capacidad disponible
        - Zonas ya asignadas (preferir adyacentes)
        """
        zone_load = self._calculate_zone_load(zone_tasks)

        # Obtener tipos de tarea en la zona
        task_types_in_zone = set(t.task_type.code for t in zone_tasks)

        best_unit = None
        best_score = -1

        for unit in available_units:
            # Verificar capacidad
            remaining_capacity = unit['available_minutes'] - unit['assigned_minutes']
            if remaining_capacity < zone_load * 0.3:  # Al menos 30% de la zona
                continue

            # Verificar elegibilidad
            can_do_tasks = task_types_in_zone.intersection(set(unit['eligible_tasks']))
            if not can_do_tasks:
                continue

            # Calcular score
            score = 0

            # Bonus por capacidad disponible
            score += min(remaining_capacity / zone_load, 1.0) * 30

            # Bonus por zonas adyacentes
            if rules['ADJACENT_ZONES_PREFERRED'] and unit['assigned_zones']:
                last_zone = unit['assigned_zones'][-1]
                try:
                    last_zone_obj = Zone.objects.get(code=last_zone)
                    if last_zone_obj.floor_number and zone.floor_number:
                        floor_diff = abs(last_zone_obj.floor_number - zone.floor_number)
                        if floor_diff <= 1:
                            score += 20
                        elif floor_diff <= 2:
                            score += 10
                except Zone.DoesNotExist:
                    pass
            elif not unit['assigned_zones']:
                # Sin zonas asignadas, bonus neutral
                score += 15

            # Penalización por muchas zonas
            if len(unit['assigned_zones']) >= rules['MAX_ZONES_PER_EMPLOYEE']:
                continue

            # Elegibilidad de tareas (más tareas = mejor)
            score += len(can_do_tasks) * 5

            if score > best_score:
                best_score = score
                best_unit = unit

        return best_unit

    def _assign_zone_to_unit(
        self,
        unit: Dict,
        zone: Zone,
        zone_tasks: List[RoomDailyTask],
        daily_plan: DailyPlan
    ) -> List[TaskAssignment]:
        """
        Asigna las tareas de una zona a una unidad.
        Ordena las tareas para recorrido eficiente dentro de la zona.
        """
        assignments = []

        # Ordenar tareas por orden en zona y prioridad de tarea
        sorted_tasks = sorted(
            zone_tasks,
            key=lambda t: (
                t.room_daily_state.room.order_in_zone,
                t.task_type.priority
            )
        )

        # Verificar elegibilidad y asignar
        order = len(unit['assigned_tasks'])
        for task in sorted_tasks:
            if task.task_type.code not in unit['eligible_tasks']:
                continue

            task_time = self.time_calculator.calculate_task_time(task)

            # Verificar capacidad
            remaining = unit['available_minutes'] - unit['assigned_minutes']
            if remaining < task_time:
                continue

            assignment = TaskAssignment(
                daily_plan=daily_plan,
                room_task=task,
                employee=unit.get('employee'),
                team=unit.get('team'),
                zone=zone,
                order_in_assignment=order,
                status='PENDING'
            )
            assignments.append(assignment)

            unit['assigned_minutes'] += task_time
            unit['assigned_tasks'].append(task.id)
            order += 1

        # Marcar zona como asignada
        if zone.code not in unit['assigned_zones']:
            unit['assigned_zones'].append(zone.code)

        return assignments

    @transaction.atomic
    def generate_daily_plan(
        self,
        target_date: date,
        week_plan: Optional[WeekPlan] = None
    ) -> DailyPlan:
        """
        Genera el plan diario con asignación zonificada.

        Args:
            target_date: Fecha del plan
            week_plan: Plan semanal asociado (opcional)

        Returns:
            DailyPlan generado
        """
        self.alerts = []

        # Verificar si ya existe
        existing = DailyPlan.objects.filter(date=target_date).first()
        if existing:
            if existing.status == 'DRAFT':
                existing.delete()
            else:
                raise ValueError(f"Ya existe un plan diario con estado {existing.status}")

        # Crear plan
        daily_plan = DailyPlan.objects.create(
            date=target_date,
            week_plan=week_plan,
            status='DRAFT'
        )

        # Obtener reglas
        rules = self._get_zone_assignment_rules()

        # Procesar cada bloque temporal
        for time_block in TimeBlock.objects.filter(is_active=True):
            self._process_time_block(
                daily_plan, target_date, time_block, week_plan, rules
            )

        # Crear alertas
        for alert_data in self.alerts:
            PlanningAlert.objects.create(
                date=target_date,
                time_block=alert_data.get('time_block'),
                alert_type=alert_data['type'],
                severity=alert_data['severity'],
                title=alert_data['title'],
                message=alert_data['message']
            )

        return daily_plan

    def _process_time_block(
        self,
        daily_plan: DailyPlan,
        target_date: date,
        time_block: TimeBlock,
        week_plan: Optional[WeekPlan],
        rules: Dict
    ):
        """Procesa un bloque temporal para asignación zonificada."""

        # Obtener unidades disponibles
        available_units = self._get_available_units_for_day(
            target_date, time_block, week_plan
        )

        if not available_units:
            return

        # Obtener tareas por zona
        tasks_by_zone = self._get_tasks_by_zone(target_date, time_block)

        if not tasks_by_zone:
            return

        # Obtener zonas ordenadas por prioridad
        zones = Zone.objects.filter(
            code__in=tasks_by_zone.keys(),
            is_active=True
        ).order_by('priority_order', 'floor_number')

        # Asignar zonas completas a unidades
        for zone in zones:
            zone_tasks = tasks_by_zone.get(zone.code, [])
            if not zone_tasks:
                continue

            # Encontrar mejor unidad para esta zona
            best_unit = self._find_best_unit_for_zone(
                zone, zone_tasks, available_units, rules
            )

            if best_unit:
                assignments = self._assign_zone_to_unit(
                    best_unit, zone, zone_tasks, daily_plan
                )
                for assignment in assignments:
                    assignment.save()

                # Actualizar estado de tareas
                for assignment in assignments:
                    assignment.room_task.status = 'ASSIGNED'
                    assignment.room_task.save(update_fields=['status'])
            else:
                # No hay unidad disponible para esta zona
                zone_load = self._calculate_zone_load(zone_tasks)
                self.alerts.append({
                    'type': 'UNDERSTAFF',
                    'severity': 'HIGH',
                    'time_block': time_block,
                    'title': f'Sin personal para {zone.name}',
                    'message': f'{len(zone_tasks)} tareas ({zone_load} min) sin asignar en {zone.name}'
                })

        # Verificar tareas sin asignar
        unassigned = RoomDailyTask.objects.filter(
            room_daily_state__date=target_date,
            time_block=time_block,
            status='PENDING'
        )
        if unassigned.exists():
            self.alerts.append({
                'type': 'WARNING',
                'severity': 'MEDIUM',
                'time_block': time_block,
                'title': 'Tareas sin asignar',
                'message': f'{unassigned.count()} tareas pendientes de asignación'
            })

    def regenerate_daily_plan(self, daily_plan: DailyPlan) -> DailyPlan:
        """
        Regenera un plan diario existente.
        """
        if daily_plan.status != 'DRAFT':
            raise ValueError("Solo se pueden regenerar planes en estado DRAFT")

        target_date = daily_plan.date
        week_plan = daily_plan.week_plan

        # Restaurar estado de tareas
        for assignment in daily_plan.task_assignments.all():
            assignment.room_task.status = 'PENDING'
            assignment.room_task.save(update_fields=['status'])

        daily_plan.delete()

        return self.generate_daily_plan(target_date, week_plan)

    def get_daily_plan_summary(
        self,
        daily_plan: DailyPlan
    ) -> Dict[str, Any]:
        """
        Obtiene un resumen del plan diario.
        """
        summary = {
            'date': daily_plan.date,
            'status': daily_plan.status,
            'by_block': {},
            'by_employee': defaultdict(lambda: {
                'zones': [],
                'tasks': [],
                'total_minutes': 0
            }),
            'by_zone': defaultdict(lambda: {
                'tasks': 0,
                'minutes': 0,
                'assigned_to': []
            }),
            'totals': {
                'tasks': 0,
                'minutes': 0,
                'completed': 0
            }
        }

        assignments = daily_plan.task_assignments.select_related(
            'room_task',
            'room_task__task_type',
            'room_task__room_daily_state__room',
            'employee',
            'team',
            'zone'
        )

        for assignment in assignments:
            task_minutes = assignment.room_task.estimated_minutes

            # Por empleado/equipo
            if assignment.employee:
                key = f"emp_{assignment.employee.id}"
                name = assignment.employee.full_name
            else:
                key = f"team_{assignment.team.id}"
                name = str(assignment.team)

            summary['by_employee'][key]['name'] = name
            if assignment.zone.code not in summary['by_employee'][key]['zones']:
                summary['by_employee'][key]['zones'].append(assignment.zone.code)
            summary['by_employee'][key]['tasks'].append({
                'room': assignment.room_task.room.number,
                'task': assignment.room_task.task_type.code,
                'minutes': task_minutes,
                'status': assignment.status
            })
            summary['by_employee'][key]['total_minutes'] += task_minutes

            # Por zona
            summary['by_zone'][assignment.zone.code]['tasks'] += 1
            summary['by_zone'][assignment.zone.code]['minutes'] += task_minutes
            if name not in summary['by_zone'][assignment.zone.code]['assigned_to']:
                summary['by_zone'][assignment.zone.code]['assigned_to'].append(name)

            # Totales
            summary['totals']['tasks'] += 1
            summary['totals']['minutes'] += task_minutes
            if assignment.status == 'COMPLETED':
                summary['totals']['completed'] += 1

        return summary
