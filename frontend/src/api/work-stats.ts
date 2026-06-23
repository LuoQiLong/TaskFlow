import client from './client'

export interface WeeklyStats {
  week_start: string
  week_end: string
  total_hours: number
  weekly_target: number
  is_custom_target: boolean
  saturation_pct: number
  task_hours: number
  work_order_hours: number
  project_breakdown: { project_id: number; project_name: string; project_color: string; hours: number }[]
  remaining_hours: number
}

export interface TrendPoint {
  week_start: string
  week_end: string
  total_hours: number
  logged_hours: number
  planned_hours: number
  saturation_pct: number
}

export interface MonthlyStats {
  year: number
  month: number
  num_weeks: number
  monthly_target: number
  total_hours: number
  saturation_pct: number
  task_hours: number
  work_order_hours: number
  remaining_hours: number
  weekly_breakdown: { week_start: string; total_hours: number; task_hours: number; work_order_hours: number }[]
  project_breakdown: { project_id: number; project_name: string; project_color: string; hours: number }[]
}

export const getWeeklyStats = (weekStart: string, targetUserId?: number) =>
  client.get<WeeklyStats>('/work-stats/weekly', { params: { week_start: weekStart, ...(targetUserId !== undefined ? { target_user_id: targetUserId } : {}) } }).then(r => r.data)

export const getTrendStats = (weeks: number = 12, targetUserId?: number) =>
  client.get<TrendPoint[]>('/work-stats/trend', { params: { weeks, ...(targetUserId !== undefined ? { target_user_id: targetUserId } : {}) } }).then(r => r.data)

export const getMonthlyStats = (year: number, month: number, targetUserId?: number) =>
  client.get<MonthlyStats>('/work-stats/monthly', { params: { year, month, ...(targetUserId !== undefined ? { target_user_id: targetUserId } : {}) } }).then(r => r.data)

// ── Dashboard (comprehensive) ──

export interface DashboardPeriod {
  year: number
  month: number
  num_weeks: number
  monthly_target: number
}

export interface DashboardSummary {
  total_hours: number
  task_hours: number
  work_order_hours: number
  saturation_pct: number
  remaining_hours: number
}

export interface ProjectHours {
  project_id: number
  project_name: string
  project_color: string
  hours: number
}

export interface TypeBreakdown {
  task_hours: number
  work_order_hours: number
}

export interface DailyHeatmapPoint {
  date: string
  hours: number
  day_of_week: number
}

export interface TagDistribution {
  tag: string
  hours: number
  count: number
}

export interface OverdueByProject {
  project_id: number
  project_name: string
  project_color: string
  overdue_count: number
}

export interface SaturationTrendPoint {
  week_start: string
  week_end: string
  total_hours: number
  logged_hours: number
  planned_hours: number
  saturation_pct: number
}

export interface CreationTrendPoint {
  week_start: string
  count: number
}

export interface WeeklyBreakdownPoint {
  week_start: string
  total_hours: number
  task_hours: number
  work_order_hours: number
}

export interface DashboardStats {
  period: DashboardPeriod
  summary: DashboardSummary
  project_hours: ProjectHours[]
  type_breakdown: TypeBreakdown
  daily_heatmap: DailyHeatmapPoint[]
  tag_distribution: TagDistribution[]
  overdue_by_project: OverdueByProject[]
  saturation_trend: SaturationTrendPoint[]
  creation_trend: CreationTrendPoint[]
  weekly_breakdown: WeeklyBreakdownPoint[]
}

export const getDashboardStats = (year: number, month: number, targetUserId?: number) =>
  client.get<DashboardStats>('/work-stats/dashboard', { params: { year, month, ...(targetUserId !== undefined ? { target_user_id: targetUserId } : {}) } }).then(r => r.data)
