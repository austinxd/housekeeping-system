"""
Management command to generate WeekPlan from forecast data.
"""
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.core.models import TimeBlock
from apps.staff.models import Employee, Team
from apps.shifts.models import ShiftTemplate
from apps.planning.models import WeekPlan, ShiftAssignment
from apps.planning.services.forecast_loader import ForecastLoader


class Command(BaseCommand):
    help = 'Generate WeekPlan from forecast data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--week-start',
            type=str,
            help='Start date of the week (YYYY-MM-DD), must be Monday'
        )

    @transaction.atomic
    def handle(self, *args, **options):
        # Datos del forecast (del PDF analizado)
        # Semana del 12-18 Enero 2026
        week_start = date(2026, 1, 12)

        forecast_data = [
            {'date': date(2026, 1, 12), 'departures': 3, 'arrivals': 3, 'occupied': 27},   # Lun
            {'date': date(2026, 1, 13), 'departures': 0, 'arrivals': 1, 'occupied': 28},   # Mar
            {'date': date(2026, 1, 14), 'departures': 9, 'arrivals': 4, 'occupied': 23},   # Mié
            {'date': date(2026, 1, 15), 'departures': 1, 'arrivals': 8, 'occupied': 30},   # Jue
            {'date': date(2026, 1, 16), 'departures': 4, 'arrivals': 6, 'occupied': 32},   # Vie
            {'date': date(2026, 1, 17), 'departures': 9, 'arrivals': 7, 'occupied': 30},   # Sáb
            {'date': date(2026, 1, 18), 'departures': 10, 'arrivals': 10, 'occupied': 30}, # Dom
        ]

        self.stdout.write(self.style.NOTICE('=== GENERANDO WEEKPLAN ===\n'))

        # Calcular carga
        loader = ForecastLoader()
        week_load = loader.calculate_week_load(forecast_data)
        requirements = loader.calculate_staffing_requirements(week_load)

        # Mostrar carga calculada
        self.stdout.write('CARGA DE TRABAJO POR DÍA:')
        self.stdout.write('-' * 70)

        day_names = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
        for i, (day_key, day_load) in enumerate(week_load['days'].items()):
            day_name = day_names[i]
            day_hours = day_load['shifts']['DAY']['hours']
            evening_hours = day_load['shifts']['EVENING']['hours']
            total_hours = day_load['total_hours']

            req = requirements['by_day'][day_key]
            day_persons = req['day_shift']['persons_needed']
            evening_persons = req['evening_shift']['persons_needed']

            self.stdout.write(
                f'{day_name} {day_key}: '
                f'DÍA {day_hours:.1f}h ({day_persons} pers) | '
                f'TARDE {evening_hours:.1f}h ({evening_persons} pers) | '
                f'TOTAL {total_hours:.1f}h'
            )

        self.stdout.write('-' * 70)
        self.stdout.write(f'TOTAL SEMANA: {week_load["totals"]["total_hours"]:.1f} horas-persona\n')

        # Crear o actualizar WeekPlan
        week_plan, created = WeekPlan.objects.update_or_create(
            week_start_date=week_start,
            defaults={
                'name': f'Semana {week_start.strftime("%d/%m/%Y")}',
                'status': 'DRAFT',
            }
        )

        if not created:
            # Eliminar asignaciones anteriores
            week_plan.shift_assignments.all().delete()
            self.stdout.write(self.style.WARNING('Plan existente actualizado'))
        else:
            self.stdout.write(self.style.SUCCESS('Nuevo plan creado'))

        # Obtener empleados y equipos
        teams = list(Team.objects.filter(is_active=True).prefetch_related('members'))
        employees_in_teams = set()
        for team in teams:
            for member in team.members.all():
                employees_in_teams.add(member.id)

        # Empleados FDC/VDC que pueden limpiar habitaciones
        housekeeping_employees = Employee.objects.filter(
            role__code__in=['FDC', 'VDC'],
            is_active=True
        ).order_by('last_name')

        # Obtener plantillas de turno
        day_block = TimeBlock.objects.get(code='DAY')
        evening_block = TimeBlock.objects.get(code='EVENING')

        fdc_morning = ShiftTemplate.objects.filter(code='FDC_MANANA').first()
        fdc_evening = ShiftTemplate.objects.filter(code='FDC_TARDE').first()
        vdc_morning = ShiftTemplate.objects.filter(code='VDC_MANANA').first()
        vdc_evening = ShiftTemplate.objects.filter(code='VDC_TARDE').first()

        # Algoritmo de asignación
        self.stdout.write('\nASIGNACIÓN DE TURNOS:')
        self.stdout.write('=' * 70)

        # Organizar empleados por rol
        fdc_employees = [e for e in housekeeping_employees if e.role.code == 'FDC']
        vdc_employees = [e for e in housekeeping_employees if e.role.code == 'VDC']

        all_employees = fdc_employees + vdc_employees
        num_employees = len(all_employees)

        # Calcular días libres consecutivos para cada empleado
        # Rotamos los días libres para cubrir todos los días
        days_off_patterns = [
            (5, 6),  # Sáb-Dom libre
            (0, 1),  # Lun-Mar libre
            (1, 2),  # Mar-Mié libre
            (2, 3),  # Mié-Jue libre
            (3, 4),  # Jue-Vie libre
        ]

        # Asignar patrones de días libres
        employee_days_off = {}
        for i, emp in enumerate(all_employees):
            pattern_idx = i % len(days_off_patterns)
            employee_days_off[emp.id] = days_off_patterns[pattern_idx]

        # Ajustar para parejas (mismo patrón)
        for team in teams:
            members = list(team.members.all())
            if len(members) >= 2:
                # Usar el patrón del primer miembro para todos
                first_member = members[0]
                if first_member.id in employee_days_off:
                    pattern = employee_days_off[first_member.id]
                    for member in members[1:]:
                        employee_days_off[member.id] = pattern

        # Ajustar días libres según carga
        # Los días con más carga (Sáb=5, Dom=6) deben tener más gente
        sorted_days = sorted(
            enumerate(week_load['days'].items()),
            key=lambda x: x[1][1]['total_hours'],
            reverse=True
        )

        # Generar asignaciones
        week_days = [week_start + timedelta(days=i) for i in range(7)]

        assignments_summary = {d.isoformat(): {'morning': [], 'evening': []} for d in week_days}

        for emp in all_employees:
            days_off = employee_days_off.get(emp.id, (5, 6))
            weekly_hours = float(emp.weekly_hours_target)
            hours_assigned = 0

            # Determinar turno (FDC = mañana, VDC = tarde para balancear)
            is_morning = emp.role.code == 'FDC'

            shift_template = fdc_morning if is_morning else vdc_evening
            if not shift_template:
                shift_template = fdc_evening if fdc_evening else vdc_morning

            for day_idx, day_date in enumerate(week_days):
                if day_idx in days_off:
                    continue

                if hours_assigned >= weekly_hours:
                    break

                # Calcular horas a asignar
                hours_per_day = min(8, weekly_hours - hours_assigned)

                assignment = ShiftAssignment.objects.create(
                    week_plan=week_plan,
                    date=day_date,
                    employee=emp,
                    shift_template=shift_template,
                    assigned_hours=hours_per_day,
                    is_day_off=False
                )

                hours_assigned += hours_per_day

                shift_type = 'morning' if is_morning else 'evening'
                assignments_summary[day_date.isoformat()][shift_type].append(emp.first_name)

        # Mostrar resultado
        self.stdout.write('\nRESULTADO DEL WEEKPLAN:')
        self.stdout.write('-' * 70)
        self.stdout.write(f'{"Día":<12} {"Mañana":<35} {"Tarde":<35}')
        self.stdout.write('-' * 70)

        for i, day_date in enumerate(week_days):
            day_key = day_date.isoformat()
            day_name = day_names[i]
            morning = ', '.join(assignments_summary[day_key]['morning']) or '-'
            evening = ', '.join(assignments_summary[day_key]['evening']) or '-'

            # Truncar si es muy largo
            if len(morning) > 33:
                morning = morning[:30] + '...'
            if len(evening) > 33:
                evening = evening[:30] + '...'

            self.stdout.write(f'{day_name} {day_date.day:02d}/01  {morning:<35} {evening:<35}')

        self.stdout.write('-' * 70)

        # Resumen por empleado
        self.stdout.write('\nHORAS POR EMPLEADO:')
        self.stdout.write('-' * 40)

        for emp in all_employees:
            total_hours = sum(
                a.assigned_hours for a in week_plan.shift_assignments.filter(employee=emp)
            )
            days_off = employee_days_off.get(emp.id, (5, 6))
            off_names = [day_names[d] for d in days_off]

            self.stdout.write(
                f'{emp.first_name:<15} {emp.role.code:<5} '
                f'{total_hours:>5.1f}h / {emp.weekly_hours_target}h  '
                f'Libre: {"-".join(off_names)}'
            )

        self.stdout.write('\n' + self.style.SUCCESS('WeekPlan generado exitosamente!'))
        self.stdout.write(f'Ver en: http://localhost:8000/admin/planning/weekplan/{week_plan.id}/change/')
