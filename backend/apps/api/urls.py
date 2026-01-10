"""
API URLs.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

# Core
router.register(r'time-blocks', views.TimeBlockViewSet)
router.register(r'task-types', views.TaskTypeViewSet)
router.register(r'buildings', views.BuildingViewSet)
router.register(r'zones', views.ZoneViewSet)
router.register(r'room-types', views.RoomTypeViewSet)
router.register(r'rooms', views.RoomViewSet)
router.register(r'days-of-week', views.DayOfWeekViewSet)

# Staff
router.register(r'roles', views.RoleViewSet)
router.register(r'employees', views.EmployeeViewSet)
router.register(r'teams', views.TeamViewSet)
router.register(r'unavailabilities', views.EmployeeUnavailabilityViewSet)

# Shifts
router.register(r'shift-templates', views.ShiftTemplateViewSet)
router.register(r'shift-sub-blocks', views.ShiftSubBlockViewSet)

# Rooms
router.register(r'room-daily-states', views.RoomDailyStateViewSet)
router.register(r'room-daily-tasks', views.RoomDailyTaskViewSet)
router.register(r'import-logs', views.ProtelImportLogViewSet)

# Rules
router.register(r'task-time-rules', views.TaskTimeRuleViewSet)
router.register(r'zone-assignment-rules', views.ZoneAssignmentRuleViewSet)
router.register(r'elasticity-rules', views.ElasticityRuleViewSet)
router.register(r'planning-parameters', views.PlanningParameterViewSet)

# Planning
router.register(r'week-plans', views.WeekPlanViewSet)
router.register(r'shift-assignments', views.ShiftAssignmentViewSet)
router.register(r'daily-plans', views.DailyPlanViewSet)
router.register(r'task-assignments', views.TaskAssignmentViewSet)
router.register(r'load-summaries', views.DailyLoadSummaryViewSet)
router.register(r'alerts', views.PlanningAlertViewSet)

urlpatterns = [
    # Router URLs
    path('', include(router.urls)),

    # Special endpoints
    path('import/protel/', views.ProtelImportView.as_view(), name='import-protel'),
    path('calculate/load/', views.LoadCalculationView.as_view(), name='calculate-load'),
    path('calculate/capacity/', views.CapacityCalculationView.as_view(), name='calculate-capacity'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),

    # Forecast & WeekPlan generation
    path('forecast/generate-weekplan/', views.ForecastWeekPlanView.as_view(), name='forecast-generate-weekplan'),
    path('forecast/upload/', views.ForecastUploadView.as_view(), name='forecast-upload'),
]
