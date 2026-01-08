"""
Load Calculator Service.
Calcula la carga de trabajo (demanda) por día y bloque temporal.
"""
from datetime import date
from typing import Dict, List, Any
from collections import defaultdict
from django.db.models import Sum

from apps.core.models import TimeBlock, Zone
from apps.rooms.models import RoomDailyState, RoomDailyTask
from apps.planning.models import DailyLoadSummary
from .time_calculator import TimeCalculator


class LoadCalculator:
    """
    Calculador de carga de trabajo.
    Determina cuánto trabajo hay que hacer por día/bloque.
    """

    def __init__(self):
        self.time_calculator = TimeCalculator()

    def compute_load(
        self,
        target_date: date,
        time_block: TimeBlock = None
    ) -> Dict[str, Any]:
        """
        Calcula la carga de trabajo para una fecha y bloque.

        Args:
            target_date: Fecha a calcular
            time_block: Bloque temporal (opcional, si None calcula todos)

        Returns:
            Diccionario con la carga calculada
        """
        result = {
            'date': target_date,
            'blocks': {},
            'total_minutes': 0,
            'total_tasks': 0,
            'by_zone': defaultdict(lambda: {'minutes': 0, 'tasks': 0}),
            'hard_rooms': [],
        }

        # Obtener bloques a calcular
        if time_block:
            blocks = [time_block]
        else:
            blocks = TimeBlock.objects.filter(is_active=True)

        for block in blocks:
            block_result = self._compute_block_load(target_date, block)
            result['blocks'][block.code] = block_result
            result['total_minutes'] += block_result['total_minutes']
            result['total_tasks'] += block_result['total_tasks']

            # Agregar a resumen por zona
            for zone_code, zone_data in block_result['by_zone'].items():
                result['by_zone'][zone_code]['minutes'] += zone_data['minutes']
                result['by_zone'][zone_code]['tasks'] += zone_data['tasks']

            # Agregar habitaciones difíciles
            result['hard_rooms'].extend(block_result['hard_rooms'])

        return result

    def _compute_block_load(
        self,
        target_date: date,
        time_block: TimeBlock
    ) -> Dict[str, Any]:
        """
        Calcula la carga para un bloque específico.
        """
        result = {
            'time_block': time_block.code,
            'total_minutes': 0,
            'total_tasks': 0,
            'by_task_type': defaultdict(lambda: {'minutes': 0, 'count': 0}),
            'by_zone': defaultdict(lambda: {'minutes': 0, 'tasks': 0, 'rooms': []}),
            'hard_rooms': [],
            'tasks_detail': [],
        }

        # Obtener tareas del día para este bloque
        tasks = RoomDailyTask.objects.filter(
            room_daily_state__date=target_date,
            time_block=time_block,
            status__in=['PENDING', 'ASSIGNED']
        ).select_related(
            'room_daily_state',
            'room_daily_state__room',
            'room_daily_state__room__zone',
            'room_daily_state__room__room_type',
            'task_type'
        )

        for task in tasks:
            room_state = task.room_daily_state
            room = room_state.room
            zone = room.zone

            # Calcular tiempo
            estimated_minutes = self.time_calculator.calculate_task_time(task, room_state)

            # Actualizar contadores
            result['total_minutes'] += estimated_minutes
            result['total_tasks'] += 1

            # Por tipo de tarea
            result['by_task_type'][task.task_type.code]['minutes'] += estimated_minutes
            result['by_task_type'][task.task_type.code]['count'] += 1

            # Por zona
            result['by_zone'][zone.code]['minutes'] += estimated_minutes
            result['by_zone'][zone.code]['tasks'] += 1
            if room.number not in result['by_zone'][zone.code]['rooms']:
                result['by_zone'][zone.code]['rooms'].append(room.number)

            # Habitaciones difíciles
            if room_state.night_expected_difficulty in ('HARD', 'VERY_HARD'):
                result['hard_rooms'].append({
                    'room': room.number,
                    'zone': zone.code,
                    'difficulty': room_state.night_expected_difficulty,
                    'reason': 'recouch_declined' if room_state.day_cleaning_status == 'DECLINED' else 'other'
                })

            # Detalle de tareas
            result['tasks_detail'].append({
                'task_id': task.id,
                'room': room.number,
                'zone': zone.code,
                'task_type': task.task_type.code,
                'estimated_minutes': estimated_minutes,
                'is_vip': room_state.is_vip,
                'difficulty': room_state.night_expected_difficulty,
            })

        return result

    def compute_week_load(
        self,
        week_start: date
    ) -> Dict[str, Any]:
        """
        Calcula la carga de trabajo para toda una semana.

        Args:
            week_start: Fecha del lunes de la semana

        Returns:
            Diccionario con carga por día
        """
        from datetime import timedelta

        result = {
            'week_start': week_start,
            'days': {},
            'totals': {
                'minutes': 0,
                'tasks': 0,
            },
            'by_block': defaultdict(lambda: {'minutes': 0, 'tasks': 0}),
        }

        for day_offset in range(7):
            current_date = week_start + timedelta(days=day_offset)
            day_load = self.compute_load(current_date)

            result['days'][current_date.isoformat()] = day_load
            result['totals']['minutes'] += day_load['total_minutes']
            result['totals']['tasks'] += day_load['total_tasks']

            for block_code, block_data in day_load['blocks'].items():
                result['by_block'][block_code]['minutes'] += block_data['total_minutes']
                result['by_block'][block_code]['tasks'] += block_data['total_tasks']

        return result

    def save_load_summary(self, target_date: date) -> List[DailyLoadSummary]:
        """
        Calcula y guarda el resumen de carga para un día.
        """
        load = self.compute_load(target_date)
        summaries = []

        for block_code, block_data in load['blocks'].items():
            time_block = TimeBlock.objects.get(code=block_code)

            summary, created = DailyLoadSummary.objects.update_or_create(
                date=target_date,
                time_block=time_block,
                defaults={
                    'total_tasks': block_data['total_tasks'],
                    'total_minutes_required': block_data['total_minutes'],
                }
            )
            summaries.append(summary)

        return summaries

    def get_zones_load(
        self,
        target_date: date,
        time_block: TimeBlock
    ) -> List[Dict[str, Any]]:
        """
        Obtiene la carga por zona para asignación zonificada.
        Ordenado por prioridad de zona.
        """
        load = self._compute_block_load(target_date, time_block)

        zones_data = []
        for zone in Zone.objects.filter(is_active=True).order_by('priority_order', 'floor_number'):
            zone_code = zone.code
            if zone_code in load['by_zone']:
                zone_load = load['by_zone'][zone_code]
                zones_data.append({
                    'zone': zone,
                    'zone_code': zone_code,
                    'zone_name': zone.name,
                    'floor': zone.floor_number,
                    'total_minutes': zone_load['minutes'],
                    'total_tasks': zone_load['tasks'],
                    'rooms': zone_load['rooms'],
                })

        return zones_data
