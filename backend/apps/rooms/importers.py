"""
CSV Protel Importer.
Parsea archivos CSV de Protel y genera RoomDailyState y RoomDailyTask.
"""
import csv
import io
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from django.db import transaction
from apps.core.models import Room, TaskType, TimeBlock
from apps.rooms.models import RoomDailyState, RoomDailyTask, ProtelImportLog


class ProtelCSVImporter:
    """
    Importador de CSV de Protel.

    Formato esperado del CSV:
    date,room,housekeeping_type,arrival_time,departure_time,status,guest_name,stay_day,vip

    Ejemplo:
    2026-01-20,305,RECOUCH,,,OCCUPIED,,3,0
    2026-01-20,305,COUVERTURE,,,OCCUPIED,,3,0
    2026-01-20,401,DEPART,,11:00,CHECKOUT,Guest Name,1,0
    2026-01-20,401,ARRIVAL,15:00,,CHECKIN,New Guest,1,1
    """

    # Mapeo de tipos de housekeeping de Protel a TaskType codes
    TASK_TYPE_MAPPING = {
        'DEPART': 'DEPART',
        'DEPARTURE': 'DEPART',
        'CHECKOUT': 'DEPART',
        'RECOUCH': 'RECOUCH',
        'RECOUCHE': 'RECOUCH',
        'OCCUPIED': 'RECOUCH',
        'ARRIVAL': 'ARRIVAL',
        'CHECKIN': 'ARRIVAL',
        'COUVERTURE': 'COUVERTURE',
        'TURNDOWN': 'COUVERTURE',
        'TOUCHUP': 'TOUCHUP',
        'TOUCH_UP': 'TOUCHUP',
    }

    # Mapeo de status de Protel a occupancy_status
    STATUS_MAPPING = {
        'VACANT': 'VACANT',
        'EMPTY': 'VACANT',
        'OCCUPIED': 'OCCUPIED',
        'STAY': 'OCCUPIED',
        'CHECKOUT': 'CHECKOUT',
        'DEPARTURE': 'CHECKOUT',
        'DEP': 'CHECKOUT',
        'CHECKIN': 'CHECKIN',
        'ARRIVAL': 'CHECKIN',
        'ARR': 'CHECKIN',
        'TURNOVER': 'TURNOVER',
        'OOO': 'OOO',
        'OUT_OF_ORDER': 'OOO',
    }

    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.stats = {
            'rows_processed': 0,
            'rows_success': 0,
            'rows_error': 0,
            'states_created': 0,
            'tasks_created': 0,
        }
        # Cache de objetos para evitar queries repetidas
        self._room_cache: Dict[str, Room] = {}
        self._task_type_cache: Dict[str, TaskType] = {}
        self._time_block_cache: Dict[str, TimeBlock] = {}

    def _get_room(self, room_number: str) -> Optional[Room]:
        """Obtiene habitación del cache o DB."""
        if room_number not in self._room_cache:
            try:
                self._room_cache[room_number] = Room.objects.get(number=room_number)
            except Room.DoesNotExist:
                self._room_cache[room_number] = None
        return self._room_cache[room_number]

    def _get_task_type(self, code: str) -> Optional[TaskType]:
        """Obtiene tipo de tarea del cache o DB."""
        mapped_code = self.TASK_TYPE_MAPPING.get(code.upper(), code.upper())
        if mapped_code not in self._task_type_cache:
            try:
                self._task_type_cache[mapped_code] = TaskType.objects.get(code=mapped_code)
            except TaskType.DoesNotExist:
                self._task_type_cache[mapped_code] = None
        return self._task_type_cache[mapped_code]

    def _get_time_block_for_task(self, task_type: TaskType) -> Optional[TimeBlock]:
        """Obtiene el bloque temporal apropiado para una tarea."""
        # Usar el primer bloque permitido de la tarea
        block = task_type.allowed_blocks.first()
        return block

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parsea fecha en varios formatos."""
        formats = ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d']
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt).date()
            except ValueError:
                continue
        return None

    def _parse_time(self, time_str: str) -> Optional[datetime]:
        """Parsea hora."""
        if not time_str or not time_str.strip():
            return None
        formats = ['%H:%M', '%H:%M:%S', '%I:%M %p']
        for fmt in formats:
            try:
                return datetime.strptime(time_str.strip(), fmt).time()
            except ValueError:
                continue
        return None

    def _process_row(
        self,
        row: Dict,
        row_number: int,
        states_by_room_date: Dict
    ) -> bool:
        """
        Procesa una fila del CSV.
        Retorna True si fue exitoso, False si hubo error.
        """
        try:
            # Extraer campos
            date_str = row.get('date', '').strip()
            room_number = row.get('room', '').strip()
            hk_type = row.get('housekeeping_type', row.get('hk_type', '')).strip()
            arrival_time = row.get('arrival_time', '').strip()
            departure_time = row.get('departure_time', '').strip()
            status = row.get('status', '').strip()
            stay_day = row.get('stay_day', '1').strip()
            vip = row.get('vip', '0').strip()

            # Validar campos requeridos
            if not date_str:
                self.errors.append(f"Fila {row_number}: fecha vacía")
                return False
            if not room_number:
                self.errors.append(f"Fila {row_number}: habitación vacía")
                return False

            # Parsear fecha
            date = self._parse_date(date_str)
            if not date:
                self.errors.append(f"Fila {row_number}: formato de fecha inválido '{date_str}'")
                return False

            # Buscar habitación
            room = self._get_room(room_number)
            if not room:
                self.errors.append(f"Fila {row_number}: habitación '{room_number}' no existe")
                return False

            # Crear o actualizar RoomDailyState
            state_key = (date, room.id)
            if state_key not in states_by_room_date:
                # Determinar occupancy_status
                occupancy_status = self.STATUS_MAPPING.get(
                    status.upper(),
                    'OCCUPIED'
                )

                state = RoomDailyState(
                    date=date,
                    room=room,
                    occupancy_status=occupancy_status,
                    stay_day_number=int(stay_day) if stay_day.isdigit() else 1,
                    expected_checkout_time=self._parse_time(departure_time),
                    expected_checkin_time=self._parse_time(arrival_time),
                    is_vip=vip in ('1', 'true', 'True', 'yes', 'Yes', 'VIP'),
                )
                states_by_room_date[state_key] = state
                self.stats['states_created'] += 1
            else:
                state = states_by_room_date[state_key]

            # Si hay tipo de housekeeping, crear tarea
            if hk_type:
                task_type = self._get_task_type(hk_type)
                if not task_type:
                    self.warnings.append(
                        f"Fila {row_number}: tipo de tarea '{hk_type}' no reconocido, ignorado"
                    )
                else:
                    time_block = self._get_time_block_for_task(task_type)
                    if time_block:
                        task = RoomDailyTask(
                            room_daily_state=state,
                            task_type=task_type,
                            time_block=time_block,
                            estimated_minutes=task_type.base_minutes,
                        )
                        # Guardar referencia para crear después
                        if not hasattr(state, '_pending_tasks'):
                            state._pending_tasks = []
                        state._pending_tasks.append(task)
                        self.stats['tasks_created'] += 1

            return True

        except Exception as e:
            self.errors.append(f"Fila {row_number}: error inesperado - {str(e)}")
            return False

    @transaction.atomic
    def import_csv(
        self,
        file_content: str,
        filename: str = 'import.csv',
        imported_by: str = ''
    ) -> Tuple[bool, ProtelImportLog]:
        """
        Importa un archivo CSV de Protel.

        Args:
            file_content: Contenido del CSV como string
            filename: Nombre del archivo
            imported_by: Usuario que realiza la importación

        Returns:
            Tuple de (success, ProtelImportLog)
        """
        # Crear log de importación
        import_log = ProtelImportLog(
            filename=filename,
            imported_by=imported_by,
            status='PROCESSING'
        )
        import_log.save()

        try:
            # Parsear CSV
            reader = csv.DictReader(io.StringIO(file_content))

            # Diccionario para agrupar estados por room+date
            states_by_room_date: Dict[Tuple, RoomDailyState] = {}

            # Procesar filas
            for row_number, row in enumerate(reader, start=2):
                self.stats['rows_processed'] += 1
                if self._process_row(row, row_number, states_by_room_date):
                    self.stats['rows_success'] += 1
                else:
                    self.stats['rows_error'] += 1

            # Guardar todos los estados
            dates = set()
            for state in states_by_room_date.values():
                # Verificar si ya existe
                existing = RoomDailyState.objects.filter(
                    date=state.date,
                    room=state.room
                ).first()

                if existing:
                    # Actualizar existente
                    existing.occupancy_status = state.occupancy_status
                    existing.stay_day_number = state.stay_day_number
                    existing.expected_checkout_time = state.expected_checkout_time
                    existing.expected_checkin_time = state.expected_checkin_time
                    existing.is_vip = state.is_vip
                    existing.save()
                    state_to_use = existing
                else:
                    state.save()
                    state_to_use = state

                dates.add(state.date)

                # Crear tareas pendientes
                if hasattr(state, '_pending_tasks'):
                    for task in state._pending_tasks:
                        task.room_daily_state = state_to_use
                        # Verificar si ya existe
                        if not RoomDailyTask.objects.filter(
                            room_daily_state=state_to_use,
                            task_type=task.task_type,
                            time_block=task.time_block
                        ).exists():
                            task.save()

            # Actualizar log
            import_log.rows_processed = self.stats['rows_processed']
            import_log.rows_success = self.stats['rows_success']
            import_log.rows_error = self.stats['rows_error']
            import_log.errors = '\n'.join(self.errors[:100])  # Limitar errores

            if dates:
                import_log.date_from = min(dates)
                import_log.date_to = max(dates)

            import_log.status = 'COMPLETED' if self.stats['rows_error'] == 0 else 'COMPLETED'
            import_log.save()

            return True, import_log

        except Exception as e:
            import_log.status = 'FAILED'
            import_log.errors = str(e)
            import_log.save()
            raise

    def get_summary(self) -> Dict:
        """Retorna resumen de la importación."""
        return {
            'stats': self.stats,
            'errors': self.errors,
            'warnings': self.warnings,
        }
