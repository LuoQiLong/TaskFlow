import client from './client'

export interface StatsOverview {
  total: number
  status_counts: { todo: number; in_progress: number; done: number }
  priority_counts: { low: number; medium: number; high: number }
}
export interface TrendPoint { date: string; count: number }

export const getOverviewStats = (targetUserId?: number) =>
  client.get<StatsOverview>('/stats/overview', {
    params: { ...(targetUserId !== undefined ? { target_user_id: targetUserId } : {}) }
  }).then(r => r.data)

export const getTrendStats = (days = 30, targetUserId?: number) =>
  client.get<TrendPoint[]>('/stats/trend', {
    params: { days, ...(targetUserId !== undefined ? { target_user_id: targetUserId } : {}) }
  }).then(r => r.data)
