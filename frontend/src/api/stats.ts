import client from './client'

export interface StatsOverview {
  total: number
  status_counts: { todo: number; in_progress: number; done: number }
  priority_counts: { low: number; medium: number; high: number }
}
export interface TrendPoint { date: string; count: number }

export const getOverviewStats = () =>
  client.get<StatsOverview>('/stats/overview').then(r => r.data)

export const getTrendStats = (days = 30) =>
  client.get<TrendPoint[]>('/stats/trend', { params: { days } }).then(r => r.data)
