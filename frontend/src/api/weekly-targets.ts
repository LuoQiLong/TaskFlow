import client from './client'

export interface WeeklyTargetResponse {
  week_start: string
  target_hours: number
  is_custom: boolean
}

export const getWeeklyTarget = (weekStart: string) =>
  client.get<WeeklyTargetResponse>('/weekly-targets', { params: { week_start: weekStart } }).then(r => r.data)

export const setWeeklyTarget = (weekStart: string, targetHours: number) =>
  client.put<WeeklyTargetResponse>('/weekly-targets', null, { params: { week_start: weekStart, target_hours: targetHours } }).then(r => r.data)
