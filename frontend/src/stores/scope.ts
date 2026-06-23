import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import { fetchUsers, type UserListItem } from '@/api/admin'

const STORAGE_KEY = 'taskflow_scope'

function loadPersisted(): number {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored !== null) return JSON.parse(stored)
  } catch {}
  return 0  // 0 = self
}

export const useScopeStore = defineStore('scope', () => {
  const targetUserId = ref<number>(loadPersisted())
  const allUsers = ref<UserListItem[]>([])

  watch(targetUserId, (val) => {
    if (val === 0) {
      localStorage.removeItem(STORAGE_KEY)
    } else {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(val))
    }
  })

  function setScope(userId: number) {
    targetUserId.value = userId
  }

  async function loadAllUsers() {
    try {
      allUsers.value = await fetchUsers({ is_active: true })
    } catch {
      allUsers.value = []
    }
  }

  return { targetUserId, allUsers, setScope, loadAllUsers }
})
