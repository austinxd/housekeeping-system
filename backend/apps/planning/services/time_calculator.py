"""
Time Calculator Service.
Calcula el tiempo estimado para tareas aplicando reglas configurables.
"""
from decimal import Decimal
from typing import Optional
from apps.core.models import TaskType, RoomType
from apps.rooms.models import RoomDailyState, RoomDailyTask
from apps.rules.models import TaskTimeRule


class TimeCalculator:
    """
    Calculador de tiempo para tareas de housekeeping.
    Aplica reglas configurables desde Admin.
    """

    def __init__(self):
        # Cache de reglas
        self._rules_cache = {}

    def _get_rules_for_task(self, task_type: TaskType) -> list:
        """Obtiene reglas para un tipo de tarea, usando cache."""
        if task_type.id not in self._rules_cache:
            self._rules_cache[task_type.id] = list(
                TaskTimeRule.objects.filter(
                    task_type=task_type,
                    is_active=True
                ).order_by('-priority')
            )
        return self._rules_cache[task_type.id]

    def calculate_task_time(
        self,
        room_task: RoomDailyTask,
        room_state: Optional[RoomDailyState] = None
    ) -> int:
        """
        Calcula el tiempo estimado para una tarea específica.

        Args:
            room_task: Tarea de habitación
            room_state: Estado diario de la habitación (opcional)

        Returns:
            Tiempo estimado en minutos
        """
        task_type = room_task.task_type
        room = room_task.room_daily_state.room
        room_type = room.room_type

        if room_state is None:
            room_state = room_task.room_daily_state

        # Obtener tiempo base
        base_minutes = task_type.base_minutes

        # Buscar regla base específica para este tipo de habitación
        rules = self._get_rules_for_task(task_type)
        for rule in rules:
            if rule.condition == 'NONE':
                if rule.room_type and rule.room_type == room_type:
                    if rule.base_minutes:
                        base_minutes = rule.base_minutes
                    break
                elif not rule.room_type and rule.base_minutes:
                    base_minutes = rule.base_minutes
                    break

        # Aplicar multiplicador por tipo de habitación
        multiplier = Decimal('1.0')
        if room_type.time_multiplier:
            multiplier *= room_type.time_multiplier

        # Aplicar reglas condicionales
        conditions_met = self._evaluate_conditions(room_state, room_task)

        for rule in rules:
            if rule.condition != 'NONE' and rule.condition in conditions_met:
                # Verificar si la regla aplica a este tipo de habitación
                if rule.room_type and rule.room_type != room_type:
                    continue
                multiplier *= rule.time_multiplier

        # Calcular tiempo final
        final_minutes = int(base_minutes * multiplier)

        return final_minutes

    def _evaluate_conditions(
        self,
        room_state: RoomDailyState,
        room_task: RoomDailyTask
    ) -> set:
        """
        Evalúa qué condiciones se cumplen para aplicar reglas.

        Returns:
            Set de códigos de condiciones cumplidas
        """
        conditions = set()

        # Suite
        if room_state.room.room_type.code.upper() in ('SUITE', 'JUNIOR_SUITE', 'PRESIDENTIAL'):
            conditions.add('SUITE')

        # VIP
        if room_state.is_vip:
            conditions.add('VIP')

        # Recouch rechazado
        if room_state.day_cleaning_status == 'DECLINED':
            conditions.add('RECOUCH_DECLINED')

        # Estancia larga
        if room_state.stay_day_number > 5:
            conditions.add('STAY_LONG')

        # Primer día
        if room_state.stay_day_number == 1:
            conditions.add('FIRST_DAY')

        # Checkout tardío (después de 12:00)
        if room_state.expected_checkout_time:
            from datetime import time
            if room_state.expected_checkout_time > time(12, 0):
                conditions.add('LATE_CHECKOUT')

        # Checkin temprano (antes de 14:00)
        if room_state.expected_checkin_time:
            from datetime import time
            if room_state.expected_checkin_time < time(14, 0):
                conditions.add('EARLY_CHECKIN')

        return conditions

    def calculate_tasks_total_time(self, tasks: list) -> int:
        """
        Calcula el tiempo total para una lista de tareas.

        Args:
            tasks: Lista de RoomDailyTask

        Returns:
            Tiempo total en minutos
        """
        total = 0
        for task in tasks:
            total += self.calculate_task_time(task)
        return total

    def update_task_estimated_time(self, room_task: RoomDailyTask) -> int:
        """
        Actualiza el tiempo estimado de una tarea y lo guarda.

        Returns:
            Tiempo calculado
        """
        estimated = self.calculate_task_time(room_task)
        room_task.estimated_minutes = estimated
        room_task.save(update_fields=['estimated_minutes'])
        return estimated
