"""
Capacity Calculator Service.
Calcula la capacidad disponible (oferta) por día y bloque temporal.
"""
from datetime import date, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict
from decimal import Decimal

from apps.core.models import TimeBlock, DayOfWeek
from apps.staff.models import Employee, Team, EmployeeUnavailability
from apps.shifts.models import ShiftTemplate
from apps.rules.models import ElasticityRule


class CapacityCalculator:
    """
    Calculador de capacidad del personal.
    Determina cuántas horas/minutos puede trabajar el equipo.
    """

    def __init__(self):
        self._elasticity_cache = None

    def _get_elasticity_rules(self) -> Dict[str, ElasticityRule]:
        """Obtiene reglas de elasticidad con cache."""
        if self._elasticity_cache is None:
            self._elasticity_cache = {
                rule.elasticity_level: rule
                for rule in ElasticityRule.objects.all()
            }
        return self._elasticity_cache

    def _get_day_of_week(self, target_date: date) -> Optional[DayOfWeek]:
        """Obtiene el DayOfWeek para una fecha."""
        iso_weekday = target_date.isoweekday()
        try:
            return DayOfWeek.objects.get(iso_weekday=iso_weekday)
        except DayOfWeek.DoesNotExist:
            return None

    def _is_employee_available(
        self,
        employee: Employee,
        target_date: date,
        time_block: TimeBlock
    ) -> bool:
        """
        Verifica si un empleado está disponible para una fecha y bloque.
        """
        # Verificar si está activo
        if not employee.is_active:
            return False

        # Verificar si puede trabajar en este bloque
        if not employee.allowed_blocks.filter(id=time_block.id).exists():
            return False

        # Verificar bloque NIGHT
        if time_block.code == 'NIGHT' and not employee.can_work_night:
            return False

        # Verificar días fijos de descanso
        day_of_week = self._get_day_of_week(target_date)
        if day_of_week and employee.fixed_days_off.filter(id=day_of_week.id).exists():
            return False

        # Verificar indisponibilidades (vacaciones, bajas, etc.)
        has_unavailability = EmployeeUnavailability.objects.filter(
            employee=employee,
            date_start__lte=target_date,
            date_end__gte=target_date
        ).exists()
        if has_unavailability:
            return False

        return True

    def _get_shift_template(
        self,
        employee: Employee,
        time_block: TimeBlock
    ) -> Optional[ShiftTemplate]:
        """Obtiene la plantilla de turno para un empleado y bloque."""
        # Usar filter().first() porque puede haber múltiples templates (ej: FDC_MANANA y FDC_MANANA_CORTO)
        return ShiftTemplate.objects.filter(
            role=employee.role,
            time_block=time_block,
            is_active=True
        ).first()

    def compute_capacity(
        self,
        target_date: date,
        time_block: TimeBlock = None
    ) -> Dict[str, Any]:
        """
        Calcula la capacidad disponible para una fecha y bloque.

        Args:
            target_date: Fecha a calcular
            time_block: Bloque temporal (opcional)

        Returns:
            Diccionario con capacidad calculada
        """
        result = {
            'date': target_date,
            'blocks': {},
            'total_minutes': 0,
            'total_employees': 0,
            'total_teams': 0,
        }

        # Obtener bloques a calcular
        if time_block:
            blocks = [time_block]
        else:
            blocks = TimeBlock.objects.filter(is_active=True)

        for block in blocks:
            block_result = self._compute_block_capacity(target_date, block)
            result['blocks'][block.code] = block_result
            result['total_minutes'] += block_result['total_minutes']
            result['total_employees'] += block_result['employee_count']

        return result

    def _compute_block_capacity(
        self,
        target_date: date,
        time_block: TimeBlock
    ) -> Dict[str, Any]:
        """Calcula capacidad para un bloque específico."""
        result = {
            'time_block': time_block.code,
            'total_minutes': 0,
            'employee_count': 0,
            'units': [],  # Unidades de trabajo (empleados individuales o equipos)
            'by_role': defaultdict(lambda: {'minutes': 0, 'count': 0}),
        }

        # Primero, procesar equipos (parejas)
        processed_employees = set()
        teams = Team.objects.filter(
            is_active=True,
            team_type__in=['FIXED', 'PREFERRED']
        ).prefetch_related('members')

        for team in teams:
            # Verificar que todos los miembros estén disponibles
            members = list(team.members.filter(is_active=True))
            if not members:
                continue

            all_available = all(
                self._is_employee_available(m, target_date, time_block)
                for m in members
            )
            if not all_available:
                continue

            # Verificar que el equipo puede trabajar en este bloque
            common_blocks = team.get_common_blocks()
            if not common_blocks.filter(id=time_block.id).exists():
                continue

            # Obtener plantilla de turno (usar la del primer miembro)
            shift_template = self._get_shift_template(members[0], time_block)
            if not shift_template:
                continue

            # Calcular minutos disponibles del equipo
            team_minutes = shift_template.total_minutes

            result['units'].append({
                'type': 'team',
                'team': team,
                'team_id': team.id,
                'team_name': str(team),
                'members': [m.id for m in members],
                'member_names': [m.full_name for m in members],
                'shift_template': shift_template,
                'shift_template_code': shift_template.code,
                'available_minutes': team_minutes,
                'eligible_tasks': list(team.get_common_eligible_tasks().values_list('code', flat=True)),
                'elasticity': min(m.elasticity for m in members),  # Usar el menor
            })

            result['total_minutes'] += team_minutes
            result['employee_count'] += len(members)

            # Marcar empleados como procesados
            for member in members:
                processed_employees.add(member.id)
                result['by_role'][member.role.code]['minutes'] += team_minutes // len(members)
                result['by_role'][member.role.code]['count'] += 1

        # Luego, procesar empleados individuales (no en equipos)
        employees = Employee.objects.filter(
            is_active=True
        ).exclude(
            id__in=processed_employees
        ).select_related('role')

        for employee in employees:
            if not self._is_employee_available(employee, target_date, time_block):
                continue

            shift_template = self._get_shift_template(employee, time_block)
            if not shift_template:
                continue

            emp_minutes = shift_template.total_minutes

            result['units'].append({
                'type': 'employee',
                'employee': employee,
                'employee_id': employee.id,
                'employee_name': employee.full_name,
                'shift_template': shift_template,
                'shift_template_code': shift_template.code,
                'available_minutes': emp_minutes,
                'eligible_tasks': list(employee.eligible_tasks.values_list('code', flat=True)),
                'elasticity': employee.elasticity,
            })

            result['total_minutes'] += emp_minutes
            result['employee_count'] += 1
            result['by_role'][employee.role.code]['minutes'] += emp_minutes
            result['by_role'][employee.role.code]['count'] += 1

        return result

    def compute_week_capacity(
        self,
        week_start: date,
        consider_hours_target: bool = True
    ) -> Dict[str, Any]:
        """
        Calcula la capacidad para una semana completa.
        Considera las horas semanales objetivo de cada empleado.
        """
        result = {
            'week_start': week_start,
            'days': {},
            'totals': {
                'minutes': 0,
                'employees': 0,
            },
            'by_employee': defaultdict(lambda: {
                'target_hours': 0,
                'available_hours': 0,
                'days_available': [],
            }),
        }

        for day_offset in range(7):
            current_date = week_start + timedelta(days=day_offset)
            day_capacity = self.compute_capacity(current_date)

            result['days'][current_date.isoformat()] = day_capacity
            result['totals']['minutes'] += day_capacity['total_minutes']

            # Acumular por empleado
            for block_data in day_capacity['blocks'].values():
                for unit in block_data['units']:
                    if unit['type'] == 'employee':
                        emp_id = unit['employee_id']
                        result['by_employee'][emp_id]['available_hours'] += unit['available_minutes'] / 60
                        result['by_employee'][emp_id]['days_available'].append(current_date.isoformat())
                    elif unit['type'] == 'team':
                        for member_id in unit['members']:
                            result['by_employee'][member_id]['available_hours'] += unit['available_minutes'] / 60 / len(unit['members'])
                            result['by_employee'][member_id]['days_available'].append(current_date.isoformat())

        # Agregar horas objetivo
        if consider_hours_target:
            for emp in Employee.objects.filter(is_active=True):
                result['by_employee'][emp.id]['target_hours'] = float(emp.weekly_hours_target)

        return result

    def get_available_units(
        self,
        target_date: date,
        time_block: TimeBlock,
        task_type_code: str = None
    ) -> List[Dict[str, Any]]:
        """
        Obtiene unidades disponibles para asignación.
        Opcionalmente filtrado por tipo de tarea.
        """
        capacity = self._compute_block_capacity(target_date, time_block)

        units = capacity['units']

        # Filtrar por elegibilidad de tarea si se especifica
        if task_type_code:
            units = [
                u for u in units
                if task_type_code in u['eligible_tasks']
            ]

        # Ordenar por elasticidad (HIGH primero para cubrir huecos)
        elasticity_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
        units.sort(key=lambda u: elasticity_order.get(u['elasticity'], 1))

        return units
