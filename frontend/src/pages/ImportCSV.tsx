import { useState, useRef } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { importProtelCSV } from '../api/client';
import { clsx } from 'clsx';

interface ImportResult {
  success: boolean;
  import_log: {
    id: number;
    filename: string;
    imported_at: string;
    rows_processed: number;
    rows_success: number;
    rows_error: number;
    date_from: string;
    date_to: string;
    status: string;
    errors: string;
  };
  summary: {
    stats: {
      rows_processed: number;
      rows_success: number;
      rows_error: number;
      states_created: number;
      tasks_created: number;
    };
    errors: string[];
    warnings: string[];
  };
}

export default function ImportCSV() {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);
  const [result, setResult] = useState<ImportResult | null>(null);

  const importMutation = useMutation({
    mutationFn: importProtelCSV,
    onSuccess: (data: ImportResult) => {
      setResult(data);
      queryClient.invalidateQueries({ queryKey: ['roomStates'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });

  const handleFile = (file: File) => {
    if (file && (file.type === 'text/csv' || file.name.endsWith('.csv'))) {
      importMutation.mutate(file);
    } else {
      alert('Por favor selecciona un archivo CSV válido');
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Importar CSV Protel</h2>
        <p className="text-gray-500 mt-1">
          Sube un archivo CSV exportado desde Protel para importar el estado de las habitaciones
        </p>
      </div>

      {/* Upload Area */}
      <div
        className={clsx(
          'card border-2 border-dashed p-12 text-center cursor-pointer transition-colors',
          dragActive ? 'border-primary-500 bg-primary-50' : 'border-gray-300 hover:border-gray-400',
          importMutation.isPending && 'opacity-50 pointer-events-none'
        )}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={handleClick}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv"
          onChange={handleChange}
          className="hidden"
        />

        {importMutation.isPending ? (
          <div>
            <div className="text-lg font-medium text-gray-900 mb-2">
              Importando archivo...
            </div>
            <div className="text-sm text-gray-500">
              Esto puede tomar unos segundos
            </div>
          </div>
        ) : (
          <div>
            <div className="text-4xl mb-4">📁</div>
            <div className="text-lg font-medium text-gray-900 mb-2">
              Arrastra un archivo CSV aquí
            </div>
            <div className="text-sm text-gray-500">
              o haz clic para seleccionar
            </div>
          </div>
        )}
      </div>

      {/* Error */}
      {importMutation.isError && (
        <div className="card bg-red-50 border border-red-200">
          <h3 className="text-lg font-semibold text-red-800 mb-2">Error de importación</h3>
          <p className="text-red-700">
            {(importMutation.error as Error)?.message || 'Error desconocido'}
          </p>
        </div>
      )}

      {/* Result */}
      {result && (
        <div className="space-y-4">
          {/* Summary Card */}
          <div
            className={clsx(
              'card',
              result.summary.stats.rows_error === 0 ? 'bg-green-50 border border-green-200' : 'bg-yellow-50 border border-yellow-200'
            )}
          >
            <h3 className="text-lg font-semibold mb-4">
              Importación {result.summary.stats.rows_error === 0 ? 'Exitosa' : 'Completada con errores'}
            </h3>

            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div>
                <div className="text-2xl font-bold">{result.summary.stats.rows_processed}</div>
                <div className="text-sm text-gray-600">Filas procesadas</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-green-600">
                  {result.summary.stats.rows_success}
                </div>
                <div className="text-sm text-gray-600">Exitosas</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-red-600">
                  {result.summary.stats.rows_error}
                </div>
                <div className="text-sm text-gray-600">Con error</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-blue-600">
                  {result.summary.stats.states_created}
                </div>
                <div className="text-sm text-gray-600">Estados creados</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-purple-600">
                  {result.summary.stats.tasks_created}
                </div>
                <div className="text-sm text-gray-600">Tareas creadas</div>
              </div>
            </div>

            {result.import_log.date_from && (
              <div className="mt-4 text-sm text-gray-600">
                Rango de fechas: {result.import_log.date_from} a {result.import_log.date_to}
              </div>
            )}
          </div>

          {/* Errors */}
          {result.summary.errors.length > 0 && (
            <div className="card bg-red-50 border border-red-200">
              <h4 className="font-semibold text-red-800 mb-2">
                Errores ({result.summary.errors.length})
              </h4>
              <ul className="text-sm text-red-700 space-y-1 max-h-48 overflow-y-auto">
                {result.summary.errors.map((error, idx) => (
                  <li key={idx}>{error}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Warnings */}
          {result.summary.warnings.length > 0 && (
            <div className="card bg-yellow-50 border border-yellow-200">
              <h4 className="font-semibold text-yellow-800 mb-2">
                Advertencias ({result.summary.warnings.length})
              </h4>
              <ul className="text-sm text-yellow-700 space-y-1 max-h-48 overflow-y-auto">
                {result.summary.warnings.map((warning, idx) => (
                  <li key={idx}>{warning}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Format Info */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">Formato esperado del CSV</h3>
        <p className="text-sm text-gray-600 mb-4">
          El archivo CSV debe tener las siguientes columnas:
        </p>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50">
                <th className="text-left p-2">Columna</th>
                <th className="text-left p-2">Descripción</th>
                <th className="text-left p-2">Ejemplo</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-t">
                <td className="p-2 font-mono">date</td>
                <td className="p-2">Fecha (YYYY-MM-DD)</td>
                <td className="p-2 font-mono">2026-01-20</td>
              </tr>
              <tr className="border-t">
                <td className="p-2 font-mono">room</td>
                <td className="p-2">Número de habitación</td>
                <td className="p-2 font-mono">305</td>
              </tr>
              <tr className="border-t">
                <td className="p-2 font-mono">housekeeping_type</td>
                <td className="p-2">Tipo de tarea</td>
                <td className="p-2 font-mono">DEPART, RECOUCH, COUVERTURE</td>
              </tr>
              <tr className="border-t">
                <td className="p-2 font-mono">arrival_time</td>
                <td className="p-2">Hora de llegada (opcional)</td>
                <td className="p-2 font-mono">15:00</td>
              </tr>
              <tr className="border-t">
                <td className="p-2 font-mono">departure_time</td>
                <td className="p-2">Hora de salida (opcional)</td>
                <td className="p-2 font-mono">11:00</td>
              </tr>
              <tr className="border-t">
                <td className="p-2 font-mono">status</td>
                <td className="p-2">Estado de ocupación</td>
                <td className="p-2 font-mono">OCCUPIED, CHECKOUT, CHECKIN</td>
              </tr>
              <tr className="border-t">
                <td className="p-2 font-mono">stay_day</td>
                <td className="p-2">Día de estancia</td>
                <td className="p-2 font-mono">3</td>
              </tr>
              <tr className="border-t">
                <td className="p-2 font-mono">vip</td>
                <td className="p-2">Es VIP (0/1)</td>
                <td className="p-2 font-mono">1</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div className="mt-4 p-3 bg-gray-50 rounded-lg">
          <div className="text-sm font-mono text-gray-600">
            date,room,housekeeping_type,arrival_time,departure_time,status,stay_day,vip<br />
            2026-01-20,305,RECOUCH,,,OCCUPIED,3,0<br />
            2026-01-20,305,COUVERTURE,,,OCCUPIED,3,0<br />
            2026-01-20,401,DEPART,,11:00,CHECKOUT,1,0
          </div>
        </div>
      </div>
    </div>
  );
}
