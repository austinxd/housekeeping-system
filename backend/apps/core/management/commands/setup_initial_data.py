"""
Management command to set up initial data for the housekeeping system.
Creates TimeBlocks, TaskTypes, Roles, Zones, Rooms, ShiftTemplates, and sample Employees.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from datetime import time

from apps.core.models import TimeBlock, TaskType, Building, Zone, RoomType, Room, DayOfWeek
from apps.staff.models import Role, Employee, Team
from apps.shifts.models import ShiftTemplate, ShiftSubBlock
from apps.rules.models import TaskTimeRule, ZoneAssignmentRule, ElasticityRule, PlanningParameter


class Command(BaseCommand):
    help = 'Set up initial data for the housekeeping system'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write('Setting up initial data...')

        self.create_days_of_week()
        self.create_time_blocks()
        self.create_task_types()
        self.create_roles()
        self.create_building_and_zones()
        self.create_room_types()
        self.create_rooms()
        self.create_shift_templates()
        self.create_rules()
        self.create_sample_employees()

        self.stdout.write(self.style.SUCCESS('Initial data created successfully!'))

    def create_days_of_week(self):
        self.stdout.write('  Creating days of week...')
        days = [
            ('LUN', 'Lunes', 1),
            ('MAR', 'Martes', 2),
            ('MIE', 'Miércoles', 3),
            ('JUE', 'Jueves', 4),
            ('VIE', 'Viernes', 5),
            ('SAB', 'Sábado', 6),
            ('DOM', 'Domingo', 7),
        ]
        for code, name, iso in days:
            DayOfWeek.objects.get_or_create(
                code=code,
                defaults={'name': name, 'iso_weekday': iso}
            )

    def create_time_blocks(self):
        self.stdout.write('  Creating time blocks...')
        blocks = [
            ('DAY', 'Mañana / Producción', 'Bloque de limpieza principal (mañana)', 1),
            ('EVENING', 'Tarde + Couverture', 'Bloque de tarde incluyendo couverture', 2),
            ('NIGHT', 'Noche', 'Bloque nocturno (équipier de nuit)', 3),
        ]
        for code, name, desc, order in blocks:
            TimeBlock.objects.get_or_create(
                code=code,
                defaults={'name': name, 'description': desc, 'order': order}
            )

    def create_task_types(self):
        self.stdout.write('  Creating task types...')
        day_block = TimeBlock.objects.get(code='DAY')
        evening_block = TimeBlock.objects.get(code='EVENING')

        tasks = [
            ('DEPART', 'Salida', 'Limpieza completa por checkout', 45, 10, [day_block]),
            ('RECOUCH', 'Recouch', 'Limpieza de habitación ocupada', 25, 30, [day_block, evening_block]),
            ('ARRIVAL', 'Llegada', 'Preparación para checkin', 30, 20, [day_block]),
            ('ARRIVAL_VIP', 'Llegada VIP', 'Preparación especial para VIP', 40, 15, [day_block]),
            ('COUVERTURE', 'Couverture', 'Servicio de cobertura nocturno', 15, 40, [evening_block]),
            ('TOUCHUP', 'Touch-up', 'Retoque rápido', 10, 50, [day_block, evening_block]),
        ]

        for code, name, desc, minutes, priority, blocks in tasks:
            task, created = TaskType.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'description': desc,
                    'base_minutes': minutes,
                    'priority': priority
                }
            )
            if created:
                task.allowed_blocks.set(blocks)

    def create_roles(self):
        self.stdout.write('  Creating roles...')
        day_block = TimeBlock.objects.get(code='DAY')
        evening_block = TimeBlock.objects.get(code='EVENING')
        night_block = TimeBlock.objects.get(code='NIGHT')

        roles = [
            ('HK_FDC', 'Femme de Chambre', 'Housekeeping - limpieza de habitaciones', [day_block, evening_block], 1),
            ('EQUIPIER', 'Équipier', 'Soporte y couverture ligera', [day_block, evening_block, night_block], 2),
            ('GOUVERNANTE', 'Gouvernante', 'Supervisión y control', [day_block, evening_block], 3),
            ('ASSISTANTE', 'Assistante Gouvernante', 'Asistencia a gouvernante', [day_block, evening_block], 4),
        ]

        for code, name, desc, blocks, order in roles:
            role, created = Role.objects.get_or_create(
                code=code,
                defaults={'name': name, 'description': desc, 'display_order': order}
            )
            if created:
                role.allowed_blocks.set(blocks)

    def create_building_and_zones(self):
        self.stdout.write('  Creating building and zones...')
        building, _ = Building.objects.get_or_create(
            code='MAIN',
            defaults={'name': 'Edificio Principal'}
        )

        zones = [
            ('P2', 'Piso 2', 2, 1),
            ('P3', 'Piso 3', 3, 2),
            ('P4', 'Piso 4', 4, 3),
            ('P5', 'Piso 5', 5, 4),
        ]

        for code, name, floor, order in zones:
            Zone.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'building': building,
                    'floor_number': floor,
                    'priority_order': order
                }
            )

    def create_room_types(self):
        self.stdout.write('  Creating room types...')
        types = [
            ('STANDARD', 'Standard', 1.0),
            ('SUPERIOR', 'Superior', 1.1),
            ('SUITE', 'Suite', 1.5),
            ('JUNIOR_SUITE', 'Junior Suite', 1.3),
        ]

        for code, name, multiplier in types:
            RoomType.objects.get_or_create(
                code=code,
                defaults={'name': name, 'time_multiplier': multiplier}
            )

    def create_rooms(self):
        self.stdout.write('  Creating rooms...')
        standard = RoomType.objects.get(code='STANDARD')
        superior = RoomType.objects.get(code='SUPERIOR')
        suite = RoomType.objects.get(code='SUITE')

        rooms_config = {
            'P2': [
                ('201', standard, 1, 'A'),
                ('202', standard, 2, 'B'),
                ('203', standard, 3, 'A'),
                ('204', standard, 4, 'B'),
                ('205', superior, 5, 'A'),
                ('206', standard, 6, 'B'),
                ('207', standard, 7, 'A'),
            ],
            'P3': [
                ('301', standard, 1, 'A'),
                ('302', superior, 2, 'B'),
                ('303', standard, 3, 'A'),
                ('304', standard, 4, 'B'),
                ('305', standard, 5, 'A'),
            ],
            'P4': [
                ('401', standard, 1, 'A'),
                ('402', standard, 2, 'B'),
                ('403', standard, 3, 'A'),
                ('404', standard, 4, 'B'),
                ('405', superior, 5, 'A'),
                ('410', suite, 6, 'A'),
            ],
            'P5': [
                ('501', suite, 1, 'A'),
                ('502', superior, 2, 'B'),
                ('503', standard, 3, 'A'),
            ],
        }

        for zone_code, rooms in rooms_config.items():
            zone = Zone.objects.get(code=zone_code)
            for number, room_type, order, side in rooms:
                Room.objects.get_or_create(
                    number=number,
                    defaults={
                        'zone': zone,
                        'room_type': room_type,
                        'order_in_zone': order,
                        'corridor_side': side
                    }
                )

    def create_shift_templates(self):
        self.stdout.write('  Creating shift templates...')
        hk_role = Role.objects.get(code='HK_FDC')
        equipier_role = Role.objects.get(code='EQUIPIER')
        day_block = TimeBlock.objects.get(code='DAY')
        evening_block = TimeBlock.objects.get(code='EVENING')
        night_block = TimeBlock.objects.get(code='NIGHT')

        templates = [
            ('HK_DAY', 'Housekeeping Mañana', hk_role, day_block,
             time(7, 0), time(15, 0), time(11, 30), time(12, 0), 30),
            ('HK_EVENING', 'Housekeeping Tarde', hk_role, evening_block,
             time(14, 0), time(22, 30), time(18, 30), time(19, 0), 30),
            ('EQ_DAY', 'Équipier Mañana', equipier_role, day_block,
             time(7, 0), time(15, 0), time(11, 30), time(12, 0), 30),
            ('EQ_EVENING', 'Équipier Tarde', equipier_role, evening_block,
             time(14, 0), time(22, 30), time(18, 30), time(19, 0), 30),
            ('EQ_NIGHT', 'Équipier Noche', equipier_role, night_block,
             time(22, 0), time(7, 0), None, None, 0),
        ]

        for code, name, role, block, start, end, break_start, break_end, break_min in templates:
            template, created = ShiftTemplate.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'role': role,
                    'time_block': block,
                    'start_time': start,
                    'end_time': end,
                    'break_start': break_start,
                    'break_end': break_end,
                    'break_minutes': break_min
                }
            )

            # Create sub-blocks for HK_EVENING
            if code == 'HK_EVENING' and created:
                ShiftSubBlock.objects.create(
                    shift_template=template,
                    code='STANDARD',
                    name='Tareas estándar',
                    start_time=time(14, 0),
                    end_time=time(18, 30),
                    order=1,
                    description='Recouch, arrivals, touch-ups'
                )
                ShiftSubBlock.objects.create(
                    shift_template=template,
                    code='BREAK',
                    name='Pausa',
                    start_time=time(18, 30),
                    end_time=time(19, 0),
                    is_break=True,
                    order=2
                )
                ShiftSubBlock.objects.create(
                    shift_template=template,
                    code='COUVERTURE',
                    name='Couverture',
                    start_time=time(19, 0),
                    end_time=time(22, 30),
                    order=3,
                    description='Servicio de cobertura nocturno'
                )

    def create_rules(self):
        self.stdout.write('  Creating rules...')

        # Task Time Rules
        depart = TaskType.objects.get(code='DEPART')
        couverture = TaskType.objects.get(code='COUVERTURE')
        suite = RoomType.objects.get(code='SUITE')

        rules = [
            (depart, 'NONE', None, None, 1.0, 'Base DEPART'),
            (depart, 'SUITE', suite, None, 1.5, 'DEPART en Suite'),
            (depart, 'VIP', None, None, 1.2, 'DEPART VIP'),
            (couverture, 'NONE', None, None, 1.0, 'Base COUVERTURE'),
            (couverture, 'RECOUCH_DECLINED', None, None, 1.4, 'COUVERTURE cuando recouch rechazado'),
            (couverture, 'VIP', None, None, 1.3, 'COUVERTURE VIP'),
        ]

        for task, condition, room_type, base_min, multiplier, desc in rules:
            TaskTimeRule.objects.get_or_create(
                task_type=task,
                condition=condition,
                room_type=room_type,
                defaults={
                    'base_minutes': base_min,
                    'time_multiplier': multiplier,
                    'description': desc
                }
            )

        # Zone Assignment Rules
        zone_rules = [
            ('COMPLETE_ZONE_FIRST', 'Completar zona antes de cambiar', True, None, ''),
            ('MAX_ZONES_PER_EMPLOYEE', 'Máximo de zonas por empleado', None, 3, ''),
            ('ADJACENT_ZONES_PREFERRED', 'Preferir zonas adyacentes', True, None, ''),
            ('PAIR_SAME_ZONE', 'Pareja trabaja misma zona', True, None, ''),
        ]

        for code, name, bool_val, int_val, text_val in zone_rules:
            ZoneAssignmentRule.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'value_boolean': bool_val,
                    'value_integer': int_val,
                    'value_text': text_val
                }
            )

        # Elasticity Rules
        elasticity = [
            ('LOW', 0, 0, 1),
            ('MEDIUM', 4, 1, 2),
            ('HIGH', 8, 2, 3),
        ]

        for level, week_max, day_max, priority in elasticity:
            ElasticityRule.objects.get_or_create(
                elasticity_level=level,
                defaults={
                    'max_extra_hours_week': week_max,
                    'max_extra_hours_day': day_max,
                    'assignment_priority': priority
                }
            )

    def create_sample_employees(self):
        self.stdout.write('  Creating sample employees...')
        hk_role = Role.objects.get(code='HK_FDC')
        equipier_role = Role.objects.get(code='EQUIPIER')
        day_block = TimeBlock.objects.get(code='DAY')
        evening_block = TimeBlock.objects.get(code='EVENING')

        # Task types for eligibility
        depart = TaskType.objects.get(code='DEPART')
        recouch = TaskType.objects.get(code='RECOUCH')
        arrival = TaskType.objects.get(code='ARRIVAL')
        couverture = TaskType.objects.get(code='COUVERTURE')

        # Days off
        lunes = DayOfWeek.objects.get(code='LUN')
        martes = DayOfWeek.objects.get(code='MAR')
        sabado = DayOfWeek.objects.get(code='SAB')
        domingo = DayOfWeek.objects.get(code='DOM')

        employees_data = [
            ('EMP001', 'María', 'García', hk_role, 35, 'MEDIUM', [day_block], [depart, recouch, arrival], [], False),
            ('EMP002', 'Carmen', 'López', hk_role, 35, 'MEDIUM', [day_block], [depart, recouch, arrival], [], False),
            ('EMP003', 'Juan', 'Martínez', hk_role, 24, 'LOW', [day_block], [depart, recouch, arrival], [lunes, martes], False),
            ('EMP004', 'Ana', 'Rodríguez', hk_role, 40, 'HIGH', [day_block, evening_block], [depart, recouch, arrival, couverture], [], False),
            ('EMP005', 'Pedro', 'Sánchez', hk_role, 20, 'LOW', [evening_block], [recouch, couverture], [sabado, domingo], False),
            ('EMP006', 'Luis', 'Fernández', equipier_role, 35, 'MEDIUM', [day_block, evening_block], [recouch, couverture], [], True),
        ]

        created_employees = {}
        for code, first, last, role, hours, elasticity, blocks, tasks, days_off, night in employees_data:
            emp, created = Employee.objects.get_or_create(
                employee_code=code,
                defaults={
                    'first_name': first,
                    'last_name': last,
                    'role': role,
                    'weekly_hours_target': hours,
                    'elasticity': elasticity,
                    'can_work_night': night
                }
            )
            if created:
                emp.allowed_blocks.set(blocks)
                emp.eligible_tasks.set(tasks)
                emp.fixed_days_off.set(days_off)
            created_employees[code] = emp

        # Create a team (María + Carmen)
        maria = created_employees.get('EMP001')
        carmen = created_employees.get('EMP002')
        if maria and carmen:
            team, created = Team.objects.get_or_create(
                name='María + Carmen',
                defaults={'team_type': 'FIXED'}
            )
            if created:
                team.members.set([maria, carmen])

        self.stdout.write(f'    Created {len(employees_data)} employees and 1 team')
