import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getDailyPlans,
  getDailyPlan,
  generateDailyPlan,
  getDailyPlanByZone,
  completeTaskAssignment,
} from '../api/client';
import { DailyPlan, TaskAssignment } from '../types';
import { format, parseISO } from 'date-fns';
import { es } from 'date-fns/locale';
import { clsx } from 'clsx';

export default function DailyPlanning() {
  const queryClient = useQueryClient();
  const [selectedPlanId, setSelectedPlanId] = useState<number | null>(null);
  const [selectedDate, setSelectedDate] = useState(() => format(new Date(), 'yyyy-MM-dd'));
  const [viewMode, setViewMode] = useState<'list' | 'zone'>('zone');

  // Queries
  const { data: dailyPlans, isLoading: loadingPlans } = useQuery({
    queryKey: ['dailyPlans'],
    queryFn: getDailyPlans,
  });

  const { data: selectedPlan, isLoading: loadingPlan } = useQuery({
    queryKey: ['dailyPlan', selectedPlanId],
    queryFn: () => getDailyPlan(selectedPlanId!),
    enabled: !!selectedPlanId,
  });

  const { data: byZone } = useQuery({
    queryKey: ['dailyPlanByZone', selectedPlanId],
    queryFn: () => getDailyPlanByZone(selectedPlanId!),
    enabled: !!selectedPlanId && viewMode === 'zone',
  });

  // Mutations
  const generateMutation = useMutation({
    mutationFn: (date: string) => generateDailyPlan(date),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['dailyPlans'] });
      setSelectedPlanId(data.id);
    },
  });

  const completeMutation = useMutation({
    mutationFn: completeTaskAssignment,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dailyPlan', selectedPlanId] });
      queryClient.invalidateQueries({ queryKey: ['dailyPlanByZone', selectedPlanId] });
    },
  });

  const handleGenerate = () => {
    generateMutation.mutate(selectedDate);
  };

  const handleComplete = (taskId: number) => {
    completeMutation.mutate(taskId);
  };

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      DRAFT: 'badge-warning',
      ACTIVE: 'badge-info',
      COMPLETED: 'badge-success',
    };
    return <span className={`badge ${styles[status] || ''}`}>{status}</span>;
  };

  const getTaskStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      PENDING: 'bg-gray-100 text-gray-800',
      IN_PROGRESS: 'bg-blue-100 text-blue-800',
      COMPLETED: 'bg-green-100 text-green-800',
      SKIPPED: 'bg-red-100 text-red-800',
    };
    return <span className={`badge ${styles[status] || ''}`}>{status}</span>;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Planning Diario</h2>
        <div className="flex items-center space-x-4">
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="input w-40"
          />
          <button
            onClick={handleGenerate}
            disabled={generateMutation.isPending}
            className="btn btn-primary"
          >
            {generateMutation.isPending ? 'Generando...' : 'Generar Plan'}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Plans List */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Planes Diarios</h3>
          {loadingPlans ? (
            <p className="text-gray-500">Cargando...</p>
          ) : (
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {dailyPlans?.results?.map((plan: DailyPlan) => (
                <button
                  key={plan.id}
                  onClick={() => setSelectedPlanId(plan.id)}
                  className={clsx(
                    'w-full text-left p-3 rounded-lg transition-colors',
                    selectedPlanId === plan.id
                      ? 'bg-primary-100 border-2 border-primary-500'
                      : 'bg-gray-50 hover:bg-gray-100'
                  )}
                >
                  <div className="flex justify-between items-center">
                    <span className="font-medium">
                      {format(parseISO(plan.date), 'EEEE d MMM', { locale: es })}
                    </span>
                    {getStatusBadge(plan.status)}
                  </div>
                  <div className="text-sm text-gray-500 mt-1">
                    {plan.completed_tasks}/{plan.total_tasks} tareas
                  </div>
                </button>
              ))}
              {(!dailyPlans?.results || dailyPlans.results.length === 0) && (
                <p className="text-gray-500 text-sm">No hay planes diarios</p>
              )}
            </div>
          )}
        </div>

        {/* Plan Detail */}
        <div className="lg:col-span-3">
          {selectedPlanId && selectedPlan ? (
            <div className="space-y-4">
              {/* Plan Header */}
              <div className="card">
                <div className="flex justify-between items-center">
                  <div>
                    <h3 className="text-lg font-semibold">
                      {format(parseISO(selectedPlan.date), 'EEEE d MMMM yyyy', { locale: es })}
                    </h3>
                    <div className="flex items-center space-x-4 mt-1">
                      {getStatusBadge(selectedPlan.status)}
                      <span className="text-sm text-gray-500">
                        {selectedPlan.completed_tasks}/{selectedPlan.total_tasks} tareas completadas
                      </span>
                    </div>
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => setViewMode('zone')}
                      className={clsx('btn', viewMode === 'zone' ? 'btn-primary' : 'btn-secondary')}
                    >
                      Por Zona
                    </button>
                    <button
                      onClick={() => setViewMode('list')}
                      className={clsx('btn', viewMode === 'list' ? 'btn-primary' : 'btn-secondary')}
                    >
                      Lista
                    </button>
                  </div>
                </div>
              </div>

              {/* Tasks by Zone */}
              {viewMode === 'zone' && byZone && (
                <div className="space-y-4">
                  {Object.entries(byZone).map(([zoneCode, zoneData]: [string, any]) => (
                    <div key={zoneCode} className="card">
                      <div className="flex justify-between items-center mb-4">
                        <div>
                          <h4 className="font-semibold text-lg">{zoneData.zone_name}</h4>
                          {zoneData.floor && (
                            <span className="text-sm text-gray-500">Piso {zoneData.floor}</span>
                          )}
                        </div>
                        <span className="badge badge-info">{zoneData.tasks.length} tareas</span>
                      </div>

                      <div className="space-y-2">
                        {zoneData.tasks.map((task: any, idx: number) => (
                          <div
                            key={idx}
                            className={clsx(
                              'flex justify-between items-center p-3 rounded-lg',
                              task.status === 'COMPLETED' ? 'bg-green-50' : 'bg-gray-50'
                            )}
                          >
                            <div className="flex items-center space-x-4">
                              <div className="font-mono font-bold text-lg">{task.room}</div>
                              <div>
                                <div className="font-medium">{task.task_type}</div>
                                <div className="text-sm text-gray-500">
                                  {task.assigned_to} - {task.estimated_minutes} min
                                </div>
                              </div>
                            </div>
                            <div className="flex items-center space-x-2">
                              {getTaskStatusBadge(task.status)}
                              {task.status === 'PENDING' && (
                                <button
                                  onClick={() => handleComplete(task.id)}
                                  className="btn btn-primary text-sm py-1"
                                  disabled={completeMutation.isPending}
                                >
                                  Completar
                                </button>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Tasks List View */}
              {viewMode === 'list' && selectedPlan.task_assignments && (
                <div className="card">
                  <table className="w-full">
                    <thead>
                      <tr className="bg-gray-50">
                        <th className="text-left p-2">Habitación</th>
                        <th className="text-left p-2">Zona</th>
                        <th className="text-left p-2">Tarea</th>
                        <th className="text-left p-2">Asignado a</th>
                        <th className="text-center p-2">Tiempo</th>
                        <th className="text-center p-2">Estado</th>
                        <th className="text-center p-2">Acción</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedPlan.task_assignments.map((task: TaskAssignment) => (
                        <tr key={task.id} className="border-t">
                          <td className="p-2 font-mono font-bold">{task.room_number}</td>
                          <td className="p-2">{task.zone_name}</td>
                          <td className="p-2">{task.task_type_code}</td>
                          <td className="p-2">{task.employee_name || task.team_name}</td>
                          <td className="p-2 text-center">{task.estimated_minutes} min</td>
                          <td className="p-2 text-center">{getTaskStatusBadge(task.status)}</td>
                          <td className="p-2 text-center">
                            {task.status === 'PENDING' && (
                              <button
                                onClick={() => handleComplete(task.id)}
                                className="text-primary-600 hover:text-primary-800 text-sm"
                                disabled={completeMutation.isPending}
                              >
                                Completar
                              </button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          ) : (
            <div className="card text-center py-12">
              <p className="text-gray-500">
                Selecciona un plan de la lista o genera uno nuevo
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
