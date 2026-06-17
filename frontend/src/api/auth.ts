import client from './client'

export interface AuthResponse { id: number; email: string; token: string }
export interface User { id: number; email: string; created_at: string | null }

export const login = (email: string, password: string) =>
  client.post<AuthResponse>('/auth/login', { email, password }).then(r => r.data)

export const register = (email: string, password: string) =>
  client.post<AuthResponse>('/auth/register', { email, password }).then(r => r.data)

export const getMe = () =>
  client.get<User>('/auth/me').then(r => r.data)
