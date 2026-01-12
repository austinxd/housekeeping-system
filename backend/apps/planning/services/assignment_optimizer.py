"""
Assignment Optimizer Service.
Calcula y optimiza las asignaciones de personal basándose en la carga de trabajo real.

PRIORIDAD DE ASIGNACIÓN:
1. Trabajadores con horas semanales disponibles (no cumplen sus 39h)
2. Solo usar elasticidad si NO hay trabajadores disponibles
"""
from datetime import date, timedelta
from typing import Dict, List, Any, Tuple, Set
from decimal import Decimal

from django.db import transaction

from apps.core.models import TimeBlock, TaskType
from apps.staff.models import Employee, Team
from apps.shifts.models import ShiftTemplate
from apps.planning.models import WeekPlan, ShiftAssignment
from apps.planning.services.forecast_loader import ForecastLoader
from apps.planning.services.daily_distribution import DailyDistributionCalculator


class AssignmentOptimizer:
    """
    Optimiza las asignaciones de personal para minimizar tiempo libre
    mientras asegura cobertura completa.

    PRIORIDAD:
    1. Usar trabajadores con horas disponibles (< 39h semanales)
    2. Solo elasticidad cuando no hay trabajadores disponibles
    """

    def __init__(self):
        self.forecast_loader = ForecastLoader()
        self.distribution_calc = DailyDistributionCalculator()
        self._load_config()

    def _load_config(self):
        """Carga configuración desde BD."""
        # Configuración de turnos
        self.day_block = TimeBlock.objects.filter(code='DAY').first()
        self.evening_block = TimeBlock.objects.filter(code='EVENING').first()

        # Horas por turno desde ShiftTemplate
        day_template = ShiftTemplate.objects.filter(code='FDC_MANANA').first()
        evening_template = ShiftTemplate.objects.filter(code='FDC_TARDE').first()
        day_short_template = ShiftTemplate.objects.filter(code='FDC_MANANA_CORTO').first()

        self.day_shift_hours = day_template.total_hours if day_template else 8.0
        self.evening_shift_hours = evening_template.total_hours if evening_template else 8.0
        self.short_shift_hours = day_short_template.total_hours if day_short_template else 7.0

        # Empleados disponibles con sus restricciones
        self.employees = list(Employee.objects.filter(
            role__code__in=['FDC', 'VDC'],
            is_active=True
        ).select_related('role').prefetch_related('allowed_blocks', 'fixed_days_off').order_by('last_name'))

        self.fdc_employees = [e for e in self.employees if e.role.code == 'FDC']
        self.vdc_employees = [e for e in self.employees if e.role.code == 'VDC']

        # Cache de restricciones por empleado
        self.employee_allowed_blocks = {}
        self.employee_days_off = {}
        for emp in self.employees:
            self.employee_allowed_blocks[emp.id] = set(emp.allowed_blocks.values_list('code', flat=True))
            # Convertir códigos de día a iso_weekday (1=Lun, 7=Dom)
            days_off_codes = list(emp.fixed_days_off.values_list('iso_weekday', flat=True))
            self.employee_days_off[emp.id] = set(days_off_codes)

        # Parejas FIXED (deben trabajar siempre juntas)
        self.teams = list(Team.objects.filter(is_active=True, team_type='FIXED').prefetch_related('members'))
        self.employee_team = {}
        self.fixed_pairs = []  # Lista de tuplas (emp1_id, emp2_id)
        for team in self.teams:
            members = list(team.members.all())
            if len(members) == 2:
                self.fixed_pairs.append((members[0].id, members[1].id))
            for member in members:
                self.employee_team[member.id] = team

        # Shift templates (normales y cortos)
        self.shifts = {
            'FDC_MANANA': ShiftTemplate.objects.filter(code='FDC_MANANA').first(),
            'FDC_TARDE': ShiftTemplate.objects.filter(code='FDC_TARDE').first(),
            'VDC_MANANA': ShiftTemplate.objects.filter(code='VDC_MANANA').first(),
            'VDC_TARDE': ShiftTemplate.objects.filter(code='VDC_TARDE').first(),
            'FDC_MANANA_CORTO': ShiftTemplate.objects.filter(code='FDC_MANANA_CORTO').first(),
            'FDC_TARDE_CORTO': ShiftTemplate.objects.filter(code='FDC_TARDE_CORTO').first(),
            'VDC_MANANA_CORTO': ShiftTemplate.objects.filter(code='VDC_MANANA_CORTO').first(),
            'VDC_TARDE_CORTO': ShiftTemplate.objects.filter(code='VDC_TARDE_CORTO').first(),
        }

    def can_employee_work_shift(self, emp_id: int, shift_type: str) -> bool:
        """Verifica si un empleado puede trabajar en un turno según sus allowed_blocks."""
        allowed = self.employee_allowed_blocks.get(emp_id, set())
        if shift_type == 'morning':
            return 'DAY' in allowed
        else:  # evening
            return 'EVENING' in allowed

    def is_employee_day_off(self, emp_id: int, day_date: date) -> bool:
        """Verifica si es un día libre fijo para el empleado."""
        days_off = self.employee_days_off.get(emp_id, set())
        # iso_weekday: 1=Lunes, 7=Domingo
        return day_date.isoweekday() in days_off

    def get_partner_id(self, emp_id: int) -> int:
        """Obtiene el ID del compañero de pareja FIXED, o None si no tiene."""
        for pair in self.fixed_pairs:
            if pair[0] == emp_id:
                return pair[1]
            if pair[1] == emp_id:
                return pair[0]
        return None

    def calculate_consecutive_days_off(
        self,
        week_start: date,
        day_workloads: List[Dict],
        employee_state: Dict[int, Dict]
    ) -> Dict[int, Set[str]]:
        """
        Calcula los días libres CONSECUTIVOS óptimos para cada empleado.

        - Si tiene fixed_days_off configurados → usar esos
        - Si no tiene → elegir los 2 días consecutivos con menor carga
        - Parejas FIXED deben tener los mismos días libres

        Returns:
            Dict[emp_id] -> Set de day_keys que son días libres
        """
        # Pares de días consecutivos posibles (iso_weekday)
        # Solo días que son realmente consecutivos en la semana Lun-Dom
        consecutive_pairs = [
            (1, 2),  # Lun-Mar
            (2, 3),  # Mar-Mié
            (3, 4),  # Mié-Jue
            (4, 5),  # Jue-Vie
            (5, 6),  # Vie-Sáb
            (6, 7),  # Sáb-Dom
        ]

        # Mapear day_idx a iso_weekday y day_key
        day_info_map = {}  # iso_weekday -> day_info
        for day_info in day_workloads:
            iso_wd = day_info['date'].isoweekday()
            day_info_map[iso_wd] = day_info

        # Calcular carga total por par de días consecutivos
        pair_workloads = []
        for pair in consecutive_pairs:
            d1, d2 = pair
            workload1 = day_info_map.get(d1, {}).get('workload', 0)
            workload2 = day_info_map.get(d2, {}).get('workload', 0)
            total_workload = workload1 + workload2
            pair_workloads.append({
                'pair': pair,
                'workload': total_workload,
            })

        # Ordenar pares por carga (menor primero = mejores días para descanso)
        pair_workloads.sort(key=lambda x: x['workload'])

        # Contar cuántos empleados ya tienen asignado cada par
        pair_usage = {pair['pair']: 0 for pair in pair_workloads}

        # Resultado
        employee_days_off_calculated = {}

        # Procesar parejas FIXED primero (deben tener los mismos días libres)
        processed_ids = set()

        for pair in self.fixed_pairs:
            emp1_id, emp2_id = pair
            if emp1_id not in employee_state or emp2_id not in employee_state:
                continue

            # Verificar si alguno tiene días libres fijos
            fixed1 = self.employee_days_off.get(emp1_id, set())
            fixed2 = self.employee_days_off.get(emp2_id, set())

            # Combinar restricciones de días libres
            combined_fixed = fixed1 | fixed2

            if len(combined_fixed) >= 2:
                # Usar los días fijos (asumiendo que son consecutivos o lo más cercano)
                days_off_keys = set()
                for day_info in day_workloads:
                    if day_info['date'].isoweekday() in combined_fixed:
                        days_off_keys.add(day_info['day_key'])
                employee_days_off_calculated[emp1_id] = days_off_keys
                employee_days_off_calculated[emp2_id] = days_off_keys
            else:
                # Elegir el mejor par de días consecutivos disponible
                best_pair = None
                for pw in pair_workloads:
                    p = pw['pair']
                    # Verificar que ambos empleados puedan tener esos días libres
                    # (no conflicta con días que DEBEN trabajar)
                    can_use = True
                    # Por ahora, elegir el par con menor uso
                    if best_pair is None or pair_usage[p] < pair_usage.get(best_pair, 999):
                        best_pair = p

                if best_pair:
                    days_off_keys = set()
                    for day_info in day_workloads:
                        if day_info['date'].isoweekday() in best_pair:
                            days_off_keys.add(day_info['day_key'])
                    employee_days_off_calculated[emp1_id] = days_off_keys
                    employee_days_off_calculated[emp2_id] = days_off_keys
                    pair_usage[best_pair] += 2  # Dos empleados usan este par

            processed_ids.add(emp1_id)
            processed_ids.add(emp2_id)

        # Procesar empleados sin pareja
        for emp_id, state in employee_state.items():
            if emp_id in processed_ids:
                continue

            # Verificar si tiene días libres fijos
            fixed_days = self.employee_days_off.get(emp_id, set())

            if len(fixed_days) >= 2:
                # Usar sus días fijos
                days_off_keys = set()
                for day_info in day_workloads:
                    if day_info['date'].isoweekday() in fixed_days:
                        days_off_keys.add(day_info['day_key'])
                employee_days_off_calculated[emp_id] = days_off_keys
            else:
                # Elegir el mejor par de días consecutivos
                # Balancear: días con menos carga + menos usado por otros
                best_pair = None
                best_score = 999999

                for pw in pair_workloads:
                    p = pw['pair']
                    # Score = carga del par + (uso * 1000) para balancear
                    score = pw['workload'] + (pair_usage[p] * 500)
                    if score < best_score:
                        best_score = score
                        best_pair = p

                if best_pair:
                    days_off_keys = set()
                    for day_info in day_workloads:
                        if day_info['date'].isoweekday() in best_pair:
                            days_off_keys.add(day_info['day_key'])
                    employee_days_off_calculated[emp_id] = days_off_keys
                    pair_usage[best_pair] += 1

            processed_ids.add(emp_id)

        return employee_days_off_calculated

    def get_employee_weekly_availability(self, week_plan: WeekPlan) -> Dict[int, Dict]:
        """
        Calcula horas disponibles por empleado para la semana.

        Returns:
            Dict con employee_id -> {
                'target': horas objetivo semanal,
                'assigned': horas ya asignadas,
                'available': horas restantes disponibles,
                'days_assigned': set de días ya asignados
            }
        """
        availability = {}

        for emp in self.employees:
            target = float(emp.weekly_hours_target) if emp.weekly_hours_target else 39.0
            availability[emp.id] = {
                'employee': emp,
                'target': target,
                'assigned': 0.0,
                'available': target,
                'days_assigned': set(),
                'shifts_by_day': {},  # day_key -> 'morning' | 'evening'
            }

        # Calcular horas ya asignadas
        for assignment in week_plan.shift_assignments.select_related('employee', 'shift_template'):
            emp_id = assignment.employee_id
            if emp_id in availability:
                hours = float(assignment.assigned_hours or 8)
                availability[emp_id]['assigned'] += hours
                availability[emp_id]['available'] = max(0, availability[emp_id]['target'] - availability[emp_id]['assigned'])

                day_key = assignment.date.isoformat()
                availability[emp_id]['days_assigned'].add(day_key)

                is_morning = 'MANANA' in (assignment.shift_template.code if assignment.shift_template else '')
                availability[emp_id]['shifts_by_day'][day_key] = 'morning' if is_morning else 'evening'

        return availability

    def get_available_employees_for_day(
        self,
        day_key: str,
        shift: str,  # 'morning' | 'evening'
        availability: Dict[int, Dict],
        exclude_ids: Set[int] = None
    ) -> List[Employee]:
        """
        Obtiene empleados disponibles para un día específico.

        Prioridad:
        1. Empleados con horas restantes que no trabajan ese día
        2. Ordenados por horas restantes (más horas = más prioridad)
        """
        exclude_ids = exclude_ids or set()

        available = []
        for emp_id, info in availability.items():
            if emp_id in exclude_ids:
                continue

            # Solo considerar si tiene horas disponibles
            if info['available'] < self.day_shift_hours:
                continue

            # No puede trabajar dos turnos el mismo día
            if day_key in info['days_assigned']:
                continue

            available.append((info['employee'], info['available']))

        # Ordenar por horas disponibles (más horas = asignar primero)
        available.sort(key=lambda x: -x[1])

        return [emp for emp, _ in available]

    def calculate_daily_needs(self, week_plan: WeekPlan) -> Dict[str, Dict]:
        """
        Calcula las necesidades reales de personal por día.
        Usa datos de forecast_data del week_plan.
        """
        daily_needs = {}
        week_start = week_plan.week_start_date
        forecast_data = week_plan.forecast_data or []

        # Indexar forecast por fecha
        forecast_by_date = {}
        for fc in forecast_data:
            fc_date = fc.get('date')
            if fc_date:
                forecast_by_date[fc_date] = fc

        # Tiempos desde config
        depart_config = self.distribution_calc.task_config.get('DEPART', {})
        recouch_config = self.distribution_calc.task_config.get('RECOUCH', {})
        couv_config = self.distribution_calc.task_config.get('COUVERTURE', {})

        DEPART_MIN = depart_config.get('base_minutes', 50)
        RECOUCH_MIN = recouch_config.get('base_minutes', 20)
        COUV_MIN = couv_config.get('base_minutes', 15)

        # Períodos disponibles (calculados dinámicamente desde ShiftTemplates)
        P1_MIN = self.distribution_calc.P1_MIN
        P2_MIN = self.distribution_calc.P2_MIN
        P3_MIN = self.distribution_calc.P3_MIN
        COUV_MIN_PERIOD = self.distribution_calc.couv_period_min

        for day_offset in range(7):
            current_date = week_start + timedelta(days=day_offset)
            day_key = current_date.isoformat()

            # Obtener forecast del día
            fc = forecast_by_date.get(day_key, {})

            if not fc:
                daily_needs[day_key] = {
                    'date': current_date,
                    'morning_persons': 2,
                    'evening_persons': 2,
                    'total_persons': 4,
                    'room_work_min': 0,
                    'couv_work_min': 0,
                }
                continue

            # Calcular carga de trabajo
            departs = fc.get('departures', 0)
            arrivals = fc.get('arrivals', 0)
            occupied = fc.get('occupied_rooms', fc.get('occupied', 0))
            stays = max(0, occupied - arrivals)
            recouch = stays  # Solo stays, no arrivals
            couvertures = occupied

            # Trabajo total en minutos
            room_work_min = (departs * DEPART_MIN) + (recouch * RECOUCH_MIN)
            couv_work_min = couvertures * COUV_MIN

            # REGLA DE NEGOCIO para personas tarde (couvertures):
            # > 38 couvertures → 4 personas
            # > 25 couvertures → 3 personas
            # > 13 couvertures → 2 personas
            # 1-13 couvertures → 1 persona
            # 0 couvertures → 0 personas
            if couvertures > 38:
                evening_persons_for_couv = 4
            elif couvertures > 25:
                evening_persons_for_couv = 3
            elif couvertures > 13:
                evening_persons_for_couv = 2
            elif couvertures > 0:
                evening_persons_for_couv = 1
            else:
                evening_persons_for_couv = 0

            # Tiempo que tarde ayuda con habitaciones (P2 + P3)
            evening_help_min = evening_persons_for_couv * (P2_MIN + P3_MIN)

            # Trabajo restante para turno mañana
            remaining_room_work = max(0, room_work_min - evening_help_min)

            # Capacidad de una persona mañana (P1 + P2)
            morning_capacity_per_person = P1_MIN + P2_MIN

            # Personas de mañana necesarias
            if remaining_room_work > 0 and morning_capacity_per_person > 0:
                morning_persons = max(2, -(-remaining_room_work // morning_capacity_per_person))
            else:
                morning_persons = 2  # Mínimo para parejas

            daily_needs[day_key] = {
                'date': current_date,
                'morning_persons': morning_persons,
                'evening_persons': evening_persons_for_couv,
                'total_persons': morning_persons + evening_persons_for_couv,
                'room_work_min': room_work_min,
                'couv_work_min': couv_work_min,
                'departs': departs,
                'recouch': recouch,
                'couvertures': couvertures,
                'morning_capacity_per_person': morning_capacity_per_person,
                'evening_help_per_person': P2_MIN + P3_MIN,
            }

        return daily_needs

    def optimize_assignments(self, week_plan: WeekPlan) -> Dict[str, Any]:
        """
        Optimiza las asignaciones del plan semanal.

        PRIORIDAD:
        1. Si hay déficit de trabajo → agregar trabajadores con horas disponibles
        2. Solo usar elasticidad si NO hay trabajadores con horas disponibles
        3. Si hay exceso de personal → remover los que tienen más horas asignadas
        """
        daily_needs = self.calculate_daily_needs(week_plan)

        # Obtener disponibilidad de empleados
        availability = self.get_employee_weekly_availability(week_plan)

        # Obtener asignaciones actuales
        current_assignments = list(week_plan.shift_assignments.select_related(
            'employee', 'shift_template'
        ).order_by('date', 'employee__last_name'))

        # Agrupar por día y turno
        by_day = {}
        for assignment in current_assignments:
            day_key = assignment.date.isoformat()
            if day_key not in by_day:
                by_day[day_key] = {'morning': [], 'evening': []}

            is_morning = 'MANANA' in (assignment.shift_template.code if assignment.shift_template else '')
            shift_key = 'morning' if is_morning else 'evening'
            by_day[day_key][shift_key].append(assignment)

        changes = {
            'removed': [],
            'added': [],
            'kept': [],
            'summary': {},
            'workers_with_available_hours': [],
            'elasticity_used': False,
        }

        # Identificar trabajadores con horas disponibles
        for emp_id, info in availability.items():
            if info['available'] >= self.day_shift_hours:
                changes['workers_with_available_hours'].append({
                    'employee': info['employee'].first_name,
                    'available_hours': info['available'],
                    'assigned_hours': info['assigned'],
                    'target_hours': info['target'],
                })

        with transaction.atomic():
            for day_key, needs in daily_needs.items():
                day_assignments = by_day.get(day_key, {'morning': [], 'evening': []})
                current_date = needs['date']

                morning_needed = needs['morning_persons']
                evening_needed = needs['evening_persons']

                morning_current = day_assignments['morning']
                evening_current = day_assignments['evening']

                # === TURNO MAÑANA ===
                morning_count = len(morning_current)

                if morning_count < morning_needed:
                    # DÉFICIT: Necesitamos más personas
                    # PRIORIDAD 1: Agregar trabajadores con horas disponibles
                    assigned_ids = {a.employee_id for a in morning_current}
                    available_employees = self.get_available_employees_for_day(
                        day_key, 'morning', availability, assigned_ids
                    )

                    # Preferir FDC para mañana
                    fdc_available = [e for e in available_employees if e.role.code == 'FDC']
                    vdc_available = [e for e in available_employees if e.role.code == 'VDC']
                    sorted_available = fdc_available + vdc_available

                    to_add = morning_needed - morning_count
                    added_count = 0

                    for emp in sorted_available:
                        if added_count >= to_add:
                            break

                        # Crear asignación
                        shift_template = self.shifts.get(f'{emp.role.code}_MANANA')
                        if shift_template:
                            ShiftAssignment.objects.create(
                                week_plan=week_plan,
                                date=current_date,
                                employee=emp,
                                shift_template=shift_template,
                                assigned_hours=self.day_shift_hours,
                                is_day_off=False
                            )
                            changes['added'].append({
                                'date': day_key,
                                'employee': emp.first_name,
                                'shift': 'mañana',
                                'reason': 'horas_disponibles',
                            })

                            # Actualizar disponibilidad
                            availability[emp.id]['assigned'] += self.day_shift_hours
                            availability[emp.id]['available'] -= self.day_shift_hours
                            availability[emp.id]['days_assigned'].add(day_key)

                            added_count += 1

                    morning_count += added_count

                elif morning_count > morning_needed:
                    # EXCESO: Remover personal (priorizar mantener parejas)
                    morning_sorted = sorted(
                        morning_current,
                        key=lambda a: (
                            0 if a.employee_id in self.employee_team else 1,
                            -availability.get(a.employee_id, {}).get('available', 0),
                            a.employee.last_name
                        )
                    )
                    for assignment in morning_sorted[morning_needed:]:
                        changes['removed'].append({
                            'date': day_key,
                            'employee': assignment.employee.first_name,
                            'shift': 'mañana',
                        })
                        # Devolver horas al empleado
                        emp_id = assignment.employee_id
                        if emp_id in availability:
                            hours = float(assignment.assigned_hours or self.day_shift_hours)
                            availability[emp_id]['assigned'] -= hours
                            availability[emp_id]['available'] += hours
                            availability[emp_id]['days_assigned'].discard(day_key)
                        assignment.delete()

                # === TURNO TARDE ===
                evening_count = len(evening_current)

                if evening_count < evening_needed:
                    # DÉFICIT: Agregar trabajadores con horas disponibles
                    assigned_ids = {a.employee_id for a in evening_current}
                    # También excluir los que trabajan mañana ese día
                    for a in morning_current:
                        assigned_ids.add(a.employee_id)

                    available_employees = self.get_available_employees_for_day(
                        day_key, 'evening', availability, assigned_ids
                    )

                    # Preferir VDC para tarde
                    vdc_available = [e for e in available_employees if e.role.code == 'VDC']
                    fdc_available = [e for e in available_employees if e.role.code == 'FDC']
                    sorted_available = vdc_available + fdc_available

                    to_add = evening_needed - evening_count
                    added_count = 0

                    for emp in sorted_available:
                        if added_count >= to_add:
                            break

                        shift_template = self.shifts.get(f'{emp.role.code}_TARDE')
                        if shift_template:
                            ShiftAssignment.objects.create(
                                week_plan=week_plan,
                                date=current_date,
                                employee=emp,
                                shift_template=shift_template,
                                assigned_hours=self.evening_shift_hours,
                                is_day_off=False
                            )
                            changes['added'].append({
                                'date': day_key,
                                'employee': emp.first_name,
                                'shift': 'tarde',
                                'reason': 'horas_disponibles',
                            })

                            availability[emp.id]['assigned'] += self.evening_shift_hours
                            availability[emp.id]['available'] -= self.evening_shift_hours
                            availability[emp.id]['days_assigned'].add(day_key)

                            added_count += 1

                    evening_count += added_count

                elif evening_count > evening_needed:
                    # EXCESO: Remover personal
                    evening_sorted = sorted(
                        evening_current,
                        key=lambda a: (
                            0 if a.employee_id in self.employee_team else 1,
                            -availability.get(a.employee_id, {}).get('available', 0),
                            a.employee.last_name
                        )
                    )
                    for assignment in evening_sorted[evening_needed:]:
                        changes['removed'].append({
                            'date': day_key,
                            'employee': assignment.employee.first_name,
                            'shift': 'tarde',
                        })
                        emp_id = assignment.employee_id
                        if emp_id in availability:
                            hours = float(assignment.assigned_hours or self.evening_shift_hours)
                            availability[emp_id]['assigned'] -= hours
                            availability[emp_id]['available'] += hours
                            availability[emp_id]['days_assigned'].discard(day_key)
                        assignment.delete()

                changes['summary'][day_key] = {
                    'needed': {'morning': morning_needed, 'evening': evening_needed},
                    'after': {
                        'morning': morning_count,
                        'evening': evening_count,
                    },
                    'deficit': {
                        'morning': max(0, morning_needed - morning_count),
                        'evening': max(0, evening_needed - evening_count),
                    },
                }

        # Resumen final de disponibilidad
        changes['final_availability'] = []
        for emp_id, info in availability.items():
            if info['available'] > 0:
                changes['final_availability'].append({
                    'employee': info['employee'].first_name,
                    'available_hours': info['available'],
                    'assigned_hours': info['assigned'],
                })

        return changes

    def generate_optimal_assignments(
        self,
        week_plan: WeekPlan,
        forecast_data: List[Dict]
    ) -> Dict[str, Any]:
        """
        Genera asignaciones óptimas garantizando horas contratadas semanales.

        PRINCIPIOS:
        1. Cada empleado DEBE cumplir sus horas contratadas semanales (ej: 39h)
        2. Respetar restricciones: allowed_blocks, fixed_days_off
        3. Parejas FIXED deben trabajar siempre juntas
        4. Usar turno corto (7h) para el último día si es necesario para llegar exacto
        5. Solo usar elasticidad si TODOS están al 100% de sus horas
        """
        # Eliminar asignaciones existentes
        week_plan.shift_assignments.all().delete()

        week_start = week_plan.week_start_date
        week_days = [week_start + timedelta(days=i) for i in range(7)]
        day_names = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']

        # Calcular necesidades por día basado en CARGA DE TRABAJO
        daily_needs = self.calculate_daily_needs(week_plan)

        # Calcular carga de trabajo por día
        day_workloads = []
        for day_offset in range(7):
            day_key = (week_start + timedelta(days=day_offset)).isoformat()
            needs = daily_needs.get(day_key, {})
            workload = needs.get('room_work_min', 0) + needs.get('couv_work_min', 0)

            day_workloads.append({
                'day_idx': day_offset,
                'date': week_days[day_offset],
                'day_key': day_key,
                'workload': workload,
                'morning_needed': needs.get('morning_persons', 2),
                'evening_needed': needs.get('evening_persons', 2),
            })

        # Ordenar días por carga de trabajo (mayor primero)
        days_by_workload = sorted(day_workloads, key=lambda x: -x['workload'])

        # Estado de cada empleado
        employee_state = {}
        for emp in self.employees:
            target = float(emp.weekly_hours_target) if emp.weekly_hours_target else 39.0
            employee_state[emp.id] = {
                'employee': emp,
                'target_hours': target,
                'assigned_hours': 0.0,
                'days_assigned': set(),
                'role': emp.role.code,
            }

        # ========== CALCULAR DÍAS LIBRES CONSECUTIVOS ==========
        # Cada empleado debe tener 2 días libres consecutivos
        employee_days_off = self.calculate_consecutive_days_off(
            week_start, day_workloads, employee_state
        )

        # Helper para verificar si es día libre
        def is_day_off(emp_id: int, day_key: str) -> bool:
            return day_key in employee_days_off.get(emp_id, set())

        # Reiniciar employee_state (el anterior era temporal para calcular días libres)
        employee_state = {}
        for emp in self.employees:
            target = float(emp.weekly_hours_target) if emp.weekly_hours_target else 39.0
            employee_state[emp.id] = {
                'employee': emp,
                'target_hours': target,
                'assigned_hours': 0.0,
                'days_assigned': set(),
                'role': emp.role.code,
            }

        assignments_created = []
        assignments_by_day = {d['day_key']: {'morning': [], 'evening': []} for d in day_workloads}

        # ========== PASO 1: Asignar PAREJAS FIXED primero ==========
        # Las parejas deben trabajar juntas, priorizando días con más carga

        for pair in self.fixed_pairs:
            emp1_id, emp2_id = pair
            state1 = employee_state.get(emp1_id)
            state2 = employee_state.get(emp2_id)

            if not state1 or not state2:
                continue

            emp1 = state1['employee']
            emp2 = state2['employee']

            # Determinar en qué turno pueden trabajar AMBOS
            emp1_can_morning = self.can_employee_work_shift(emp1_id, 'morning')
            emp1_can_evening = self.can_employee_work_shift(emp1_id, 'evening')
            emp2_can_morning = self.can_employee_work_shift(emp2_id, 'morning')
            emp2_can_evening = self.can_employee_work_shift(emp2_id, 'evening')

            # La pareja solo puede trabajar donde AMBOS pueden
            pair_can_morning = emp1_can_morning and emp2_can_morning
            pair_can_evening = emp1_can_evening and emp2_can_evening

            # Calcular días necesarios para la pareja (usar el menor de los dos)
            target1 = state1['target_hours']
            target2 = state2['target_hours']
            # 4 días de 8h + 1 día de 7h = 39h
            days_of_8h = 4
            needs_short_day = (target1 == 39.0 or target2 == 39.0)

            # Asignar a días con más carga, respetando días libres
            days_assigned_pair = 0
            for day_info in days_by_workload:
                if days_assigned_pair >= 5:  # Ya asignamos 5 días
                    break

                day_date = day_info['date']
                day_key = day_info['day_key']
                day_idx = day_info['day_idx']

                # Verificar días libres de AMBOS (consecutivos calculados)
                if is_day_off(emp1_id, day_key):
                    continue
                if is_day_off(emp2_id, day_key):
                    continue

                # Ya asignados este día?
                if day_key in state1['days_assigned'] or day_key in state2['days_assigned']:
                    continue

                # Determinar turno (preferir mañana si pueden)
                if pair_can_morning:
                    shift_type = 'morning'
                    shift_suffix = 'MANANA'
                elif pair_can_evening:
                    shift_type = 'evening'
                    shift_suffix = 'TARDE'
                else:
                    continue  # No pueden trabajar juntos en ningún turno

                # Determinar si es turno corto (último día para llegar a 39h)
                is_short = (days_assigned_pair == 4 and needs_short_day)
                if is_short:
                    shift_suffix += '_CORTO'
                    hours = self.short_shift_hours
                else:
                    hours = self.day_shift_hours if shift_type == 'morning' else self.evening_shift_hours

                # Asignar ambos empleados de la pareja
                for emp in [emp1, emp2]:
                    shift_template = self.shifts.get(f'{emp.role.code}_{shift_suffix}')
                    if not shift_template:
                        shift_template = self.shifts.get(f'FDC_{shift_suffix}') or self.shifts.get(f'VDC_{shift_suffix}')

                    ShiftAssignment.objects.create(
                        week_plan=week_plan,
                        date=day_date,
                        employee=emp,
                        shift_template=shift_template,
                        assigned_hours=hours,
                        is_day_off=False
                    )

                    employee_state[emp.id]['assigned_hours'] += hours
                    employee_state[emp.id]['days_assigned'].add(day_key)
                    assignments_by_day[day_key][shift_type].append(emp.id)

                    assignments_created.append({
                        'day': day_names[day_idx],
                        'date': day_key,
                        'employee': emp.first_name,
                        'shift': 'mañana' if shift_type == 'morning' else 'tarde',
                        'hours': hours,
                        'is_pair': True,
                    })

                days_assigned_pair += 1

        # ========== PASO 2: Asignar empleados SIN pareja ==========
        # Ordenar por horas pendientes

        for day_info in days_by_workload:
            day_date = day_info['date']
            day_key = day_info['day_key']
            day_idx = day_info['day_idx']
            morning_needed = max(2, day_info['morning_needed'])
            evening_needed = max(2, day_info['evening_needed'])

            # Cuántos ya hay asignados
            morning_count = len(assignments_by_day[day_key]['morning'])
            evening_count = len(assignments_by_day[day_key]['evening'])

            # === TURNO MAÑANA ===
            if morning_count < morning_needed:
                morning_candidates = []
                for emp_id, state in employee_state.items():
                    # Saltar si ya cumplió sus horas
                    if state['assigned_hours'] >= state['target_hours']:
                        continue
                    # Saltar si ya trabaja este día
                    if day_key in state['days_assigned']:
                        continue
                    # Saltar si es día libre (consecutivo)
                    if is_day_off(emp_id, day_key):
                        continue
                    # Saltar si no puede trabajar mañana
                    if not self.can_employee_work_shift(emp_id, 'morning'):
                        continue
                    # Saltar si es parte de pareja FIXED (ya procesados)
                    if self.get_partner_id(emp_id) is not None:
                        continue

                    morning_candidates.append(state)

                # Ordenar: FDC primero, más horas pendientes primero
                morning_candidates.sort(key=lambda s: (
                    0 if s['role'] == 'FDC' else 1,
                    -(s['target_hours'] - s['assigned_hours']),
                ))

                to_assign = morning_needed - morning_count
                for state in morning_candidates[:to_assign]:
                    emp = state['employee']
                    emp_id = emp.id

                    # Determinar si es turno corto
                    remaining = state['target_hours'] - state['assigned_hours']
                    is_short = (remaining <= self.short_shift_hours + 0.5 and remaining < self.day_shift_hours)

                    if is_short:
                        shift_template = self.shifts.get(f'{emp.role.code}_MANANA_CORTO')
                        hours = self.short_shift_hours
                    else:
                        shift_template = self.shifts.get(f'{emp.role.code}_MANANA')
                        hours = self.day_shift_hours

                    if not shift_template:
                        shift_template = self.shifts.get('FDC_MANANA')
                        hours = self.day_shift_hours

                    ShiftAssignment.objects.create(
                        week_plan=week_plan,
                        date=day_date,
                        employee=emp,
                        shift_template=shift_template,
                        assigned_hours=hours,
                        is_day_off=False
                    )

                    state['assigned_hours'] += hours
                    state['days_assigned'].add(day_key)
                    assignments_by_day[day_key]['morning'].append(emp_id)

                    assignments_created.append({
                        'day': day_names[day_idx],
                        'date': day_key,
                        'employee': emp.first_name,
                        'shift': 'mañana',
                        'hours': hours,
                    })

            # === TURNO TARDE ===
            if evening_count < evening_needed:
                evening_candidates = []
                for emp_id, state in employee_state.items():
                    if state['assigned_hours'] >= state['target_hours']:
                        continue
                    if day_key in state['days_assigned']:
                        continue
                    if is_day_off(emp_id, day_key):
                        continue
                    if not self.can_employee_work_shift(emp_id, 'evening'):
                        continue
                    if self.get_partner_id(emp_id) is not None:
                        continue

                    evening_candidates.append(state)

                # VDC primero para tarde
                evening_candidates.sort(key=lambda s: (
                    0 if s['role'] == 'VDC' else 1,
                    -(s['target_hours'] - s['assigned_hours']),
                ))

                to_assign = evening_needed - evening_count
                for state in evening_candidates[:to_assign]:
                    emp = state['employee']
                    emp_id = emp.id

                    remaining = state['target_hours'] - state['assigned_hours']
                    is_short = (remaining <= self.short_shift_hours + 0.5 and remaining < self.evening_shift_hours)

                    if is_short:
                        shift_template = self.shifts.get(f'{emp.role.code}_TARDE_CORTO')
                        hours = self.short_shift_hours
                    else:
                        shift_template = self.shifts.get(f'{emp.role.code}_TARDE')
                        hours = self.evening_shift_hours

                    if not shift_template:
                        shift_template = self.shifts.get('VDC_TARDE')
                        hours = self.evening_shift_hours

                    ShiftAssignment.objects.create(
                        week_plan=week_plan,
                        date=day_date,
                        employee=emp,
                        shift_template=shift_template,
                        assigned_hours=hours,
                        is_day_off=False
                    )

                    state['assigned_hours'] += hours
                    state['days_assigned'].add(day_key)
                    assignments_by_day[day_key]['evening'].append(emp_id)

                    assignments_created.append({
                        'day': day_names[day_idx],
                        'date': day_key,
                        'employee': emp.first_name,
                        'shift': 'tarde',
                        'hours': hours,
                    })

        # ========== PASO 3: Completar horas de empleados que no llegaron ==========
        employees_needing_hours = [
            (emp_id, state) for emp_id, state in employee_state.items()
            if state['assigned_hours'] < state['target_hours']
        ]
        employees_needing_hours.sort(key=lambda x: -(x[1]['target_hours'] - x[1]['assigned_hours']))

        for emp_id, state in employees_needing_hours:
            emp = state['employee']

            while state['assigned_hours'] < state['target_hours']:
                remaining = state['target_hours'] - state['assigned_hours']
                if remaining < 1:  # Menos de 1h, ignorar
                    break

                # Buscar mejor día disponible
                best_day = None
                best_shift = None
                best_score = -999

                for day_info in days_by_workload:
                    day_date = day_info['date']
                    day_key = day_info['day_key']

                    if day_key in state['days_assigned']:
                        continue
                    if is_day_off(emp_id, day_key):
                        continue

                    # Verificar qué turnos puede hacer
                    can_morning = self.can_employee_work_shift(emp_id, 'morning')
                    can_evening = self.can_employee_work_shift(emp_id, 'evening')

                    morning_count = len(assignments_by_day[day_key]['morning'])
                    evening_count = len(assignments_by_day[day_key]['evening'])
                    morning_deficit = day_info['morning_needed'] - morning_count
                    evening_deficit = day_info['evening_needed'] - evening_count

                    # Calcular score para cada turno
                    if can_morning:
                        score = day_info['workload'] + (morning_deficit * 100)
                        if state['role'] == 'FDC':
                            score += 50
                        if score > best_score:
                            best_score = score
                            best_day = day_info
                            best_shift = 'morning'

                    if can_evening:
                        score = day_info['workload'] + (evening_deficit * 100)
                        if state['role'] == 'VDC':
                            score += 50
                        if score > best_score:
                            best_score = score
                            best_day = day_info
                            best_shift = 'evening'

                if not best_day:
                    break  # No hay más días disponibles

                day_date = best_day['date']
                day_key = best_day['day_key']
                day_idx = best_day['day_idx']

                # Determinar si turno corto
                is_short = (remaining <= self.short_shift_hours + 0.5)

                if best_shift == 'morning':
                    if is_short:
                        shift_template = self.shifts.get(f'{emp.role.code}_MANANA_CORTO')
                        hours = self.short_shift_hours
                    else:
                        shift_template = self.shifts.get(f'{emp.role.code}_MANANA')
                        hours = self.day_shift_hours
                else:
                    if is_short:
                        shift_template = self.shifts.get(f'{emp.role.code}_TARDE_CORTO')
                        hours = self.short_shift_hours
                    else:
                        shift_template = self.shifts.get(f'{emp.role.code}_TARDE')
                        hours = self.evening_shift_hours

                if not shift_template:
                    shift_template = self.shifts.get('FDC_MANANA')
                    hours = self.day_shift_hours

                ShiftAssignment.objects.create(
                    week_plan=week_plan,
                    date=day_date,
                    employee=emp,
                    shift_template=shift_template,
                    assigned_hours=hours,
                    is_day_off=False
                )

                state['assigned_hours'] += hours
                state['days_assigned'].add(day_key)
                assignments_by_day[day_key][best_shift].append(emp_id)

                assignments_created.append({
                    'day': day_names[day_idx],
                    'date': day_key,
                    'employee': emp.first_name,
                    'shift': 'mañana' if best_shift == 'morning' else 'tarde',
                    'hours': hours,
                    'reason': 'completar_horas',
                })

        # ========== RESUMEN ==========
        employee_summary = {}
        employees_at_target = 0
        employees_under_target = 0

        for emp_id, state in employee_state.items():
            emp_name = state['employee'].first_name
            employee_summary[emp_name] = {
                'target': state['target_hours'],
                'assigned': state['assigned_hours'],
                'remaining': max(0, state['target_hours'] - state['assigned_hours']),
                'days_worked': len(state['days_assigned']),
            }
            if state['assigned_hours'] >= state['target_hours']:
                employees_at_target += 1
            else:
                employees_under_target += 1

        return {
            'assignments': assignments_created,
            'employee_summary': employee_summary,
            'stats': {
                'employees_at_target': employees_at_target,
                'employees_under_target': employees_under_target,
                'total_employees': len(self.employees),
            },
            'daily_coverage': {
                day_key: {
                    'morning': len(assignments_by_day[day_key]['morning']),
                    'evening': len(assignments_by_day[day_key]['evening']),
                }
                for day_key in assignments_by_day
            },
        }
