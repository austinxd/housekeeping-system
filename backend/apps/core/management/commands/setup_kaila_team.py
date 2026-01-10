"""
Management command to set up Le Kaila hotel team data.
Creates real roles, shift templates, and employees.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from datetime import time

from apps.core.models import TimeBlock, TaskType, DayOfWeek
from apps.staff.models import Role, Employee, Team
from apps.shifts.models import ShiftTemplate
from apps.rules.models import TaskTimeRule


class Command(BaseCommand):
    help = 'Set up Le Kaila hotel team data'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write('Setting up Le Kaila team...')

        self.create_roles()
        self.create_shift_templates()
        self.create_employees()
        self.update_task_times()

        self.stdout.write(self.style.SUCCESS('Le Kaila team configured successfully!'))

    def create_roles(self):
        self.stdout.write('  Updating roles...')
        day_block = TimeBlock.objects.get(code='DAY')
        evening_block = TimeBlock.objects.get(code='EVENING')
        night_block = TimeBlock.objects.get(code='NIGHT')

        # Clear existing data (order matters due to foreign keys)
        Employee.objects.all().delete()
        Team.objects.all().delete()
        ShiftTemplate.objects.all().delete()
        Role.objects.all().delete()

        roles = [
            ('GG', 'Gouvernante Générale', 'Supervisión general y gestión', [day_block], 1, False),
            ('ASST_GG', 'Assistante GG', 'Asistente de gouvernante', [day_block, evening_block], 2, False),
            ('GOUV_SOIR', 'Gouvernante du Soir', 'Supervisión turno tarde', [day_block, evening_block], 3, False),
            ('FDC', 'Femme de Chambre', 'Housekeeping - limpieza habitaciones', [day_block, evening_block], 4, True),
            ('VDC', 'Valet de Chambre', 'Housekeeping - limpieza habitaciones', [day_block, evening_block], 5, True),
            ('EQUIPIER_JOUR', 'Équipier Jour', 'Áreas comunes y suministros - día', [day_block, evening_block], 6, False),
            ('EQUIPIER_NUIT', 'Équipier Nuit', 'Áreas comunes y suministros - noche', [night_block], 7, True),
        ]

        for code, name, desc, blocks, order, cleans_rooms in roles:
            role = Role.objects.create(
                code=code,
                name=name,
                description=desc,
                display_order=order,
                can_clean_rooms=cleans_rooms
            )
            role.allowed_blocks.set(blocks)
            self.stdout.write(f'    Created role: {name}')

    def create_shift_templates(self):
        self.stdout.write('  Creating shift templates...')

        # Clear existing templates
        ShiftTemplate.objects.all().delete()

        day_block = TimeBlock.objects.get(code='DAY')
        evening_block = TimeBlock.objects.get(code='EVENING')
        night_block = TimeBlock.objects.get(code='NIGHT')

        gg = Role.objects.get(code='GG')
        asst_gg = Role.objects.get(code='ASST_GG')
        gouv_soir = Role.objects.get(code='GOUV_SOIR')
        fdc = Role.objects.get(code='FDC')
        vdc = Role.objects.get(code='VDC')
        eq_jour = Role.objects.get(code='EQUIPIER_JOUR')
        eq_nuit = Role.objects.get(code='EQUIPIER_NUIT')

        templates = [
            # GG - fixed schedule
            ('GG_DIA', 'GG Día', gg, day_block, time(8, 0), time(17, 30), 45, 9),

            # Assistante GG - variable
            ('ASST_MANANA', 'Assistante Mañana', asst_gg, day_block, time(8, 0), time(16, 30), 41, 8),
            ('ASST_TARDE', 'Assistante Tarde', asst_gg, evening_block, time(14, 0), time(22, 0), 41, 8),

            # Gouvernante du soir - variable
            ('GOUV_SOIR_MANANA', 'Gouv. Soir Mañana', gouv_soir, day_block, time(8, 0), time(16, 30), 42, 8),
            ('GOUV_SOIR_TARDE', 'Gouv. Soir Tarde', gouv_soir, evening_block, time(14, 0), time(22, 30), 42, 8),

            # FDC - morning and afternoon
            ('FDC_MANANA', 'FDC Mañana', fdc, day_block, time(9, 0), time(17, 0), 39, 8),
            ('FDC_TARDE', 'FDC Tarde', fdc, evening_block, time(13, 30), time(21, 30), 39, 8),

            # VDC - morning and afternoon
            ('VDC_MANANA', 'VDC Mañana', vdc, day_block, time(9, 0), time(17, 0), 39, 8),
            ('VDC_TARDE', 'VDC Tarde', vdc, evening_block, time(13, 30), time(21, 30), 39, 8),

            # Équipier jour
            ('EQ_JOUR_MANANA', 'Équipier Día Mañana', eq_jour, day_block, time(9, 0), time(17, 0), 39, 8),
            ('EQ_JOUR_TARDE', 'Équipier Día Tarde', eq_jour, evening_block, time(13, 30), time(21, 30), 39, 8),

            # Équipier nuit
            ('EQ_NUIT', 'Équipier Noche', eq_nuit, night_block, time(22, 0), time(6, 0), 39, 8),
        ]

        for code, name, role, block, start, end, weekly_hours, max_daily in templates:
            ShiftTemplate.objects.create(
                code=code,
                name=name,
                role=role,
                time_block=block,
                start_time=start,
                end_time=end,
                weekly_hours_target=weekly_hours,
                max_daily_hours=max_daily
            )
            self.stdout.write(f'    Created shift: {name}')

    def create_employees(self):
        self.stdout.write('  Creating employees...')

        # Clear existing employees
        Employee.objects.all().delete()
        Team.objects.all().delete()

        # Get roles
        gg = Role.objects.get(code='GG')
        asst_gg = Role.objects.get(code='ASST_GG')
        gouv_soir = Role.objects.get(code='GOUV_SOIR')
        fdc = Role.objects.get(code='FDC')
        vdc = Role.objects.get(code='VDC')
        eq_jour = Role.objects.get(code='EQUIPIER_JOUR')
        eq_nuit = Role.objects.get(code='EQUIPIER_NUIT')

        # Get blocks
        day_block = TimeBlock.objects.get(code='DAY')
        evening_block = TimeBlock.objects.get(code='EVENING')
        night_block = TimeBlock.objects.get(code='NIGHT')

        # Task types
        all_tasks = list(TaskType.objects.all())
        room_tasks = list(TaskType.objects.filter(code__in=['DEPART', 'RECOUCH', 'ARRIVAL', 'ARRIVAL_VIP', 'COUVERTURE', 'TOUCHUP']))

        employees_data = [
            # GG (1)
            ('GG001', 'Ingrid', 'FRANCO', gg, 45, 'LOW', [day_block], False),

            # Assistante GG (1)
            ('ASST001', 'Joell', 'MERIN', asst_gg, 41, 'MEDIUM', [day_block, evening_block], False),

            # Gouvernante du soir (1)
            ('GSOIR001', 'Charlène', 'GODARD', gouv_soir, 42, 'MEDIUM', [day_block, evening_block], False),

            # FDC (5)
            ('FDC001', 'Dorine', 'TORRES', fdc, 39, 'MEDIUM', [day_block, evening_block], False),
            ('FDC002', 'Rogelio', 'SANTIAGO', fdc, 39, 'MEDIUM', [day_block, evening_block], False),
            ('FDC003', 'Wendy', 'RUBIO', fdc, 39, 'MEDIUM', [day_block, evening_block], False),
            ('FDC004', 'Gabriela', 'CORREA', fdc, 39, 'MEDIUM', [day_block, evening_block], False),
            ('FDC005', 'Francisco', 'BLANCO', fdc, 39, 'MEDIUM', [day_block, evening_block], False),

            # VDC (5)
            ('VDC001', 'Vida', 'LE BAIL', vdc, 39, 'MEDIUM', [day_block, evening_block], False),
            ('VDC002', 'Christophe', 'LASALA', vdc, 39, 'MEDIUM', [day_block, evening_block], False),
            ('VDC003', 'Suzette', 'BRILLE', vdc, 39, 'MEDIUM', [day_block, evening_block], False),
            ('VDC004', 'Sébastien', 'CAMELIARE', vdc, 39, 'MEDIUM', [day_block, evening_block], False),
            ('VDC005', 'Javier', 'JOUBERT', vdc, 39, 'MEDIUM', [day_block, evening_block], False),

            # Équipier jour (3)
            ('EQJOUR001', 'Benjamin', 'BILLARD', eq_jour, 39, 'MEDIUM', [day_block, evening_block], False),
            ('EQJOUR002', 'Empleado', 'EQUIPIER2', eq_jour, 39, 'MEDIUM', [day_block, evening_block], False),
            ('EQJOUR003', 'Empleado', 'EQUIPIER3', eq_jour, 39, 'MEDIUM', [day_block, evening_block], False),

            # Équipier nuit (2)
            ('EQNUIT001', 'Philippe', 'CABANAS', eq_nuit, 39, 'MEDIUM', [night_block], True),
            ('EQNUIT002', 'Romain', 'LEGUARD', eq_nuit, 39, 'MEDIUM', [night_block], True),
        ]

        for code, first, last, role, hours, elasticity, blocks, night in employees_data:
            emp = Employee.objects.create(
                employee_code=code,
                first_name=first,
                last_name=last,
                role=role,
                weekly_hours_target=hours,
                elasticity=elasticity,
                can_work_night=night,
                is_active=True
            )
            emp.allowed_blocks.set(blocks)

            # Set eligible tasks based on role
            if role.can_clean_rooms:
                emp.eligible_tasks.set(room_tasks)

            self.stdout.write(f'    Created: {first} {last} ({role.code}) - {hours}h/sem')

        self.stdout.write(f'  Total: {Employee.objects.count()} employees created')

    def update_task_times(self):
        self.stdout.write('  Updating task times...')

        # Update base minutes for tasks (adjustable in admin)
        task_times = {
            'DEPART': 30,      # Salida/checkout - 30 min
            'RECOUCH': 15,     # Repaso/estancia - 15 min
            'ARRIVAL': 10,     # Llegada - 10 min extra
            'ARRIVAL_VIP': 20, # Llegada VIP - 20 min extra
            'COUVERTURE': 15,  # Couverture - 15 min
            'TOUCHUP': 10,     # Touch-up - 10 min
        }

        for code, minutes in task_times.items():
            TaskType.objects.filter(code=code).update(base_minutes=minutes)
            self.stdout.write(f'    {code}: {minutes} min')
