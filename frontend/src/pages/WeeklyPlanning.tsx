import { useState, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getWeekPlans,
  getWeekPlan,
  publishWeekPlan,
  deleteWeekPlan,
  getWeekPlanByEmployee,
  uploadForecastPDF,
  getWeekPlanLoadExplanation,
  ForecastUploadResult,
} from '../api/client';
import { WeekPlan } from '../types';
import { format, parseISO, addDays, isValid } from 'date-fns';
import { es, fr } from 'date-fns/locale';
import { clsx } from 'clsx';
import { useLanguage } from '../i18n';

// Safe date parsing to avoid crashes
const safeParseISO = (dateStr: string | null | undefined): Date | null => {
  if (!dateStr) return null;
  try {
    const date = parseISO(dateStr);
    return isValid(date) ? date : null;
  } catch {
    return null;
  }
};

const safeFormat = (date: Date | string | null | undefined, formatStr: string, options?: { locale?: Locale }): string => {
  if (!date) return '-';
  try {
    const d = typeof date === 'string' ? parseISO(date) : date;
    if (!isValid(d)) return '-';
    return format(d, formatStr, options);
  } catch {
    return '-';
  }
};

const SHIFT_COLORS: Record<string, string> = {
  DAY: 'bg-blue-100 text-blue-800 border-blue-200',
  EVENING: 'bg-orange-100 text-orange-800 border-orange-200',
  NIGHT: 'bg-purple-100 text-purple-800 border-purple-200',
};

const getShiftColor = (shiftCode: string): string => {
  if (shiftCode?.includes('MANANA') || shiftCode?.includes('DIA') || shiftCode?.includes('JOUR')) {
    return SHIFT_COLORS.DAY;
  }
  if (shiftCode?.includes('TARDE') || shiftCode?.includes('SOIR')) {
    return SHIFT_COLORS.EVENING;
  }
  if (shiftCode?.includes('NUIT') || shiftCode?.includes('NOCHE')) {
    return SHIFT_COLORS.NIGHT;
  }
  return 'bg-gray-100 text-gray-800';
};

export default function WeeklyPlanning() {
  const { t, language } = useLanguage();
  const dateLocale = language === 'fr' ? fr : es;

  const queryClient = useQueryClient();
  const [selectedPlanId, setSelectedPlanId] = useState<number | null>(null);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadResult, setUploadResult] = useState<ForecastUploadResult | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Queries
  const { data: weekPlans, isLoading: loadingPlans } = useQuery({
    queryKey: ['weekPlans'],
    queryFn: getWeekPlans,
  });

  const { data: selectedPlan } = useQuery({
    queryKey: ['weekPlan', selectedPlanId],
    queryFn: () => getWeekPlan(selectedPlanId!),
    enabled: !!selectedPlanId,
  });

  const { data: byEmployee } = useQuery({
    queryKey: ['weekPlanByEmployee', selectedPlanId],
    queryFn: () => getWeekPlanByEmployee(selectedPlanId!),
    enabled: !!selectedPlanId,
  });

  const { data: loadExplanation } = useQuery({
    queryKey: ['weekPlanLoadExplanation', selectedPlanId],
    queryFn: () => getWeekPlanLoadExplanation(selectedPlanId!),
    enabled: !!selectedPlanId,
  });

  // Mutations
  const publishMutation = useMutation({
    mutationFn: publishWeekPlan,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['weekPlans'] });
      queryClient.invalidateQueries({ queryKey: ['weekPlan', selectedPlanId] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteWeekPlan,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['weekPlans'] });
      setSelectedPlanId(null);
    },
  });

  const uploadMutation = useMutation({
    mutationFn: uploadForecastPDF,
    onSuccess: (data) => {
      setUploadResult(data);
      queryClient.invalidateQueries({ queryKey: ['weekPlans'] });
      setSelectedPlanId(data.week_plan_id);
    },
  });

  const handleFileUpload = (file: File) => {
    if (file && file.type === 'application/pdf') {
      uploadMutation.mutate(file);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    const file = e.dataTransfer.files[0];
    handleFileUpload(file);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(true);
  };

  const handleDragLeave = () => {
    setDragActive(false);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileUpload(file);
    }
  };

  const handlePublish = () => {
    if (selectedPlanId) {
      publishMutation.mutate(selectedPlanId);
    }
  };

  const handleDelete = () => {
    if (selectedPlanId && confirm(t.weekly.confirmDelete || 'Are you sure?')) {
      deleteMutation.mutate(selectedPlanId);
    }
  };

  const closeModal = () => {
    setShowUploadModal(false);
    setUploadResult(null);
    uploadMutation.reset();
  };

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      DRAFT: 'bg-yellow-100 text-yellow-800',
      REVIEW: 'bg-blue-100 text-blue-800',
      APPROVED: 'bg-green-100 text-green-800',
      PUBLISHED: 'bg-green-100 text-green-800',
      ARCHIVED: 'bg-gray-100 text-gray-800',
    };
    const statusKey = status.toLowerCase() as keyof typeof t.weekly.status;
    const label = t.weekly.status[statusKey] || status;
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${styles[status] || ''}`}>
        {label}
      </span>
    );
  };

  const getWeekDays = (startDate: string) => {
    const start = safeParseISO(startDate);
    if (!start) return [];
    return Array.from({ length: 7 }, (_, i) => addDays(start, i));
  };

  const getDayName = (index: number): string => {
    const dayKeys = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'] as const;
    return t.days[dayKeys[index]];
  };

  const getShiftDisplay = (shift: any) => {
    if (!shift || shift.is_day_off) return null;

    const colorClass = getShiftColor(shift.shift);
    const startTime = shift.start_time?.slice(0, 5) || '09:00';
    const endTime = shift.end_time?.slice(0, 5) || '17:00';
    const hours = shift.hours || 8;

    // Calcular hora de almuerzo (depende del turno)
    const startHour = parseInt(startTime.split(':')[0]);
    const lunchTime = startHour < 12 ? '12:30' : '18:30'; // Mañana: 12:30, Tarde: 18:30

    return (
      <div className={`px-2 py-1.5 rounded border text-xs ${colorClass}`}>
        <div className="font-semibold">{startTime}</div>
        <div className="text-[10px] text-gray-500 flex items-center gap-1">
          <span>🍽️</span>
          <span>{lunchTime}</span>
        </div>
        <div className="text-[10px] opacity-75">{hours}h</div>
        <div className="font-semibold">{endTime}</div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">{t.weekly.title}</h2>
        <button
          onClick={() => setShowUploadModal(true)}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium"
        >
          {t.weekly.uploadForecast}
        </button>
      </div>

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-xl font-bold">{t.weekly.uploadTitle}</h3>
                <button
                  onClick={closeModal}
                  className="text-gray-500 hover:text-gray-700 text-2xl"
                >
                  &times;
                </button>
              </div>

              {/* Upload Area */}
              {!uploadResult && !uploadMutation.isPending && (
                <div
                  onDrop={handleDrop}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onClick={() => fileInputRef.current?.click()}
                  className={clsx(
                    'border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors',
                    dragActive
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-300 hover:border-gray-400'
                  )}
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".pdf"
                    onChange={handleFileSelect}
                    className="hidden"
                  />
                  <div className="text-5xl mb-4">📄</div>
                  <p className="text-lg font-medium text-gray-700 mb-2">
                    {t.weekly.dragPdf}
                  </p>
                  <p className="text-sm text-gray-500">
                    {t.weekly.clickToSelect}
                  </p>
                </div>
              )}

              {/* Loading */}
              {uploadMutation.isPending && (
                <div className="text-center py-12">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                  <p className="text-gray-600">{t.weekly.processingPdf}</p>
                </div>
              )}

              {/* Error */}
              {uploadMutation.isError && (
                <div className="mb-6 p-4 bg-red-50 rounded-lg">
                  <p className="text-red-700 font-medium">{t.weekly.errorProcessing}</p>
                  <p className="text-red-600 text-sm mt-1">
                    {(uploadMutation.error as Error)?.message || t.weekly.unknownError}
                  </p>
                  <button
                    onClick={() => uploadMutation.reset()}
                    className="mt-4 px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded"
                  >
                    {t.weekly.tryAgain}
                  </button>
                </div>
              )}

              {/* Success Result */}
              {uploadResult && (
                <div className="space-y-6">
                  <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                    <h4 className="font-semibold text-green-800 mb-3">
                      {t.weekly.planGenerated}
                    </h4>

                    <div className="grid grid-cols-3 gap-4 text-sm mb-4">
                      <div className="bg-white p-3 rounded">
                        <div className="text-gray-500 text-xs">{t.weekly.totalHours}</div>
                        <div className="font-bold text-lg">
                          {uploadResult.load_summary.total_hours.toFixed(1)}h
                        </div>
                      </div>
                      <div className="bg-white p-3 rounded">
                        <div className="text-gray-500 text-xs">{t.weekly.dayShift}</div>
                        <div className="font-bold text-lg text-blue-600">
                          {uploadResult.load_summary.day_shift_hours.toFixed(1)}h
                        </div>
                      </div>
                      <div className="bg-white p-3 rounded">
                        <div className="text-gray-500 text-xs">{t.weekly.eveningShift}</div>
                        <div className="font-bold text-lg text-orange-600">
                          {uploadResult.load_summary.evening_shift_hours.toFixed(1)}h
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="flex justify-end">
                    <button
                      onClick={closeModal}
                      className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium"
                    >
                      {t.weekly.viewPlan}
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Plans List */}
        <div className="bg-white rounded-lg shadow p-4">
          <h3 className="text-lg font-semibold mb-4">{t.weekly.plans}</h3>
          {loadingPlans ? (
            <p className="text-gray-500">{t.common.loading}</p>
          ) : (
            <div className="space-y-2">
              {weekPlans?.results?.map((plan: WeekPlan) => (
                <button
                  key={plan.id}
                  onClick={() => setSelectedPlanId(plan.id)}
                  className={clsx(
                    'w-full text-left p-3 rounded-lg transition-colors border',
                    selectedPlanId === plan.id
                      ? 'bg-blue-50 border-blue-500'
                      : 'bg-gray-50 hover:bg-gray-100 border-transparent'
                  )}
                >
                  <div className="flex justify-between items-center">
                    <span className="font-medium">
                      {safeFormat(plan.week_start_date, 'd MMM yyyy', { locale: dateLocale })}
                    </span>
                    {getStatusBadge(plan.status)}
                  </div>
                </button>
              ))}
              {(!weekPlans?.results || weekPlans.results.length === 0) && (
                <p className="text-gray-500 text-sm">{t.weekly.noPlans}</p>
              )}
            </div>
          )}
        </div>

        {/* Plan Detail */}
        <div className="lg:col-span-4">
          {selectedPlanId && selectedPlan ? (
            <div className="space-y-4">
              {/* Plan Header */}
              <div className="bg-white rounded-lg shadow p-4">
                <div className="flex justify-between items-center">
                  <div>
                    <h3 className="text-xl font-bold">
                      {t.weekly.weekOf} {safeFormat(selectedPlan.week_start_date, 'd MMMM yyyy', { locale: dateLocale })}
                    </h3>
                    <div className="flex items-center gap-3 mt-2">
                      {getStatusBadge(selectedPlan.status)}
                      <span className="text-sm text-gray-500">
                        {selectedPlan.total_assigned_hours || 0}{t.weekly.hoursAssigned}
                      </span>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={handleDelete}
                      disabled={deleteMutation.isPending}
                      className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg font-medium"
                    >
                      {deleteMutation.isPending ? t.weekly.deleting : t.weekly.delete}
                    </button>
                    {selectedPlan.status === 'DRAFT' && (
                      <button
                        onClick={handlePublish}
                        disabled={publishMutation.isPending}
                        className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg font-medium"
                      >
                        {publishMutation.isPending ? t.weekly.publishing : t.weekly.publish}
                      </button>
                    )}
                  </div>
                </div>
              </div>

              {/* Schedule Grid */}
              {byEmployee && Object.keys(byEmployee).length > 0 && (
                <div className="bg-white rounded-lg shadow overflow-hidden">
                  <div className="p-4 border-b">
                    <h4 className="font-semibold">{t.weekly.scheduleByEmployee}</h4>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="bg-gray-50">
                          <th className="text-left p-3 font-semibold border-b w-48">{t.weekly.employee}</th>
                          {getWeekDays(selectedPlan.week_start_date).map((day) => (
                            <th key={day.toISOString()} className="text-center p-3 font-semibold border-b min-w-24">
                              <div className="text-sm">{format(day, 'EEE', { locale: dateLocale })}</div>
                              <div className="text-xs text-gray-500 font-normal">
                                {format(day, 'd MMM', { locale: dateLocale })}
                              </div>
                            </th>
                          ))}
                          <th className="text-center p-3 font-semibold border-b w-20">{t.common.total}</th>
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
                            <tr key={key} className="border-b hover:bg-gray-50">
                              <td className="p-3">
                                <div className="font-medium text-gray-900">{emp.name}</div>
                                <div className="text-xs text-gray-500">{emp.role}</div>
                              </td>
                              {weekDays.map((day) => {
                                const dateStr = format(day, 'yyyy-MM-dd');
                                const shift = shiftsByDate[dateStr];

                                return (
                                  <td key={dateStr} className="text-center p-2">
                                    {shift ? (
                                      shift.is_day_off ? (
                                        <span className="text-gray-300 text-lg">-</span>
                                      ) : (
                                        getShiftDisplay(shift)
                                      )
                                    ) : (
                                      <span className="inline-block px-2 py-1 bg-green-50 text-green-600 rounded text-xs font-medium">
                                        {t.common.free}
                                      </span>
                                    )}
                                  </td>
                                );
                              })}
                              <td className="text-center p-3 font-bold text-gray-900">
                                {totalHours}h
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Legend - Load Explanation */}
              {loadExplanation && loadExplanation.days.length > 0 && (
                <div className="bg-white rounded-lg shadow overflow-hidden">
                  <div className="p-4 border-b bg-gray-50">
                    <h4 className="font-semibold">{t.weekly.legend.title}</h4>
                    <p className="text-sm text-gray-500 mt-1">
                      {t.weekly.legend.totalWeek}: {loadExplanation.totals.total_hours}h
                      ({t.weekly.legend.morning}: {loadExplanation.totals.day_shift_hours}h, {t.weekly.legend.evening}: {loadExplanation.totals.evening_shift_hours}h)
                    </p>
                  </div>

                  {/* Resumen semanal de horas */}
                  {(loadExplanation as any).weekly_summary && (
                    <div className="p-4 bg-blue-50 border-b">
                      <h5 className="font-semibold text-blue-800 mb-3">{t.weekly.legend.weeklySummary}</h5>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-3">
                        <div className="bg-white rounded p-2 text-center">
                          <div className="text-xs text-gray-500">{t.weekly.legend.contracted}</div>
                          <div className="font-bold text-lg">{(loadExplanation as any).weekly_summary.totals.contracted}h</div>
                        </div>
                        <div className="bg-white rounded p-2 text-center">
                          <div className="text-xs text-gray-500">{t.weekly.legend.assigned}</div>
                          <div className="font-bold text-lg">{(loadExplanation as any).weekly_summary.totals.assigned}h</div>
                        </div>
                        <div className="bg-white rounded p-2 text-center">
                          <div className="text-xs text-gray-500">{t.weekly.legend.needed}</div>
                          <div className="font-bold text-lg">{(loadExplanation as any).weekly_summary.totals.needed}h</div>
                        </div>
                        <div className="bg-white rounded p-2 text-center">
                          <div className="text-xs text-gray-500">{t.weekly.legend.spareDeficit}</div>
                          <div className={`font-bold text-lg ${(loadExplanation as any).weekly_summary.totals.assigned_vs_needed >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {(loadExplanation as any).weekly_summary.totals.assigned_vs_needed >= 0 ? '+' : ''}
                            {(loadExplanation as any).weekly_summary.totals.assigned_vs_needed}h
                          </div>
                        </div>
                      </div>
                      <div className="text-xs text-blue-700">
                        <span className="font-medium">{t.weekly.legend.byEmployee}: </span>
                        {(loadExplanation as any).weekly_summary.employees.map((emp: any, idx: number) => (
                          <span key={idx}>
                            {emp.name.split(' ')[0]}: {emp.assigned}h/{emp.contracted}h
                            {emp.pending !== 0 && <span className={emp.pending > 0 ? 'text-yellow-600' : 'text-green-600'}> ({emp.pending > 0 ? t.weekly.legend.missing : t.weekly.legend.extra} {Math.abs(emp.pending)}h)</span>}
                            {idx < (loadExplanation as any).weekly_summary.employees.length - 1 && ' · '}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="divide-y">
                    {loadExplanation.days.map((day, index) => {
                      const stays = Math.max(0, day.forecast.occupied - day.forecast.arrivals);
                      return (
                        <div key={day.date} className="p-4">
                          <div className="flex items-start gap-4">
                            {/* Day Header */}
                            <div className="w-28 flex-shrink-0">
                              <div className="font-bold text-gray-900">{getDayName(index)}</div>
                              <div className="text-sm text-gray-500">
                                {safeFormat(day.date, 'd MMM', { locale: dateLocale })}
                              </div>
                            </div>

                            {/* Forecast Data */}
                            <div className="flex-1">
                              <div className="flex flex-wrap gap-3 mb-2">
                                <span className="inline-flex items-center px-2 py-1 rounded bg-red-50 text-red-700 text-sm">
                                  {day.forecast.departures} {t.weekly.legend.departures}
                                </span>
                                <span className="inline-flex items-center px-2 py-1 rounded bg-green-50 text-green-700 text-sm">
                                  {day.forecast.arrivals} {t.weekly.legend.arrivals}
                                </span>
                                <span className="inline-flex items-center px-2 py-1 rounded bg-blue-50 text-blue-700 text-sm">
                                  {day.forecast.occupied} {t.weekly.legend.occupied}
                                </span>
                                <span className="inline-flex items-center px-2 py-1 rounded bg-purple-50 text-purple-700 text-sm">
                                  {stays} {t.weekly.legend.stays}
                                </span>
                              </div>

                              {/* Distribución del día */}
                              {(() => {
                                const numDay = day.assigned.DAY.length;
                                const numEvening = day.assigned.EVENING.length;
                                const departures = day.forecast.departures;
                                const totalRooms = departures + stays;
                                const occupied = day.forecast.occupied;

                                // Tiempos de tareas (en minutos)
                                const DEPART_MIN = 50;
                                const RECOUCH_MIN = 20;
                                const COUV_MIN = 20;

                                // Horas disponibles por período
                                const P1_HOURS = 3.5; // 09:00-12:30
                                const P2_HOURS = 3.5; // 13:30-17:00
                                const P3_HOURS = 1.5; // 17:00-18:30
                                const COUV_HOURS = 2.5; // 19:00-21:30

                                // P1: Mañana sola (09:00-12:30)
                                const p1Available = numDay * P1_HOURS * 60; // minutos disponibles
                                const p1Needed = (departures * DEPART_MIN + stays * RECOUCH_MIN) * 0.4; // ~40% del trabajo
                                const p1Balance = (p1Available - p1Needed) / 60;

                                // P2: Mañana + Tarde (13:30-17:00)
                                const p2Available = (numDay + numEvening) * P2_HOURS * 60;
                                const p2Needed = (departures * DEPART_MIN + stays * RECOUCH_MIN) * 0.5; // ~50% del trabajo
                                const p2Balance = (p2Available - p2Needed) / 60;

                                // P3: Tarde sola termina (17:00-18:30)
                                const p3Available = numEvening * P3_HOURS * 60;
                                const p3Needed = (departures * DEPART_MIN + stays * RECOUCH_MIN) * 0.1; // ~10% restante
                                const p3Balance = (p3Available - p3Needed) / 60;

                                // Couverture (19:00-21:30)
                                const couvAvailable = numEvening * COUV_HOURS * 60;
                                const couvNeeded = occupied * COUV_MIN;
                                const couvBalance = (couvAvailable - couvNeeded) / 60;

                                // Función para mostrar balance
                                const renderBalance = (balance: number) => {
                                  const isPositive = balance >= 0;
                                  return (
                                    <span className={`text-[10px] font-medium ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
                                      {isPositive ? '✓' : '⚠'} {isPositive ? '+' : ''}{balance.toFixed(1)}h
                                    </span>
                                  );
                                };

                                // Cálculos de habitaciones por período (estimación)
                                const pairsP1 = Math.max(1, Math.floor(numDay / 2));
                                const pairsP2 = Math.max(1, Math.floor((numDay + numEvening) / 2));
                                const departsPerHour = 1.2;
                                const recouchPerHour = 3;
                                const departsDoneP1 = Math.min(departures, Math.floor(pairsP1 * P1_HOURS * departsPerHour));
                                const hoursLeftP1 = P1_HOURS - (departsDoneP1 / departsPerHour / pairsP1);
                                const recouchDoneP1 = Math.min(stays, Math.floor(pairsP1 * hoursLeftP1 * recouchPerHour));
                                const departsLeft = departures - departsDoneP1;
                                const recouchLeft = stays - recouchDoneP1;
                                const departsDoneP2 = Math.min(departsLeft, Math.floor(pairsP2 * P2_HOURS * departsPerHour));
                                const hoursLeftP2 = P2_HOURS - (departsDoneP2 / departsPerHour / pairsP2);
                                const recouchDoneP2 = Math.min(recouchLeft, Math.floor(pairsP2 * hoursLeftP2 * recouchPerHour));
                                const recouchLeftP3 = Math.max(0, stays - recouchDoneP1 - recouchDoneP2);

                                const dayNames = day.assigned.DAY.map(a => a.employee?.split(' ')[0]).join(' + ');
                                const eveningNames = day.assigned.EVENING.map(a => a.employee?.split(' ')[0]).join(' + ');

                                return (
                                  <div className="mt-3 bg-gradient-to-b from-gray-50 to-white rounded-lg border border-gray-200 overflow-hidden">
                                    {/* Header */}
                                    <div className="bg-gray-100 px-3 py-2 border-b border-gray-200">
                                      <div className="flex justify-between items-center text-sm">
                                        <span className="font-semibold text-gray-700">{t.weekly.legend.dailyDistribution}</span>
                                        <span className="text-gray-500">{totalRooms} {t.weekly.legend.rooms} + {occupied} {t.weekly.legend.couv}</span>
                                      </div>
                                    </div>

                                    <div className="divide-y divide-gray-100">
                                      {/* Período 1: Mañana sola */}
                                      <div className="px-3 py-2 flex items-start gap-3">
                                        <div className="text-lg">🌅</div>
                                        <div className="flex-1 min-w-0">
                                          <div className="flex items-baseline justify-between">
                                            <span className="font-medium text-blue-700 text-sm">09:00 - 12:30</span>
                                            <div className="flex items-center gap-2">
                                              <span className="text-xs text-gray-500">{t.weekly.legend.morningAlone}</span>
                                              {renderBalance(p1Balance)}
                                            </div>
                                          </div>
                                          <div className="text-xs text-gray-600 mt-0.5">
                                            <span className="font-medium">{departsDoneP1 + recouchDoneP1} {t.weekly.legend.rooms}</span>
                                            {departsDoneP1 > 0 && <span className="text-red-600 ml-1">({departsDoneP1} {t.weekly.legend.depart})</span>}
                                            {recouchDoneP1 > 0 && <span className="text-green-600 ml-1">({recouchDoneP1} {t.weekly.legend.recouch})</span>}
                                          </div>
                                          {numDay > 0 && <div className="text-xs text-blue-600 mt-0.5">{dayNames}</div>}
                                        </div>
                                      </div>

                                      {/* Almuerzo Mañana */}
                                      <div className="px-3 py-1.5 bg-gray-50 flex items-center gap-3">
                                        <div className="text-base">🍽️</div>
                                        <span className="text-xs text-gray-500">12:30 - 13:30 {t.weekly.legend.morningLunch}</span>
                                      </div>

                                      {/* Período 2: Mañana + Tarde */}
                                      <div className="px-3 py-2 flex items-start gap-3">
                                        <div className="text-lg">🔄</div>
                                        <div className="flex-1 min-w-0">
                                          <div className="flex items-baseline justify-between">
                                            <span className="font-medium text-purple-700 text-sm">13:30 - 17:00</span>
                                            <div className="flex items-center gap-2">
                                              <span className="text-xs text-gray-500">{t.weekly.legend.morningEvening}</span>
                                              {renderBalance(p2Balance)}
                                            </div>
                                          </div>
                                          <div className="text-xs text-gray-600 mt-0.5">
                                            <span className="font-medium">{departsDoneP2 + recouchDoneP2} {t.weekly.legend.rooms}</span>
                                            {departsDoneP2 > 0 && <span className="text-red-600 ml-1">({departsDoneP2} {t.weekly.legend.depart})</span>}
                                            {recouchDoneP2 > 0 && <span className="text-green-600 ml-1">({recouchDoneP2} {t.weekly.legend.recouch})</span>}
                                          </div>
                                          <div className="text-xs mt-0.5">
                                            {numDay > 0 && <span className="text-blue-600">{dayNames}</span>}
                                            {numDay > 0 && numEvening > 0 && <span className="text-gray-400 mx-1">·</span>}
                                            {numEvening > 0 && <span className="text-orange-600">{eveningNames}</span>}
                                          </div>
                                        </div>
                                      </div>

                                      {/* Período 3: Tarde termina limpieza */}
                                      <div className="px-3 py-2 flex items-start gap-3">
                                        <div className="text-lg">⏰</div>
                                        <div className="flex-1 min-w-0">
                                          <div className="flex items-baseline justify-between">
                                            <span className="font-medium text-yellow-700 text-sm">17:00 - 18:30</span>
                                            <div className="flex items-center gap-2">
                                              <span className="text-xs text-gray-500">{t.weekly.legend.eveningFinishes}</span>
                                              {renderBalance(p3Balance)}
                                            </div>
                                          </div>
                                          <div className="text-xs text-gray-600 mt-0.5">
                                            {recouchLeftP3 > 0
                                              ? <span className="font-medium">{recouchLeftP3} {t.weekly.legend.recouch} {t.weekly.legend.pending}</span>
                                              : <span className="text-green-600">{t.weekly.legend.noPending}</span>
                                            }
                                          </div>
                                          {numEvening > 0 && <div className="text-xs text-orange-600 mt-0.5">{eveningNames}</div>}
                                        </div>
                                      </div>

                                      {/* Almuerzo Tarde */}
                                      <div className="px-3 py-1.5 bg-gray-50 flex items-center gap-3">
                                        <div className="text-base">🍽️</div>
                                        <span className="text-xs text-gray-500">18:30 - 19:00 {t.weekly.legend.eveningLunch}</span>
                                      </div>

                                      {/* Couverture */}
                                      <div className="px-3 py-2 flex items-start gap-3 bg-orange-50">
                                        <div className="text-lg">🌙</div>
                                        <div className="flex-1 min-w-0">
                                          <div className="flex items-baseline justify-between">
                                            <span className="font-medium text-orange-700 text-sm">19:00 - 21:30</span>
                                            <div className="flex items-center gap-2">
                                              <span className="text-xs text-gray-500">{t.weekly.legend.couvertures}</span>
                                              {renderBalance(couvBalance)}
                                            </div>
                                          </div>
                                          <div className="text-xs text-gray-600 mt-0.5">
                                            <span className="font-medium">{occupied} {t.weekly.legend.couvertures}</span>
                                            {numEvening > 0 && <span className="text-orange-600 ml-1">(~{Math.round(occupied/numEvening)} {t.weekly.legend.perPerson})</span>}
                                          </div>
                                          {numEvening > 0 && <div className="text-xs text-orange-600 mt-0.5">{eveningNames}</div>}
                                        </div>
                                      </div>

                                      {/* Balance de horas */}
                                      {(day as any).hours_balance && (
                                        <div className="px-3 py-2 bg-gray-100 border-t border-gray-200">
                                          <div className="flex items-center gap-2 text-xs">
                                            <span className="font-semibold text-gray-700">{t.weekly.legend.balance}:</span>
                                            {(() => {
                                              const balance = (day as any).hours_balance;
                                              const spare = balance.total.spare;
                                              const spareClass = spare >= 0 ? 'text-green-600' : 'text-red-600';
                                              const spareIcon = spare >= 0 ? '✓' : '⚠';
                                              return (
                                                <>
                                                  <span className="text-gray-600">
                                                    {balance.total.assigned}h {t.weekly.legend.assignedHours} / {balance.total.needed}h {t.weekly.legend.neededHours}
                                                  </span>
                                                  <span className={`font-medium ${spareClass}`}>
                                                    {spareIcon} {spare >= 0 ? '+' : ''}{spare}h
                                                  </span>
                                                </>
                                              );
                                            })()}
                                          </div>
                                        </div>
                                      )}
                                    </div>
                                  </div>
                                );
                              })()}
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow p-12 text-center">
              <div className="text-5xl mb-4">📅</div>
              <p className="text-gray-500 text-lg">
                {t.weekly.selectPlan}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
