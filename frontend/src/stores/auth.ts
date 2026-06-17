import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as authApi from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<{ id: number; email: string } | null>(null)
  const token = ref<string | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  const isAuthenticated = computed(() => !!token)

  // Init from localStorage
  const stored = localStorage.getItem('auth')
  if (stored) {
    try {
      const data = JSON.parse(stored)
      token.value = data.token
      user.value = data.user
    } catch {}
  }

  function save() {
    localStorage.setItem('auth', JSON.stringify({ token: token.value, user: user.value, isAuthenticated: true }))
  }

  async function login(email: string, password: string) {
    isLoading.value = true; error.value = null
    try {
      const res = await authApi.login(email, password)
      user.value = { id: res.id, email: res.email }
      token.value = res.token
      save()
    } catch (e: any) {
      error.value = e.response?.data?.detail || '登录失败'
      throw e
    } finally { isLoading.value = false }
  }

  async function register(email: string, password: string) {
    isLoading.value = true; error.value = null
    try {
      const res = await authApi.register(email, password)
      user.value = { id: res.id, email: res.email }
      token.value = res.token
      save()
    } catch (e: any) {
      error.value = e.response?.data?.detail || '注册失败'
      throw e
    } finally { isLoading.value = false }
  }

  function logout() {
    user.value = null; token.value = null; error.value = null
    localStorage.removeItem('auth')
  }

  return { user, token, isLoading, error, isAuthenticated, login, register, logout }
})
