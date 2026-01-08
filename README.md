# Sistema de Planificación de Housekeeping

Sistema completo para planificación de housekeeping en hoteles, basado en reglas reales de hotelería.

## Características

- **WeekPlan**: Horario laboral semanal de cada empleado
- **DailyPlan**: Asignación de tareas específicas por día
- **Asignación zonificada**: Optimiza desplazamientos agrupando por pisos/zonas
- **Bloques temporales**: DAY, EVENING, NIGHT (configurable)
- **Gestión de parejas**: Equipos fijos o preferidos
- **Reglas configurables**: Todo editable desde Admin
- **Importación CSV Protel**: Sin necesidad de API

## Filosofía

> El sistema no manda personas. El sistema explica el trabajo. La humana decide.

## Instalación

### Backend (Django)

```bash
cd backend

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Migraciones
python manage.py migrate

# Crear datos iniciales
python manage.py setup_initial_data

# Crear superusuario
python manage.py createsuperuser

# Ejecutar servidor
python manage.py runserver
```

### Frontend (React)

```bash
cd frontend

# Instalar dependencias
npm install

# Ejecutar en desarrollo
npm run dev
```

## Uso

### 1. Configuración Inicial

Accede al Admin de Django (`http://localhost:8000/admin/`) para:

- Verificar/modificar **TimeBlocks** (DAY, EVENING, NIGHT)
- Verificar/modificar **TaskTypes** (DEPART, RECOUCH, COUVERTURE...)
- Verificar/modificar **Roles** (HK_FDC, EQUIPIER, GOUVERNANTE...)
- Agregar/modificar **Zonas** y **Habitaciones**
- Configurar **Empleados** y **Equipos**
- Ajustar **Reglas de Tiempo** y **Parámetros**

### 2. Importar CSV Protel

1. Ve a `/import` en el frontend
2. Sube un archivo CSV con el formato esperado
3. El sistema creará los `RoomDailyState` y `RoomDailyTask`

### 3. Generar Plan Semanal

1. Ve a `/weekly` en el frontend
2. Selecciona la fecha de inicio de semana (lunes)
3. Click en "Generar Plan"
4. Revisa las asignaciones por empleado
5. Ajusta manualmente si es necesario
6. Click en "Publicar" para confirmar

### 4. Generar Plan Diario

1. Ve a `/daily` en el frontend
2. Selecciona la fecha
3. Click en "Generar Plan"
4. Revisa las asignaciones por zona
5. Las tareas se asignan de forma zonificada

### 5. Dashboard

El dashboard muestra:
- Carga vs Capacidad semanal
- Alertas de sobrecarga o déficit
- Distribución por día y bloque

## Estructura del Proyecto

```
housekeeping-system/
├── backend/
│   ├── apps/
│   │   ├── core/          # TimeBlock, TaskType, Zone, Room
│   │   ├── staff/         # Employee, Team, Role
│   │   ├── shifts/        # ShiftTemplate, ShiftSubBlock
│   │   ├── rooms/         # RoomDailyState, RoomDailyTask, Importer
│   │   ├── rules/         # TaskTimeRule, ElasticityRule
│   │   ├── planning/      # WeekPlan, DailyPlan, Services
│   │   └── api/           # REST API (DRF)
│   └── config/            # Django settings
├── frontend/
│   └── src/
│       ├── pages/         # Dashboard, WeeklyPlanning, DailyPlanning...
│       ├── api/           # API client
│       └── types/         # TypeScript types
└── samples/               # Archivos CSV de ejemplo
```

## API Endpoints

### Core
- `GET /api/time-blocks/`
- `GET /api/task-types/`
- `GET /api/zones/`
- `GET /api/rooms/`

### Staff
- `GET /api/employees/`
- `GET /api/teams/`

### Planning
- `GET /api/week-plans/`
- `POST /api/week-plans/generate/`
- `POST /api/week-plans/{id}/publish/`
- `GET /api/daily-plans/`
- `POST /api/daily-plans/generate/`
- `GET /api/daily-plans/{id}/by_zone/`

### Import
- `POST /api/import/protel/`

### Dashboard
- `GET /api/dashboard/?week_start=YYYY-MM-DD`

## Formato CSV Protel

```csv
date,room,housekeeping_type,arrival_time,departure_time,status,stay_day,vip
2026-01-20,305,RECOUCH,,,OCCUPIED,3,0
2026-01-20,305,COUVERTURE,,,OCCUPIED,3,0
2026-01-20,401,DEPART,,11:00,CHECKOUT,1,0
```

## Reglas de Negocio

### Bloques Temporales
- **DAY**: Limpieza principal (mañana)
- **EVENING**: Tarde + Couverture
- **NIGHT**: Solo équipier de nuit (sin housekeeping)

### Roles y Bloques Permitidos
| Rol | DAY | EVENING | NIGHT |
|-----|-----|---------|-------|
| HK_FDC | ✓ | ✓ | ✗ |
| Équipier | ✓ | ✓ | ✓ |
| Gouvernante | ✓ | ✓ | ✗ |

### Estado de Habitación → Dificultad Nocturna
Si `stay_day >= 2` y `recouch = DECLINED` → `night_difficulty = HARD` (×1.4 tiempo)

### Asignación Zonificada
1. Agrupar tareas por zona
2. Asignar zona completa a un empleado/equipo
3. Ordenar tareas dentro de zona por número de habitación
4. Preferir zonas adyacentes para el mismo empleado
