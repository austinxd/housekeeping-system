"""
Rooms models - Room Daily State and Tasks.
El estado diario de la habitación es el corazón del sistema.
Conecta lo que pasa en el día con lo que pasa en la noche.
"""
from django.db import models
from django.core.validators import MinValueValidator
from apps.core.models import Room, TaskType, TimeBlock


class RoomDailyState(models.Model):
    """
    Estado diario de una habitación.
    Generado desde CSV Protel o manualmente.

    Regla crítica: Si stay >= 2 y RECOUCH = DECLINED,
    la couverture nocturna será más difícil (HARD).
    """
    date = models.DateField(
        help_text="Fecha del estado"
    )
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name='daily_states'
    )

    # Estado de ocupación
    OCCUPANCY_STATUS_CHOICES = [
        ('VACANT', 'Vacante'),
        ('OCCUPIED', 'Ocupada'),
        ('CHECKOUT', 'Checkout (salida)'),
        ('CHECKIN', 'Checkin (llegada)'),
        ('TURNOVER', 'Turnover (salida + llegada)'),
        ('OOO', 'Fuera de servicio'),
    ]
    occupancy_status = models.CharField(
        max_length=20,
        choices=OCCUPANCY_STATUS_CHOICES,
        default='VACANT'
    )

    # Día de estancia (para clientes que se quedan varios días)
    stay_day_number = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Día de estancia del huésped (1 = primera noche)"
    )

    # Horas de check-in/check-out (si aplica)
    expected_checkout_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Hora prevista de checkout"
    )
    expected_checkin_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Hora prevista de checkin"
    )

    # Estado de limpieza del día
    DAY_CLEANING_STATUS_CHOICES = [
        ('PENDING', 'Pendiente'),
        ('IN_PROGRESS', 'En progreso'),
        ('DONE', 'Realizado'),
        ('DECLINED', 'Rechazado por huésped'),
        ('NOT_REQUIRED', 'No requerido'),
    ]
    day_cleaning_status = models.CharField(
        max_length=20,
        choices=DAY_CLEANING_STATUS_CHOICES,
        default='PENDING'
    )

    # Dificultad esperada de la couverture nocturna
    # Se calcula automáticamente basado en el estado del día
    NIGHT_DIFFICULTY_CHOICES = [
        ('NORMAL', 'Normal'),
        ('HARD', 'Difícil (recouch rechazado)'),
        ('VERY_HARD', 'Muy difícil'),
    ]
    night_expected_difficulty = models.CharField(
        max_length=20,
        choices=NIGHT_DIFFICULTY_CHOICES,
        default='NORMAL'
    )

    # VIP o cliente especial
    is_vip = models.BooleanField(
        default=False,
        help_text="¿Es cliente VIP?"
    )

    # Notas especiales
    notes = models.TextField(
        blank=True,
        help_text="Notas especiales para este día"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['date', 'room']
        ordering = ['date', 'room__zone', 'room__order_in_zone']
        verbose_name = 'Estado Diario de Habitación'
        verbose_name_plural = 'Estados Diarios de Habitaciones'

    def __str__(self):
        return f"{self.room.number} - {self.date} ({self.get_occupancy_status_display()})"

    def update_night_difficulty(self):
        """
        Actualiza la dificultad nocturna basado en el estado del día.
        Si stay >= 2 y recouch fue rechazado, la couverture es HARD.
        """
        if self.stay_day_number >= 2 and self.day_cleaning_status == 'DECLINED':
            self.night_expected_difficulty = 'HARD'
        else:
            self.night_expected_difficulty = 'NORMAL'

    def save(self, *args, **kwargs):
        self.update_night_difficulty()
        super().save(*args, **kwargs)


class RoomDailyTask(models.Model):
    """
    Tarea específica para una habitación en un día.
    Generado desde CSV Protel.
    """
    room_daily_state = models.ForeignKey(
        RoomDailyState,
        on_delete=models.CASCADE,
        related_name='tasks'
    )
    task_type = models.ForeignKey(
        TaskType,
        on_delete=models.PROTECT,
        related_name='room_tasks'
    )
    time_block = models.ForeignKey(
        TimeBlock,
        on_delete=models.PROTECT,
        related_name='room_tasks',
        help_text="Bloque temporal donde se debe realizar"
    )

    # Tiempo estimado (calculado con reglas)
    estimated_minutes = models.PositiveIntegerField(
        default=0,
        help_text="Tiempo estimado en minutos"
    )

    # Estado de la tarea
    STATUS_CHOICES = [
        ('PENDING', 'Pendiente'),
        ('ASSIGNED', 'Asignada'),
        ('IN_PROGRESS', 'En progreso'),
        ('COMPLETED', 'Completada'),
        ('CANCELLED', 'Cancelada'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )

    # Prioridad (para ordenar)
    priority = models.PositiveIntegerField(
        default=50,
        help_text="Prioridad 1-100 (menor = más prioritario)"
    )

    # Notas
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['priority', 'task_type__priority']
        verbose_name = 'Tarea de Habitación'
        verbose_name_plural = 'Tareas de Habitaciones'

    def __str__(self):
        return f"{self.room_daily_state.room.number} - {self.task_type.code} ({self.get_status_display()})"

    @property
    def date(self):
        return self.room_daily_state.date

    @property
    def room(self):
        return self.room_daily_state.room


class ProtelImportLog(models.Model):
    """
    Log de importaciones de CSV Protel.
    Para auditoría y tracking.
    """
    filename = models.CharField(max_length=255)
    imported_at = models.DateTimeField(auto_now_add=True)
    imported_by = models.CharField(
        max_length=100,
        blank=True,
        help_text="Usuario que realizó la importación"
    )

    # Estadísticas
    rows_processed = models.PositiveIntegerField(default=0)
    rows_success = models.PositiveIntegerField(default=0)
    rows_error = models.PositiveIntegerField(default=0)

    # Rango de fechas importadas
    date_from = models.DateField(null=True, blank=True)
    date_to = models.DateField(null=True, blank=True)

    # Errores encontrados
    errors = models.TextField(
        blank=True,
        help_text="Lista de errores encontrados durante la importación"
    )

    # Estado
    STATUS_CHOICES = [
        ('PENDING', 'Pendiente'),
        ('PROCESSING', 'Procesando'),
        ('COMPLETED', 'Completado'),
        ('FAILED', 'Fallido'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )

    class Meta:
        ordering = ['-imported_at']
        verbose_name = 'Log de Importación Protel'
        verbose_name_plural = 'Logs de Importación Protel'

    def __str__(self):
        return f"{self.filename} - {self.imported_at.strftime('%Y-%m-%d %H:%M')}"
