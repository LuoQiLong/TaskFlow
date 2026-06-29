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
  week_end: string | null
  is_cross_week: boolean
  week_hours: Record<string, number> | null
  completed_weeks: string[]
  num_weeks: number
  tags: string[]
  column_order: number
  start_date: string | null
  end_date: string | null
  due_date: string | null
  attachments: {name:string;url:string;size:number}[]
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
  week_end?: string | null
  week_hours?: Record<string, number> | null
  tags?: string[]
  attachments?: {name:string;url:string;size:number}[]
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
  week_end?: string | null
  week_hours?: Record<string, number> | null
  tags?: string[]
  column_order?: number
  attachments?: {name:string;url:string;size:number}[]
  start_date?: string
  end_date?: string
  due_date?: string
}

export interface WorkItemStatusUpdate {
  status: string
  column_order: number
  week_start?: string  // for cross-week: which week is being completed
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
  search?: string
  overdue?: boolean
  target_user_id?: number
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

export const cleanupWorkImages = (urls: string[]) =>
  client.post('/work-items/images/cleanup', urls).then(r => r.data)

export const uploadAttachment = (file: File) => {
  const form = new FormData()
  form.append('file', file)
  return client.post<{name:string;url:string;size:number}>('/work-items/upload-attachment', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then(r => r.data)
}
