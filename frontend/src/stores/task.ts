import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as tasksApi from '@/api/tasks'
import type { Task, TaskCreate, TaskUpdate, StatusUpdate, ReorderItem, TaskFilters } from '@/api/tasks'
import { useScopeStore } from './scope'

export const useTaskStore = defineStore('task', () => {
  const tasks = ref<Task[]>([])
  const filters = ref<TaskFilters>({})
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  async function fetchTasks() {
    isLoading.value = true; error.value = null
    try {
      const scope = useScopeStore()
      const params = { ...filters.value }
      if (scope.targetUserId !== 0) params.target_user_id = scope.targetUserId
      tasks.value = await tasksApi.fetchTasks(params)
    } catch {
      error.value = '无法加载任务'
    } finally { isLoading.value = false }
  }

  async function addTask(data: TaskCreate) {
    const task = await tasksApi.createTask(data)
    tasks.value.push(task)
    return task
  }

  async function updateTask(id: number, data: TaskUpdate) {
    const updated = await tasksApi.updateTask(id, data)
    const idx = tasks.value.findIndex(t => t.id === id)
    if (idx > -1) tasks.value[idx] = updated
  }

  async function removeTask(id: number) {
    await tasksApi.deleteTask(id)
    tasks.value = tasks.value.filter(t => t.id !== id)
  }

  async function moveTask(taskId: number, newStatus: string, newOrder: number) {
    const task = tasks.value.find(t => t.id === taskId)
    if (!task) return
    const oldStatus = task.status

    // Optimistic
    task.status = newStatus as Task['status']
    task.column_order = newOrder
    tasks.value
      .filter(t => t.status === oldStatus && t.id !== taskId)
      .sort((a, b) => a.column_order - b.column_order)
      .forEach((t, i) => t.column_order = i)
    tasks.value
      .filter(t => t.status === newStatus)
      .sort((a, b) => a.column_order - b.column_order)
      .forEach((t, i) => t.column_order = i)
    // Trigger reactivity
    tasks.value = [...tasks.value]

    try {
      await tasksApi.updateTaskStatus(taskId, { status: newStatus, column_order: newOrder })
    } catch {
      await fetchTasks()
    }
  }

  function setFilter(key: keyof TaskFilters, value: string | boolean | undefined) {
    if (value === '' || value === null || value === undefined) {
      delete filters.value[key]
    } else {
      (filters.value as any)[key] = value
    }
    fetchTasks()
  }
  function clearFilters() {
    filters.value = {}
    fetchTasks()
  }

  async function archiveTask(id: number) {
    await tasksApi.updateTaskStatus(id, { status: 'archived', column_order: 0 })
    tasks.value = tasks.value.filter(t => t.id !== id)
  }
  async function unarchiveTask(id: number) {
    await tasksApi.updateTaskStatus(id, { status: 'todo', column_order: 0 })
    await fetchTasks()
  }
  async function fetchArchivedTasks(search?: string): Promise<Task[]> {
    const params: any = { include_archived: true, status: 'archived' }
    if (search) params.search = search
    return tasksApi.fetchTasks(params)
  }
  async function deleteArchivedTask(id: number) {
    await tasksApi.deleteTask(id)
  }

  return { tasks, filters, isLoading, error, fetchTasks, addTask, updateTask, removeTask, moveTask, setFilter, clearFilters, archiveTask, unarchiveTask, fetchArchivedTasks, deleteArchivedTask }
})
