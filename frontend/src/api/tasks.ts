import client from './client'

export interface Task {
  id: number; title: string; description: string | null
  status: 'todo' | 'in_progress' | 'done' | 'archived'; priority: 'low' | 'medium' | 'high'
  column_order: number; due_date: string | null; assignee: string | null
  tags: string[]
  user_id: number; created_at: string | null; updated_at: string | null
}
export interface TaskCreate { title: string; description?: string; priority?: string; due_date?: string; assignee?: string; tags?: string[] }
export interface TaskUpdate { title?: string; description?: string; status?: string; priority?: string; column_order?: number; due_date?: string; assignee?: string; tags?: string[] }
export interface StatusUpdate { status: string; column_order: number }
export interface ReorderItem { id: number; status: string; column_order: number }
export interface TaskFilters { status?: string; priority?: string; tag?: string; search?: string; date_from?: string; date_to?: string; overdue?: boolean; include_archived?: boolean; target_user_id?: number }

export const fetchTasks = (filters: TaskFilters = {}) =>
  client.get<Task[]>('/tasks', { params: filters }).then(r => r.data)

export const createTask = (data: TaskCreate) =>
  client.post<Task>('/tasks', data).then(r => r.data)

export const updateTask = (id: number, data: TaskUpdate) =>
  client.put<Task>(`/tasks/${id}`, data).then(r => r.data)

export const deleteTask = (id: number) =>
  client.delete(`/tasks/${id}`)

export const updateTaskStatus = (id: number, data: StatusUpdate) =>
  client.patch<Task>(`/tasks/${id}/status`, data).then(r => r.data)

export const reorderTasks = (items: ReorderItem[]) =>
  client.patch<Task[]>('/tasks/reorder', items).then(r => r.data)
