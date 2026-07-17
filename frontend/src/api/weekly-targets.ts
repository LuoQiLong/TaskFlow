import client from './client'

export interface WeeklyTargetResponse {
  week_start: string
  target_hours: number
  is_custom: boolean
  notes: string | null
}

export const getWeeklyTarget = (weekStart: string) =>
  client.get<WeeklyTargetResponse>('/weekly-targets', { params: { week_start: weekStart } }).then(r => r.data)

export const setWeeklyTarget = (weekStart: string, targetHours: number, notes?: string) =>
  client.put<WeeklyTargetResponse>('/weekly-targets', null, { params: { week_start: weekStart, target_hours: targetHours, ...(notes !== undefined ? { notes } : {}) } }).then(r => r.data)
