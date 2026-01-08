"""
Planning models - WeekPlan, DailyPlan, Assignments.
WeekPlan = Horario laboral de cada empleado
DailyPlan = Asignación de tareas específicas del día
"""
from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from apps.core.models import TimeBlock, Zone
from apps.staff.models import Employee, Team
from apps.shifts.models import ShiftTemplate
from apps.rooms.models import RoomDailyTask


class WeekPlan(models.Model):
    """
    Plan semanal = Horario laboral de cada empleado.
    Define qué días trabaja cada persona y en qué turno.
    """
    # Identificación de la semana
    week_start_date = models.DateField(
        help_text="Fecha del lunes de la semana"
    )
    name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Nombre opcional (ej: 'Semana 3 - Enero')"
    )

    # Estado
    STATUS_CHOICES = [
        ('DRAFT', 'Borrador'),
        ('REVIEW', 'En revisión'),
        ('APPROVED', 'Aprobado'),
        ('PUBLISHED', 'Publicado'),
        ('ARCHIVED', 'Archivado'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='DRAFT'
    )

    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=100, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)

    # Notas
    notes = models.TextField(
        blank=True,
        help_text="Notas sobre el plan semanal"
    )

    class Meta:
        unique_together = ['week_start_date']
        ordering = ['-week_start_date']
        verbose_name = 'Plan Semanal'
        verbose_name_plural = 'Planes Semanales'

    def __str__(self):
        status_display = self.get_status_display()
        return f"Semana {self.week_start_date} ({status_display})"

    def clean(self):
        # Verificar que week_start_date sea un lunes
        if self.week_start_date and self.week_start_date.weekday() != 0:
            raise ValidationError("La fecha de inicio debe ser un lunes.")

    @property
    def week_end_date(self):
        """Retorna el domingo de la semana."""
        from datetime import timedelta
        return self.week_start_date + timedelta(days=6)

    def get_days(self):
        """Retorna lista de fechas de la semana."""
        from datetime import timedelta
        return [self.week_start_date + timedelta(days=i) for i in range(7)]

    def get_total_assigned_hours(self):
        """Total de horas asignadas en el plan."""
        return sum(
            a.assigned_hours for a in self.shift_assignments.all()
        )


class ShiftAssignment(models.Model):
    """
    Asignación de turno a un empleado o equipo para un día específico.
    Es parte del WeekPlan (horario laboral).
    """
    week_plan = models.ForeignKey(
        WeekPlan,
        on_delete=models.CASCADE,
        related_name='shift_assignments'
    )
    date = models.DateField(
        help_text="Fecha específica"
    )

    # Asignación a empleado O equipo (uno de los dos)
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='shift_assignments'
    )
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='shift_assignments'
    )

    # Turno asignado
    shift_template = models.ForeignKey(
        ShiftTemplate,
        on_delete=models.PROTECT,
        related_name='assignments'
    )

    # Horas asignadas (puede diferir del template si hay ajuste)
    assigned_hours = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        help_text="Horas asignadas (puede ajustarse del template)"
    )

    # Es día libre?
    is_day_off = models.BooleanField(
        default=False,
        help_text="Marcar si es día libre"
    )

    # Notas
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['date', 'shift_template__time_block__order']
        verbose_name = 'Asignación de Turno'
        verbose_name_plural = 'Asignaciones de Turno'

    def __str__(self):
        assignee = self.employee or self.team
        if self.is_day_off:
            return f"{self.date} - {assignee} - LIBRE"
        return f"{self.date} - {assignee} - {self.shift_template.code}"

    def clean(self):
        if not self.employee and not self.team:
            raise ValidationError("Debe asignar a un empleado o a un equipo.")
        if self.employee and self.team:
            raise ValidationError("No puede asignar a empleado y equipo simultáneamente.")

    @property
    def time_block(self):
        return self.shift_template.time_block

    def get_assignee_name(self):
        """Nombre del asignado."""
        if self.employee:
            return self.employee.full_name
        if self.team:
            return str(self.team)
        return "Sin asignar"


class DailyPlan(models.Model):
    """
    Plan diario = Asignación de tareas específicas.
    Define qué habitaciones le tocan a cada empleado/equipo.
    """
    date = models.DateField(unique=True)
    week_plan = models.ForeignKey(
        WeekPlan,
        on_delete=models.CASCADE,
        related_name='daily_plans',
        null=True,
        blank=True
    )

    # Estado
    STATUS_CHOICES = [
        ('DRAFT', 'Borrador'),
        ('ACTIVE', 'Activo'),
        ('COMPLETED', 'Completado'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='DRAFT'
    )

    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-date']
        verbose_name = 'Plan Diario'
        verbose_name_plural = 'Planes Diarios'

    def __str__(self):
        return f"Plan {self.date} ({self.get_status_display()})"

    def get_total_tasks(self):
        return self.task_assignments.count()

    def get_completed_tasks(self):
        return self.task_assignments.filter(status='COMPLETED').count()


class TaskAssignment(models.Model):
    """
    Asignación de una tarea específica a un empleado/equipo.
    Es parte del DailyPlan.
    """
    daily_plan = models.ForeignKey(
        DailyPlan,
        on_delete=models.CASCADE,
        related_name='task_assignments'
    )
    room_task = models.ForeignKey(
        RoomDailyTask,
        on_delete=models.CASCADE,
        related_name='assignments'
    )

    # Asignación
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='task_assignments'
    )
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='task_assignments'
    )

    # Zona asignada (para tracking)
    zone = models.ForeignKey(
        Zone,
        on_delete=models.PROTECT,
        related_name='task_assignments'
    )

    # Orden dentro de la asignación del día
    order_in_assignment = models.PositiveIntegerField(
        default=0,
        help_text="Orden de la tarea para este empleado/equipo"
    )

    # Estado
    STATUS_CHOICES = [
        ('PENDING', 'Pendiente'),
        ('IN_PROGRESS', 'En progreso'),
        ('COMPLETED', 'Completada'),
        ('SKIPPED', 'Omitida'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )

    # Hora real de ejecución
    started_at = models.TimeField(null=True, blank=True)
    completed_at = models.TimeField(null=True, blank=True)

    # Notas
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['zone', 'order_in_assignment']
        verbose_name = 'Asignación de Tarea'
        verbose_name_plural = 'Asignaciones de Tareas'

    def __str__(self):
        assignee = self.employee or self.team
        return f"{self.room_task} → {assignee}"

    def clean(self):
        if not self.employee and not self.team:
            raise ValidationError("Debe asignar a un empleado o a un equipo.")

    @property
    def room(self):
        return self.room_task.room

    @property
    def task_type(self):
        return self.room_task.task_type


class DailyLoadSummary(models.Model):
    """
    Resumen de carga diaria por bloque temporal.
    Calculado automáticamente para dashboard.
    """
    date = models.DateField()
    time_block = models.ForeignKey(
        TimeBlock,
        on_delete=models.CASCADE,
        related_name='load_summaries'
    )

    # Carga (demanda)
    total_tasks = models.PositiveIntegerField(default=0)
    total_minutes_required = models.PositiveIntegerField(default=0)

    # Capacidad (oferta)
    total_employees = models.PositiveIntegerField(default=0)
    total_minutes_available = models.PositiveIntegerField(default=0)

    # Balance
    @property
    def balance_minutes(self):
        return self.total_minutes_available - self.total_minutes_required

    @property
    def load_percentage(self):
        if self.total_minutes_available == 0:
            return 0
        return round(
            (self.total_minutes_required / self.total_minutes_available) * 100,
            1
        )

    @property
    def is_overloaded(self):
        return self.total_minutes_required > self.total_minutes_available

    # Timestamps
    calculated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['date', 'time_block']
        ordering = ['date', 'time_block__order']
        verbose_name = 'Resumen de Carga Diaria'
        verbose_name_plural = 'Resúmenes de Carga Diaria'

    def __str__(self):
        return f"{self.date} - {self.time_block.code}: {self.load_percentage}%"


class PlanningAlert(models.Model):
    """
    Alertas generadas durante la planificación.
    Para mostrar en dashboard.
    """
    date = models.DateField()
    time_block = models.ForeignKey(
        TimeBlock,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='alerts'
    )

    # Tipo de alerta
    ALERT_TYPE_CHOICES = [
        ('OVERLOAD', 'Sobrecarga'),
        ('UNDERSTAFF', 'Falta personal'),
        ('CONFLICT', 'Conflicto de asignación'),
        ('WARNING', 'Advertencia'),
        ('INFO', 'Información'),
    ]
    alert_type = models.CharField(
        max_length=20,
        choices=ALERT_TYPE_CHOICES,
        default='WARNING'
    )

    # Severidad
    SEVERITY_CHOICES = [
        ('LOW', 'Baja'),
        ('MEDIUM', 'Media'),
        ('HIGH', 'Alta'),
        ('CRITICAL', 'Crítica'),
    ]
    severity = models.CharField(
        max_length=10,
        choices=SEVERITY_CHOICES,
        default='MEDIUM'
    )

    # Mensaje
    title = models.CharField(max_length=200)
    message = models.TextField()

    # Estado
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.CharField(max_length=100, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Alerta de Planificación'
        verbose_name_plural = 'Alertas de Planificación'

    def __str__(self):
        return f"{self.date} - {self.title}"
