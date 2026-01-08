// Core Types
export interface TimeBlock {
  id: number;
  code: string;
  name: string;
  description: string;
  order: number;
  is_active: boolean;
}

export interface TaskType {
  id: number;
  code: string;
  name: string;
  description: string;
  base_minutes: number;
  priority: number;
  is_active: boolean;
  allowed_blocks: TimeBlock[];
}

export interface Zone {
  id: number;
  code: string;
  name: string;
  floor_number: number | null;
  priority_order: number;
  is_active: boolean;
  room_count: number;
}

export interface Room {
  id: number;
  number: string;
  zone: number;
  zone_name: string;
  room_type: number;
  room_type_name: string;
  order_in_zone: number;
  corridor_side: 'A' | 'B' | 'N';
  is_active: boolean;
}

// Staff Types
export interface Role {
  id: number;
  code: string;
  name: string;
  description: string;
  employee_count: number;
}

export interface Employee {
  id: number;
  employee_code: string;
  first_name: string;
  last_name: string;
  full_name: string;
  role: number;
  role_name: string;
  weekly_hours_target: number;
  elasticity: 'LOW' | 'MEDIUM' | 'HIGH';
  can_work_night: boolean;
  is_active: boolean;
  allowed_blocks: TimeBlock[];
  eligible_tasks: TaskType[];
}

export interface Team {
  id: number;
  name: string;
  team_type: 'FIXED' | 'PREFERRED' | 'TEMPORARY';
  members: Employee[];
  member_count: number;
  is_active: boolean;
}

// Shift Types
export interface ShiftTemplate {
  id: number;
  code: string;
  name: string;
  role: number;
  role_name: string;
  time_block: number;
  time_block_code: string;
  start_time: string;
  end_time: string;
  total_hours: number;
  is_active: boolean;
}

// Room State Types
export interface RoomDailyState {
  id: number;
  date: string;
  room: number;
  room_number: string;
  zone_code: string;
  zone_name: string;
  occupancy_status: 'VACANT' | 'OCCUPIED' | 'CHECKOUT' | 'CHECKIN' | 'TURNOVER' | 'OOO';
  stay_day_number: number;
  day_cleaning_status: 'PENDING' | 'IN_PROGRESS' | 'DONE' | 'DECLINED' | 'NOT_REQUIRED';
  night_expected_difficulty: 'NORMAL' | 'HARD' | 'VERY_HARD';
  is_vip: boolean;
  tasks: RoomDailyTask[];
}

export interface RoomDailyTask {
  id: number;
  room_daily_state: number;
  task_type: number;
  task_type_code: string;
  task_type_name: string;
  time_block: number;
  time_block_code: string;
  estimated_minutes: number;
  status: 'PENDING' | 'ASSIGNED' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED';
  priority: number;
}

// Planning Types
export interface WeekPlan {
  id: number;
  week_start_date: string;
  week_end_date: string;
  name: string;
  status: 'DRAFT' | 'REVIEW' | 'APPROVED' | 'PUBLISHED' | 'ARCHIVED';
  created_at: string;
  published_at: string | null;
  shift_assignments: ShiftAssignment[];
  total_assigned_hours: number;
}

export interface ShiftAssignment {
  id: number;
  week_plan: number;
  date: string;
  employee: number | null;
  employee_name: string | null;
  team: number | null;
  team_name: string | null;
  shift_template: number;
  shift_template_code: string;
  time_block_code: string;
  assigned_hours: number;
  is_day_off: boolean;
}

export interface DailyPlan {
  id: number;
  date: string;
  week_plan: number | null;
  status: 'DRAFT' | 'ACTIVE' | 'COMPLETED';
  task_assignments: TaskAssignment[];
  total_tasks: number;
  completed_tasks: number;
}

export interface TaskAssignment {
  id: number;
  daily_plan: number;
  room_task: number;
  room_number: string;
  task_type_code: string;
  employee: number | null;
  employee_name: string | null;
  team: number | null;
  team_name: string | null;
  zone: number;
  zone_code: string;
  zone_name: string;
  order_in_assignment: number;
  estimated_minutes: number;
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'SKIPPED';
}

// Alert Types
export interface PlanningAlert {
  id: number;
  date: string;
  time_block: number | null;
  time_block_code: string | null;
  alert_type: 'OVERLOAD' | 'UNDERSTAFF' | 'CONFLICT' | 'WARNING' | 'INFO';
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  title: string;
  message: string;
  is_resolved: boolean;
  created_at: string;
}

// Dashboard Types
export interface DashboardData {
  week_start: string;
  week_end: string;
  load: {
    total_minutes: number;
    total_tasks: number;
    by_block: Record<string, { minutes: number; tasks: number }>;
  };
  capacity: {
    total_minutes: number;
  };
  balance: {
    minutes: number;
    percentage: number;
  };
  days: DayData[];
  alerts: PlanningAlert[];
}

export interface DayData {
  date: string;
  day_name: string;
  load_minutes: number;
  capacity_minutes: number;
  load_percentage: number;
  is_overloaded: boolean;
}
