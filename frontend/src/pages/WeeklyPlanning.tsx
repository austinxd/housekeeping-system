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
  const [uploadStep, setUploadStep] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);
  const [buildStep, setBuildStep] = useState(0); // 0-7 para animar cada día
  const [isAnimatingCalendar, setIsAnimatingCalendar] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Pasos del proceso de carga
  const uploadSteps = [
    { icon: '📄', text: 'Leyendo PDF...', color: 'text-blue-600' },
    { icon: '📊', text: 'Analizando forecast...', color: 'text-purple-600' },
    { icon: '🧮', text: 'Calculando carga de trabajo...', color: 'text-orange-600' },
    { icon: '👥', text: 'Asignando personal...', color: 'text-green-600' },
    { icon: '⚡', text: 'Optimizando distribución...', color: 'text-yellow-600' },
    { icon: '✨', text: '¡Plan generado!', color: 'text-emerald-600' },
  ];

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
    onSuccess: async (data) => {
      // Cerrar modal y mostrar resultado
      setShowUploadModal(false);
      setIsProcessing(false);
      setUploadResult(data);
      queryClient.invalidateQueries({ queryKey: ['weekPlans'] });
      setSelectedPlanId(data.week_plan_id);

      // Iniciar animación del calendario principal
      setIsAnimatingCalendar(true);
      setBuildStep(0);

      // Animar día por día
      for (let i = 0; i <= 7; i++) {
        await new Promise(resolve => setTimeout(resolve, 250));
        setBuildStep(i + 1);
      }

      // Terminar animación
      await new Promise(resolve => setTimeout(resolve, 300));
      setIsAnimatingCalendar(false);
    },
    onError: () => {
      setIsProcessing(false);
      setUploadStep(0);
    },
  });

  const handleFileUpload = async (file: File) => {
    if (file && file.type === 'application/pdf') {
      setIsProcessing(true);
      setUploadStep(0);
      setUploadResult(null);

      // Animar pasos mientras se procesa
      const stepDurations = [300, 400, 500, 400, 300];
      for (let i = 0; i < 5; i++) {
        await new Promise(resolve => setTimeout(resolve, stepDurations[i]));
        setUploadStep(i + 1);
      }

      // Hacer la petición real
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
    setUploadStep(0);
    setIsProcessing(false);
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

  // Obtener mapa de elasticidad por fecha desde loadExplanation
  const getElasticityByDate = (): Record<string, { extraMin: number; canCover: boolean }> => {
    const map: Record<string, { extraMin: number; canCover: boolean }> = {};
    if (loadExplanation?.days) {
      for (const day of loadExplanation.days) {
        const couv = (day as any).daily_distribution?.periods?.couvertures;
        if (couv?.can_cover_with_elasticity && couv.elasticity_extra_per_person_min > 0) {
          map[day.date] = {
            extraMin: couv.elasticity_extra_per_person_min,
            canCover: true,
          };
        }
      }
    }
    return map;
  };

  const elasticityByDate = getElasticityByDate();

  const getShiftDisplay = (shift: any, elasticityInfo?: { extraMin: number; canCover: boolean }) => {
    if (!shift || shift.is_day_off) return null;

    const startTime = shift.start_time?.slice(0, 5) || '09:00';
    const endTime = shift.end_time?.slice(0, 5) || '17:00';
    const hours = shift.hours || 8;
    const freeHours = shift.free_hours || 0;

    const isMorning = shift.shift?.includes('MANANA') || shift.shift?.includes('DIA') || shift.shift?.includes('JOUR');
    const isEvening = shift.shift?.includes('TARDE') || shift.shift?.includes('SOIR') || shift.shift?.includes('EVENING');
    const hasElasticity = isEvening && elasticityInfo?.canCover && elasticityInfo.extraMin > 0;

    // Colores según turno
    const gradientBg = isMorning
      ? 'bg-gradient-to-br from-sky-100 to-blue-50'
      : 'bg-gradient-to-br from-amber-100 to-orange-50';
    const textColor = isMorning ? 'text-sky-800' : 'text-amber-800';
    const borderStyle = hasElasticity ? 'ring-2 ring-blue-400' : 'border border-gray-200';

    return (
      <div className={`relative rounded-lg ${gradientBg} ${borderStyle} shadow-sm hover:shadow-md transition-shadow`}>
        <div className="p-2">
          {/* Horarios con iconos */}
          <div className="space-y-0.5">
            <div className={`flex items-center justify-center gap-1.5 text-xs ${textColor}`}>
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
              <span className="font-semibold">{startTime}</span>
            </div>
            <div className={`flex items-center justify-center gap-1.5 text-xs ${textColor}`}>
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
              </svg>
              <span className="font-semibold">{endTime}</span>
            </div>
          </div>

          {/* Horas de trabajo / Horas libres */}
          <div className="text-center mt-1">
            <span className="text-sm font-semibold text-gray-600">{hours}h</span>
            {freeHours > 0 && (
              <>
                <span className="text-xs text-gray-300">/</span>
                <span className="text-xs text-red-400">
                  {freeHours >= 1 ? `${freeHours}h` : `${Math.round(freeHours * 60)}m`}
                </span>
              </>
            )}
          </div>

          {/* Elasticidad */}
          {hasElasticity && (
            <div className="mt-1 text-center">
              <span className="text-[9px] font-medium text-blue-600">
                ⚡+{elasticityInfo.extraMin}m
              </span>
            </div>
          )}
        </div>
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
              {!uploadResult && !isProcessing && (
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

              {/* Processing Animation */}
              {isProcessing && (
                <div className="py-12 text-center">
                  {/* Spinner */}
                  <div className="inline-flex items-center justify-center w-16 h-16 mb-4">
                    <div className="w-12 h-12 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
                  </div>

                  {/* Status text */}
                  <p className={clsx(
                    'text-lg font-medium transition-colors duration-300',
                    uploadSteps[uploadStep]?.color || 'text-gray-600'
                  )}>
                    {uploadSteps[uploadStep]?.icon} {uploadSteps[uploadStep]?.text}
                  </p>

                  {/* Progress bar */}
                  <div className="mt-6 max-w-xs mx-auto">
                    <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-sky-500 via-blue-500 to-emerald-500 rounded-full transition-all duration-500 ease-out"
                        style={{ width: `${(uploadStep / (uploadSteps.length - 1)) * 100}%` }}
                      />
                    </div>
                  </div>
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
                <div className={clsx(
                  "bg-white rounded-lg shadow overflow-hidden transition-all duration-500",
                  isAnimatingCalendar && "ring-2 ring-blue-400 ring-opacity-50"
                )}>
                  <div className="p-4 border-b flex items-center justify-between">
                    <h4 className="font-semibold">{t.weekly.scheduleByEmployee}</h4>
                    {isAnimatingCalendar && (
                      <span className="text-sm text-blue-600 animate-pulse flex items-center gap-2">
                        <span className="w-2 h-2 bg-blue-500 rounded-full animate-ping"></span>
                        Cargando planificación...
                      </span>
                    )}
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="bg-gray-50">
                          <th className="text-left p-3 font-semibold border-b w-48">{t.weekly.employee}</th>
                          {getWeekDays(selectedPlan.week_start_date).map((day, dayIndex) => (
                            <th
                              key={day.toISOString()}
                              className={clsx(
                                "text-center p-3 font-semibold border-b min-w-24 transition-all duration-300",
                                isAnimatingCalendar && buildStep <= dayIndex && "opacity-30 bg-gray-100"
                              )}
                              style={isAnimatingCalendar ? { transitionDelay: `${dayIndex * 50}ms` } : undefined}
                            >
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
                        {Object.entries(byEmployee).map(([key, emp]: [string, any], empIndex: number) => {
                          const weekDays = getWeekDays(selectedPlan.week_start_date);
                          const shiftsByDate: Record<string, any> = {};
                          emp.shifts.forEach((shift: any) => {
                            shiftsByDate[shift.date] = shift;
                          });

                          // Calcular horas totales incluyendo elasticidad
                          const totalHours = emp.shifts.reduce((sum: number, s: any) => {
                            if (s.is_day_off) return sum;
                            const baseHours = s.hours || 0;
                            const elasticity = elasticityByDate[s.date];
                            const isEvening = s.shift?.includes('TARDE') || s.shift?.includes('SOIR') || s.shift?.includes('EVENING');
                            const extraHours = (isEvening && elasticity?.canCover) ? (elasticity.extraMin / 60) : 0;
                            return sum + baseHours + extraHours;
                          }, 0);

                          const showRow = !isAnimatingCalendar || buildStep > 0;

                          return (
                            <tr
                              key={key}
                              className={clsx(
                                "border-b hover:bg-gray-50 transition-all duration-300",
                                isAnimatingCalendar && !showRow && "opacity-0"
                              )}
                              style={isAnimatingCalendar ? { transitionDelay: `${empIndex * 80}ms` } : undefined}
                            >
                              <td className="p-3">
                                <div className="font-medium text-gray-900">{emp.name}</div>
                                <div className="text-xs text-gray-500">{emp.role}</div>
                              </td>
                              {weekDays.map((day, dayIndex) => {
                                const dateStr = format(day, 'yyyy-MM-dd');
                                const shift = shiftsByDate[dateStr];
                                const elasticityInfo = elasticityByDate[dateStr];
                                const showCell = !isAnimatingCalendar || buildStep > dayIndex;

                                return (
                                  <td
                                    key={dateStr}
                                    className={clsx(
                                      "text-center p-2 transition-all duration-300",
                                      isAnimatingCalendar && !showCell && "opacity-0 scale-75"
                                    )}
                                    style={isAnimatingCalendar ? { transitionDelay: `${dayIndex * 40 + empIndex * 30}ms` } : undefined}
                                  >
                                    {shift ? (
                                      shift.is_day_off ? (
                                        <span className="text-gray-300 text-lg">-</span>
                                      ) : (
                                        <div className={isAnimatingCalendar && showCell ? 'animate-scaleIn' : ''}>
                                          {getShiftDisplay(shift, elasticityInfo)}
                                        </div>
                                      )
                                    ) : (
                                      <span className="inline-block px-2 py-1 bg-green-50 text-green-600 rounded text-xs font-medium">
                                        {t.common.free}
                                      </span>
                                    )}
                                  </td>
                                );
                              })}
                              <td className={clsx(
                                "text-center p-3 font-bold text-gray-900 transition-all duration-500",
                                isAnimatingCalendar && buildStep < 7 && "opacity-0"
                              )}>
                                {totalHours % 1 === 0 ? totalHours : totalHours.toFixed(1)}h
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

                              {/* Distribución del día - usando datos pre-calculados del backend */}
                              {(day as any).daily_distribution && (() => {
                                const dist = (day as any).daily_distribution;
                                const p1 = dist.periods.p1;
                                const p2 = dist.periods.p2;
                                const p3 = dist.periods.p3;
                                const couv = dist.periods.couvertures;
                                const summary = dist.summary;

                                return (
                                  <div className="mt-3 bg-gradient-to-b from-gray-50 to-white rounded-lg border border-gray-200 overflow-hidden">
                                    {/* Header con resumen de necesidades */}
                                    <div className="bg-gray-100 px-3 py-2 border-b border-gray-200">
                                      <div className="flex justify-between items-center text-sm">
                                        <span className="font-semibold text-gray-700">{t.weekly.legend.dailyDistribution}</span>
                                        <div className="flex gap-2 text-xs">
                                          <span className="text-red-600 font-medium">{summary.total_departs}D</span>
                                          <span className="text-gray-400">·</span>
                                          <span className="text-green-600 font-medium">{summary.total_recouches}R</span>
                                          <span className="text-gray-400">·</span>
                                          <span className="text-purple-600 font-medium">{summary.total_couvertures}C</span>
                                          {summary.has_deficit && (
                                            <span className="text-red-600 font-medium ml-1">⚠</span>
                                          )}
                                          {summary.couv_needs_more_persons && (
                                            <span className="text-yellow-700 font-medium ml-1">💡+{summary.couv_extra_persons_needed}</span>
                                          )}
                                        </div>
                                      </div>
                                    </div>

                                    <div className="divide-y divide-gray-100">
                                      {/* Período 1: Mañana sola */}
                                      <div className="px-3 py-2 flex items-start gap-3">
                                        <div className="text-lg">🌅</div>
                                        <div className="flex-1 min-w-0">
                                          <div className="flex items-baseline justify-between">
                                            <span className="font-medium text-blue-700 text-sm">{p1.time_range}</span>
                                            <div className="flex items-center gap-2">
                                              <span className="text-xs text-gray-500">
                                                {t.weekly.legend.morningAlone} ({p1.pairs} {p1.pairs === 1 ? 'par' : 'pares'})
                                                {p1.solos > 0 && <span className="text-yellow-600 ml-1">+{p1.solos} solo</span>}
                                              </span>
                                              {p1.spare.display && (
                                                <span className={`text-[10px] font-medium ${p1.spare.is_positive ? 'text-green-600' : 'text-red-600'}`}>
                                                  {p1.spare.display}
                                                </span>
                                              )}
                                            </div>
                                          </div>
                                          <div className="text-xs text-gray-600 mt-0.5">
                                            <span className="font-medium">{p1.rooms_done} {t.weekly.legend.rooms}</span>
                                            {p1.departs_done > 0 && <span className="text-red-600 ml-1">({p1.departs_done} {t.weekly.legend.depart})</span>}
                                            {p1.recouch_done > 0 && <span className="text-green-600 ml-1">({p1.recouch_done} {t.weekly.legend.recouch})</span>}
                                          </div>
                                          {p1.work_display && <div className="text-xs text-blue-600 mt-0.5">{p1.work_display}</div>}
                                        </div>
                                      </div>

                                      {/* Almuerzo Mañana */}
                                      <div className="px-3 py-1.5 bg-gray-50 flex items-center gap-3">
                                        <div className="text-base">🍽️</div>
                                        <span className="text-xs text-gray-500">{dist.periods.lunch_morning.time_range} {t.weekly.legend.morningLunch}</span>
                                      </div>

                                      {/* Período 2: Mañana + Tarde */}
                                      <div className="px-3 py-2 flex items-start gap-3">
                                        <div className="text-lg">🔄</div>
                                        <div className="flex-1 min-w-0">
                                          <div className="flex items-baseline justify-between">
                                            <span className="font-medium text-purple-700 text-sm">{p2.time_range}</span>
                                            <div className="flex items-center gap-2">
                                              <span className="text-xs text-gray-500">
                                                {t.weekly.legend.morningEvening} ({p2.pairs} {p2.pairs === 1 ? 'par' : 'pares'})
                                                {p2.solos > 0 && <span className="text-yellow-600 ml-1">+{p2.solos} solo</span>}
                                              </span>
                                              {p2.spare.display && (
                                                <span className={`text-[10px] font-medium ${p2.spare.is_positive ? 'text-green-600' : 'text-red-600'}`}>
                                                  {p2.spare.display}
                                                </span>
                                              )}
                                            </div>
                                          </div>
                                          <div className="text-xs text-gray-600 mt-0.5">
                                            <span className="font-medium">{p2.rooms_done} {t.weekly.legend.rooms}</span>
                                            {p2.departs_done > 0 && <span className="text-red-600 ml-1">({p2.departs_done} {t.weekly.legend.depart})</span>}
                                            {p2.recouch_done > 0 && <span className="text-green-600 ml-1">({p2.recouch_done} {t.weekly.legend.recouch})</span>}
                                          </div>
                                          {p2.work_display && <div className="text-xs text-purple-600 mt-0.5">{p2.work_display}</div>}
                                        </div>
                                      </div>

                                      {/* Período 3: Tarde termina limpieza */}
                                      <div className="px-3 py-2 flex items-start gap-3">
                                        <div className="text-lg">⏰</div>
                                        <div className="flex-1 min-w-0">
                                          <div className="flex items-baseline justify-between">
                                            <span className="font-medium text-yellow-700 text-sm">{p3.time_range}</span>
                                            <div className="flex items-center gap-2">
                                              <span className="text-xs text-gray-500">
                                                {t.weekly.legend.eveningFinishes} ({p3.pairs} {p3.pairs === 1 ? 'par' : 'pares'})
                                                {p3.solos > 0 && <span className="text-yellow-600 ml-1">+{p3.solos} solo</span>}
                                              </span>
                                              {p3.spare.display && (
                                                <span className={`text-[10px] font-medium ${p3.spare.is_positive ? 'text-green-600' : 'text-red-600'}`}>
                                                  {p3.spare.display}
                                                </span>
                                              )}
                                            </div>
                                          </div>
                                          <div className="text-xs text-gray-600 mt-0.5">
                                            {p3.rooms_done > 0
                                              ? <>
                                                  <span className="font-medium">{p3.rooms_done} {t.weekly.legend.rooms}</span>
                                                  {p3.departs_done > 0 && <span className="text-red-600 ml-1">({p3.departs_done} {t.weekly.legend.depart})</span>}
                                                  {p3.recouch_done > 0 && <span className="text-green-600 ml-1">({p3.recouch_done} {t.weekly.legend.recouch})</span>}
                                                </>
                                              : <span className="text-green-600">{t.weekly.legend.noPending}</span>
                                            }
                                            {p3.rooms_deficit > 0 && <span className="text-red-600 font-medium ml-2">⚠ {p3.rooms_deficit} {t.weekly.legend.rooms} sin hacer!</span>}
                                          </div>
                                          {p3.work_display && <div className="text-xs text-orange-600 mt-0.5">{p3.work_display}</div>}
                                        </div>
                                      </div>

                                      {/* Almuerzo Tarde */}
                                      <div className="px-3 py-1.5 bg-gray-50 flex items-center gap-3">
                                        <div className="text-base">🍽️</div>
                                        <span className="text-xs text-gray-500">{dist.periods.lunch_evening.time_range} {t.weekly.legend.eveningLunch}</span>
                                      </div>

                                      {/* Couverture */}
                                      <div className={`px-3 py-2 flex items-start gap-3 ${couv.needs_more_persons ? 'bg-yellow-50' : couv.can_cover_with_elasticity ? 'bg-blue-50' : 'bg-orange-50'}`}>
                                        <div className="text-lg">🌙</div>
                                        <div className="flex-1 min-w-0">
                                          <div className="flex items-baseline justify-between">
                                            <span className="font-medium text-orange-700 text-sm">{couv.time_range}</span>
                                            <div className="flex items-center gap-2">
                                              <span className="text-xs text-gray-500">{t.weekly.legend.couvertures}</span>
                                              {couv.needs_more_persons ? (
                                                <span className="text-[10px] font-medium text-yellow-700">
                                                  {couv.persons_assigned}/{couv.persons_needed} pers. (+{couv.extra_persons_needed})
                                                </span>
                                              ) : couv.can_cover_with_elasticity ? (
                                                <span className="text-[10px] font-medium text-blue-600">
                                                  ⚡ {couv.persons_assigned} pers. +elasticidad
                                                </span>
                                              ) : (
                                                <span className="text-[10px] font-medium text-green-600">
                                                  ✓ {couv.persons_assigned} pers.
                                                </span>
                                              )}
                                              {couv.spare?.display && (
                                                <span className={`text-[10px] font-medium ${couv.spare.is_positive ? 'text-green-600' : 'text-red-600'}`}>
                                                  {couv.spare.display}
                                                </span>
                                              )}
                                            </div>
                                          </div>
                                          <div className="text-xs text-gray-600 mt-0.5">
                                            <span className="font-medium">{couv.couvertures_count} {t.weekly.legend.couvertures}</span>
                                            <span className="text-orange-600 ml-1">(~{couv.per_person} {t.weekly.legend.perPerson})</span>
                                            <span className="text-gray-500 ml-1">· {couv.time_per_person_min}min c/u</span>
                                          </div>
                                          {couv.persons_display && <div className="text-xs text-orange-600 mt-0.5">{couv.persons_display}</div>}
                                          {couv.can_cover_with_elasticity && !couv.needs_more_persons && (
                                            <div className="text-xs text-blue-700 mt-0.5 font-medium">
                                              ✓ Déficit de {couv.deficit_min}min cubierto con elasticidad (+{couv.elasticity_extra_per_person_min}min/persona)
                                            </div>
                                          )}
                                          {couv.needs_more_persons && (
                                            <div className="text-xs text-yellow-700 mt-0.5 font-medium">
                                              💡 Necesitas {couv.extra_persons_needed} persona(s) más para couvertures (elasticidad insuficiente)
                                            </div>
                                          )}
                                        </div>
                                      </div>

                                      {/* Balance de horas */}
                                      {(day as any).hours_balance && (
                                        <div className={`px-3 py-2 border-t border-gray-200 ${summary.has_deficit ? 'bg-red-50' : summary.couv_needs_more_persons ? 'bg-yellow-50' : 'bg-gray-100'}`}>
                                          <div className="flex flex-col gap-1 text-xs">
                                            <div className="flex items-center gap-2">
                                              <span className="font-semibold text-gray-700">{t.weekly.legend.balance}:</span>
                                              {(() => {
                                                const balance = (day as any).hours_balance;
                                                const spareClass = summary.has_deficit ? 'text-red-600' : 'text-green-600';
                                                const spareIcon = summary.has_deficit ? '⚠' : '✓';
                                                return (
                                                  <>
                                                    <span className="text-gray-600">
                                                      {balance.total.assigned}h {t.weekly.legend.assignedHours} / {balance.total.needed}h {t.weekly.legend.neededHours}
                                                    </span>
                                                    <span className={`font-medium ${spareClass}`}>
                                                      {spareIcon} {!summary.has_deficit && balance.total.spare >= 0 ? '+' : ''}{balance.total.spare}h
                                                    </span>
                                                  </>
                                                );
                                              })()}
                                            </div>
                                            {summary.has_deficit && summary.rooms_deficit > 0 && (
                                              <div className="text-red-600 font-medium">
                                                ⚠ {summary.rooms_deficit} hab. sin personal
                                              </div>
                                            )}
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
