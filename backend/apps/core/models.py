"""
Core models - Base configuration entities.
Defines TimeBlocks, TaskTypes, Zones, and Rooms.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class TimeBlock(models.Model):
    """
    Bloques temporales del día.
    Configurable desde Admin - NO hardcodeado.
    Ejemplos: DAY (mañana), EVENING (tarde+couverture), NIGHT (madrugada)
    """
    code = models.CharField(
        max_length=20,
        unique=True,
        help_text="Código único (ej: DAY, EVENING, NIGHT)"
    )
    name = models.CharField(
        max_length=100,
        help_text="Nombre descriptivo"
    )
    description = models.TextField(
        blank=True,
        help_text="Descripción del bloque"
    )
    start_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Hora de inicio del bloque (ej: 09:00)"
    )
    end_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Hora de fin del bloque (ej: 18:30)"
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Orden de aparición (menor = primero)"
    )
    # Mínimo de personas por turno (para trabajo en parejas)
    min_staff = models.PositiveIntegerField(
        default=2,
        validators=[MinValueValidator(1), MaxValueValidator(20)],
        help_text="Mínimo de personas por turno (ej: 2 para trabajo en parejas)"
    )
    # Horas que este turno ayuda con tareas del otro turno
    helps_other_shift_hours = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=0,
        help_text="Horas que ayuda con tareas del turno DAY (ej: 4.5 para EVENING)"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']
        verbose_name = 'Bloque Temporal'
        verbose_name_plural = 'Bloques Temporales'

    def __str__(self):
        return f"{self.code} - {self.name}"


class TaskType(models.Model):
    """
    Tipos de tareas de housekeeping.
    Configurable desde Admin.
    Ejemplos: DEPART, RECOUCH, ARRIVAL, COUVERTURE
    """
    code = models.CharField(
        max_length=30,
        unique=True,
        help_text="Código único (ej: DEPART, RECOUCH)"
    )
    name = models.CharField(
        max_length=100,
        help_text="Nombre descriptivo"
    )
    description = models.TextField(
        blank=True
    )
    # En qué bloques puede realizarse esta tarea
    allowed_blocks = models.ManyToManyField(
        TimeBlock,
        related_name='task_types',
        help_text="Bloques temporales donde puede realizarse esta tarea"
    )
    # Tiempo base en minutos (para completar la tarea con persons_required personas)
    base_minutes = models.PositiveIntegerField(
        default=30,
        help_text="Tiempo en minutos para completar la tarea (con el número de personas indicado)"
    )
    # Personas requeridas para cumplir el tiempo base
    persons_required = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Personas necesarias para completar en base_minutes (ej: 2 para DEPART)"
    )
    # Hora más temprana para iniciar esta tarea (ej: couverture no antes de 19:00)
    earliest_start_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Hora más temprana para esta tarea (ej: 19:00 para couverture)"
    )
    # Hora límite para terminar esta tarea (ej: recouch antes de 18:30)
    latest_end_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Hora límite para terminar (ej: 18:30 para depart/recouch)"
    )
    # Prioridad para ordenar (menor = más prioritario)
    priority = models.PositiveIntegerField(
        default=50,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text="Prioridad 1-100 (menor = más prioritario)"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['priority', 'code']
        verbose_name = 'Tipo de Tarea'
        verbose_name_plural = 'Tipos de Tareas'

    def __str__(self):
        return f"{self.code} - {self.name}"


class Building(models.Model):
    """
    Edificio del hotel (para hoteles con múltiples edificios).
    """
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Edificio'
        verbose_name_plural = 'Edificios'

    def __str__(self):
        return self.name


class Zone(models.Model):
    """
    Zonas del hotel para asignación eficiente.
    Puede ser: Piso, Ala, Sección, etc.
    """
    code = models.CharField(
        max_length=20,
        unique=True,
        help_text="Código único (ej: P2, ALA_NORTE)"
    )
    name = models.CharField(
        max_length=100,
        help_text="Nombre descriptivo (ej: Piso 2, Ala Norte)"
    )
    building = models.ForeignKey(
        Building,
        on_delete=models.CASCADE,
        related_name='zones',
        null=True,
        blank=True
    )
    floor_number = models.IntegerField(
        null=True,
        blank=True,
        help_text="Número de piso (para ordenar por proximidad)"
    )
    priority_order = models.PositiveIntegerField(
        default=0,
        help_text="Orden de prioridad para asignación"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['building', 'floor_number', 'priority_order']
        verbose_name = 'Zona'
        verbose_name_plural = 'Zonas'

    def __str__(self):
        if self.building:
            return f"{self.building.code} - {self.name}"
        return self.name


class RoomType(models.Model):
    """
    Tipos de habitación con sus multiplicadores de tiempo.
    """
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=100)
    # Multiplicador de tiempo (ej: Suite = 1.5, VIP = 1.3)
    time_multiplier = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=1.00,
        validators=[MinValueValidator(0.5), MaxValueValidator(3.0)],
        help_text="Multiplicador de tiempo (1.0 = normal, 1.5 = 50% más)"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Tipo de Habitación'
        verbose_name_plural = 'Tipos de Habitación'

    def __str__(self):
        return f"{self.code} (x{self.time_multiplier})"


class Room(models.Model):
    """
    Habitación del hotel.
    """
    number = models.CharField(
        max_length=20,
        unique=True,
        help_text="Número de habitación"
    )
    zone = models.ForeignKey(
        Zone,
        on_delete=models.CASCADE,
        related_name='rooms'
    )
    room_type = models.ForeignKey(
        RoomType,
        on_delete=models.PROTECT,
        related_name='rooms'
    )
    # Orden dentro de la zona (para recorrido eficiente)
    order_in_zone = models.PositiveIntegerField(
        default=0,
        help_text="Orden dentro de la zona para recorrido eficiente"
    )
    # Lado del pasillo (para dividir zona si es necesario)
    SIDE_CHOICES = [
        ('A', 'Lado A (Par/Izquierda)'),
        ('B', 'Lado B (Impar/Derecha)'),
        ('N', 'No aplica'),
    ]
    corridor_side = models.CharField(
        max_length=1,
        choices=SIDE_CHOICES,
        default='N',
        help_text="Lado del pasillo para optimizar recorrido"
    )
    is_active = models.BooleanField(default=True)
    notes = models.TextField(
        blank=True,
        help_text="Notas especiales sobre la habitación"
    )

    class Meta:
        ordering = ['zone', 'order_in_zone', 'number']
        verbose_name = 'Habitación'
        verbose_name_plural = 'Habitaciones'

    def __str__(self):
        return f"{self.number} ({self.zone.code})"

    @property
    def floor(self):
        """Retorna el piso basado en la zona."""
        return self.zone.floor_number


class DayOfWeek(models.Model):
    """
    Días de la semana - para configuración.
    """
    code = models.CharField(max_length=3, unique=True)  # LUN, MAR, MIE...
    name = models.CharField(max_length=20)
    iso_weekday = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(7)],
        help_text="1=Lunes, 7=Domingo (ISO)"
    )

    class Meta:
        ordering = ['iso_weekday']
        verbose_name = 'Día de la Semana'
        verbose_name_plural = 'Días de la Semana'

    def __str__(self):
        return self.name
