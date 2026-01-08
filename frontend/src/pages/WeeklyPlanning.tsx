import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getWeekPlans,
  getWeekPlan,
  generateWeekPlan,
  publishWeekPlan,
  getWeekPlanByEmployee,
} from '../api/client';
import { WeekPlan } from '../types';
import { format, parseISO, startOfWeek, addDays } from 'date-fns';
import { es } from 'date-fns/locale';
import { clsx } from 'clsx';

export default function WeeklyPlanning() {
  const queryClient = useQueryClient();
  const [selectedPlanId, setSelectedPlanId] = useState<number | null>(null);
  const [newWeekStart, setNewWeekStart] = useState(() => {
    const today = new Date();
    return format(startOfWeek(today, { weekStartsOn: 1 }), 'yyyy-MM-dd');
  });

  // Queries
  const { data: weekPlans, isLoading: loadingPlans } = useQuery({
    queryKey: ['weekPlans'],
    queryFn: getWeekPlans,
  });

  const { data: selectedPlan, isLoading: loadingPlan } = useQuery({
    queryKey: ['weekPlan', selectedPlanId],
    queryFn: () => getWeekPlan(selectedPlanId!),
    enabled: !!selectedPlanId,
  });

  const { data: byEmployee } = useQuery({
    queryKey: ['weekPlanByEmployee', selectedPlanId],
    queryFn: () => getWeekPlanByEmployee(selectedPlanId!),
    enabled: !!selectedPlanId,
  });

  // Mutations
  const generateMutation = useMutation({
    mutationFn: generateWeekPlan,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['weekPlans'] });
      setSelectedPlanId(data.id);
    },
  });

  const publishMutation = useMutation({
    mutationFn: publishWeekPlan,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['weekPlans'] });
      queryClient.invalidateQueries({ queryKey: ['weekPlan', selectedPlanId] });
    },
  });

  const handleGenerate = () => {
    generateMutation.mutate(newWeekStart);
  };

  const handlePublish = () => {
    if (selectedPlanId) {
      publishMutation.mutate(selectedPlanId);
    }
  };

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      DRAFT: 'badge-warning',
      REVIEW: 'badge-info',
      APPROVED: 'badge-success',
      PUBLISHED: 'badge-success',
      ARCHIVED: 'badge-secondary',
    };
    return <span className={`badge ${styles[status] || ''}`}>{status}</span>;
  };

  // Get week days for header
  const getWeekDays = (startDate: string) => {
    const start = parseISO(startDate);
    return Array.from({ length: 7 }, (_, i) => addDays(start, i));
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Planning Semanal</h2>
        <div className="flex items-center space-x-4">
          <input
            type="date"
            value={newWeekStart}
            onChange={(e) => setNewWeekStart(e.target.value)}
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
          <h3 className="text-lg font-semibold mb-4">Planes</h3>
          {loadingPlans ? (
            <p className="text-gray-500">Cargando...</p>
          ) : (
            <div className="space-y-2">
              {weekPlans?.results?.map((plan: WeekPlan) => (
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
                      {format(parseISO(plan.week_start_date), 'd MMM', { locale: es })}
                    </span>
                    {getStatusBadge(plan.status)}
                  </div>
                  <div className="text-sm text-gray-500 mt-1">
                    {plan.name || 'Sin nombre'}
                  </div>
                </button>
              ))}
              {(!weekPlans?.results || weekPlans.results.length === 0) && (
                <p className="text-gray-500 text-sm">No hay planes creados</p>
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
                      Semana {format(parseISO(selectedPlan.week_start_date), 'd MMMM', { locale: es })}
                    </h3>
                    <div className="flex items-center space-x-2 mt-1">
                      {getStatusBadge(selectedPlan.status)}
                      <span className="text-sm text-gray-500">
                        {selectedPlan.total_assigned_hours}h asignadas
                      </span>
                    </div>
                  </div>
                  {selectedPlan.status === 'DRAFT' && (
                    <button
                      onClick={handlePublish}
                      disabled={publishMutation.isPending}
                      className="btn btn-primary"
                    >
                      {publishMutation.isPending ? 'Publicando...' : 'Publicar'}
                    </button>
                  )}
                </div>
              </div>

              {/* Schedule Grid */}
              {byEmployee && (
                <div className="card overflow-x-auto">
                  <h4 className="font-semibold mb-4">Horarios por Empleado</h4>
                  <table className="w-full">
                    <thead>
                      <tr>
                        <th className="text-left p-2 bg-gray-50">Empleado</th>
                        {getWeekDays(selectedPlan.week_start_date).map((day) => (
                          <th key={day.toISOString()} className="text-center p-2 bg-gray-50">
                            <div>{format(day, 'EEE', { locale: es })}</div>
                            <div className="text-xs text-gray-500">
                              {format(day, 'd', { locale: es })}
                            </div>
                          </th>
                        ))}
                        <th className="text-center p-2 bg-gray-50">Total</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(byEmployee).map(([key, emp]: [string, any]) => {
                        const weekDays = getWeekDays(selectedPlan.week_start_date);
                        const shiftsByDate: Record<string, any> = {};
                        emp.shifts.forEach((shift: any) => {
                          shiftsByDate[shift.date] = shift;
                        });

                        const totalHours = emp.shifts.reduce(
                          (sum: number, s: any) => sum + (s.is_day_off ? 0 : s.hours),
                          0
                        );

                        return (
                          <tr key={key} className="border-t">
                            <td className="p-2">
                              <div className="font-medium">{emp.name}</div>
                              <div className="text-xs text-gray-500">{emp.type}</div>
                            </td>
                            {weekDays.map((day) => {
                              const dateStr = format(day, 'yyyy-MM-dd');
                              const shift = shiftsByDate[dateStr];

                              return (
                                <td key={dateStr} className="text-center p-2">
                                  {shift ? (
                                    shift.is_day_off ? (
                                      <span className="text-gray-400">-</span>
                                    ) : (
                                      <div>
                                        <div className="text-sm font-medium">{shift.shift}</div>
                                        <div className="text-xs text-gray-500">{shift.hours}h</div>
                                      </div>
                                    )
                                  ) : (
                                    <span className="text-gray-300">-</span>
                                  )}
                                </td>
                              );
                            })}
                            <td className="text-center p-2 font-semibold">{totalHours}h</td>
                          </tr>
                        );
                      })}
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
