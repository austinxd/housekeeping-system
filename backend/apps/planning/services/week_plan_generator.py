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

    def _get_shift_template_for_block(self, employee: Employee, block_code: str) -> Optional[ShiftTemplate]:
        """Obtiene la plantilla de turno para un bloque específico."""
        try:
            block = TimeBlock.objects.get(code=block_code)
            if employee.allowed_blocks.filter(id=block.id).exists():
                return ShiftTemplate.objects.filter(
                    role=employee.role,
                    time_block=block,
                    is_active=True
                ).first()
        except TimeBlock.DoesNotExist:
            pass
        return None

    def _get_employees_by_shift_capability(self) -> Dict[str, List[Employee]]:
        """
        Agrupa empleados activos por su capacidad de turno.
        Returns dict con 'EVENING' y 'DAY' como claves.
        """
        employees = Employee.objects.filter(is_active=True).prefetch_related('allowed_blocks')
        result = {'EVENING': [], 'DAY': [], 'BOTH': []}

        for emp in employees:
            block_codes = set(emp.allowed_blocks.values_list('code', flat=True))
            if 'EVENING' in block_codes and 'DAY' in block_codes:
                result['BOTH'].append(emp)
            elif 'EVENING' in block_codes:
                result['EVENING'].append(emp)
            elif 'DAY' in block_codes:
                result['DAY'].append(emp)

        return result

    def _calculate_daily_staffing_needs(
        self,
        week_start: date,
        week_load: Dict
    ) -> Dict[str, Dict[str, int]]:
        """
        Calcula las necesidades de personal por día basándose en la carga calculada.

        Regla de negocio para EVENING (couvertures):
        - > 15 couvertures → mínimo 2 personas
        - ≤ 15 couvertures → 1 persona es suficiente

        Returns: Dict con fecha ISO como clave y {'day': n, 'evening': n} como valor
        """
        from apps.core.models import TimeBlock

        result = {}

        # Obtener configuración desde BD
        day_block = TimeBlock.objects.filter(code='DAY').first()
        evening_block = TimeBlock.objects.filter(code='EVENING').first()

        # Horas de trabajo por turno
        day_shift_hours = 8.0
        if day_block and day_block.start_time and day_block.end_time:
            from datetime import datetime
            start = datetime.combine(week_start, day_block.start_time)
            end = datetime.combine(week_start, day_block.end_time)
            day_shift_hours = (end - start).total_seconds() / 3600

        # Contribución del turno EVENING al turno DAY
        evening_helps_hours = float(evening_block.helps_other_shift_hours) if evening_block else 4.5

        # Mínimo de staff para turno día
        day_min_staff = day_block.min_staff if day_block else 2

        # Calcular necesidades por día
        week_days = self._get_week_days(week_start)

        for day in week_days:
            day_key = day.isoformat()

            if day_key not in week_load['days']:
                result[day_key] = {'day': 0, 'evening': 0}
                continue

            day_load = week_load['days'][day_key]
            blocks = day_load.get('blocks', {})

            # Obtener número de couvertures (= habitaciones ocupadas)
            # desde week_load que tiene el forecast
            couvertures_count = day_load.get('forecast', {}).get('occupied', 0)

            # REGLA DE NEGOCIO:
            # > 38 couvertures → 4 personas
            # > 25 couvertures → 3 personas
            # > 13 couvertures → 2 personas
            # 1-13 couvertures → 1 persona
            # 0 couvertures → 0 personas
            if couvertures_count > 38:
                evening_persons = 4
            elif couvertures_count > 25:
                evening_persons = 3
            elif couvertures_count > 13:
                evening_persons = 2
            elif couvertures_count > 0:
                evening_persons = 1
            else:
                evening_persons = 0

            # Carga del bloque DAY (DEPART + RECOUCH)
            day_block_load = blocks.get('DAY', {})
            day_minutes = day_block_load.get('total_minutes', 0)
            day_hours = day_minutes / 60

            # Calcular contribución del turno EVENING al turno DAY
            evening_contribution_to_day = evening_persons * evening_helps_hours

            # Calcular personas DAY necesarias (restando contribución EVENING)
            remaining_day_hours = max(0, day_hours - evening_contribution_to_day)
            day_persons = 0
            if remaining_day_hours > 0 and day_shift_hours > 0:
                calculated = round(remaining_day_hours / day_shift_hours)
                day_persons = max(day_min_staff, calculated) if calculated > 0 else 0

            result[day_key] = {
                'day': day_persons,
                'evening': evening_persons,
                'couvertures': couvertures_count,  # Para debug
            }

        return result

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

    def _assign_evening_shifts_for_day(
        self,
        day: date,
        persons_needed: int,
        available_employees: List[Employee],
        week_plan: WeekPlan,
        employee_hours: Dict[int, Decimal],
        processed_today: set
    ) -> List[ShiftAssignment]:
        """
        Asigna turnos de tarde para cubrir couvertures de un día.

        PRIORIDAD: Couvertures DEBEN cubrirse. Si no hay suficientes empleados
        con horas disponibles, asignar empleados con elasticidad (horas extra).

        Args:
            day: Fecha del día
            persons_needed: Número de personas necesarias para couvertures
            available_employees: Lista de empleados que pueden trabajar en turno EVENING
            week_plan: Plan semanal
            employee_hours: Dict con horas ya asignadas por empleado
            processed_today: Set de empleados ya procesados hoy

        Returns:
            Lista de asignaciones creadas
        """
        assignments = []
        assigned_count = 0

        # Primera pasada: empleados con horas disponibles
        candidates_with_hours = []
        candidates_over_target = []

        for employee in available_employees:
            if employee.id in processed_today:
                continue

            # Obtener plantilla de turno EVENING
            shift_template = self._get_shift_template_for_block(employee, 'EVENING')
            if not shift_template:
                continue

            current_hours = employee_hours.get(employee.id, Decimal('0'))

            if current_hours < employee.weekly_hours_target:
                candidates_with_hours.append((employee, shift_template, current_hours))
            else:
                # Empleado ya cumplió horas pero puede trabajar con elasticidad
                candidates_over_target.append((employee, shift_template, current_hours))

        # Asignar primero los que tienen horas disponibles
        for employee, shift_template, current_hours in candidates_with_hours:
            if assigned_count >= persons_needed:
                break

            hours_per_shift = Decimal(str(shift_template.total_hours))
            remaining = employee.weekly_hours_target - current_hours
            assigned_hours = min(remaining, hours_per_shift)

            assignment = ShiftAssignment(
                week_plan=week_plan,
                date=day,
                employee=employee,
                shift_template=shift_template,
                assigned_hours=assigned_hours,
                is_day_off=False
            )
            assignments.append(assignment)

            employee_hours[employee.id] = current_hours + assigned_hours
            processed_today.add(employee.id)
            assigned_count += 1

        # Si aún faltan personas, usar empleados con elasticidad
        if assigned_count < persons_needed:
            for employee, shift_template, current_hours in candidates_over_target:
                if assigned_count >= persons_needed:
                    break

                # Verificar elasticidad del empleado
                from apps.rules.models import ElasticityRule
                try:
                    rule = ElasticityRule.objects.get(elasticity_level=employee.elasticity)
                    max_extra_hours = Decimal(str(rule.max_extra_hours_week))
                except ElasticityRule.DoesNotExist:
                    max_extra_hours = Decimal('0')

                if max_extra_hours <= 0:
                    continue

                hours_per_shift = Decimal(str(shift_template.total_hours))
                # Asignar hasta el límite de elasticidad semanal
                extra_already = max(Decimal('0'), current_hours - employee.weekly_hours_target)
                remaining_elasticity = max_extra_hours - extra_already

                if remaining_elasticity <= 0:
                    continue

                assigned_hours = min(remaining_elasticity, hours_per_shift)

                assignment = ShiftAssignment(
                    week_plan=week_plan,
                    date=day,
                    employee=employee,
                    shift_template=shift_template,
                    assigned_hours=assigned_hours,
                    is_day_off=False
                )
                assignments.append(assignment)

                employee_hours[employee.id] = current_hours + assigned_hours
                processed_today.add(employee.id)
                assigned_count += 1

                # Registrar alerta de uso de elasticidad
                self.alerts.append({
                    'type': 'INFO',
                    'severity': 'LOW',
                    'title': f'Elasticidad usada: {employee.full_name}',
                    'message': f'Asignado turno tarde el {day} usando horas extra ({assigned_hours}h)',
                })

        return assignments

    def _assign_day_shifts_for_day(
        self,
        day: date,
        persons_needed: int,
        available_employees: List[Employee],
        week_plan: WeekPlan,
        employee_hours: Dict[int, Decimal],
        processed_today: set
    ) -> List[ShiftAssignment]:
        """
        Asigna turnos de día para un día específico.
        """
        assignments = []
        assigned_count = 0

        for employee in available_employees:
            if assigned_count >= persons_needed:
                break

            if employee.id in processed_today:
                continue

            # Verificar si ya cumplió sus horas semanales
            current_hours = employee_hours.get(employee.id, Decimal('0'))
            if current_hours >= employee.weekly_hours_target:
                continue

            # Obtener plantilla de turno DAY
            shift_template = self._get_shift_template_for_block(employee, 'DAY')
            if not shift_template:
                continue

            hours_per_shift = Decimal(str(shift_template.total_hours))
            remaining = employee.weekly_hours_target - current_hours
            assigned_hours = min(remaining, hours_per_shift)

            assignment = ShiftAssignment(
                week_plan=week_plan,
                date=day,
                employee=employee,
                shift_template=shift_template,
                assigned_hours=assigned_hours,
                is_day_off=False
            )
            assignments.append(assignment)

            # Actualizar tracking
            employee_hours[employee.id] = current_hours + assigned_hours
            processed_today.add(employee.id)
            assigned_count += 1

        return assignments

    @transaction.atomic
    def generate_week_plan(
        self,
        week_start: date,
        created_by: str = ''
    ) -> WeekPlan:
        """
        Genera un plan semanal completo.

        Estrategia de asignación:
        1. Calcular necesidades de personal por día (usando ForecastLoader)
        2. Asignar empleados EVENING primero (para cubrir couvertures)
        3. Luego asignar empleados DAY
        4. Verificar balance y generar alertas

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

        # Calcular necesidades de personal por día
        staffing_needs = self._calculate_daily_staffing_needs(week_start, week_load)

        # Crear plan
        week_plan = WeekPlan.objects.create(
            week_start_date=week_start,
            name=f"Semana {week_start.strftime('%d/%m/%Y')}",
            status='DRAFT',
            created_by=created_by
        )

        # Obtener empleados por capacidad de turno
        employees_by_shift = self._get_employees_by_shift_capability()

        # Pool de empleados para cada turno
        # EVENING: empleados que solo pueden hacer tarde + los que pueden hacer ambos
        # DAY: empleados que solo pueden hacer día + los que pueden hacer ambos (si no están asignados a tarde)
        evening_pool = employees_by_shift['EVENING'] + employees_by_shift['BOTH']
        day_pool = employees_by_shift['DAY'] + employees_by_shift['BOTH']

        # Tracking de horas asignadas por empleado
        employee_hours: Dict[int, Decimal] = defaultdict(Decimal)

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
                # Track hours for team members
                if assignment.employee:
                    employee_hours[assignment.employee.id] += assignment.assigned_hours

            # Marcar miembros como procesados (para toda la semana)
            for member in team.members.all():
                processed_employees.add(member.id)

        # Filtrar pools para excluir empleados en equipos
        evening_pool = [e for e in evening_pool if e.id not in processed_employees]
        day_pool = [e for e in day_pool if e.id not in processed_employees]

        # Procesar cada día de la semana
        week_days = self._get_week_days(week_start)

        for day in week_days:
            day_key = day.isoformat()
            processed_today = set()

            # Obtener necesidades del día
            day_needs = staffing_needs.get(day_key, {'day': 0, 'evening': 0})
            evening_needed = day_needs['evening']
            day_needed = day_needs['day']

            # 1. Primero asignar EVENING (para couvertures)
            if evening_needed > 0:
                evening_assignments = self._assign_evening_shifts_for_day(
                    day, evening_needed, evening_pool,
                    week_plan, employee_hours, processed_today
                )
                for assignment in evening_assignments:
                    assignment.save()

                # Verificar si se cubrieron las necesidades
                if len(evening_assignments) < evening_needed:
                    deficit = evening_needed - len(evening_assignments)
                    self.alerts.append({
                        'type': 'UNDERSTAFF',
                        'severity': 'HIGH',
                        'title': f'Faltan {deficit} persona(s) para turno tarde',
                        'message': f'El día {day} necesita {evening_needed} personas para couvertures, solo hay {len(evening_assignments)} disponibles',
                    })

            # 2. Luego asignar DAY
            if day_needed > 0:
                day_assignments = self._assign_day_shifts_for_day(
                    day, day_needed, day_pool,
                    week_plan, employee_hours, processed_today
                )
                for assignment in day_assignments:
                    assignment.save()

                # Verificar si se cubrieron las necesidades
                if len(day_assignments) < day_needed:
                    deficit = day_needed - len(day_assignments)
                    self.alerts.append({
                        'type': 'UNDERSTAFF',
                        'severity': 'MEDIUM',
                        'title': f'Faltan {deficit} persona(s) para turno día',
                        'message': f'El día {day} necesita {day_needed} personas para turno día, solo hay {len(day_assignments)} disponibles',
                    })

        # Verificar empleados con horas no cumplidas
        for employee in evening_pool + day_pool:
            if employee.id in processed_employees:
                continue
            assigned = employee_hours.get(employee.id, Decimal('0'))
            if assigned < employee.weekly_hours_target:
                deficit = employee.weekly_hours_target - assigned
                self.alerts.append({
                    'type': 'WARNING',
                    'severity': 'LOW',
                    'title': f'Déficit de horas para {employee.full_name}',
                    'message': f'Asignadas {assigned}h de {employee.weekly_hours_target}h objetivo (faltan {deficit}h)',
                })

        # Crear alertas en BD
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
