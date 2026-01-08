"""
Week Plan Generator Service.
Genera el plan semanal (horarios de trabajo).
"""
from datetime import date, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
from decimal import Decimal
from django.db import transaction

from apps.core.models import TimeBlock, DayOfWeek
from apps.staff.models import Employee, Team
from apps.shifts.models import ShiftTemplate
from apps.planning.models import WeekPlan, ShiftAssignment, PlanningAlert
from apps.rules.models import ElasticityRule
from .load import LoadCalculator
from .capacity import CapacityCalculator


class WeekPlanGenerator:
    """
    Generador de planes semanales.
    Crea el horario laboral de cada empleado para la semana.
    """

    def __init__(self):
        self.load_calculator = LoadCalculator()
        self.capacity_calculator = CapacityCalculator()
        self.alerts: List[Dict] = []

    def _get_week_days(self, week_start: date) -> List[date]:
        """Retorna los 7 días de la semana."""
        return [week_start + timedelta(days=i) for i in range(7)]

    def _get_day_of_week_map(self) -> Dict[int, DayOfWeek]:
        """Mapea iso_weekday a DayOfWeek."""
        return {
            dow.iso_weekday: dow
            for dow in DayOfWeek.objects.all()
        }

    def _calculate_optimal_days_off(
        self,
        employee: Employee,
        week_load: Dict,
        week_start: date,
        days_needed_off: int = 2
    ) -> List[date]:
        """
        Calcula los días óptimos de descanso para un empleado.
        Elige días con menor carga.
        """
        week_days = self._get_week_days(week_start)
        day_loads = []

        for day in week_days:
            day_key = day.isoformat()
            if day_key in week_load['days']:
                total_load = week_load['days'][day_key]['total_minutes']
            else:
                total_load = 0
            day_loads.append((day, total_load))

        # Ordenar por carga (menor primero)
        day_loads.sort(key=lambda x: x[1])

        # Tomar los días con menor carga
        return [d[0] for d in day_loads[:days_needed_off]]

    def _calculate_days_to_work(
        self,
        employee: Employee,
        week_start: date,
        week_load: Dict
    ) -> Tuple[List[date], List[date]]:
        """
        Determina qué días trabaja y cuáles descansa un empleado.

        Returns:
            Tuple de (días_trabajo, días_descanso)
        """
        week_days = self._get_week_days(week_start)
        dow_map = self._get_day_of_week_map()

        # Si tiene días fijos de descanso
        fixed_days_off_ids = set(employee.fixed_days_off.values_list('iso_weekday', flat=True))

        if fixed_days_off_ids:
            # Usar días fijos
            days_off = [d for d in week_days if d.isoweekday() in fixed_days_off_ids]
            days_work = [d for d in week_days if d.isoweekday() not in fixed_days_off_ids]
        else:
            # Calcular días óptimos de descanso
            # Calcular cuántos días necesita para cumplir horas objetivo
            shift_template = self._get_primary_shift_template(employee)
            if shift_template:
                hours_per_day = shift_template.total_hours
                days_needed = int(float(employee.weekly_hours_target) / hours_per_day)
                days_needed = min(days_needed, 7)
                days_off_needed = 7 - days_needed
            else:
                days_off_needed = 2

            days_off = self._calculate_optimal_days_off(
                employee, week_load, week_start, days_off_needed
            )
            days_work = [d for d in week_days if d not in days_off]

        return days_work, days_off

    def _get_primary_shift_template(self, employee: Employee) -> Optional[ShiftTemplate]:
        """Obtiene la plantilla de turno principal del empleado."""
        # Preferir DAY, luego EVENING
        for block_code in ['DAY', 'EVENING', 'NIGHT']:
            try:
                block = TimeBlock.objects.get(code=block_code)
                if employee.allowed_blocks.filter(id=block.id).exists():
                    template = ShiftTemplate.objects.filter(
                        role=employee.role,
                        time_block=block,
                        is_active=True
                    ).first()
                    if template:
                        return template
            except TimeBlock.DoesNotExist:
                continue
        return None

    def _assign_shifts_to_employee(
        self,
        employee: Employee,
        days_work: List[date],
        week_plan: WeekPlan,
        week_load: Dict
    ) -> List[ShiftAssignment]:
        """
        Asigna turnos a un empleado para los días de trabajo.
        Intenta cumplir las horas semanales objetivo.
        """
        assignments = []
        total_hours_assigned = Decimal('0')
        target_hours = employee.weekly_hours_target

        # Obtener plantilla de turno
        shift_template = self._get_primary_shift_template(employee)
        if not shift_template:
            self.alerts.append({
                'type': 'WARNING',
                'severity': 'MEDIUM',
                'title': f'Sin plantilla de turno para {employee.full_name}',
                'message': f'No se encontró plantilla de turno para el rol {employee.role.code}',
            })
            return assignments

        hours_per_shift = Decimal(str(shift_template.total_hours))

        for day in days_work:
            if total_hours_assigned >= target_hours:
                break

            # Calcular horas a asignar
            remaining = target_hours - total_hours_assigned
            if remaining < hours_per_shift:
                # Último día, asignar solo lo que falta
                assigned_hours = remaining
            else:
                assigned_hours = hours_per_shift

            assignment = ShiftAssignment(
                week_plan=week_plan,
                date=day,
                employee=employee,
                shift_template=shift_template,
                assigned_hours=assigned_hours,
                is_day_off=False
            )
            assignments.append(assignment)
            total_hours_assigned += assigned_hours

        # Verificar si se cumplieron las horas
        if total_hours_assigned < target_hours:
            deficit = target_hours - total_hours_assigned
            self.alerts.append({
                'type': 'WARNING',
                'severity': 'LOW',
                'title': f'Déficit de horas para {employee.full_name}',
                'message': f'Asignadas {total_hours_assigned}h de {target_hours}h objetivo (faltan {deficit}h)',
            })

        return assignments

    def _assign_shifts_to_team(
        self,
        team: Team,
        week_plan: WeekPlan,
        week_load: Dict,
        week_start: date
    ) -> List[ShiftAssignment]:
        """
        Asigna turnos a un equipo completo.
        Los miembros del equipo trabajan juntos.
        """
        assignments = []
        members = list(team.members.filter(is_active=True))

        if not members:
            return assignments

        # Usar el primer miembro como referencia
        reference_member = members[0]

        # Calcular días de trabajo (comunes para todo el equipo)
        days_work, days_off = self._calculate_days_to_work(
            reference_member, week_start, week_load
        )

        # Obtener plantilla de turno
        shift_template = self._get_primary_shift_template(reference_member)
        if not shift_template:
            return assignments

        # Calcular horas objetivo promedio del equipo
        avg_target_hours = sum(m.weekly_hours_target for m in members) / len(members)
        hours_per_shift = Decimal(str(shift_template.total_hours))
        total_hours_assigned = Decimal('0')

        for day in days_work:
            if total_hours_assigned >= avg_target_hours:
                break

            remaining = avg_target_hours - total_hours_assigned
            assigned_hours = min(remaining, hours_per_shift)

            assignment = ShiftAssignment(
                week_plan=week_plan,
                date=day,
                team=team,
                shift_template=shift_template,
                assigned_hours=assigned_hours,
                is_day_off=False
            )
            assignments.append(assignment)
            total_hours_assigned += assigned_hours

        return assignments

    @transaction.atomic
    def generate_week_plan(
        self,
        week_start: date,
        created_by: str = ''
    ) -> WeekPlan:
        """
        Genera un plan semanal completo.

        Args:
            week_start: Fecha del lunes de la semana
            created_by: Usuario que crea el plan

        Returns:
            WeekPlan generado
        """
        self.alerts = []

        # Validar que sea lunes
        if week_start.weekday() != 0:
            raise ValueError("week_start debe ser un lunes")

        # Verificar si ya existe
        existing = WeekPlan.objects.filter(week_start_date=week_start).first()
        if existing:
            # Eliminar el existente si está en borrador
            if existing.status == 'DRAFT':
                existing.delete()
            else:
                raise ValueError(f"Ya existe un plan para esta semana con estado {existing.status}")

        # Calcular carga de la semana
        week_load = self.load_calculator.compute_week_load(week_start)

        # Crear plan
        week_plan = WeekPlan.objects.create(
            week_start_date=week_start,
            name=f"Semana {week_start.strftime('%d/%m/%Y')}",
            status='DRAFT',
            created_by=created_by
        )

        # Procesar equipos primero
        processed_employees = set()
        teams = Team.objects.filter(
            is_active=True,
            team_type__in=['FIXED', 'PREFERRED']
        ).prefetch_related('members')

        for team in teams:
            assignments = self._assign_shifts_to_team(
                team, week_plan, week_load, week_start
            )
            for assignment in assignments:
                assignment.save()

            # Marcar miembros como procesados
            for member in team.members.all():
                processed_employees.add(member.id)

        # Procesar empleados individuales
        employees = Employee.objects.filter(
            is_active=True
        ).exclude(
            id__in=processed_employees
        )

        for employee in employees:
            days_work, days_off = self._calculate_days_to_work(
                employee, week_start, week_load
            )
            assignments = self._assign_shifts_to_employee(
                employee, days_work, week_plan, week_load
            )
            for assignment in assignments:
                assignment.save()

        # Crear alertas
        for alert_data in self.alerts:
            PlanningAlert.objects.create(
                date=week_start,
                alert_type=alert_data['type'],
                severity=alert_data['severity'],
                title=alert_data['title'],
                message=alert_data['message']
            )

        # Verificar balance carga vs capacidad
        self._verify_week_balance(week_plan, week_load, week_start)

        return week_plan

    def _verify_week_balance(
        self,
        week_plan: WeekPlan,
        week_load: Dict,
        week_start: date
    ):
        """Verifica el balance entre carga y capacidad."""
        week_days = self._get_week_days(week_start)

        for day in week_days:
            day_key = day.isoformat()
            if day_key not in week_load['days']:
                continue

            day_load = week_load['days'][day_key]

            for block_code, block_data in day_load['blocks'].items():
                load_minutes = block_data['total_minutes']

                # Calcular capacidad asignada para este día/bloque
                try:
                    time_block = TimeBlock.objects.get(code=block_code)
                except TimeBlock.DoesNotExist:
                    continue

                capacity_minutes = 0
                assignments = week_plan.shift_assignments.filter(
                    date=day,
                    shift_template__time_block=time_block,
                    is_day_off=False
                )
                for assignment in assignments:
                    capacity_minutes += int(assignment.assigned_hours * 60)

                # Verificar déficit
                if load_minutes > capacity_minutes:
                    deficit_hours = (load_minutes - capacity_minutes) / 60
                    PlanningAlert.objects.create(
                        date=day,
                        time_block=time_block,
                        alert_type='UNDERSTAFF',
                        severity='HIGH' if deficit_hours > 2 else 'MEDIUM',
                        title=f'Déficit de personal - {block_code}',
                        message=f'Faltan {deficit_hours:.1f}h de capacidad para cubrir la carga'
                    )

    def regenerate_week_plan(self, week_plan: WeekPlan) -> WeekPlan:
        """
        Regenera un plan semanal existente.
        Solo funciona si está en DRAFT.
        """
        if week_plan.status != 'DRAFT':
            raise ValueError("Solo se pueden regenerar planes en estado DRAFT")

        week_start = week_plan.week_start_date
        created_by = week_plan.created_by

        # Eliminar y recrear
        week_plan.delete()

        return self.generate_week_plan(week_start, created_by)
