"""
Daily Distribution Calculator Service.
Calcula la distribución del trabajo por períodos y parejas.
Todos los cálculos están centralizados aquí para evitar duplicación en el frontend.
"""
from typing import Dict, List, Any, Tuple
from apps.core.models import TaskType, TimeBlock
from apps.staff.models import Team


class DailyDistributionCalculator:
    """
    Calcula la distribución del trabajo diario por períodos.
    Maneja parejas configuradas vs temporales y calcula tiempo sobrante/déficit.
    """

    def __init__(self):
        self._load_task_config()
        self._load_shift_config()
        self._load_teams()

    def _load_task_config(self):
        """Carga configuración de tareas desde BD."""
        self.task_config = {}
        for task in TaskType.objects.all():
            self.task_config[task.code] = {
                'base_minutes': task.base_minutes,      # Tiempo con PAREJA
                'solo_minutes': getattr(task, 'solo_minutes', task.base_minutes),  # Tiempo con 1 persona
                'persons_required': task.persons_required,
                'earliest_start': task.earliest_start_time,
                'latest_end': task.latest_end_time,
            }

        # Valores por defecto si no existen
        if 'DEPART' not in self.task_config:
            self.task_config['DEPART'] = {'base_minutes': 50, 'solo_minutes': 75, 'persons_required': 2}
        if 'RECOUCH' not in self.task_config:
            self.task_config['RECOUCH'] = {'base_minutes': 20, 'solo_minutes': 30, 'persons_required': 2}
        if 'COUVERTURE' not in self.task_config:
            self.task_config['COUVERTURE'] = {'base_minutes': 15, 'solo_minutes': 15, 'persons_required': 1}

    def _load_shift_config(self):
        """Carga configuración de turnos desde BD y calcula períodos dinámicamente."""
        from apps.shifts.models import ShiftTemplate

        # Cargar ShiftTemplates de housekeeping (FDC/VDC)
        self.day_template = ShiftTemplate.objects.filter(
            code__in=['FDC_MANANA', 'VDC_MANANA'],
            is_active=True
        ).first()

        self.evening_template = ShiftTemplate.objects.filter(
            code__in=['FDC_TARDE', 'VDC_TARDE'],
            is_active=True
        ).first()

        # Valores por defecto si no hay templates
        if not self.day_template:
            self.day_start = '09:00'
            self.day_end = '17:30'
            self.day_break_start = '12:30'
            self.day_break_end = '13:30'
            self.day_break_min = 60
        else:
            self.day_start = self.day_template.start_time.strftime('%H:%M')
            self.day_end = self.day_template.end_time.strftime('%H:%M')
            self.day_break_start = self.day_template.break_start.strftime('%H:%M') if self.day_template.break_start else '12:30'
            self.day_break_end = self.day_template.break_end.strftime('%H:%M') if self.day_template.break_end else '13:30'
            self.day_break_min = self.day_template.break_minutes or 60

        if not self.evening_template:
            self.evening_start = '13:30'
            self.evening_end = '22:00'
            self.evening_break_start = '18:30'
            self.evening_break_end = '19:00'
            self.evening_break_min = 30
        else:
            self.evening_start = self.evening_template.start_time.strftime('%H:%M')
            self.evening_end = self.evening_template.end_time.strftime('%H:%M')
            self.evening_break_start = self.evening_template.break_start.strftime('%H:%M') if self.evening_template.break_start else '18:30'
            self.evening_break_end = self.evening_template.break_end.strftime('%H:%M') if self.evening_template.break_end else '19:00'
            self.evening_break_min = self.evening_template.break_minutes or 30

        # Calcular períodos dinámicamente
        # P1: Mañana sola (inicio turno día hasta break mañana)
        self.P1_START = self.day_start
        self.P1_END = self.day_break_start
        self.P1_MIN = self._time_to_minutes(self.P1_END) - self._time_to_minutes(self.P1_START)

        # Almuerzo mañana
        self.LUNCH_DAY_START = self.day_break_start
        self.LUNCH_DAY_END = self.day_break_end

        # P2: Mañana + Tarde juntos (después break mañana hasta fin turno día)
        p2_start_min = max(self._time_to_minutes(self.day_break_end), self._time_to_minutes(self.evening_start))
        p2_end_min = min(self._time_to_minutes(self.day_end), self._time_to_minutes(self.evening_break_start))
        self.P2_START = self._minutes_to_time(p2_start_min)
        self.P2_END = self._minutes_to_time(p2_end_min)
        self.P2_MIN = p2_end_min - p2_start_min

        # P3: Tarde sola antes de cena (fin turno día hasta break tarde)
        p3_start_min = self._time_to_minutes(self.day_end)
        p3_end_min = self._time_to_minutes(self.evening_break_start)
        self.P3_START = self._minutes_to_time(p3_start_min)
        self.P3_END = self._minutes_to_time(p3_end_min)
        self.P3_MIN = max(0, p3_end_min - p3_start_min)

        # Cena tarde
        self.LUNCH_EVENING_START = self.evening_break_start
        self.LUNCH_EVENING_END = self.evening_break_end

        # Couvertures: después de cena hasta fin turno tarde
        couv = self.task_config.get('COUVERTURE', {})
        couv_earliest = couv.get('earliest_start')

        # Usar el mayor entre: fin de cena o earliest_start de couverture
        if couv_earliest and hasattr(couv_earliest, 'strftime'):
            couv_start_from_task = couv_earliest.strftime('%H:%M')
            couv_start_min = max(self._time_to_minutes(self.evening_break_end), self._time_to_minutes(couv_start_from_task))
        else:
            couv_start_min = self._time_to_minutes(self.evening_break_end)

        self.couv_start = self._minutes_to_time(couv_start_min)
        self.couv_end = self.evening_end
        self.couv_period_min = self._time_to_minutes(self.couv_end) - couv_start_min

        # Config legacy para compatibilidad
        self.shift_config = {
            'DAY': {
                'start': self.day_start,
                'end': self.day_end,
                'break_start': self.day_break_start,
                'break_end': self.day_break_end,
                'break_minutes': self.day_break_min,
            },
            'EVENING': {
                'start': self.evening_start,
                'end': self.evening_end,
                'break_start': self.evening_break_start,
                'break_end': self.evening_break_end,
                'break_minutes': self.evening_break_min,
            },
        }

    def _load_teams(self):
        """Carga equipos configurados desde BD."""
        self.teams = []
        for team in Team.objects.filter(is_active=True).prefetch_related('members'):
            self.teams.append({
                'id': team.id,
                'name': team.name,
                'type': team.team_type,
                'member_ids': list(team.members.values_list('id', flat=True)),
            })

    def _time_to_minutes(self, time_str: str) -> int:
        """Convierte HH:MM a minutos desde medianoche."""
        if not time_str:
            return 0
        parts = time_str.split(':')
        return int(parts[0]) * 60 + int(parts[1])

    def _minutes_to_time(self, minutes: int) -> str:
        """Convierte minutos desde medianoche a HH:MM."""
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours:02d}:{mins:02d}"

    def _format_spare(self, minutes: int, num_workers: int = 1) -> Dict[str, Any]:
        """Formatea tiempo sobrante para mostrar (por persona y total)."""
        if minutes == 0:
            return {'value': 0, 'display': None, 'is_positive': True, 'per_person': 0, 'total': 0}

        abs_min = abs(minutes)
        sign = '+' if minutes > 0 else '-'
        is_positive = minutes >= 0

        # Tiempo por persona
        per_person_min = abs_min / num_workers if num_workers > 0 else abs_min

        # Formatear total
        if abs_min < 60:
            total_display = f"{sign}{abs_min}min"
        else:
            hours = abs_min / 60
            total_display = f"{sign}{hours:.1f}h"

        # Formatear por persona
        if per_person_min < 60:
            per_person_display = f"{sign}{int(per_person_min)}min/pers"
        else:
            per_person_hours = per_person_min / 60
            per_person_display = f"{sign}{per_person_hours:.1f}h/pers"

        # Display combinado
        if num_workers > 1:
            display = f"{per_person_display} ({total_display} total)"
        else:
            display = total_display

        return {
            'value': minutes,
            'display': display,
            'is_positive': is_positive,
            'per_person_min': round(per_person_min, 1),
            'total_min': abs_min,
            'num_workers': num_workers,
        }

    def distribute_work_to_units(
        self,
        pairs: List[Dict],
        solos: List[str],
        departs_to_do: int,
        recouches_to_do: int,
        period_minutes: int,
        depart_pair_min: int,
        depart_solo_min: int,
        recouch_pair_min: int,
        recouch_solo_min: int,
    ) -> Dict[str, Any]:
        """
        Distribuye trabajo BALANCEADO entre unidades.
        Cada unidad recibe una carga proporcional para equilibrar tiempo libre.
        """
        num_pairs = len(pairs)
        num_solos = len(solos)
        total_units = num_pairs + num_solos

        if total_units == 0:
            return {
                'units': [],
                'display': '',
                'total_departs': 0,
                'total_recouches': 0,
                'total_spare_min': 0,
                'departs_remaining': departs_to_do,
                'recouches_remaining': recouches_to_do,
            }

        # Calcular trabajo total en minutos (usando tiempo de pareja como referencia)
        total_work_min = (departs_to_do * depart_pair_min) + (recouches_to_do * recouch_pair_min)
        total_capacity_min = total_units * period_minutes

        # Si no hay trabajo, todos libres con tiempo completo
        if total_work_min == 0:
            units_work = []
            for pair in pairs:
                units_work.append({
                    'type': 'pair', 'display': pair.get('display', ''),
                    'names': pair.get('names', []), 'departs': 0, 'recouches': 0,
                    'spare_min': period_minutes,
                })
            for solo_name in solos:
                units_work.append({
                    'type': 'solo', 'display': solo_name,
                    'names': [solo_name], 'departs': 0, 'recouches': 0,
                    'spare_min': period_minutes,
                })
            # Formatear display con tiempo libre
            display_parts = []
            for u in units_work:
                spare_str = f"⏱️+{period_minutes // 60}h{period_minutes % 60}min" if period_minutes % 60 else f"⏱️+{period_minutes // 60}h"
                display_parts.append(f"{u['display']}:libre {spare_str}")
            return {
                'units': units_work,
                'display': ' · '.join(display_parts),
                'total_departs': 0, 'total_recouches': 0,
                'total_spare_min': total_capacity_min,
                'departs_remaining': 0, 'recouches_remaining': 0,
            }

        # Calcular cuota de trabajo por unidad (en minutos)
        work_quota_per_unit = total_work_min / total_units

        units_work = []
        departs_left = departs_to_do
        recouches_left = recouches_to_do

        # Distribuir a parejas (más eficientes)
        for pair in pairs:
            target_work_min = work_quota_per_unit
            unit_departs = 0
            unit_recouches = 0
            work_done_min = 0

            # Asignar departs primero (más prioritarios)
            if departs_left > 0 and depart_pair_min > 0:
                # Cuántos departs para alcanzar la cuota
                departs_for_quota = int(target_work_min / depart_pair_min)
                unit_departs = min(departs_left, departs_for_quota, period_minutes // depart_pair_min)
                work_done_min += unit_departs * depart_pair_min
                departs_left -= unit_departs

            # Completar con recouches hasta la cuota
            remaining_quota = target_work_min - work_done_min
            if recouches_left > 0 and recouch_pair_min > 0 and remaining_quota > 0:
                recouches_for_quota = int(remaining_quota / recouch_pair_min)
                max_capacity = (period_minutes - work_done_min) // recouch_pair_min
                unit_recouches = min(recouches_left, recouches_for_quota, max_capacity)
                work_done_min += unit_recouches * recouch_pair_min
                recouches_left -= unit_recouches

            spare_min = period_minutes - work_done_min
            units_work.append({
                'type': 'pair',
                'display': pair.get('display', ''),
                'names': pair.get('names', []),
                'ids': pair.get('ids', []),  # Track employee IDs for per-employee spare
                'shifts': pair.get('shifts', []),  # Track which shift each member belongs to
                'departs': unit_departs,
                'recouches': unit_recouches,
                'spare_min': max(0, spare_min),
            })

        # Distribuir a solos (menos eficientes, más tiempo por tarea)
        for solo_item in solos:
            # Handle both dict (with shift info) and string (legacy) formats
            if isinstance(solo_item, dict):
                solo_name = solo_item.get('name', solo_item.get('display', 'Anónimo'))
                solo_shift = solo_item.get('shift', 'unknown')
                solo_id = solo_item.get('id')
            else:
                solo_name = solo_item
                solo_shift = 'unknown'
                solo_id = None
            target_work_min = work_quota_per_unit
            unit_departs = 0
            unit_recouches = 0
            work_done_min = 0

            # Solo trabaja más lento, ajustar cuota al ratio de velocidad
            # Si pareja=50min y solo=75min, solo hace 50/75 = 0.67 de las habitaciones
            depart_ratio = depart_pair_min / depart_solo_min if depart_solo_min > 0 else 1
            recouch_ratio = recouch_pair_min / recouch_solo_min if recouch_solo_min > 0 else 1

            # Asignar departs
            if departs_left > 0 and depart_solo_min > 0:
                departs_for_quota = int((target_work_min / depart_pair_min) * depart_ratio)
                unit_departs = min(departs_left, departs_for_quota, period_minutes // depart_solo_min)
                work_done_min += unit_departs * depart_solo_min
                departs_left -= unit_departs

            # Completar con recouches
            remaining_time = period_minutes - work_done_min
            if recouches_left > 0 and recouch_solo_min > 0 and remaining_time > 0:
                recouches_for_quota = int(((target_work_min - (unit_departs * depart_pair_min)) / recouch_pair_min) * recouch_ratio)
                max_capacity = remaining_time // recouch_solo_min
                unit_recouches = min(recouches_left, max(0, recouches_for_quota), max_capacity)
                work_done_min += unit_recouches * recouch_solo_min
                recouches_left -= unit_recouches

            spare_min = period_minutes - work_done_min
            units_work.append({
                'type': 'solo',
                'display': solo_name,
                'names': [solo_name],
                'ids': [solo_id] if solo_id else [],  # Track employee ID for per-employee spare
                'shifts': [solo_shift],  # Track shift for solo worker
                'departs': unit_departs,
                'recouches': unit_recouches,
                'spare_min': max(0, spare_min),
            })

        # Segunda pasada: redistribuir trabajo restante a unidades con capacidad
        for _ in range(3):  # Máximo 3 pasadas de rebalanceo
            if departs_left <= 0 and recouches_left <= 0:
                break

            for unit in units_work:
                if departs_left <= 0 and recouches_left <= 0:
                    break

                is_pair = unit['type'] == 'pair'
                d_min = depart_pair_min if is_pair else depart_solo_min
                r_min = recouch_pair_min if is_pair else recouch_solo_min

                # Calcular tiempo usado actual
                time_used = unit['departs'] * d_min + unit['recouches'] * r_min
                available = period_minutes - time_used

                # Asignar departs extras
                if departs_left > 0 and d_min > 0 and available >= d_min:
                    extra_departs = min(departs_left, available // d_min)
                    unit['departs'] += extra_departs
                    departs_left -= extra_departs
                    available -= extra_departs * d_min
                    unit['spare_min'] = max(0, available)

                # Asignar recouches extras
                if recouches_left > 0 and r_min > 0 and available >= r_min:
                    extra_recouches = min(recouches_left, available // r_min)
                    unit['recouches'] += extra_recouches
                    recouches_left -= extra_recouches
                    available -= extra_recouches * r_min
                    unit['spare_min'] = max(0, available)

        # Generar display formateado con tiempo libre individual
        display_parts = []
        for unit in units_work:
            work_str = ""
            if unit['departs'] > 0 and unit['recouches'] > 0:
                work_str = f"{unit['departs']}D+{unit['recouches']}R"
            elif unit['departs'] > 0:
                work_str = f"{unit['departs']}D"
            elif unit['recouches'] > 0:
                work_str = f"{unit['recouches']}R"

            # Agregar tiempo libre si hay
            spare_min = unit.get('spare_min', 0)
            spare_str = ""
            if spare_min >= 60:
                spare_str = f"⏱️+{spare_min // 60}h{spare_min % 60}min" if spare_min % 60 else f"⏱️+{spare_min // 60}h"
            elif spare_min > 0:
                spare_str = f"⏱️+{spare_min}min"

            if work_str:
                if spare_str:
                    display_parts.append(f"{unit['display']}:{work_str} {spare_str}")
                else:
                    display_parts.append(f"{unit['display']}:{work_str}")
            else:
                display_parts.append(f"{unit['display']}:libre {spare_str}" if spare_str else f"{unit['display']}:libre")

        total_departs = sum(u['departs'] for u in units_work)
        total_recouches = sum(u['recouches'] for u in units_work)
        total_spare = sum(u['spare_min'] for u in units_work)

        return {
            'units': units_work,
            'display': ' · '.join(display_parts),
            'total_departs': total_departs,
            'total_recouches': total_recouches,
            'total_spare_min': total_spare,
            'departs_remaining': departs_left,
            'recouches_remaining': recouches_left,
        }

    def calculate_pairs(self, assigned_employees: List[Dict]) -> Dict[str, Any]:
        """
        Calcula parejas configuradas y temporales.

        Args:
            assigned_employees: Lista de empleados asignados con employee_id

        Returns:
            Diccionario con parejas configuradas, temporales, solos y totales
        """
        employee_ids = [emp.get('employee_id') or emp.get('id') for emp in assigned_employees if emp]

        configured_pairs = []  # Parejas de equipos configurados
        temp_pairs = []        # Parejas temporales
        solos = []             # Personas sin pareja
        used_employees = set()

        # 1. Buscar parejas configuradas (equipos donde ambos miembros están asignados)
        for team in self.teams:
            member_ids = team.get('member_ids', [])
            assigned_members = [mid for mid in member_ids if mid in employee_ids]

            # Si al menos 2 miembros del equipo están asignados, forman pareja
            if len(assigned_members) >= 2:
                # Tomar los primeros 2
                pair_ids = assigned_members[:2]
                for emp_id in pair_ids:
                    used_employees.add(emp_id)

                # Obtener nombres
                pair_names = []
                for emp_id in pair_ids:
                    for emp in assigned_employees:
                        if (emp.get('employee_id') or emp.get('id')) == emp_id:
                            name = emp.get('employee_short') or emp.get('employee', '').split(' ')[0]
                            pair_names.append(name)
                            break

                # Track shifts of pair members (for P2 spare calculation)
                pair_shifts = []
                for emp_id in pair_ids:
                    for emp in assigned_employees:
                        if (emp.get('employee_id') or emp.get('id')) == emp_id:
                            pair_shifts.append(emp.get('_shift', 'unknown'))
                            break

                configured_pairs.append({
                    'ids': pair_ids,
                    'names': pair_names,
                    'team_name': team.get('name'),
                    'display': f"({'+'.join(pair_names)})",
                    'shifts': pair_shifts,  # e.g. ['morning', 'morning'] or ['morning', 'evening']
                })

        # 2. Empleados sin pareja configurada pueden formar parejas temporales
        remaining_employees = [
            emp for emp in assigned_employees
            if (emp.get('employee_id') or emp.get('id')) not in used_employees
        ]

        # Helper function to get name safely
        def get_employee_name(emp_dict):
            name = emp_dict.get('employee_short')
            if name:
                return name
            full_name = emp_dict.get('employee') or emp_dict.get('team_name') or 'Anónimo'
            if full_name and ' ' in full_name:
                return full_name.split(' ')[0]
            return full_name

        # Formar parejas temporales con los restantes
        for i in range(0, len(remaining_employees), 2):
            if i + 1 < len(remaining_employees):
                emp1 = remaining_employees[i]
                emp2 = remaining_employees[i+1]
                name1 = get_employee_name(emp1)
                name2 = get_employee_name(emp2)
                shift1 = emp1.get('_shift', 'unknown')
                shift2 = emp2.get('_shift', 'unknown')
                id1 = emp1.get('employee_id') or emp1.get('id')
                id2 = emp2.get('employee_id') or emp2.get('id')
                temp_pairs.append({
                    'names': [name1, name2],
                    'ids': [id1, id2],  # Track employee IDs
                    'display': f"[{name1}+{name2}]",
                    'shifts': [shift1, shift2],
                })
            else:
                # Impar - queda solo
                emp = remaining_employees[i]
                name = get_employee_name(emp)
                solo_shift = emp.get('_shift', 'unknown')
                solo_id = emp.get('employee_id') or emp.get('id')
                solos.append({'name': name, 'shift': solo_shift, 'id': solo_id})

        total_pairs = len(configured_pairs) + len(temp_pairs)

        # Generar display formateado
        display_parts = []
        for pair in configured_pairs:
            display_parts.append(pair['display'])
        for pair in temp_pairs:
            display_parts.append(pair['display'])
        for solo in solos:
            # solos can be dict (with shift info) or string (legacy)
            if isinstance(solo, dict):
                display_parts.append(solo['name'])
            else:
                display_parts.append(solo)

        return {
            'configured_pairs': configured_pairs,
            'temp_pairs': temp_pairs,
            'solos': solos,
            'total_pairs': total_pairs,
            'total_solos': len(solos),
            'display': ' · '.join(display_parts),
        }

    def calculate_day_distribution(
        self,
        forecast: Dict[str, int],
        assigned_day: List[Dict],
        assigned_evening: List[Dict],
    ) -> Dict[str, Any]:
        """
        Calcula la distribución completa del trabajo para un día.

        Args:
            forecast: {departures, arrivals, occupied}
            assigned_day: Lista de empleados asignados turno día
            assigned_evening: Lista de empleados asignados turno tarde

        Returns:
            Diccionario con toda la distribución por períodos
        """
        departures = forecast.get('departures', 0)
        arrivals = forecast.get('arrivals', 0)
        occupied = forecast.get('occupied', 0)
        stays = max(0, occupied - arrivals)

        total_departs = departures
        total_recouches = stays
        total_rooms = total_departs + total_recouches

        # Tiempos de tareas (PAREJA)
        DEPART_MIN = self.task_config.get('DEPART', {}).get('base_minutes', 50)
        RECOUCH_MIN = self.task_config.get('RECOUCH', {}).get('base_minutes', 20)
        COUV_MIN = self.task_config.get('COUVERTURE', {}).get('base_minutes', 15)

        # Tiempos de tareas (SOLO)
        DEPART_SOLO_MIN = self.task_config.get('DEPART', {}).get('solo_minutes', 75)
        RECOUCH_SOLO_MIN = self.task_config.get('RECOUCH', {}).get('solo_minutes', 30)

        # Períodos de trabajo (calculados dinámicamente desde ShiftTemplates)
        P1_MIN = self.P1_MIN  # Mañana sola
        P2_MIN = self.P2_MIN  # Mañana + Tarde juntos
        P3_MIN = self.P3_MIN  # Tarde sola antes de cena

        # Calcular parejas por turno
        day_pair_info = self.calculate_pairs(assigned_day)
        evening_pair_info = self.calculate_pairs(assigned_evening)

        # Para P2, marcamos cada empleado con su turno de origen
        # Esto nos permite calcular spare separado para mañana vs tarde
        day_with_shift = [{**emp, '_shift': 'morning'} for emp in assigned_day]
        evening_with_shift = [{**emp, '_shift': 'evening'} for emp in assigned_evening]
        p2_pair_info = self.calculate_pairs(day_with_shift + evening_with_shift)

        pairs_day = day_pair_info['total_pairs']
        pairs_evening = evening_pair_info['total_pairs']
        pairs_p2 = p2_pair_info['total_pairs']

        num_day = len(assigned_day)
        num_evening = len(assigned_evening)

        # ========== PASO 1: CALCULAR COUVERTURES PRIMERO ==========
        # Couvertures son prioritarias y determinan cuántas personas necesitamos

        # Nombres individuales para couvertures
        evening_individual_names = ', '.join([
            emp.get('employee_short') or emp.get('employee', '').split(' ')[0]
            for emp in assigned_evening
        ])

        # Calcular hora de fin real basada en los horarios de los empleados
        actual_couv_end = self.couv_end  # fallback al máximo permitido
        if assigned_evening:
            end_times = [emp.get('end_time') for emp in assigned_evening if emp.get('end_time')]
            if end_times:
                actual_couv_end = max(end_times)

        # Período real de couvertures (desde couv_start hasta fin de turno)
        actual_couv_period_min = self._time_to_minutes(actual_couv_end) - self._time_to_minutes(self.couv_start)
        if actual_couv_period_min <= 0:
            actual_couv_period_min = self.couv_period_min  # fallback

        # Trabajo total de couvertures
        total_couv_work_min = occupied * COUV_MIN

        # Capacidad actual con personas asignadas
        current_couv_capacity = num_evening * actual_couv_period_min

        # Déficit real en minutos (puede ser negativo si hay exceso)
        couv_deficit_min = total_couv_work_min - current_couv_capacity

        # === PRIORIDAD DE COBERTURA DE DÉFICIT ===
        # 1. Primero: Trabajadores con horas semanales disponibles (no cumplen 39h)
        # 2. Segundo: Elasticidad (solo si no hay trabajadores disponibles)

        from apps.staff.models import Employee
        from apps.rules.models import ElasticityRule

        # Obtener IDs de empleados ya asignados
        assigned_employee_ids = set()
        for emp in assigned_day + assigned_evening:
            emp_id = emp.get('employee_id') or emp.get('id')
            if emp_id:
                assigned_employee_ids.add(emp_id)

        # Buscar trabajadores con horas disponibles (no asignados este día)
        workers_with_available_hours = []
        all_hk_employees = Employee.objects.filter(
            role__code__in=['FDC', 'VDC'],
            is_active=True
        ).select_related('role')

        for emp in all_hk_employees:
            if emp.id not in assigned_employee_ids:
                target = float(emp.weekly_hours_target) if emp.weekly_hours_target else 39.0
                # TODO: Calcular horas ya asignadas en la semana para este empleado
                # Por ahora asumimos que si no está asignado este día, tiene horas disponibles
                workers_with_available_hours.append({
                    'id': emp.id,
                    'name': emp.first_name,
                    'role': emp.role.code,
                    'weekly_target': target,
                })

        has_workers_available = len(workers_with_available_hours) > 0

        # Cargar reglas de elasticidad
        elasticity_rules = {}
        for rule in ElasticityRule.objects.all():
            elasticity_rules[rule.elasticity_level] = {
                'max_day': float(rule.max_extra_hours_day) * 60,
                'max_week': float(rule.max_extra_hours_week) * 60,
            }

        # Calcular elasticidad disponible total de los empleados EVENING
        total_elasticity_available = 0
        elasticity_per_person = 0
        for emp in assigned_evening:
            emp_id = emp.get('employee_id') or emp.get('id')
            if emp_id:
                try:
                    employee = Employee.objects.get(id=emp_id)
                    rule = elasticity_rules.get(employee.elasticity, {})
                    emp_elasticity = rule.get('max_day', 0)
                    total_elasticity_available += emp_elasticity
                except Employee.DoesNotExist:
                    pass

        if num_evening > 0:
            elasticity_per_person = total_elasticity_available / num_evening

        MAX_ELASTICITY_PER_PERSON = 60

        extra_min_per_person_raw = 0
        if couv_deficit_min > 0 and num_evening > 0:
            extra_min_per_person_raw = couv_deficit_min / num_evening

        def round_to_15(minutes):
            if minutes <= 0:
                return 0
            return int(((minutes + 14) // 15) * 15)

        extra_min_per_person = round_to_15(extra_min_per_person_raw)

        # NUEVA LÓGICA DE PRIORIDAD:
        # 1. Si hay déficit Y hay trabajadores disponibles → sugerir agregar trabajadores
        # 2. Solo si NO hay trabajadores disponibles → considerar elasticidad
        can_add_workers = couv_deficit_min > 0 and has_workers_available

        # Solo considerar elasticidad si NO hay trabajadores disponibles
        can_cover_with_elasticity = (
            couv_deficit_min > 0 and
            not has_workers_available and
            extra_min_per_person <= MAX_ELASTICITY_PER_PERSON and
            couv_deficit_min <= total_elasticity_available
        )

        # Necesitamos más personas si:
        # 1. Hay déficit Y hay trabajadores disponibles (agregar trabajador primero)
        # 2. O si no hay trabajadores Y la elasticidad no alcanza
        couv_needs_more_persons = (
            (couv_deficit_min > 0 and has_workers_available) or
            (couv_deficit_min > 0 and not has_workers_available and (
                couv_deficit_min > total_elasticity_available or
                extra_min_per_person_raw > MAX_ELASTICITY_PER_PERSON
            ))
        )

        couv_extra_persons_needed = 0
        if couv_needs_more_persons and actual_couv_period_min > 0:
            # Calcular cuántas personas más necesitamos
            # Si el problema es que cada persona necesita más de 60 min, calculamos con el límite
            if extra_min_per_person_raw > MAX_ELASTICITY_PER_PERSON:
                # Cuánto trabajo queda después de usar 60 min de cada persona asignada
                covered_by_elasticity = num_evening * MAX_ELASTICITY_PER_PERSON
                remaining_work = couv_deficit_min - covered_by_elasticity
                if remaining_work > 0:
                    couv_extra_persons_needed = max(1, int((remaining_work + actual_couv_period_min - 1) // actual_couv_period_min))
            else:
                # La elasticidad total no alcanza
                remaining_deficit = couv_deficit_min - total_elasticity_available
                couv_extra_persons_needed = max(1, int((remaining_deficit + actual_couv_period_min - 1) // actual_couv_period_min))

        # Tiempo que cada persona dedica a couvertures
        couv_time_per_person = (total_couv_work_min / num_evening) if num_evening > 0 else total_couv_work_min

        # Spare time (considerando elasticidad usada)
        if can_cover_with_elasticity:
            # Si usamos elasticidad, el spare es lo que queda de la elasticidad
            actual_couv_spare = total_elasticity_available - couv_deficit_min
        elif couv_deficit_min <= 0:
            # Si no hay déficit, el spare es la capacidad - trabajo
            actual_couv_spare = -couv_deficit_min
        else:
            # Si hay déficit y no podemos cubrir, spare es 0
            actual_couv_spare = 0

        # Personas efectivas = las asignadas (ya no inflamos el número)
        effective_couv_persons = num_evening

        # ========== PASO 2: DISTRIBUIR HABITACIONES ==========
        # Usar la nueva función que distribuye a unidades específicas

        departs_left = total_departs
        recouches_left = total_recouches

        # Obtener parejas y solos de cada turno
        day_pairs = day_pair_info['configured_pairs'] + day_pair_info['temp_pairs']
        day_solos = day_pair_info['solos']
        evening_pairs = evening_pair_info['configured_pairs'] + evening_pair_info['temp_pairs']
        evening_solos = evening_pair_info['solos']
        p2_pairs = p2_pair_info['configured_pairs'] + p2_pair_info['temp_pairs']
        p2_solos = p2_pair_info['solos']

        # Unidades de trabajo
        units_day = len(day_pairs) + len(day_solos)
        units_evening = len(evening_pairs) + len(evening_solos)
        units_p2 = len(p2_pairs) + len(p2_solos)

        # P1: Solo mañana (09:00 - 12:30 = 210 min)
        p1_work = self.distribute_work_to_units(
            pairs=day_pairs,
            solos=day_solos,
            departs_to_do=departs_left,
            recouches_to_do=recouches_left,
            period_minutes=P1_MIN,
            depart_pair_min=DEPART_MIN,
            depart_solo_min=DEPART_SOLO_MIN,
            recouch_pair_min=RECOUCH_MIN,
            recouch_solo_min=RECOUCH_SOLO_MIN,
        )
        departs_left = p1_work['departs_remaining']
        recouches_left = p1_work['recouches_remaining']

        # P2: Mañana + Tarde juntos (13:30 - 17:00 = 210 min)
        p2_work = self.distribute_work_to_units(
            pairs=p2_pairs,
            solos=p2_solos,
            departs_to_do=departs_left,
            recouches_to_do=recouches_left,
            period_minutes=P2_MIN,
            depart_pair_min=DEPART_MIN,
            depart_solo_min=DEPART_SOLO_MIN,
            recouch_pair_min=RECOUCH_MIN,
            recouch_solo_min=RECOUCH_SOLO_MIN,
        )
        departs_left = p2_work['departs_remaining']
        recouches_left = p2_work['recouches_remaining']

        # P3: Solo tarde termina (17:00 - 18:30 = 90 min)
        p3_work = self.distribute_work_to_units(
            pairs=evening_pairs,
            solos=evening_solos,
            departs_to_do=departs_left,
            recouches_to_do=recouches_left,
            period_minutes=P3_MIN,
            depart_pair_min=DEPART_MIN,
            depart_solo_min=DEPART_SOLO_MIN,
            recouch_pair_min=RECOUCH_MIN,
            recouch_solo_min=RECOUCH_SOLO_MIN,
        )
        departs_left = p3_work['departs_remaining']
        recouches_left = p3_work['recouches_remaining']

        # ========== PASO 3: VERIFICAR ESTADO TOTAL ==========
        rooms_deficit = departs_left + recouches_left
        # Solo hay déficit si no podemos completar las habitaciones
        # Couvertures no genera déficit porque calculamos con personas efectivas
        has_deficit = rooms_deficit > 0

        # ========== PASO 4: CALCULAR SPARE POR EMPLEADO EN P2 ==========
        # En P2, mañana y tarde trabajan juntos. Cada empleado tiene su propio
        # spare basado en la unidad donde trabaja.
        #
        # IMPORTANTE: Cuando una pareja trabaja junta, AMBOS tienen el mismo tiempo libre.
        # El spare de la unidad NO se divide entre ellos - si la pareja tiene 120min
        # spare, cada persona tiene 120min libre (trabajan juntos, descansan juntos).

        # Build per-employee spare mapping for P2
        p2_employee_spare = {}  # employee_id -> spare_min

        for unit in p2_work['units']:
            unit_spare = unit.get('spare_min', 0)
            unit_ids = unit.get('ids', [])

            # Each person in the unit gets the FULL spare time
            for emp_id in unit_ids:
                if emp_id:
                    p2_employee_spare[emp_id] = unit_spare

        # Also calculate averages per shift for fallback
        p2_morning_spare_total = 0
        p2_morning_persons = 0
        p2_evening_spare_total = 0
        p2_evening_persons = 0

        for unit in p2_work['units']:
            unit_spare = unit.get('spare_min', 0)
            unit_shifts = unit.get('shifts', [])

            morning_in_unit = sum(1 for s in unit_shifts if s == 'morning')
            evening_in_unit = sum(1 for s in unit_shifts if s == 'evening')

            if morning_in_unit > 0:
                p2_morning_spare_total += unit_spare * morning_in_unit
                p2_morning_persons += morning_in_unit
            if evening_in_unit > 0:
                p2_evening_spare_total += unit_spare * evening_in_unit
                p2_evening_persons += evening_in_unit

        p2_morning_spare_pp = (p2_morning_spare_total / p2_morning_persons) if p2_morning_persons > 0 else 0
        p2_evening_spare_pp = (p2_evening_spare_total / p2_evening_persons) if p2_evening_persons > 0 else 0

        return {
            'summary': {
                'total_rooms': total_rooms,
                'total_departs': total_departs,
                'total_recouches': total_recouches,
                'total_couvertures': occupied,
                'stays': stays,
                'has_deficit': has_deficit,
                'rooms_deficit': rooms_deficit,
                'couv_needs_more_persons': couv_needs_more_persons,
                'couv_extra_persons_needed': couv_extra_persons_needed,
            },
            'periods': {
                'p1': {
                    'name': 'morning_alone',
                    'time_range': f"{self.P1_START} - {self.P1_END}",
                    'pairs': len(day_pairs),
                    'solos': len(day_solos),
                    'units': units_day,
                    'units_work': p1_work['units'],
                    'work_display': p1_work['display'],
                    'spare': self._format_spare(p1_work['total_spare_min'], units_day),
                    'departs_done': p1_work['total_departs'],
                    'recouch_done': p1_work['total_recouches'],
                    'rooms_done': p1_work['total_departs'] + p1_work['total_recouches'],
                },
                'lunch_morning': {
                    'name': 'morning_lunch',
                    'time_range': f"{self.LUNCH_DAY_START} - {self.LUNCH_DAY_END}",
                },
                'p2': {
                    'name': 'morning_evening',
                    'time_range': f"{self.P2_START} - {self.P2_END}",
                    'pairs': len(p2_pairs),
                    'solos': len(p2_solos),
                    'units': units_p2,
                    'units_work': p2_work['units'],
                    'work_display': p2_work['display'],
                    'spare': self._format_spare(p2_work['total_spare_min'], units_p2),
                    # Per-employee spare mapping (employee_id -> spare_min)
                    'employee_spare': p2_employee_spare,
                    # Fallback averages by shift
                    'morning_spare_pp': round(p2_morning_spare_pp, 1),
                    'evening_spare_pp': round(p2_evening_spare_pp, 1),
                    'morning_persons': p2_morning_persons,
                    'evening_persons': p2_evening_persons,
                    'departs_done': p2_work['total_departs'],
                    'recouch_done': p2_work['total_recouches'],
                    'rooms_done': p2_work['total_departs'] + p2_work['total_recouches'],
                },
                'p3': {
                    'name': 'evening_finishes',
                    'time_range': f"{self.P3_START} - {self.P3_END}",
                    'pairs': len(evening_pairs),
                    'solos': len(evening_solos),
                    'units': units_evening,
                    'units_work': p3_work['units'],
                    'work_display': p3_work['display'],
                    'spare': self._format_spare(p3_work['total_spare_min'], units_evening),
                    'departs_done': p3_work['total_departs'],
                    'recouch_done': p3_work['total_recouches'],
                    'rooms_done': p3_work['total_departs'] + p3_work['total_recouches'],
                    'rooms_deficit': rooms_deficit,
                },
                'lunch_evening': {
                    'name': 'evening_lunch',
                    'time_range': f"{self.LUNCH_EVENING_START} - {self.LUNCH_EVENING_END}",
                },
                'couvertures': {
                    'name': 'couvertures',
                    'time_range': f"{self.couv_start} - {actual_couv_end}",
                    'persons_assigned': num_evening,
                    'persons_needed': num_evening if not couv_needs_more_persons else num_evening + couv_extra_persons_needed,
                    'persons_effective': effective_couv_persons,
                    'needs_more_persons': couv_needs_more_persons,
                    'extra_persons_needed': couv_extra_persons_needed,
                    'persons_display': evening_individual_names,
                    'capacity_min': current_couv_capacity,
                    'period_min': actual_couv_period_min,
                    'work_min': total_couv_work_min,
                    'deficit_min': max(0, couv_deficit_min),
                    'time_per_person_min': round(couv_time_per_person, 1),
                    'spare_min': round(actual_couv_spare, 1),
                    'spare': self._format_spare(int(actual_couv_spare), num_evening),
                    'couvertures_count': occupied,
                    'per_person': round(occupied / num_evening, 1) if num_evening > 0 else 0,
                    # PRIORIDAD: Trabajadores disponibles ANTES que elasticidad
                    'has_workers_available': has_workers_available,
                    'workers_available': workers_with_available_hours[:3],  # Top 3 sugeridos
                    'can_add_workers': can_add_workers,
                    # Elasticidad (solo si no hay trabajadores disponibles)
                    'can_cover_with_elasticity': can_cover_with_elasticity,
                    'elasticity_available_min': round(total_elasticity_available, 1),
                    'elasticity_extra_per_person_min': round(extra_min_per_person, 1),
                    'has_deficit': couv_needs_more_persons,
                    # Sugerencia clara
                    'suggestion': (
                        f"Agregar trabajador: {workers_with_available_hours[0]['name']}" if can_add_workers and workers_with_available_hours
                        else f"+{extra_min_per_person}min/persona (elasticidad)" if can_cover_with_elasticity
                        else "Sin cobertura posible" if couv_deficit_min > 0
                        else None
                    ),
                },
            },
            'workers': {
                'day_count': num_day,
                'evening_count': num_evening,
                'total_count': num_day + num_evening,
            },
            'task_config': {
                'depart_pair_min': DEPART_MIN,
                'depart_solo_min': DEPART_SOLO_MIN,
                'recouch_pair_min': RECOUCH_MIN,
                'recouch_solo_min': RECOUCH_SOLO_MIN,
                'couv_min': COUV_MIN,
                'couv_period_min': self.couv_period_min,
            },
        }
