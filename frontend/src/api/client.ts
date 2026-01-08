import axios from 'axios';

const API_BASE_URL = '/api';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Dashboard
export const getDashboard = async (weekStart?: string) => {
  const params = weekStart ? { week_start: weekStart } : {};
  const response = await apiClient.get('/dashboard/', { params });
  return response.data;
};

// Week Plans
export const getWeekPlans = async () => {
  const response = await apiClient.get('/week-plans/');
  return response.data;
};

export const getWeekPlan = async (id: number) => {
  const response = await apiClient.get(`/week-plans/${id}/`);
  return response.data;
};

export const generateWeekPlan = async (weekStartDate: string) => {
  const response = await apiClient.post('/week-plans/generate/', {
    week_start_date: weekStartDate,
  });
  return response.data;
};

export const publishWeekPlan = async (id: number) => {
  const response = await apiClient.post(`/week-plans/${id}/publish/`);
  return response.data;
};

export const getWeekPlanByEmployee = async (id: number) => {
  const response = await apiClient.get(`/week-plans/${id}/by_employee/`);
  return response.data;
};

// Daily Plans
export const getDailyPlans = async () => {
  const response = await apiClient.get('/daily-plans/');
  return response.data;
};

export const getDailyPlan = async (id: number) => {
  const response = await apiClient.get(`/daily-plans/${id}/`);
  return response.data;
};

export const generateDailyPlan = async (date: string, weekPlanId?: number) => {
  const response = await apiClient.post('/daily-plans/generate/', {
    date,
    week_plan_id: weekPlanId,
  });
  return response.data;
};

export const getDailyPlanByZone = async (id: number) => {
  const response = await apiClient.get(`/daily-plans/${id}/by_zone/`);
  return response.data;
};

export const getDailyPlanSummary = async (id: number) => {
  const response = await apiClient.get(`/daily-plans/${id}/summary/`);
  return response.data;
};

// Employees
export const getEmployees = async () => {
  const response = await apiClient.get('/employees/');
  return response.data;
};

export const getEmployee = async (id: number) => {
  const response = await apiClient.get(`/employees/${id}/`);
  return response.data;
};

export const createEmployee = async (data: Record<string, unknown>) => {
  const response = await apiClient.post('/employees/', data);
  return response.data;
};

export const updateEmployee = async (id: number, data: Record<string, unknown>) => {
  const response = await apiClient.patch(`/employees/${id}/`, data);
  return response.data;
};

// Teams
export const getTeams = async () => {
  const response = await apiClient.get('/teams/');
  return response.data;
};

export const createTeam = async (data: Record<string, unknown>) => {
  const response = await apiClient.post('/teams/', data);
  return response.data;
};

// Room States
export const getRoomDailyStates = async (date: string) => {
  const response = await apiClient.get('/room-daily-states/', {
    params: { date },
  });
  return response.data;
};

export const updateRoomCleaningStatus = async (id: number, status: string) => {
  const response = await apiClient.post(`/room-daily-states/${id}/update_cleaning_status/`, {
    day_cleaning_status: status,
  });
  return response.data;
};

// Task Assignments
export const completeTaskAssignment = async (id: number) => {
  const response = await apiClient.post(`/task-assignments/${id}/complete/`);
  return response.data;
};

// Alerts
export const getAlerts = async (resolved?: boolean) => {
  const params: Record<string, unknown> = {};
  if (resolved !== undefined) {
    params.is_resolved = resolved;
  }
  const response = await apiClient.get('/alerts/', { params });
  return response.data;
};

export const resolveAlert = async (id: number) => {
  const response = await apiClient.post(`/alerts/${id}/resolve/`);
  return response.data;
};

// Import
export const importProtelCSV = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('filename', file.name);

  const response = await apiClient.post('/import/protel/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

// Calculation
export const calculateLoad = async (date: string, block?: string) => {
  const params: Record<string, string> = { date };
  if (block) params.block = block;
  const response = await apiClient.get('/calculate/load/', { params });
  return response.data;
};

export const calculateCapacity = async (date: string, block?: string) => {
  const params: Record<string, string> = { date };
  if (block) params.block = block;
  const response = await apiClient.get('/calculate/capacity/', { params });
  return response.data;
};

// Core data
export const getTimeBlocks = async () => {
  const response = await apiClient.get('/time-blocks/');
  return response.data;
};

export const getTaskTypes = async () => {
  const response = await apiClient.get('/task-types/');
  return response.data;
};

export const getZones = async () => {
  const response = await apiClient.get('/zones/');
  return response.data;
};

export const getRooms = async () => {
  const response = await apiClient.get('/rooms/');
  return response.data;
};

export const getRoles = async () => {
  const response = await apiClient.get('/roles/');
  return response.data;
};
