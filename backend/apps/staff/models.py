"""
Staff models - Employees, Teams, and Availability.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from apps.core.models import TimeBlock, TaskType, DayOfWeek


class Role(models.Model):
    """
    Roles del personal.
    Ejemplos: FDC, VDC, EQUIPIER_JOUR, EQUIPIER_NUIT, GG, ASST_GG, GOUV_SOIR
    """
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    # Bloques donde este rol puede trabajar
    allowed_blocks = models.ManyToManyField(
        TimeBlock,
        related_name='roles',
        help_text="Bloques temporales donde este rol puede trabajar"
    )
    # ¿Este rol limpia habitaciones?
    can_clean_rooms = models.BooleanField(
        default=False,
        help_text="¿Este rol realiza limpieza de habitaciones?"
    )
    # Orden para mostrar en UI
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['display_order', 'code']
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'

    def __str__(self):
        return f"{self.code} - {self.name}"


class Employee(models.Model):
    """
    Empleado del equipo de housekeeping.
    """
    # Identificación
    employee_code = models.CharField(
        max_length=20,
        unique=True,
        help_text="Código único del empleado"
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    # Rol
    role = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,
        related_name='employees'
    )

    # Bloques donde puede trabajar (subconjunto de los del rol)
    allowed_blocks = models.ManyToManyField(
        TimeBlock,
        related_name='employees',
        help_text="Bloques donde puede trabajar este empleado"
    )

    # Horas semanales - VARIABLE por empleado
    weekly_hours_target = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        validators=[MinValueValidator(0), MaxValueValidator(48)],
        help_text="Horas semanales objetivo (ej: 35, 24, 20)"
    )

    # Elasticidad
    ELASTICITY_CHOICES = [
        ('LOW', 'Baja - No estirar horas'),
        ('MEDIUM', 'Media - Puede hacer ±2h'),
        ('HIGH', 'Alta - Flexible, puede cubrir huecos'),
    ]
    elasticity = models.CharField(
        max_length=10,
        choices=ELASTICITY_CHOICES,
        default='MEDIUM',
        help_text="Flexibilidad para ajustar horas"
    )

    # Días de descanso fijos (opcional)
    # Si está vacío, el sistema elige los días óptimos
    fixed_days_off = models.ManyToManyField(
        DayOfWeek,
        blank=True,
        related_name='employees_off',
        help_text="Días fijos de descanso. Si vacío, el sistema elige."
    )

    # Tareas elegibles
    eligible_tasks = models.ManyToManyField(
        TaskType,
        related_name='eligible_employees',
        help_text="Tareas que puede realizar este empleado"
    )

    # Puede trabajar NIGHT
    can_work_night = models.BooleanField(
        default=False,
        help_text="¿Puede trabajar en bloque NIGHT?"
    )

    # Estado
    is_active = models.BooleanField(default=True)
    hire_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['last_name', 'first_name']
        verbose_name = 'Empleado'
        verbose_name_plural = 'Empleados'

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.role.code})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def clean(self):
        """Validar que los bloques del empleado estén dentro de los del rol."""
        if self.pk and self.role:
            role_blocks = set(self.role.allowed_blocks.values_list('id', flat=True))
            emp_blocks = set(self.allowed_blocks.values_list('id', flat=True))
            if not emp_blocks.issubset(role_blocks):
                raise ValidationError(
                    "Los bloques del empleado deben estar dentro de los permitidos por su rol."
                )


class Team(models.Model):
    """
    Equipo/Pareja de trabajo.
    Las parejas son unidades de cálculo para asignación.
    """
    name = models.CharField(
        max_length=100,
        help_text="Nombre del equipo (ej: 'María + Carmen')"
    )

    # Miembros del equipo
    members = models.ManyToManyField(
        Employee,
        related_name='teams'
    )

    # Tipo de pareja
    TEAM_TYPE_CHOICES = [
        ('FIXED', 'Fija - Siempre juntas'),
        ('PREFERRED', 'Preferida - Juntas por defecto'),
        ('TEMPORARY', 'Temporal - Solo para esta semana'),
    ]
    team_type = models.CharField(
        max_length=20,
        choices=TEAM_TYPE_CHOICES,
        default='FIXED'
    )

    # Activo
    is_active = models.BooleanField(default=True)

    # Notas
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Equipo/Pareja'
        verbose_name_plural = 'Equipos/Parejas'

    def __str__(self):
        if self.members.exists():
            names = ' + '.join([e.first_name for e in self.members.all()[:3]])
            return f"{names} ({self.get_team_type_display()})"
        return self.name

    @property
    def member_count(self):
        return self.members.count()

    def get_combined_weekly_hours(self):
        """Suma de horas semanales de todos los miembros."""
        return sum(m.weekly_hours_target for m in self.members.all())

    def get_common_eligible_tasks(self):
        """Tareas que pueden hacer TODOS los miembros."""
        members = list(self.members.all())
        if not members:
            return TaskType.objects.none()

        common_tasks = set(members[0].eligible_tasks.values_list('id', flat=True))
        for member in members[1:]:
            member_tasks = set(member.eligible_tasks.values_list('id', flat=True))
            common_tasks = common_tasks.intersection(member_tasks)

        return TaskType.objects.filter(id__in=common_tasks)

    def get_common_blocks(self):
        """Bloques donde pueden trabajar TODOS los miembros."""
        members = list(self.members.all())
        if not members:
            return TimeBlock.objects.none()

        common_blocks = set(members[0].allowed_blocks.values_list('id', flat=True))
        for member in members[1:]:
            member_blocks = set(member.allowed_blocks.values_list('id', flat=True))
            common_blocks = common_blocks.intersection(member_blocks)

        return TimeBlock.objects.filter(id__in=common_blocks)


class EmployeeUnavailability(models.Model):
    """
    Indisponibilidades específicas de empleados.
    Para vacaciones, bajas, etc.
    """
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='unavailabilities'
    )
    date_start = models.DateField()
    date_end = models.DateField()

    REASON_CHOICES = [
        ('VACATION', 'Vacaciones'),
        ('SICK', 'Baja médica'),
        ('PERSONAL', 'Asunto personal'),
        ('TRAINING', 'Formación'),
        ('OTHER', 'Otro'),
    ]
    reason = models.CharField(
        max_length=20,
        choices=REASON_CHOICES,
        default='OTHER'
    )
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Indisponibilidad'
        verbose_name_plural = 'Indisponibilidades'
        ordering = ['date_start']

    def __str__(self):
        return f"{self.employee} - {self.date_start} a {self.date_end}"

    def clean(self):
        if self.date_end < self.date_start:
            raise ValidationError("La fecha fin no puede ser anterior a la fecha inicio.")
