import { useQuery } from '@tanstack/react-query';
import { getDashboard, resolveAlert } from '../api/client';
import { DashboardData, PlanningAlert } from '../types';
import { format, parseISO, startOfWeek, addDays } from 'date-fns';
import { es, fr } from 'date-fns/locale';
import { clsx } from 'clsx';
import { useState } from 'react';
import { useLanguage } from '../i18n';

export default function Dashboard() {
  const { t, language } = useLanguage();
  const dateLocale = language === 'fr' ? fr : es;

  const [weekStart, setWeekStart] = useState(() => {
    const today = new Date();
    return format(startOfWeek(today, { weekStartsOn: 1 }), 'yyyy-MM-dd');
  });

  const { data, isLoading, error, refetch } = useQuery<DashboardData>({
    queryKey: ['dashboard', weekStart],
    queryFn: () => getDashboard(weekStart),
  });

  const handleResolveAlert = async (alertId: number) => {
    await resolveAlert(alertId);
    refetch();
  };

  const changeWeek = (direction: number) => {
    const current = parseISO(weekStart);
    const newDate = addDays(current, direction * 7);
    setWeekStart(format(newDate, 'yyyy-MM-dd'));
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">{t.common.loadingDashboard}</div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="bg-red-50 p-4 rounded-md">
        <p className="text-red-800">{t.dashboard.errorLoading}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">{t.dashboard.title}</h2>
          <p className="text-gray-500">
            {t.dashboard.weekOf} {format(parseISO(data.week_start), 'd MMMM', { locale: dateLocale })} {t.dashboard.to}{' '}
            {format(parseISO(data.week_end), 'd MMMM yyyy', { locale: dateLocale })}
          </p>
        </div>
        <div className="flex space-x-2">
          <button onClick={() => changeWeek(-1)} className="btn btn-secondary">
            {t.dashboard.previousWeek}
          </button>
          <button onClick={() => changeWeek(1)} className="btn btn-secondary">
            {t.dashboard.nextWeek}
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card">
          <div className="text-sm text-gray-500">{t.dashboard.totalLoad}</div>
          <div className="text-2xl font-bold">
            {Math.round(data.load.total_minutes / 60)}h
          </div>
          <div className="text-sm text-gray-400">
            {data.load.total_tasks} {t.common.tasks}
          </div>
        </div>

        <div className="card">
          <div className="text-sm text-gray-500">{t.dashboard.capacity}</div>
          <div className="text-2xl font-bold">
            {Math.round(data.capacity.total_minutes / 60)}h
          </div>
        </div>

        <div className="card">
          <div className="text-sm text-gray-500">{t.dashboard.balance}</div>
          <div
            className={clsx(
              'text-2xl font-bold',
              data.balance.minutes >= 0 ? 'text-green-600' : 'text-red-600'
            )}
          >
            {data.balance.minutes >= 0 ? '+' : ''}
            {Math.round(data.balance.minutes / 60)}h
          </div>
        </div>

        <div className="card">
          <div className="text-sm text-gray-500">{t.dashboard.occupancy}</div>
          <div
            className={clsx(
              'text-2xl font-bold',
              data.balance.percentage > 100 ? 'text-red-600' : 'text-green-600'
            )}
          >
            {data.balance.percentage}%
          </div>
        </div>
      </div>

      {/* Daily View */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">{t.dashboard.loadByDay}</h3>
        <div className="grid grid-cols-7 gap-2">
          {data.days.map((day) => (
            <div
              key={day.date}
              className={clsx(
                'p-3 rounded-lg text-center',
                day.is_overloaded ? 'bg-red-50 border-2 border-red-200' : 'bg-gray-50'
              )}
            >
              <div className="text-sm font-medium text-gray-600">
                {format(parseISO(day.date), 'EEE', { locale: dateLocale })}
              </div>
              <div className="text-xs text-gray-400">
                {format(parseISO(day.date), 'd MMM', { locale: dateLocale })}
              </div>
              <div
                className={clsx(
                  'text-xl font-bold mt-2',
                  day.is_overloaded ? 'text-red-600' : 'text-gray-900'
                )}
              >
                {day.load_percentage}%
              </div>
              <div className="text-xs text-gray-500 mt-1">
                {Math.round(day.load_minutes / 60)}h / {Math.round(day.capacity_minutes / 60)}h
              </div>
              {day.is_overloaded && (
                <span className="badge badge-danger mt-2">{t.dashboard.overload}</span>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Alerts */}
      {data.alerts.length > 0 && (
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">
            {t.dashboard.alerts} ({data.alerts.length})
          </h3>
          <div className="space-y-3">
            {data.alerts.map((alert: PlanningAlert) => (
              <div
                key={alert.id}
                className={clsx(
                  'p-3 rounded-lg flex justify-between items-start',
                  alert.severity === 'CRITICAL' && 'bg-red-100',
                  alert.severity === 'HIGH' && 'bg-orange-100',
                  alert.severity === 'MEDIUM' && 'bg-yellow-100',
                  alert.severity === 'LOW' && 'bg-blue-100'
                )}
              >
                <div>
                  <div className="flex items-center space-x-2">
                    <span
                      className={clsx(
                        'badge',
                        alert.severity === 'CRITICAL' && 'badge-danger',
                        alert.severity === 'HIGH' && 'badge-warning',
                        alert.severity === 'MEDIUM' && 'badge-info',
                        alert.severity === 'LOW' && 'badge-success'
                      )}
                    >
                      {alert.severity}
                    </span>
                    <span className="font-medium">{alert.title}</span>
                  </div>
                  <p className="text-sm text-gray-600 mt-1">{alert.message}</p>
                  <p className="text-xs text-gray-400 mt-1">
                    {format(parseISO(alert.date), 'd MMM', { locale: dateLocale })}
                    {alert.time_block_code && ` - ${alert.time_block_code}`}
                  </p>
                </div>
                <button
                  onClick={() => handleResolveAlert(alert.id)}
                  className="text-sm text-gray-500 hover:text-gray-700"
                >
                  {t.common.resolve}
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Load by Block */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">{t.dashboard.loadByBlock}</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {Object.entries(data.load.by_block).map(([blockCode, blockData]) => (
            <div key={blockCode} className="bg-gray-50 p-4 rounded-lg">
              <div className="font-medium text-gray-900">{blockCode}</div>
              <div className="text-2xl font-bold mt-2">
                {Math.round(blockData.minutes / 60)}h
              </div>
              <div className="text-sm text-gray-500">{blockData.tasks} {t.common.tasks}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
