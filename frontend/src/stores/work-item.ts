import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import {
  fetchWorkItems, createWorkItem, updateWorkItem, deleteWorkItem, updateWorkItemStatus,
  type WorkItem, type WorkItemCreate, type WorkItemFilters,
} from '@/api/work-items'
import { fetchWorkLogs, createWorkLog, updateWorkLog, deleteWorkLog, type WorkLog, type WorkLogCreate } from '@/api/work-logs'

export const useWorkItemStore = defineStore('work-item', () => {
  const items = ref<WorkItem[]>([])
  const isLoading = ref(false)
  const filters = ref<WorkItemFilters>({})

  async function fetch() {
    isLoading.value = true
    try {
      items.value = await fetchWorkItems(filters.value)
    } catch { /* handled by interceptor */ }
    finally { isLoading.value = false }
  }

  async function add(data: WorkItemCreate) {
    const item = await createWorkItem(data)
    items.value.push(item)
    return item
  }

  async function update(id: number, data: Partial<WorkItemCreate>) {
    const item = await updateWorkItem(id, data)
    const idx = items.value.findIndex(x => x.id === id)
    if (idx !== -1) items.value[idx] = item
    return item
  }

  async function remove(id: number) {
    await deleteWorkItem(id)
    items.value = items.value.filter(x => x.id !== id)
  }

  async function moveItem(itemId: number, newStatus: string, newOrder: number) {
    const item = items.value.find(x => x.id === itemId)
    if (!item) return
    const oldStatus = item.status
    item.status = newStatus as WorkItem['status']
    item.column_order = newOrder
    // Trigger reactivity by replacing array reference after in-place mutation
    items.value = [...items.value]
    try {
      await updateWorkItemStatus(itemId, { status: newStatus, column_order: newOrder })
    } catch {
      item.status = oldStatus
      await fetch()
    }
  }

  function setFilter(key: keyof WorkItemFilters, value: any) {
    if (value === '' || value === null || value === undefined) {
      delete filters.value[key]
    } else {
      (filters.value as any)[key] = value
    }
    fetch()
  }

  function clearFilters() {
    filters.value = {}
    fetch()
  }

  // Work log cache — use reactive object (not Map) for proper Vue reactivity
  const workLogs = reactive<Record<number, WorkLog[]>>({})

  async function loadLogs(workItemId: number) {
    const logs = await fetchWorkLogs({ work_item_id: workItemId })
    workLogs[workItemId] = logs
    return logs
  }

  async function addLog(data: WorkLogCreate) {
    const log = await createWorkLog(data)
    const existing = workLogs[data.work_item_id] || []
    workLogs[data.work_item_id] = [...existing, log]
    return log
  }

  async function editLog(logId: number, workItemId: number, data: Partial<WorkLogCreate>) {
    const log = await updateWorkLog(logId, data)
    const existing = workLogs[workItemId] || []
    const idx = existing.findIndex(x => x.id === logId)
    if (idx !== -1) existing[idx] = log
    workLogs[workItemId] = [...existing]
  }

  async function removeLog(logId: number, workItemId: number) {
    await deleteWorkLog(logId)
    const existing = workLogs[workItemId] || []
    workLogs[workItemId] = existing.filter(x => x.id !== logId)
  }

  function getLogs(workItemId: number): WorkLog[] {
    return workLogs[workItemId] || []
  }

  function getTotalHours(workItemId: number): number {
    const logs = workLogs[workItemId] || []
    return logs.reduce((sum, l) => sum + l.hours, 0)
  }

  return {
    items, isLoading, filters,
    fetch, add, update, remove, moveItem,
    setFilter, clearFilters,
    workLogs, loadLogs, addLog, editLog, removeLog, getLogs, getTotalHours,
  }
})
