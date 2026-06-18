import client from './client'

export interface WorkItem {
  id: number
  project_id: number
  type: 'task' | 'work_order'
  title: string
  description: string | null
  status: 'todo' | 'in_progress' | 'done'
  priority: 'low' | 'medium' | 'high'
  estimated_hours: number | null
  week_start: string | null
  is_cross_week: boolean
  tags: string[]
  column_order: number
  start_date: string | null
  end_date: string | null
  due_date: string | null
  user_id: number
  created_at: string | null
  updated_at: string | null
}

export interface WorkItemCreate {
  project_id: number
  type?: string
  title: string
  description?: string
  priority?: string
  estimated_hours?: number
  week_start: string
  is_cross_week?: boolean
  tags?: string[]
  start_date?: string
  end_date?: string
  due_date?: string
}

export interface WorkItemUpdate {
  project_id?: number
  type?: string
  title?: string
  description?: string
  status?: string
  priority?: string
  estimated_hours?: number
  week_start?: string
  is_cross_week?: boolean
  tags?: string[]
  column_order?: number
  start_date?: string
  end_date?: string
  due_date?: string
}

export interface WorkItemStatusUpdate {
  status: string
  column_order: number
}

export interface WorkItemFilters {
  project_id?: number
  type?: string
  status?: string
  week_start?: string
  week_start_from?: string
  week_start_to?: string
  tag?: string
  priority?: string
  overdue?: boolean
}

export const fetchWorkItems = (filters: WorkItemFilters = {}) =>
  client.get<WorkItem[]>('/work-items', { params: filters }).then(r => r.data)

export const createWorkItem = (data: WorkItemCreate) =>
  client.post<WorkItem>('/work-items', data).then(r => r.data)

export const updateWorkItem = (id: number, data: WorkItemUpdate) =>
  client.put<WorkItem>(`/work-items/${id}`, data).then(r => r.data)

export const deleteWorkItem = (id: number) =>
  client.delete(`/work-items/${id}`)

export const updateWorkItemStatus = (id: number, data: WorkItemStatusUpdate) =>
  client.patch<WorkItem>(`/work-items/${id}/status`, data).then(r => r.data)
