"""
Shifts models - Shift Templates and Sub-blocks.
Templates son plantillas de turno completas con sus sub-bloques.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from apps.core.models import TimeBlock
from apps.staff.models import Role


class ShiftTemplate(models.Model):
    """
    Plantilla de turno.
    Define un turno completo con hora inicio, fin, y pausas.
    Ejemplo: HK_DAY (7:00-15:00), HK_EVENING (14:00-22:30)
    """
    code = models.CharField(
        max_length=30,
        unique=True,
        help_text="Código único (ej: HK_DAY, HK_EVENING, EQ_NIGHT)"
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    # Rol para el que aplica esta plantilla
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name='shift_templates'
    )

    # Bloque temporal
    time_block = models.ForeignKey(
        TimeBlock,
        on_delete=models.CASCADE,
        related_name='shift_templates'
    )

    # Horario
    start_time = models.TimeField(help_text="Hora de inicio")
    end_time = models.TimeField(help_text="Hora de fin")

    # Pausa principal (si la hay)
    break_start = models.TimeField(
        null=True,
        blank=True,
        help_text="Inicio de pausa principal"
    )
    break_end = models.TimeField(
        null=True,
        blank=True,
        help_text="Fin de pausa principal"
    )
    break_minutes = models.PositiveIntegerField(
        default=0,
        help_text="Duración de pausa en minutos"
    )

    # Horas objetivo y máximo
    weekly_hours_target = models.PositiveIntegerField(
        default=39,
        help_text="Horas semanales objetivo para este turno"
    )
    max_daily_hours = models.PositiveIntegerField(
        default=8,
        help_text="Máximo de horas por día"
    )

    # Horas efectivas de trabajo
    @property
    def total_minutes(self):
        """Calcula minutos totales del turno."""
        from datetime import datetime, timedelta
        start = datetime.combine(datetime.today(), self.start_time)
        end = datetime.combine(datetime.today(), self.end_time)
        if end < start:
            end += timedelta(days=1)
        diff = (end - start).seconds // 60
        return diff - self.break_minutes

    @property
    def total_hours(self):
        """Horas efectivas de trabajo."""
        return round(self.total_minutes / 60, 2)

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['role', 'time_block__order']
        verbose_name = 'Plantilla de Turno'
        verbose_name_plural = 'Plantillas de Turno'

    def __str__(self):
        return f"{self.code} ({self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')})"

    def clean(self):
        # Validar que break_start y break_end vengan juntos
        if self.break_start and not self.break_end:
            raise ValidationError("Si hay inicio de pausa, debe haber fin de pausa.")
        if self.break_end and not self.break_start:
            raise ValidationError("Si hay fin de pausa, debe haber inicio de pausa.")


class ShiftSubBlock(models.Model):
    """
    Sub-bloque dentro de un turno.
    Ejemplo en HK_EVENING:
      - 14:00-18:30 → STANDARD (recouch, arrivals)
      - 18:30-19:00 → BREAK
      - 19:00-22:30 → COUVERTURE
    """
    shift_template = models.ForeignKey(
        ShiftTemplate,
        on_delete=models.CASCADE,
        related_name='sub_blocks'
    )
    code = models.CharField(
        max_length=30,
        help_text="Código del sub-bloque (ej: STANDARD, COUVERTURE, BREAK)"
    )
    name = models.CharField(max_length=100)

    start_time = models.TimeField()
    end_time = models.TimeField()

    # Es pausa?
    is_break = models.BooleanField(
        default=False,
        help_text="¿Es un bloque de descanso?"
    )

    # Orden dentro del turno
    order = models.PositiveIntegerField(default=0)

    # Descripción de qué se hace en este sub-bloque
    description = models.TextField(
        blank=True,
        help_text="Descripción de las tareas típicas en este sub-bloque"
    )

    class Meta:
        ordering = ['shift_template', 'order', 'start_time']
        verbose_name = 'Sub-bloque de Turno'
        verbose_name_plural = 'Sub-bloques de Turno'

    def __str__(self):
        return f"{self.shift_template.code} / {self.code} ({self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')})"

    @property
    def duration_minutes(self):
        """Duración en minutos."""
        from datetime import datetime, timedelta
        start = datetime.combine(datetime.today(), self.start_time)
        end = datetime.combine(datetime.today(), self.end_time)
        if end < start:
            end += timedelta(days=1)
        return (end - start).seconds // 60
