import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getRoomDailyStates, updateRoomCleaningStatus } from '../api/client';
import { RoomDailyState } from '../types';
import { format } from 'date-fns';
import { clsx } from 'clsx';

export default function RoomStates() {
  const queryClient = useQueryClient();
  const [selectedDate, setSelectedDate] = useState(() => format(new Date(), 'yyyy-MM-dd'));

  // Query
  const { data, isLoading } = useQuery({
    queryKey: ['roomStates', selectedDate],
    queryFn: () => getRoomDailyStates(selectedDate),
  });

  // Mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) =>
      updateRoomCleaningStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['roomStates', selectedDate] });
    },
  });

  const handleStatusChange = (roomState: RoomDailyState, newStatus: string) => {
    updateMutation.mutate({ id: roomState.id, status: newStatus });
  };

  const getOccupancyBadge = (status: string) => {
    const styles: Record<string, string> = {
      VACANT: 'bg-gray-100 text-gray-800',
      OCCUPIED: 'bg-blue-100 text-blue-800',
      CHECKOUT: 'bg-orange-100 text-orange-800',
      CHECKIN: 'bg-green-100 text-green-800',
      TURNOVER: 'bg-purple-100 text-purple-800',
      OOO: 'bg-red-100 text-red-800',
    };
    return <span className={`badge ${styles[status] || ''}`}>{status}</span>;
  };

  const getCleaningStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      PENDING: 'bg-yellow-100 text-yellow-800',
      IN_PROGRESS: 'bg-blue-100 text-blue-800',
      DONE: 'bg-green-100 text-green-800',
      DECLINED: 'bg-red-100 text-red-800',
      NOT_REQUIRED: 'bg-gray-100 text-gray-800',
    };
    return <span className={`badge ${styles[status] || ''}`}>{status}</span>;
  };

  const getDifficultyBadge = (difficulty: string) => {
    const styles: Record<string, string> = {
      NORMAL: 'bg-green-100 text-green-800',
      HARD: 'bg-orange-100 text-orange-800',
      VERY_HARD: 'bg-red-100 text-red-800',
    };
    return <span className={`badge ${styles[difficulty] || ''}`}>{difficulty}</span>;
  };

  const roomStates: RoomDailyState[] = data?.results || [];

  // Group by zone
  const byZone: Record<string, RoomDailyState[]> = {};
  roomStates.forEach((state) => {
    const zoneKey = state.zone_code;
    if (!byZone[zoneKey]) {
      byZone[zoneKey] = [];
    }
    byZone[zoneKey].push(state);
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Estado de Habitaciones</h2>
        <div className="flex items-center space-x-4">
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="input w-40"
          />
        </div>
      </div>

      {/* Stats */}
      {roomStates.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <div className="card text-center">
            <div className="text-2xl font-bold">{roomStates.length}</div>
            <div className="text-sm text-gray-500">Total</div>
          </div>
          <div className="card text-center">
            <div className="text-2xl font-bold text-blue-600">
              {roomStates.filter((r) => r.occupancy_status === 'OCCUPIED').length}
            </div>
            <div className="text-sm text-gray-500">Ocupadas</div>
          </div>
          <div className="card text-center">
            <div className="text-2xl font-bold text-orange-600">
              {roomStates.filter((r) => r.occupancy_status === 'CHECKOUT').length}
            </div>
            <div className="text-sm text-gray-500">Checkout</div>
          </div>
          <div className="card text-center">
            <div className="text-2xl font-bold text-green-600">
              {roomStates.filter((r) => r.day_cleaning_status === 'DONE').length}
            </div>
            <div className="text-sm text-gray-500">Limpias</div>
          </div>
          <div className="card text-center">
            <div className="text-2xl font-bold text-red-600">
              {roomStates.filter((r) => r.night_expected_difficulty === 'HARD').length}
            </div>
            <div className="text-sm text-gray-500">Difíciles (noche)</div>
          </div>
        </div>
      )}

      {/* Room States by Zone */}
      {isLoading ? (
        <div className="card">
          <p className="text-gray-500">Cargando estados...</p>
        </div>
      ) : roomStates.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-gray-500">No hay datos para esta fecha</p>
          <p className="text-sm text-gray-400 mt-2">
            Importa un CSV de Protel para ver los estados de las habitaciones
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {Object.entries(byZone).map(([zoneCode, states]) => (
            <div key={zoneCode} className="card">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold">
                  {states[0]?.zone_name || zoneCode}
                </h3>
                <span className="badge badge-info">{states.length} habitaciones</span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="bg-gray-50">
                      <th className="text-left p-2">Hab.</th>
                      <th className="text-center p-2">Ocupación</th>
                      <th className="text-center p-2">Día estancia</th>
                      <th className="text-center p-2">Limpieza día</th>
                      <th className="text-center p-2">Dificultad noche</th>
                      <th className="text-center p-2">VIP</th>
                      <th className="text-center p-2">Tareas</th>
                      <th className="text-center p-2">Acción</th>
                    </tr>
                  </thead>
                  <tbody>
                    {states.map((state) => (
                      <tr
                        key={state.id}
                        className={clsx(
                          'border-t',
                          state.night_expected_difficulty === 'HARD' && 'bg-orange-50',
                          state.night_expected_difficulty === 'VERY_HARD' && 'bg-red-50'
                        )}
                      >
                        <td className="p-2 font-mono font-bold">{state.room_number}</td>
                        <td className="p-2 text-center">
                          {getOccupancyBadge(state.occupancy_status)}
                        </td>
                        <td className="p-2 text-center">{state.stay_day_number}</td>
                        <td className="p-2 text-center">
                          {getCleaningStatusBadge(state.day_cleaning_status)}
                        </td>
                        <td className="p-2 text-center">
                          {getDifficultyBadge(state.night_expected_difficulty)}
                        </td>
                        <td className="p-2 text-center">
                          {state.is_vip ? (
                            <span className="text-yellow-600 font-bold">VIP</span>
                          ) : (
                            '-'
                          )}
                        </td>
                        <td className="p-2 text-center">
                          <div className="flex justify-center space-x-1">
                            {state.tasks?.map((task) => (
                              <span
                                key={task.id}
                                className="badge badge-info text-xs"
                                title={`${task.task_type_name} - ${task.estimated_minutes}min`}
                              >
                                {task.task_type_code}
                              </span>
                            ))}
                          </div>
                        </td>
                        <td className="p-2 text-center">
                          {state.day_cleaning_status === 'PENDING' && (
                            <div className="flex justify-center space-x-1">
                              <button
                                onClick={() => handleStatusChange(state, 'DONE')}
                                className="text-green-600 hover:text-green-800 text-xs"
                                disabled={updateMutation.isPending}
                              >
                                Hecho
                              </button>
                              <span className="text-gray-300">|</span>
                              <button
                                onClick={() => handleStatusChange(state, 'DECLINED')}
                                className="text-red-600 hover:text-red-800 text-xs"
                                disabled={updateMutation.isPending}
                              >
                                Rechazado
                              </button>
                            </div>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
