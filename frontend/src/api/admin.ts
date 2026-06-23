import client from './client'

export interface UserListItem {
  id: number
  email: string
  role: string
  display_name: string | null
  is_active: boolean
  avatar_url: string | null
  created_at: string | null
}

export interface UserUpdateData {
  role?: string
  is_active?: boolean
  display_name?: string
}

export const fetchUsers = (params?: { search?: string; role?: string; is_active?: boolean }) =>
  client.get<UserListItem[]>('/admin/users', { params }).then(r => r.data)

export const updateUser = (id: number, data: UserUpdateData) =>
  client.patch<{ message: string }>(`/admin/users/${id}`, data).then(r => r.data)

export const adminResetPassword = (id: number, new_password: string) =>
  client.post<{ message: string }>(`/admin/users/${id}/reset-password`, { new_password }).then(r => r.data)

export const deleteUser = (id: number) =>
  client.delete(`/admin/users/${id}`)
