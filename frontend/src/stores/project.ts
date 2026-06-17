import { defineStore } from 'pinia'
import { ref } from 'vue'
import { fetchProjects, createProject, updateProject, deleteProject, type Project, type ProjectCreate } from '@/api/projects'

export const useProjectStore = defineStore('project', () => {
  const projects = ref<Project[]>([])
  const isLoading = ref(false)

  async function fetch() {
    isLoading.value = true
    try {
      projects.value = await fetchProjects()
    } catch { /* handled by interceptor */ }
    finally { isLoading.value = false }
  }

  async function add(data: ProjectCreate) {
    const p = await createProject(data)
    projects.value.push(p)
    return p
  }

  async function update(id: number, data: Partial<ProjectCreate>) {
    const p = await updateProject(id, data)
    const idx = projects.value.findIndex(x => x.id === id)
    if (idx !== -1) projects.value[idx] = p
    return p
  }

  async function remove(id: number) {
    await deleteProject(id)
    projects.value = projects.value.filter(x => x.id !== id)
  }

  return { projects, isLoading, fetch, add, update, remove }
})
