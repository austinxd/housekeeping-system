"""
Rules models - Configurable time rules and modifiers.
Todo es configurable desde Admin, no hardcodeado.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.core.models import TaskType, RoomType


class TaskTimeRule(models.Model):
    """
    Reglas de tiempo para tareas.
    Define el tiempo base y multiplicadores por condiciones.

    Ejemplo:
    - DEPART base: 45 min
    - DEPART + Suite: ×1.5
    - COUVERTURE + recouch_declined: ×1.4
    """
    task_type = models.ForeignKey(
        TaskType,
        on_delete=models.CASCADE,
        related_name='time_rules'
    )

    # Condición (opcional)
    CONDITION_CHOICES = [
        ('NONE', 'Sin condición (base)'),
        ('SUITE', 'Es Suite'),
        ('VIP', 'Es VIP'),
        ('RECOUCH_DECLINED', 'Recouch rechazado'),
        ('STAY_LONG', 'Estancia larga (>5 días)'),
        ('FIRST_DAY', 'Primer día'),
        ('LATE_CHECKOUT', 'Checkout tardío'),
        ('EARLY_CHECKIN', 'Checkin temprano'),
    ]
    condition = models.CharField(
        max_length=30,
        choices=CONDITION_CHOICES,
        default='NONE',
        help_text="Condición para aplicar esta regla"
    )

    # Tipo de habitación específico (opcional)
    room_type = models.ForeignKey(
        RoomType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='time_rules',
        help_text="Si se especifica, la regla solo aplica a este tipo"
    )

    # Tiempo o multiplicador
    base_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Tiempo base en minutos (si es regla base)"
    )
    time_multiplier = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=1.00,
        validators=[MinValueValidator(0.5), MaxValueValidator(3.0)],
        help_text="Multiplicador de tiempo (ej: 1.4 = +40%)"
    )

    # Prioridad (para resolver conflictos)
    priority = models.PositiveIntegerField(
        default=10,
        help_text="Prioridad de la regla (mayor = se aplica primero)"
    )

    # Descripción para Admin
    description = models.TextField(
        blank=True,
        help_text="Explicación de cuándo y por qué aplica esta regla"
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['task_type', '-priority']
        verbose_name = 'Regla de Tiempo'
        verbose_name_plural = 'Reglas de Tiempo'

    def __str__(self):
        cond = f" ({self.get_condition_display()})" if self.condition != 'NONE' else ""
        room = f" [{self.room_type}]" if self.room_type else ""
        return f"{self.task_type.code}{cond}{room} → ×{self.time_multiplier}"


class ZoneAssignmentRule(models.Model):
    """
    Reglas para asignación de zonas.
    Configura cómo se asignan las zonas a los empleados.
    """
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    # Valor de la regla
    value_boolean = models.BooleanField(
        null=True,
        blank=True,
        help_text="Valor booleano para reglas tipo on/off"
    )
    value_integer = models.IntegerField(
        null=True,
        blank=True,
        help_text="Valor entero para reglas numéricas"
    )
    value_text = models.CharField(
        max_length=200,
        blank=True,
        help_text="Valor texto para reglas de configuración"
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Regla de Asignación de Zona'
        verbose_name_plural = 'Reglas de Asignación de Zona'

    def __str__(self):
        return f"{self.code}: {self.name}"

    @classmethod
    def get_value(cls, code, default=None):
        """Obtiene el valor de una regla por su código."""
        try:
            rule = cls.objects.get(code=code, is_active=True)
            if rule.value_boolean is not None:
                return rule.value_boolean
            if rule.value_integer is not None:
                return rule.value_integer
            if rule.value_text:
                return rule.value_text
            return default
        except cls.DoesNotExist:
            return default


class ElasticityRule(models.Model):
    """
    Reglas de elasticidad para ajuste de horas.
    Define cuántas horas extra puede hacer cada nivel de elasticidad.
    """
    ELASTICITY_CHOICES = [
        ('LOW', 'Baja'),
        ('MEDIUM', 'Media'),
        ('HIGH', 'Alta'),
    ]
    elasticity_level = models.CharField(
        max_length=10,
        choices=ELASTICITY_CHOICES,
        unique=True
    )

    # Horas extra máximas por semana
    max_extra_hours_week = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        default=0,
        help_text="Máximo de horas extra por semana"
    )

    # Horas extra máximas por día
    max_extra_hours_day = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=0,
        help_text="Máximo de horas extra por día"
    )

    # Prioridad para asignar extras (mayor = primero)
    assignment_priority = models.PositiveIntegerField(
        default=1,
        help_text="Prioridad al asignar horas extra (mayor = primero)"
    )

    description = models.TextField(blank=True)

    class Meta:
        ordering = ['-assignment_priority']
        verbose_name = 'Regla de Elasticidad'
        verbose_name_plural = 'Reglas de Elasticidad'

    def __str__(self):
        return f"{self.get_elasticity_level_display()}: max {self.max_extra_hours_week}h/semana"


class PlanningParameter(models.Model):
    """
    Parámetros generales de planificación.
    Configuración global del sistema.
    """
    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Código único del parámetro"
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    # Valor
    value_type = models.CharField(
        max_length=20,
        choices=[
            ('INTEGER', 'Entero'),
            ('DECIMAL', 'Decimal'),
            ('BOOLEAN', 'Booleano'),
            ('TEXT', 'Texto'),
            ('TIME', 'Hora'),
        ],
        default='INTEGER'
    )
    value = models.CharField(
        max_length=200,
        help_text="Valor del parámetro"
    )

    # Categoría para agrupar en Admin
    category = models.CharField(
        max_length=50,
        default='GENERAL',
        help_text="Categoría para agrupar parámetros"
    )

    class Meta:
        ordering = ['category', 'code']
        verbose_name = 'Parámetro de Planificación'
        verbose_name_plural = 'Parámetros de Planificación'

    def __str__(self):
        return f"{self.code} = {self.value}"

    def get_typed_value(self):
        """Retorna el valor convertido al tipo correcto."""
        if self.value_type == 'INTEGER':
            return int(self.value)
        elif self.value_type == 'DECIMAL':
            return float(self.value)
        elif self.value_type == 'BOOLEAN':
            return self.value.lower() in ('true', '1', 'yes', 'si')
        elif self.value_type == 'TIME':
            from datetime import datetime
            return datetime.strptime(self.value, '%H:%M').time()
        return self.value

    @classmethod
    def get(cls, code, default=None):
        """Obtiene valor de parámetro por código."""
        try:
            param = cls.objects.get(code=code)
            return param.get_typed_value()
        except cls.DoesNotExist:
            return default
