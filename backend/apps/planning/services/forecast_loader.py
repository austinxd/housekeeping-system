"""
Forecast Loader Service.
Carga datos de forecast y calcula la carga de trabajo.
"""
from datetime import date, timedelta
from typing import Dict, List, Any
from decimal import Decimal
from django.db import transaction

from apps.core.models import TaskType, TimeBlock


class ForecastLoader:
    """
    Carga y procesa datos de forecast de ocupación.
    Calcula la carga de trabajo basada en llegadas, salidas y ocupación.
    """

    def __init__(self):
        self.task_times = self._load_task_times()
        self.task_persons = self._load_task_persons()
        self.task_constraints = self._load_task_constraints()
        self.shift_config = self._load_shift_config()

    def _load_shift_config(self) -> Dict[str, Dict]:
        """Carga la configuración de turnos desde la base de datos."""
        config = {}
        for block in TimeBlock.objects.filter(is_active=True):
            shift_hours = 8.0
            if block.start_time and block.end_time:
                from datetime import datetime
                start = datetime.combine(date.today(), block.start_time)
                end = datetime.combine(date.today(), block.end_time)
                shift_hours = (end - start).total_seconds() / 3600

            config[block.code] = {
                'start_time': block.start_time,
                'end_time': block.end_time,
                'shift_hours': shift_hours,
                'min_staff': block.min_staff,
                'helps_other_shift_hours': float(block.helps_other_shift_hours),
            }
        return config

    def _load_task_times(self) -> Dict[str, int]:
        """Carga los tiempos de tarea desde la base de datos."""
        times = {}
        for task in TaskType.objects.all():
            times[task.code] = task.base_minutes
        return times

    def _load_task_persons(self) -> Dict[str, int]:
        """Carga las personas requeridas por tarea desde la base de datos."""
        persons = {}
        for task in TaskType.objects.all():
            persons[task.code] = task.persons_required
        return persons

    def _load_task_constraints(self) -> Dict[str, Dict]:
        """Carga las restricciones de horario de cada tarea."""
        from datetime import datetime, time as dt_time
        constraints = {}
        for task in TaskType.objects.all():
            available_hours = 8.0  # Default
            if task.earliest_start_time and task.latest_end_time:
                # Calcular horas disponibles para esta tarea
                start = datetime.combine(date.today(), task.earliest_start_time)
                end = datetime.combine(date.today(), task.latest_end_time)
                diff = (end - start).total_seconds() / 3600
                available_hours = max(0.5, diff)  # Mínimo 30 minutos
            constraints[task.code] = {
                'earliest_start': task.earliest_start_time,
                'latest_end': task.latest_end_time,
                'available_hours': available_hours,
            }
        return constraints

    def calculate_daily_load(
        self,
        departures: int,
        arrivals: int,
        occupied: int
    ) -> Dict[str, Any]:
        """
        Calcula la carga de trabajo para un día.

        Args:
            departures: Número de salidas (checkouts)
            arrivals: Número de llegadas (checkins)
            occupied: Número de habitaciones ocupadas

        Returns:
            Diccionario con carga por turno y tarea
        """
        # Calcular tareas
        depart_count = departures
        recouch_count = occupied - arrivals  # Estancias = ocupadas - llegadas
        couverture_count = occupied  # Todas las ocupadas reciben couverture

        # Asegurar valores no negativos
        recouch_count = max(0, recouch_count)

        # Calcular minutos-persona (tiempo × personas requeridas)
        depart_minutes = depart_count * self.task_times.get('DEPART', 50) * self.task_persons.get('DEPART', 2)
        recouch_minutes = recouch_count * self.task_times.get('RECOUCH', 20) * self.task_persons.get('RECOUCH', 2)
        couverture_minutes = couverture_count * self.task_times.get('COUVERTURE', 20) * self.task_persons.get('COUVERTURE', 1)

        # Carga por turno
        day_minutes = depart_minutes + recouch_minutes
        evening_minutes = couverture_minutes

        return {
            'tasks': {
                'DEPART': {'count': depart_count, 'minutes': depart_minutes},
                'RECOUCH': {'count': recouch_count, 'minutes': recouch_minutes},
                'COUVERTURE': {'count': couverture_count, 'minutes': couverture_minutes},
            },
            'shifts': {
                'DAY': {'minutes': day_minutes, 'hours': day_minutes / 60},
                'EVENING': {'minutes': evening_minutes, 'hours': evening_minutes / 60},
            },
            'total_minutes': day_minutes + evening_minutes,
            'total_hours': (day_minutes + evening_minutes) / 60,
        }

    def calculate_week_load(
        self,
        week_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calcula la carga de trabajo para una semana completa.

        Args:
            week_data: Lista de 7 diccionarios con datos por día:
                [{'date': date, 'departures': int, 'arrivals': int, 'occupied': int}, ...]

        Returns:
            Diccionario con carga por día y totales
        """
        result = {
            'days': {},
            'totals': {
                'day_minutes': 0,
                'evening_minutes': 0,
                'total_minutes': 0,
            },
            'persons_needed': {},
        }

        for day_data in week_data:
            day_date = day_data['date']
            day_load = self.calculate_daily_load(
                departures=day_data['departures'],
                arrivals=day_data['arrivals'],
                occupied=day_data['occupied']
            )

            day_key = day_date.isoformat() if isinstance(day_date, date) else day_date
            result['days'][day_key] = day_load

            # Acumular totales
            result['totals']['day_minutes'] += day_load['shifts']['DAY']['minutes']
            result['totals']['evening_minutes'] += day_load['shifts']['EVENING']['minutes']
            result['totals']['total_minutes'] += day_load['total_minutes']

            # Calcular personas necesarias (asumiendo 8h por turno)
            day_persons = day_load['shifts']['DAY']['hours'] / 8
            evening_persons = day_load['shifts']['EVENING']['hours'] / 8

            result['persons_needed'][day_key] = {
                'day': round(day_persons, 1),
                'evening': round(evening_persons, 1),
                'total': round(day_persons + evening_persons, 1),
            }

        result['totals']['total_hours'] = result['totals']['total_minutes'] / 60

        return result

    def calculate_staffing_requirements(
        self,
        week_load: Dict[str, Any],
        hours_per_shift: float = 8.0
    ) -> Dict[str, Any]:
        """
        Calcula los requerimientos de personal para la semana.

        Modelo de turnos:
        - MAÑANA (09:00-17:00, 8h): Hace RECOUCH desde 9am, DEPART desde 11am
        - TARDE (13:30-21:30, 8h):
          * 13:30-18:30 (5h): Ayuda con DEPART + RECOUCH
          * 19:00-21:30 (2.5h): Hace COUVERTURE

        Cálculo:
        1. Primero: personas TARDE necesarias para COUVERTURE
        2. Esas personas TARDE también aportan 5h a tareas DAY
        3. Calcular personas MAÑANA adicionales para cubrir resto de DAY

        Args:
            week_load: Resultado de calculate_week_load
            hours_per_shift: Horas por turno (default 8)

        Returns:
            Requerimientos de personal por día
        """
        requirements = {
            'by_day': {},
            'summary': {
                'max_day_shift': 0,
                'max_evening_shift': 0,
                'avg_day_shift': 0,
                'avg_evening_shift': 0,
            }
        }

        day_totals = []
        evening_totals = []

        # Configuración de turnos desde BD
        day_config = self.shift_config.get('DAY', {})
        evening_config = self.shift_config.get('EVENING', {})

        morning_shift_hours = day_config.get('shift_hours', 8.0)
        morning_min_staff = day_config.get('min_staff', 2)

        evening_help_day_hours = evening_config.get('helps_other_shift_hours', 4.5)
        evening_min_staff = evening_config.get('min_staff', 2)
        evening_couverture_hours = self.task_constraints.get('COUVERTURE', {}).get('available_hours', 3.5)

        for day_key, day_load in week_load['days'].items():
            day_task_hours = day_load['shifts']['DAY']['hours']  # Horas totales DEPART + RECOUCH
            couverture_hours = day_load['shifts']['EVENING']['hours']  # Horas totales COUVERTURE

            # Paso 1: Calcular personas TARDE necesarias para COUVERTURE
            # Cada persona TARDE puede hacer couvertures durante evening_couverture_hours
            evening_persons = 0
            if couverture_hours > 0:
                evening_persons = max(evening_min_staff, round(couverture_hours / evening_couverture_hours))

            # Paso 2: Esas personas TARDE también ayudan con tareas DAY
            # Cada persona TARDE aporta evening_help_day_hours a tareas DEPART/RECOUCH
            evening_contribution_to_day = evening_persons * evening_help_day_hours

            # Paso 3: Calcular personas MAÑANA necesarias para el resto
            remaining_day_hours = max(0, day_task_hours - evening_contribution_to_day)
            morning_persons = 0
            if remaining_day_hours > 0:
                # Aplicar mínimo de staff para trabajo en parejas
                calculated = round(remaining_day_hours / morning_shift_hours)
                morning_persons = max(morning_min_staff, calculated) if calculated > 0 else 0

            requirements['by_day'][day_key] = {
                'day_shift': {
                    'hours_needed': round(day_task_hours, 1),
                    'persons_needed': morning_persons,
                    'pairs_needed': (morning_persons + 1) // 2,
                    'available_hours_per_person': morning_shift_hours,
                    'covered_by_evening': round(evening_contribution_to_day, 1),
                    'remaining_hours': round(remaining_day_hours, 1),
                },
                'evening_shift': {
                    'hours_needed': round(couverture_hours, 1),
                    'persons_needed': evening_persons,
                    'available_hours_per_person': evening_couverture_hours,
                    'also_helps_day_hours': evening_help_day_hours,
                },
            }

            day_totals.append(morning_persons)
            evening_totals.append(evening_persons)

        requirements['summary']['max_day_shift'] = max(day_totals) if day_totals else 0
        requirements['summary']['max_evening_shift'] = max(evening_totals) if evening_totals else 0
        requirements['summary']['avg_day_shift'] = sum(day_totals) / len(day_totals) if day_totals else 0
        requirements['summary']['avg_evening_shift'] = sum(evening_totals) / len(evening_totals) if evening_totals else 0

        return requirements
