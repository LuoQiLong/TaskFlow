import client from './client'

export interface Project {
  id: number
  name: string
  color: string
  description: string | null
  user_id: number
  created_at: string | null
}

export interface ProjectCreate {
  name: string
  color?: string
  description?: string
}

export interface ProjectUpdate {
  name?: string
  color?: string
  description?: string
}

export const fetchProjects = () =>
  client.get<Project[]>('/projects').then(r => r.data)

export const createProject = (data: ProjectCreate) =>
  client.post<Project>('/projects', data).then(r => r.data)

export const updateProject = (id: number, data: ProjectUpdate) =>
  client.put<Project>(`/projects/${id}`, data).then(r => r.data)

export const deleteProject = (id: number) =>
  client.delete(`/projects/${id}`)
