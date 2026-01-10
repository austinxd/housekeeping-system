import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getEmployees, getTeams, updateEmployee } from '../api/client';
import { Employee, Team } from '../types';
import { clsx } from 'clsx';
import { useLanguage } from '../i18n';

export default function Employees() {
  const { t } = useLanguage();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<'employees' | 'teams'>('employees');
  const [editingId, setEditingId] = useState<number | null>(null);

  // Queries
  const { data: employeesData, isLoading: loadingEmployees } = useQuery({
    queryKey: ['employees'],
    queryFn: getEmployees,
  });

  const { data: teamsData, isLoading: loadingTeams } = useQuery({
    queryKey: ['teams'],
    queryFn: getTeams,
  });

  // Mutations
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Record<string, unknown> }) =>
      updateEmployee(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['employees'] });
      setEditingId(null);
    },
  });

  const handleUpdateHours = (employee: Employee, newHours: number) => {
    updateMutation.mutate({
      id: employee.id,
      data: { weekly_hours_target: newHours },
    });
  };

  const getElasticityBadge = (elasticity: string) => {
    const styles: Record<string, string> = {
      LOW: 'bg-red-100 text-red-800',
      MEDIUM: 'bg-yellow-100 text-yellow-800',
      HIGH: 'bg-green-100 text-green-800',
    };
    return <span className={`badge ${styles[elasticity]}`}>{elasticity}</span>;
  };

  const employees = employeesData?.results || [];
  const teams = teamsData?.results || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">{t.employees.title}</h2>
      </div>

      {/* Tabs */}
      <div className="border-b">
        <nav className="flex space-x-8">
          <button
            onClick={() => setActiveTab('employees')}
            className={clsx(
              'py-2 px-1 border-b-2 font-medium text-sm',
              activeTab === 'employees'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            )}
          >
            {t.employees.employeesTab} ({employees.length})
          </button>
          <button
            onClick={() => setActiveTab('teams')}
            className={clsx(
              'py-2 px-1 border-b-2 font-medium text-sm',
              activeTab === 'teams'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            )}
          >
            {t.employees.teamsTab} ({teams.length})
          </button>
        </nav>
      </div>

      {/* Employees List */}
      {activeTab === 'employees' && (
        <div className="card">
          {loadingEmployees ? (
            <p className="text-gray-500">{t.common.loadingEmployees}</p>
          ) : (
            <table className="w-full">
              <thead>
                <tr className="bg-gray-50">
                  <th className="text-left p-3">{t.employees.code}</th>
                  <th className="text-left p-3">{t.employees.name}</th>
                  <th className="text-left p-3">{t.employees.role}</th>
                  <th className="text-center p-3">{t.employees.hoursWeek}</th>
                  <th className="text-center p-3">{t.employees.elasticity}</th>
                  <th className="text-center p-3">{t.employees.blocks}</th>
                  <th className="text-center p-3">Night</th>
                  <th className="text-center p-3">{t.employees.status}</th>
                </tr>
              </thead>
              <tbody>
                {employees.map((employee: Employee) => (
                  <tr key={employee.id} className="border-t hover:bg-gray-50">
                    <td className="p-3 font-mono">{employee.employee_code}</td>
                    <td className="p-3">
                      <div className="font-medium">{employee.full_name}</div>
                    </td>
                    <td className="p-3">{employee.role_name}</td>
                    <td className="p-3 text-center">
                      {editingId === employee.id ? (
                        <input
                          type="number"
                          defaultValue={employee.weekly_hours_target}
                          className="input w-20 text-center"
                          onBlur={(e) => handleUpdateHours(employee, parseFloat(e.target.value))}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                              handleUpdateHours(employee, parseFloat((e.target as HTMLInputElement).value));
                            }
                          }}
                          autoFocus
                        />
                      ) : (
                        <button
                          onClick={() => setEditingId(employee.id)}
                          className="hover:text-primary-600"
                        >
                          {employee.weekly_hours_target}h
                        </button>
                      )}
                    </td>
                    <td className="p-3 text-center">
                      {getElasticityBadge(employee.elasticity)}
                    </td>
                    <td className="p-3 text-center">
                      <div className="flex justify-center space-x-1">
                        {employee.allowed_blocks?.map((block) => (
                          <span key={block.id} className="badge badge-info text-xs">
                            {block.code}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="p-3 text-center">
                      {employee.can_work_night ? (
                        <span className="text-green-600">{t.employees.yes}</span>
                      ) : (
                        <span className="text-gray-400">{t.employees.no}</span>
                      )}
                    </td>
                    <td className="p-3 text-center">
                      {employee.is_active ? (
                        <span className="badge badge-success">{t.employees.active}</span>
                      ) : (
                        <span className="badge badge-danger">{t.employees.inactive}</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* Teams List */}
      {activeTab === 'teams' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {loadingTeams ? (
            <p className="text-gray-500">{t.common.loadingTeams}</p>
          ) : (
            teams.map((team: Team) => (
              <div key={team.id} className="card">
                <div className="flex justify-between items-start mb-3">
                  <h4 className="font-semibold">{team.name}</h4>
                  <span
                    className={clsx(
                      'badge',
                      team.team_type === 'FIXED' && 'badge-success',
                      team.team_type === 'PREFERRED' && 'badge-info',
                      team.team_type === 'TEMPORARY' && 'badge-warning'
                    )}
                  >
                    {team.team_type}
                  </span>
                </div>

                <div className="space-y-2">
                  <div className="text-sm text-gray-500">
                    {team.member_count} {t.employees.members}
                  </div>

                  <div className="space-y-1">
                    {team.members?.map((member) => (
                      <div key={member.id} className="text-sm flex justify-between items-center">
                        <span>{member.full_name}</span>
                        <span className="text-gray-400">{member.role_name}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {!team.is_active && (
                  <div className="mt-3">
                    <span className="badge badge-danger">{t.employees.inactive}</span>
                  </div>
                )}
              </div>
            ))
          )}
          {teams.length === 0 && (
            <p className="text-gray-500 col-span-full text-center py-8">
              {t.employees.noTeams}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
