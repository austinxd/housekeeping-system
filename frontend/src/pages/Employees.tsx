import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getEmployees,
  getTeams,
  getRoles,
  updateEmployee,
  createEmployee,
  deleteEmployee,
  createTeam,
  updateTeam,
  deleteTeam
} from '../api/client';
import { Employee, Team, Role } from '../types';
import { clsx } from 'clsx';
import { useLanguage } from '../i18n';

interface EmployeeFormData {
  first_name: string;
  last_name: string;
  employee_code: string;
  role: number | '';
  weekly_hours_target: number;
  elasticity: 'LOW' | 'MEDIUM' | 'HIGH';
  can_work_night: boolean;
  is_active: boolean;
}

interface TeamFormData {
  name: string;
  team_type: 'FIXED' | 'PREFERRED' | 'TEMPORARY';
  members: number[];
  is_active: boolean;
}

const initialEmployeeForm: EmployeeFormData = {
  first_name: '',
  last_name: '',
  employee_code: '',
  role: '',
  weekly_hours_target: 35,
  elasticity: 'MEDIUM',
  can_work_night: false,
  is_active: true,
};

const initialTeamForm: TeamFormData = {
  name: '',
  team_type: 'FIXED',
  members: [],
  is_active: true,
};

export default function Employees() {
  const { t } = useLanguage();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<'employees' | 'teams'>('employees');

  // Employee modal state
  const [showEmployeeModal, setShowEmployeeModal] = useState(false);
  const [editingEmployee, setEditingEmployee] = useState<Employee | null>(null);
  const [employeeForm, setEmployeeForm] = useState<EmployeeFormData>(initialEmployeeForm);

  // Team modal state
  const [showTeamModal, setShowTeamModal] = useState(false);
  const [editingTeam, setEditingTeam] = useState<Team | null>(null);
  const [teamForm, setTeamForm] = useState<TeamFormData>(initialTeamForm);

  // Queries
  const { data: employeesData, isLoading: loadingEmployees } = useQuery({
    queryKey: ['employees'],
    queryFn: getEmployees,
  });

  const { data: teamsData, isLoading: loadingTeams } = useQuery({
    queryKey: ['teams'],
    queryFn: getTeams,
  });

  const { data: rolesData } = useQuery({
    queryKey: ['roles'],
    queryFn: getRoles,
  });

  // Employee Mutations
  const createEmployeeMutation = useMutation({
    mutationFn: createEmployee,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['employees'] });
      closeEmployeeModal();
    },
  });

  const updateEmployeeMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Record<string, unknown> }) =>
      updateEmployee(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['employees'] });
      closeEmployeeModal();
    },
  });

  const deleteEmployeeMutation = useMutation({
    mutationFn: deleteEmployee,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['employees'] });
    },
  });

  // Team Mutations
  const createTeamMutation = useMutation({
    mutationFn: createTeam,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teams'] });
      closeTeamModal();
    },
  });

  const updateTeamMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Record<string, unknown> }) =>
      updateTeam(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teams'] });
      closeTeamModal();
    },
  });

  const deleteTeamMutation = useMutation({
    mutationFn: deleteTeam,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teams'] });
    },
  });

  // Employee Modal handlers
  const openNewEmployeeModal = () => {
    setEditingEmployee(null);
    setEmployeeForm(initialEmployeeForm);
    setShowEmployeeModal(true);
  };

  const openEditEmployeeModal = (employee: Employee) => {
    setEditingEmployee(employee);
    setEmployeeForm({
      first_name: employee.first_name,
      last_name: employee.last_name,
      employee_code: employee.employee_code,
      role: employee.role,
      weekly_hours_target: employee.weekly_hours_target,
      elasticity: employee.elasticity,
      can_work_night: employee.can_work_night,
      is_active: employee.is_active,
    });
    setShowEmployeeModal(true);
  };

  const closeEmployeeModal = () => {
    setShowEmployeeModal(false);
    setEditingEmployee(null);
    setEmployeeForm(initialEmployeeForm);
  };

  const handleEmployeeSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const data = {
      ...employeeForm,
      role: employeeForm.role || undefined,
    };

    if (editingEmployee) {
      updateEmployeeMutation.mutate({ id: editingEmployee.id, data });
    } else {
      createEmployeeMutation.mutate(data);
    }
  };

  const handleDeleteEmployee = (employee: Employee) => {
    if (confirm(`${t.employees.confirmDelete} "${employee.full_name}"?`)) {
      deleteEmployeeMutation.mutate(employee.id);
    }
  };

  // Team Modal handlers
  const openNewTeamModal = () => {
    setEditingTeam(null);
    setTeamForm(initialTeamForm);
    setShowTeamModal(true);
  };

  const openEditTeamModal = (team: Team) => {
    setEditingTeam(team);
    setTeamForm({
      name: team.name,
      team_type: team.team_type,
      members: team.members?.map(m => m.id) || [],
      is_active: team.is_active,
    });
    setShowTeamModal(true);
  };

  const closeTeamModal = () => {
    setShowTeamModal(false);
    setEditingTeam(null);
    setTeamForm(initialTeamForm);
  };

  const handleTeamSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const data = teamForm as unknown as Record<string, unknown>;
    if (editingTeam) {
      updateTeamMutation.mutate({ id: editingTeam.id, data });
    } else {
      createTeamMutation.mutate(data);
    }
  };

  const handleDeleteTeam = (team: Team) => {
    if (confirm(`${t.employees.confirmDelete} "${team.name}"?`)) {
      deleteTeamMutation.mutate(team.id);
    }
  };

  const toggleTeamMember = (employeeId: number) => {
    setTeamForm(prev => ({
      ...prev,
      members: prev.members.includes(employeeId)
        ? prev.members.filter(id => id !== employeeId)
        : [...prev.members, employeeId],
    }));
  };

  const getElasticityBadge = (elasticity: string) => {
    const styles: Record<string, string> = {
      LOW: 'bg-red-100 text-red-800',
      MEDIUM: 'bg-yellow-100 text-yellow-800',
      HIGH: 'bg-green-100 text-green-800',
    };
    return <span className={`badge ${styles[elasticity]}`}>{elasticity}</span>;
  };

  const employees: Employee[] = employeesData?.results || [];
  const teams: Team[] = teamsData?.results || [];
  const roles: Role[] = rolesData?.results || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">{t.employees.title}</h2>
        <button
          onClick={activeTab === 'employees' ? openNewEmployeeModal : openNewTeamModal}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium"
        >
          + {activeTab === 'employees' ? t.employees.newEmployee : t.employees.newTeam}
        </button>
      </div>

      {/* Tabs */}
      <div className="border-b">
        <nav className="flex space-x-8">
          <button
            onClick={() => setActiveTab('employees')}
            className={clsx(
              'py-2 px-1 border-b-2 font-medium text-sm',
              activeTab === 'employees'
                ? 'border-blue-500 text-blue-600'
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
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            )}
          >
            {t.employees.teamsTab} ({teams.length})
          </button>
        </nav>
      </div>

      {/* Employees List */}
      {activeTab === 'employees' && (
        <div className="card overflow-x-auto">
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
                  <th className="text-center p-3">Night</th>
                  <th className="text-center p-3">{t.employees.status}</th>
                  <th className="text-center p-3">{t.employees.actions}</th>
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
                    <td className="p-3 text-center">{employee.weekly_hours_target}h</td>
                    <td className="p-3 text-center">
                      {getElasticityBadge(employee.elasticity)}
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
                    <td className="p-3 text-center">
                      <div className="flex justify-center gap-2">
                        <button
                          onClick={() => openEditEmployeeModal(employee)}
                          className="text-blue-600 hover:text-blue-800 text-sm"
                        >
                          {t.common.edit}
                        </button>
                        <button
                          onClick={() => handleDeleteEmployee(employee)}
                          className="text-red-600 hover:text-red-800 text-sm"
                        >
                          {t.common.delete}
                        </button>
                      </div>
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

                <div className="mt-4 pt-3 border-t flex justify-between items-center">
                  {!team.is_active && (
                    <span className="badge badge-danger">{t.employees.inactive}</span>
                  )}
                  <div className="flex gap-2 ml-auto">
                    <button
                      onClick={() => openEditTeamModal(team)}
                      className="text-blue-600 hover:text-blue-800 text-sm"
                    >
                      {t.common.edit}
                    </button>
                    <button
                      onClick={() => handleDeleteTeam(team)}
                      className="text-red-600 hover:text-red-800 text-sm"
                    >
                      {t.common.delete}
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
          {teams.length === 0 && !loadingTeams && (
            <p className="text-gray-500 col-span-full text-center py-8">
              {t.employees.noTeams}
            </p>
          )}
        </div>
      )}

      {/* Employee Modal */}
      {showEmployeeModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-lg w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-xl font-bold">
                  {editingEmployee ? t.employees.editEmployee : t.employees.newEmployee}
                </h3>
                <button onClick={closeEmployeeModal} className="text-gray-500 hover:text-gray-700 text-2xl">
                  &times;
                </button>
              </div>

              <form onSubmit={handleEmployeeSubmit} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {t.employees.firstName}
                    </label>
                    <input
                      type="text"
                      value={employeeForm.first_name}
                      onChange={(e) => setEmployeeForm({ ...employeeForm, first_name: e.target.value })}
                      className="input w-full"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {t.employees.lastName}
                    </label>
                    <input
                      type="text"
                      value={employeeForm.last_name}
                      onChange={(e) => setEmployeeForm({ ...employeeForm, last_name: e.target.value })}
                      className="input w-full"
                      required
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {t.employees.code}
                    </label>
                    <input
                      type="text"
                      value={employeeForm.employee_code}
                      onChange={(e) => setEmployeeForm({ ...employeeForm, employee_code: e.target.value })}
                      className="input w-full"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {t.employees.role}
                    </label>
                    <select
                      value={employeeForm.role}
                      onChange={(e) => setEmployeeForm({ ...employeeForm, role: Number(e.target.value) || '' })}
                      className="input w-full"
                      required
                    >
                      <option value="">{t.employees.selectRole}</option>
                      {roles.map((role) => (
                        <option key={role.id} value={role.id}>{role.name}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {t.employees.hoursWeek}
                    </label>
                    <input
                      type="number"
                      value={employeeForm.weekly_hours_target}
                      onChange={(e) => setEmployeeForm({ ...employeeForm, weekly_hours_target: Number(e.target.value) })}
                      className="input w-full"
                      min="0"
                      max="60"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {t.employees.elasticity}
                    </label>
                    <select
                      value={employeeForm.elasticity}
                      onChange={(e) => setEmployeeForm({ ...employeeForm, elasticity: e.target.value as 'LOW' | 'MEDIUM' | 'HIGH' })}
                      className="input w-full"
                    >
                      <option value="LOW">LOW</option>
                      <option value="MEDIUM">MEDIUM</option>
                      <option value="HIGH">HIGH</option>
                    </select>
                  </div>
                </div>

                <div className="flex items-center gap-6">
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={employeeForm.can_work_night}
                      onChange={(e) => setEmployeeForm({ ...employeeForm, can_work_night: e.target.checked })}
                      className="w-4 h-4"
                    />
                    <span className="text-sm">{t.employees.canWorkNight}</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={employeeForm.is_active}
                      onChange={(e) => setEmployeeForm({ ...employeeForm, is_active: e.target.checked })}
                      className="w-4 h-4"
                    />
                    <span className="text-sm">{t.employees.active}</span>
                  </label>
                </div>

                <div className="flex justify-end gap-3 pt-4">
                  <button type="button" onClick={closeEmployeeModal} className="btn btn-secondary">
                    {t.common.cancel}
                  </button>
                  <button
                    type="submit"
                    className="btn btn-primary"
                    disabled={createEmployeeMutation.isPending || updateEmployeeMutation.isPending}
                  >
                    {createEmployeeMutation.isPending || updateEmployeeMutation.isPending
                      ? t.common.loading
                      : t.common.save}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Team Modal */}
      {showTeamModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-lg w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-xl font-bold">
                  {editingTeam ? t.employees.editTeam : t.employees.newTeam}
                </h3>
                <button onClick={closeTeamModal} className="text-gray-500 hover:text-gray-700 text-2xl">
                  &times;
                </button>
              </div>

              <form onSubmit={handleTeamSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {t.employees.teamName}
                  </label>
                  <input
                    type="text"
                    value={teamForm.name}
                    onChange={(e) => setTeamForm({ ...teamForm, name: e.target.value })}
                    className="input w-full"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {t.employees.teamType}
                  </label>
                  <select
                    value={teamForm.team_type}
                    onChange={(e) => setTeamForm({ ...teamForm, team_type: e.target.value as 'FIXED' | 'PREFERRED' | 'TEMPORARY' })}
                    className="input w-full"
                  >
                    <option value="FIXED">FIXED ({t.employees.fixedDesc})</option>
                    <option value="PREFERRED">PREFERRED ({t.employees.preferredDesc})</option>
                    <option value="TEMPORARY">TEMPORARY ({t.employees.temporaryDesc})</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    {t.employees.selectMembers}
                  </label>
                  <div className="border rounded-lg max-h-48 overflow-y-auto">
                    {employees.filter(e => e.is_active).map((employee) => (
                      <label
                        key={employee.id}
                        className={clsx(
                          'flex items-center gap-3 p-3 hover:bg-gray-50 cursor-pointer border-b last:border-b-0',
                          teamForm.members.includes(employee.id) && 'bg-blue-50'
                        )}
                      >
                        <input
                          type="checkbox"
                          checked={teamForm.members.includes(employee.id)}
                          onChange={() => toggleTeamMember(employee.id)}
                          className="w-4 h-4"
                        />
                        <div className="flex-1">
                          <div className="font-medium">{employee.full_name}</div>
                          <div className="text-xs text-gray-500">{employee.role_name}</div>
                        </div>
                      </label>
                    ))}
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    {teamForm.members.length} {t.employees.selected}
                  </p>
                </div>

                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={teamForm.is_active}
                    onChange={(e) => setTeamForm({ ...teamForm, is_active: e.target.checked })}
                    className="w-4 h-4"
                  />
                  <span className="text-sm">{t.employees.active}</span>
                </label>

                <div className="flex justify-end gap-3 pt-4">
                  <button type="button" onClick={closeTeamModal} className="btn btn-secondary">
                    {t.common.cancel}
                  </button>
                  <button
                    type="submit"
                    className="btn btn-primary"
                    disabled={createTeamMutation.isPending || updateTeamMutation.isPending}
                  >
                    {createTeamMutation.isPending || updateTeamMutation.isPending
                      ? t.common.loading
                      : t.common.save}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
