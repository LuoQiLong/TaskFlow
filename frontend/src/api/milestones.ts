import client from './client'

export interface Milestone {
  id: number
  work_item_id: number
  title: string
  description: string | null
  hours: number | null
  target_date: string | null
  is_completed: boolean
  completed_at: string | null
  is_locked: boolean
  week_start: string | null  // for cross-week: which week this milestone belongs to
  sort_order: number
  user_id: number
  created_at: string | null
}

export interface MilestoneCreate {
  work_item_id: number
  title: string
  description?: string
  hours?: number
  target_date?: string
  week_start?: string  // auto-set to current browsing week
}

export interface MilestoneUpdate {
  title?: string
  description?: string
  hours?: number
  target_date?: string
  is_completed?: boolean
  week_start?: string
  sort_order?: number
}

export const fetchMilestones = (workItemId: number) =>
  client.get<Milestone[]>('/milestones', { params: { work_item_id: workItemId } }).then(r => r.data)

export const createMilestone = (data: MilestoneCreate) =>
  client.post<Milestone>('/milestones', data).then(r => r.data)

export const updateMilestone = (id: number, data: MilestoneUpdate) =>
  client.put<Milestone>(`/milestones/${id}`, data).then(r => r.data)

export const deleteMilestone = (id: number) =>
  client.delete(`/milestones/${id}`)

export const reorderMilestones = (items: { id: number; sort_order: number }[]) =>
  client.patch<Milestone[]>('/milestones/reorder', items).then(r => r.data)
