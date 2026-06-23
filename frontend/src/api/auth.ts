import client from './client'

export interface AuthResponse { id: number; email: string; token: string; role: string }
export interface User { id: number; email: string; role: string; display_name: string | null; is_active: boolean; avatar_url: string | null; created_at: string | null }

export const login = (email: string, password: string) =>
  client.post<AuthResponse>('/auth/login', { email, password }).then(r => r.data)

export const register = (email: string, password: string) =>
  client.post<AuthResponse>('/auth/register', { email, password }).then(r => r.data)

export const getMe = () =>
  client.get<User>('/auth/me').then(r => r.data)

export const forgotPassword = (email: string) =>
  client.post<{ message: string }>('/auth/forgot-password', { email }).then(r => r.data)

export const resetPassword = (token: string, new_password: string) =>
  client.post<{ message: string }>('/auth/reset-password', { token, new_password }).then(r => r.data)

export const uploadAvatar = (file: File) => {
  const fd = new FormData()
  fd.append('file', file)
  return client.post<{ avatar_url: string }>('/auth/avatar', fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then(r => r.data)
}

export const updateProfile = (data: { display_name?: string | null; password?: string }) =>
  client.patch<{ message: string }>('/auth/profile', data).then(r => r.data)
