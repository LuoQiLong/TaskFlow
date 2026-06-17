import client from './client'

export interface WorkLog {
  id: number
  work_item_id: number
  week_start: string | null
  hours: number
  log_date: string | null
  note: string | null
  is_system: boolean
  user_id: number
  created_at: string | null
}

export interface WorkLogCreate {
  work_item_id: number
  week_start: string
  hours: number
  log_date?: string
  note?: string
}

export interface WorkLogFilters {
  work_item_id?: number
  week_start?: string
}

export const fetchWorkLogs = (filters: WorkLogFilters = {}) =>
  client.get<WorkLog[]>('/work-logs', { params: filters }).then(r => r.data)

export const createWorkLog = (data: WorkLogCreate) =>
  client.post<WorkLog>('/work-logs', data).then(r => r.data)

export const updateWorkLog = (id: number, data: Partial<WorkLogCreate>) =>
  client.put<WorkLog>(`/work-logs/${id}`, data).then(r => r.data)

export const deleteWorkLog = (id: number) =>
  client.delete(`/work-logs/${id}`)
