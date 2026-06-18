<template>
  <div style="display:flex;flex-direction:column;height:calc(100vh - 64px);background:var(--el-bg-color-page)">
    <!-- Toolbar -->
    <div class="search-toolbar" style="background:var(--el-bg-color);padding:20px 28px;border-bottom:1px solid var(--el-border-color-light);display:flex;gap:12px;align-items:center;flex-wrap:wrap">
      <el-input v-model="searchText" placeholder="搜索任务..." :prefix-icon="Search" clearable style="width:500px" size="large" @clear="searchText=''" @input="onSearch"/>
      <el-select v-model="filters.tag" placeholder="标签" clearable style="width:110px" size="large" @change="onFilterChange('tag', $event)">
        <el-option v-for="t in allTags" :key="t" :label="t" :value="t"/>
      </el-select>
      <el-select v-model="filters.status" placeholder="状态" clearable style="width:110px" size="large" @change="onFilterChange('status', $event)">
        <el-option v-for="o in statusOptions" :key="o.value" :label="o.label" :value="o.value"/>
      </el-select>
      <el-select v-model="filters.priority" placeholder="优先级" clearable style="width:130px" size="large" @change="onFilterChange('priority', $event)">
        <el-option label="🔴 高" value="high"/>
        <el-option label="🟡 中" value="medium"/>
        <el-option label="🟢 低" value="low"/>
      </el-select>
      <div style="width:500px;flex-shrink:0"><el-date-picker v-model="dateRange" type="daterange" range-separator="至" start-placeholder="开始" end-placeholder="结束" format="YYYY-MM-DD" value-format="YYYY-MM-DD" size="large" style="width:100%" @change="onDateChange"/></div>
      <el-select v-model="sortBy" placeholder="排序" size="large" style="width:140px" @change="onSortChange">
        <el-option label="📅 按日期" value="date"/>
        <el-option label="🔥 按优先级" value="priority"/>
        <el-option label="📅+🔥 日期+优先级" value="date_priority"/>
      </el-select>

      <el-checkbox v-model="overdueFilter" size="large" @change="onOverdueChange" style="height:40px;align-items:center">
        <span style="color:#f56c6c;font-weight:600">⏰ 超期</span>
      </el-checkbox>

      <el-button size="large" @click="openArchiveDrawer" style="margin-left:auto;border-radius:8px">
        <span style="font-weight:600">📦 已归档</span>
      </el-button>
    </div>

    <!-- Kanban Board + Stats -->
    <div style="flex:1;display:flex;gap:0;overflow:hidden">
      <!-- Kanban columns -->
      <div style="flex:1;display:flex;gap:20px;padding:20px 28px;overflow-x:auto;min-height:0" v-loading="store.isLoading">
        <div v-for="col in columns" :key="col.key"
          :style="{ flex: 1, minWidth: '260px', maxWidth: '380px', background: col.bg, borderRadius: '18px', display: 'flex', flexDirection: 'column', border: '1px solid var(--el-border-color-light)' }"
          @dragover.prevent @drop="onDrop($event, col.key)">
          <div style="display:flex;align-items:center;justify-content:space-between;padding:16px 18px;background:var(--el-fill-color-light)">
            <div style="display:flex;align-items:center;gap:8px">
              <span :style="{ width:'10px',height:'10px',borderRadius:'50%',background:col.dotColor,boxShadow:`0 0 0 3px ${col.dotColor}20` }"/>
              <span style="font-size:14px;font-weight:700;color:var(--el-text-color-primary)">{{ col.label }}</span>
              <span style="background:var(--el-bg-color);color:var(--el-text-color-secondary);font-size:12px;min-width:22px;height:22px;border-radius:11px;display:flex;align-items:center;justify-content:center;border:1px solid var(--el-border-color);padding:0 6px;font-weight:600">
                {{ colTasks(col.key).length }}
              </span>
            </div>
            <el-button size="small" circle @click="openCreate(col.key)">+</el-button>
          </div>

          <div style="flex:1;padding:12px 14px 16px;overflow-y:auto;display:flex;flex-direction:column;gap:10px;min-height:100px">
            <div v-for="(task, idx) in colTasks(col.key)" :key="task.id"
              draggable="true"
              @dragstart="onDragStart($event, task, idx, col.key)"
              @dragover="onDragOver($event, idx)"
              @dragend="onDragEnd"
              style="background:var(--el-bg-color);border-radius:14px;padding:16px;cursor:grab;box-shadow:var(--el-box-shadow-light);transition:all 0.2s;border-left:4px solid"
              :style="{ borderLeftColor: priorityColor(task.priority) }"
              @click="openEdit(task)">
              <!-- Title row with priority on the right -->
              <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:8px;margin-bottom:8px">
                <div style="font-size:14px;font-weight:600;color:var(--el-text-color-primary);word-break:break-word;line-height:1.5;flex:1;min-width:0">{{ task.title }}</div>
                <div style="display:flex;align-items:center;gap:4px;flex-shrink:0">
                  <span v-if="task.status === 'done'" @click.stop="handleArchive(task.id)" title="归档" style="cursor:pointer;font-size:14px;opacity:0.5;transition:opacity 0.2s" @mouseenter="($event.target as HTMLElement).style.opacity='1'" @mouseleave="($event.target as HTMLElement).style.opacity='0.5'">📦</span>
                  <span :style="{ fontSize:'11px',padding:'2px 10px',borderRadius:'10px',fontWeight:600,background:priorityBg(task.priority),color:priorityColor(task.priority),border:`1px solid ${priorityColor(task.priority)}`,whiteSpace:'nowrap' }">{{ priorityMap[task.priority] }}</span>
                </div>
              </div>
              <div v-if="task.description" style="font-size:12px;color:var(--el-text-color-secondary);margin-bottom:8px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden">{{ task.description }}</div>
              <!-- Tags row -->
              <div v-if="(task.tags||[]).length" style="display:flex;gap:4px;flex-wrap:wrap;margin-bottom:10px">
                <span v-for="t in (task.tags||[])" :key="t" style="background:var(--el-color-primary-light-9);color:var(--el-color-primary);font-size:12px;padding:2px 10px;border-radius:8px;font-weight:500">#{{ t }}</span>
              </div>
              <!-- Meta row -->
              <div style="display:flex;align-items:center;gap:5px;flex-wrap:wrap">
                <span v-if="task.due_date" :style="{ fontSize:'12px', color: isOverdue(task) ? '#f56c6c' : 'var(--el-text-color-secondary)' }">📅 {{ formatDate(task.due_date) }}</span>
                <span v-if="isOverdue(task)" style="font-size:10px;padding:0 6px;borderRadius:4px;fontWeight:600;background:#fef0f0;color:#f56c6c;border:1px solid #f56c6c">⏰ 已超期</span>
                <span v-if="task.assignee" style="font-size:12px;color:var(--el-text-color-secondary);margin-left:auto">👤 {{ task.assignee }}</span>
              </div>
            </div>
            <div v-if="colTasks(col.key).length===0" style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;color:var(--el-text-color-placeholder);font-size:13px;padding:24px">
              <span style="font-size:32px;margin-bottom:8px;opacity:0.5">{{ col.emptyIcon }}</span>
              <span>暂无任务</span>
              <span style="font-size:12px;margin-top:4px">点击 + 添加</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Right Stats Panel -->
      <div style="width:370px;flex-shrink:0;background:var(--el-bg-color);border-left:1px solid var(--el-border-color-light);overflow-y:auto;padding:20px">
        <h3 style="font-size:16px;font-weight:700;color:var(--el-text-color-primary);margin-bottom:18px">数据概览</h3>
        <!-- Stat cards -->
        <el-row :gutter="10" style="margin-bottom:20px">
          <el-col :span="12" v-for="card in statCards" :key="card.key" style="margin-bottom:10px">
            <el-card shadow="hover" :body-style="{ padding:'14px 12px', display:'flex', alignItems:'center', gap:'10px' }"
              :style="{ background: card.bg, borderRadius:'12px', border:'none' }">
              <div :style="{ width:'36px',height:'36px',borderRadius:'8px',background:card.iconBg,display:'flex',alignItems:'center',justifyContent:'center',fontSize:'16px' }">{{ card.icon }}</div>
              <div>
                <div style="font-size:22px;font-weight:800;color:var(--el-text-color-primary);line-height:1.3">{{ card.value }}</div>
                <div style="font-size:11px;color:var(--el-text-color-secondary);font-weight:500">{{ card.label }}</div>
              </div>
            </el-card>
          </el-col>
        </el-row>
        <!-- Status bar chart -->
        <el-card shadow="never" style="border-radius:12px;margin-bottom:14px">
          <template #header><span style="font-weight:700;font-size:13px">状态分布</span></template>
          <v-chart :option="statusBarOption" style="height:200px" autoresize />
        </el-card>
        <!-- Priority donut -->
        <el-card shadow="never" style="border-radius:12px">
          <template #header><span style="font-weight:700;font-size:13px">优先级占比</span></template>
          <v-chart :option="priorityPieOption" style="height:200px" autoresize />
        </el-card>
      </div>
    </div>

    <!-- Task Dialog -->
    <el-dialog v-model="dialogVisible" width="540px" destroy-on-close class="task-dialog">
      <template #header>
        <div style="display:flex;align-items:center;gap:10px">
          <div style="width:36px;height:36px;border-radius:10px;background:linear-gradient(135deg,#6366f1,#8b5cf6);display:flex;align-items:center;justify-content:center">
            <el-icon color="#fff" size="18"><EditPen v-if="editingTask"/><Plus v-else/></el-icon>
          </div>
          <span style="font-size:17px;font-weight:700;color:var(--el-text-color-primary)">{{ editingTask ? '编辑任务' : '创建任务' }}</span>
        </div>
      </template>
      <el-form :model="taskForm" label-position="top">
        <el-form-item :error="formErrors.title">
          <template #label><span style="display:flex;align-items:center;gap:4px"><el-icon><EditPen/></el-icon> 标题</span></template>
          <el-input v-model="taskForm.title" placeholder="任务标题" maxlength="100" size="large"/>
        </el-form-item>
        <el-form-item>
          <template #label><span style="display:flex;align-items:center;gap:4px"><el-icon><Document/></el-icon> 描述</span></template>
          <el-input v-model="taskForm.description" type="textarea" :rows="8" placeholder="任务描述（可选）" size="large"/>
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item>
              <template #label><span style="display:flex;align-items:center;gap:4px"><el-icon><PriceTag/></el-icon> 标签</span></template>
              <div style="display:flex;flex-wrap:wrap;gap:4px;align-items:center">
                <el-tag v-for="(t, i) in taskForm.tags" :key="i" closable @close="taskForm.tags.splice(i,1)">{{ t }}</el-tag>
                <el-input v-if="tagInputVisible" ref="tagInputRef" v-model="tagInputValue" style="width:100px" size="large" @keyup.enter="addTag" @blur="addTag" placeholder="输入标签"/>
                <el-button v-else size="large" @click="showTagInput">+ 标签</el-button>
              </div>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item>
              <template #label><span style="display:flex;align-items:center;gap:4px"><el-icon><Flag/></el-icon> 优先级</span></template>
              <el-select v-model="taskForm.priority" style="width:100%" size="large">
                <el-option v-for="o in priorityOptions" :key="o.value" :label="o.label" :value="o.value"/>
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12" v-if="editingTask">
            <el-form-item>
              <template #label><span style="display:flex;align-items:center;gap:4px"><el-icon><List/></el-icon> 状态</span></template>
              <el-select v-model="taskForm.status" style="width:100%" size="large">
                <el-option v-for="o in statusOptions" :key="o.value" :label="o.label" :value="o.value"/>
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="editingTask ? 12 : 12">
            <el-form-item>
              <template #label><span style="display:flex;align-items:center;gap:4px"><el-icon><User/></el-icon> 负责人</span></template>
              <el-input v-model="taskForm.assignee" placeholder="姓名" size="large"/>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item>
          <template #label><span style="display:flex;align-items:center;gap:4px"><el-icon><Calendar/></el-icon> 截止日期</span></template>
          <el-date-picker v-model="taskForm.dueDate" type="datetime" placeholder="选择日期" style="width:100%" format="YYYY-MM-DD HH:mm" value-format="YYYY-MM-DDTHH:mm:ss" size="large"/>
        </el-form-item>
      </el-form>
      <template #footer>
        <div style="display:flex;justify-content:space-between">
          <el-button v-if="editingTask" type="danger" @click="handleDelete" plain size="large">删除任务</el-button>
          <div style="display:flex;gap:8px;margin-left:auto">
            <el-button @click="dialogVisible=false" size="large">取消</el-button>
            <el-button type="primary" @click="handleSave" :loading="saving" size="large" style="background:linear-gradient(135deg,#6366f1,#8b5cf6);border:none">保存</el-button>
          </div>
        </div>
      </template>
    </el-dialog>

    <!-- Archive Drawer -->
    <el-drawer v-model="archiveDrawerVisible" direction="rtl" size="65%" :before-close="onArchiveDrawerClose" custom-class="archive-drawer-panel">
      <template #header>
        <div style="display:flex;align-items:center;gap:12px">
          <div style="width:36px;height:36px;border-radius:10px;background:linear-gradient(135deg,#909399,#606266);display:flex;align-items:center;justify-content:center">
            <span style="font-size:18px">📦</span>
          </div>
          <span style="font-size:18px;font-weight:700;color:var(--el-text-color-primary)">已归档任务</span>
          <el-tag type="info" round size="small" style="font-weight:600">{{ archiveTotal }} 条</el-tag>
        </div>
      </template>
      <div class="archive-drawer-inner">
        <!-- Search bar -->
      <div style="margin-bottom:20px;display:flex;gap:12px;align-items:center">
        <el-input v-model="archiveSearch" placeholder="搜索归档任务..." :prefix-icon="Search" clearable size="large" style="flex:1" @input="onArchiveSearch"/>
      </div>

      <!-- Archive table -->
      <el-table :data="filteredArchivedTasks" stripe size="medium" v-loading="archiveLoading" style="width:100%;border-radius:12px;overflow:hidden" :default-sort="{ prop: 'updated_at', order: 'descending' }" header-row-style="font-weight:700" row-style="font-size:13px">
        <el-table-column prop="title" label="标题" min-width="160" show-overflow-tooltip>
          <template #default="{ row }">
            <span style="font-weight:600;color:var(--el-text-color-primary)">{{ row.title }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="priority" label="优先级" width="100" align="center">
          <template #default="{ row }">
            <span :style="{ fontSize:'12px',padding:'2px 10px',borderRadius:'10px',fontWeight:600,background:priorityBg(row.priority),color:priorityColor(row.priority),border:`1px solid ${priorityColor(row.priority)}` }">{{ priorityMap[row.priority] }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="140" show-overflow-tooltip>
          <template #default="{ row }">
            <span style="color:var(--el-text-color-secondary)">{{ row.description || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="due_date" label="截止日期" width="120" align="center">
          <template #default="{ row }">
            <span :style="{ color: row.due_date && new Date(row.due_date) < new Date() ? '#f56c6c' : 'var(--el-text-color-secondary)', fontSize:'13px' }">
              {{ row.due_date ? formatDate(row.due_date) : '-' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="assignee" label="负责人" width="100" align="center">
          <template #default="{ row }">
            <span style="color:var(--el-text-color-secondary)">{{ row.assignee || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="tags" label="标签" min-width="120">
          <template #default="{ row }">
            <div style="display:flex;gap:4px;flex-wrap:wrap">
              <el-tag v-for="t in (row.tags || [])" :key="t" size="small" type="" style="background:#eef4ff;color:#6169ee;border:none;font-weight:500">#{{ t }}</el-tag>
              <span v-if="!row.tags || !row.tags.length" style="color:var(--el-text-color-placeholder)">-</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="updated_at" label="归档时间" width="170" align="center" sortable>
          <template #default="{ row }">
            <span style="font-size:12px;color:var(--el-text-color-secondary)">{{ row.updated_at ? new Date(row.updated_at).toLocaleString('zh-CN') : '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" align="center" fixed="right">
          <template #default="{ row }">
            <div style="display:flex;gap:6px;justify-content:center">
              <el-button size="small" type="primary" plain @click="handleUnarchive(row.id)" :loading="row._unarchiving">
                <el-icon style="margin-right:2px"><Back/></el-icon> 恢复
              </el-button>
              <el-button size="small" type="danger" plain @click="handleDeleteArchived(row.id)" :loading="row._deleting">
                <el-icon style="margin-right:2px"><Delete/></el-icon> 删除
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <!-- Empty state -->
      <div v-if="!archiveLoading && filteredArchivedTasks.length === 0" style="display:flex;flex-direction:column;align-items:center;justify-content:center;padding:60px 20px;color:var(--el-text-color-placeholder)">
        <span style="font-size:48px;margin-bottom:12px">📭</span>
        <span style="font-size:15px">{{ archiveSearch ? '没有匹配的归档任务' : '暂无归档任务' }}</span>
        <span style="font-size:12px;margin-top:4px">完成看板中的任务后点击 📦 即可归档</span>
      </div>
      </div><!-- /archive-drawer-inner -->
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { useChartTheme } from '@/composables/useChartTheme'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, EditPen, Plus, Document, PriceTag, Flag, List, User, Calendar, Back, Delete } from '@element-plus/icons-vue'
import { use } from 'echarts/core'
import { BarChart, PieChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, LegendComponent, GridComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import VChart from 'vue-echarts'
import { useTaskStore } from '@/stores/task'
import type { Task } from '@/api/tasks'
import { STATUS_OPTIONS, PRIORITY_OPTIONS, STATUS_MAP, PRIORITY_MAP } from '@/types'

use([BarChart, PieChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent, CanvasRenderer])

const store = useTaskStore()
const statusOptions = STATUS_OPTIONS
const priorityOptions = PRIORITY_OPTIONS
const priorityMap = PRIORITY_MAP

const columns = [
  { key: 'todo', label: '待处理', bg: 'var(--el-color-primary-light-9)', dotColor: '#667eea', emptyIcon: '📥' },
  { key: 'in_progress', label: '进行中', bg: 'var(--el-color-warning-light-9)', dotColor: '#e6a23c', emptyIcon: '⚡' },
  { key: 'done', label: '已完成', bg: 'var(--el-color-success-light-9)', dotColor: '#67c23a', emptyIcon: '🎉' },
]

// All unique tags from all tasks
const allTags = computed(() => {
  const set = new Set<string>()
  store.tasks.forEach(t => (t.tags || []).forEach(tag => set.add(tag)))
  return Array.from(set).sort()
})

const searchText = ref('')
let searchTimer: any = null
function onSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => store.setFilter('search', searchText.value), 300)
}

const dateRange = ref<[string, string] | null>(null)
function onDateChange(val: [string, string] | null) {
  store.setFilter('date_from', val?.[0] || '')
  store.setFilter('date_to', val?.[1] || '')
}
const overdueFilter = ref(false)
function onOverdueChange(val: boolean) {
  store.setFilter('overdue', val || undefined)
}

// Sort
const sortBy = ref('')
const PRIORITY_ORDER: Record<string, number> = { high: 0, medium: 1, low: 2 }
function onSortChange() {}

// ── Archive ──
const archiveDrawerVisible = ref(false)
const archiveSearch = ref('')
const archiveLoading = ref(false)
const archivedTasks = ref<(Task & { _unarchiving?: boolean; _deleting?: boolean })[]>([])
const archiveTotal = ref(0)

const filteredArchivedTasks = computed(() => {
  if (!archiveSearch.value) return archivedTasks.value
  const kw = archiveSearch.value.toLowerCase()
  return archivedTasks.value.filter(t =>
    t.title.toLowerCase().includes(kw) ||
    (t.description || '').toLowerCase().includes(kw) ||
    (t.assignee || '').toLowerCase().includes(kw) ||
    (t.tags || []).some(tag => tag.toLowerCase().includes(kw))
  )
})

let archiveSearchTimer: any = null
function onArchiveSearch() {
  clearTimeout(archiveSearchTimer)
  archiveSearchTimer = setTimeout(() => loadArchivedTasks(), 300)
}

async function openArchiveDrawer() {
  archiveDrawerVisible.value = true
  archiveSearch.value = ''
  await loadArchivedTasks()
}

async function loadArchivedTasks() {
  archiveLoading.value = true
  try {
    const params: any = { include_archived: true, status: 'archived' }
    if (archiveSearch.value) params.search = archiveSearch.value
    archivedTasks.value = await store.fetchArchivedTasks(archiveSearch.value || undefined)
    archiveTotal.value = archivedTasks.value.length
  } finally {
    archiveLoading.value = false
  }
}

function onArchiveDrawerClose(done: () => void) {
  archiveSearch.value = ''
  done()
}

async function handleArchive(id: number) {
  try {
    await ElMessageBox.confirm('确定归档此任务？归档后可在"已归档"中查看和恢复。', '确认归档', {
      confirmButtonText: '归档', cancelButtonText: '取消', type: 'info'
    })
    await store.archiveTask(id)
    ElMessage.success('任务已归档')
  } catch {}
}

async function handleUnarchive(id: number) {
  const idx = archivedTasks.value.findIndex(t => t.id === id)
  if (idx > -1) archivedTasks.value[idx]._unarchiving = true
  try {
    await store.unarchiveTask(id)
    archivedTasks.value = archivedTasks.value.filter(t => t.id !== id)
    archiveTotal.value = archivedTasks.value.length
    ElMessage.success('已恢复到待处理')
  } catch {
    if (idx > -1) archivedTasks.value[idx]._unarchiving = false
    ElMessage.error('操作失败')
  }
}

async function handleDeleteArchived(id: number) {
  try {
    await ElMessageBox.confirm('确定永久删除此归档任务？此操作不可撤销。', '确认删除', {
      confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning'
    })
    const idx = archivedTasks.value.findIndex(t => t.id === id)
    if (idx > -1) archivedTasks.value[idx]._deleting = true
    await store.deleteArchivedTask(id)
    archivedTasks.value = archivedTasks.value.filter(t => t.id !== id)
    archiveTotal.value = archivedTasks.value.length
    ElMessage.success('任务已删除')
  } catch {}
}
const filters = reactive({ tag: '', status: '', priority: '' })
function onFilterChange(key: string, val: string) { store.setFilter(key as any, val) }
function colTasks(status: string) {
  let list = store.tasks.filter(t => t.status === status)

  // Apply sort if active
  if (sortBy.value === 'date') {
    list.sort((a, b) => {
      if (!a.due_date && !b.due_date) return 0
      if (!a.due_date) return 1
      if (!b.due_date) return -1
      return new Date(a.due_date).getTime() - new Date(b.due_date).getTime()
    })
  } else if (sortBy.value === 'priority') {
    list.sort((a, b) => (PRIORITY_ORDER[a.priority] ?? 2) - (PRIORITY_ORDER[b.priority] ?? 2))
  } else if (sortBy.value === 'date_priority') {
    list.sort((a, b) => {
      const da = a.due_date ? a.due_date.slice(0, 10) : ''
      const db = b.due_date ? b.due_date.slice(0, 10) : ''
      if (da && db && da !== db) return da.localeCompare(db)
      if (da && !db) return -1
      if (!da && db) return 1
      return (PRIORITY_ORDER[a.priority] ?? 2) - (PRIORITY_ORDER[b.priority] ?? 2)
    })
  } else {
    // Default: column_order
    list.sort((a, b) => a.column_order - b.column_order)
  }

  return list
}
function priorityColor(p: string) { return p === 'high' ? '#f56c6c' : p === 'medium' ? '#e6a23c' : '#67c23a' }
function priorityBg(p: string) { return p === 'high' ? '#fef0f0' : p === 'medium' ? '#fdf6ec' : '#eefbe6' }
function formatDate(d: string) { return new Date(d).toLocaleDateString('zh-CN') }
function isOverdue(t: Task) { return t.due_date && new Date(t.due_date) < new Date() && t.status !== 'done' }

// Drag and drop
let draggedTask: Task | null = null
let draggedFrom: string = ''
let dragOverIdx = -1
function onDragStart(e: DragEvent, task: Task, idx: number, col: string) {
  draggedTask = task; draggedFrom = col
  if (e.dataTransfer) { e.dataTransfer.effectAllowed = 'move'; e.dataTransfer.setData('text/plain', String(task.id)) }
}
function onDragEnd() { draggedTask = null; draggedFrom = ''; dragOverIdx = -1 }
function onDragOver(e: DragEvent, idx: number) { e.preventDefault(); dragOverIdx = idx }
async function onDrop(e: DragEvent, toCol: string) {
  if (!draggedTask) return
  const targetIdx = dragOverIdx >= 0 ? dragOverIdx : colTasks(toCol).length
  await store.moveTask(draggedTask.id, toCol, targetIdx)
  await store.fetchTasks() // force full reload from server
  ElMessage.success('任务已移动')
}

// Dialog
const dialogVisible = ref(false)
const editingTask = ref<Task | null>(null)
const saving = ref(false)
const taskForm = reactive<{ title: string; description: string; priority: string; status: string; assignee: string; dueDate: string; tags: string[] }>({
  title: '', description: '', priority: 'medium', status: 'todo', assignee: '', dueDate: '', tags: []
})
const formErrors = reactive({ title: '' })

// Tag input
const tagInputVisible = ref(false)
const tagInputValue = ref('')
const tagInputRef = ref<any>(null)

function showTagInput() {
  tagInputVisible.value = true
  nextTick(() => tagInputRef.value?.focus?.())
}
function addTag() {
  const val = tagInputValue.value.trim()
  if (val && !taskForm.tags.includes(val)) taskForm.tags.push(val)
  tagInputValue.value = ''
  tagInputVisible.value = false
}

function openCreate(status: string) {
  editingTask.value = null
  taskForm.title = ''; taskForm.description = ''; taskForm.priority = 'medium'; taskForm.status = status
  taskForm.assignee = ''; taskForm.dueDate = ''; taskForm.tags = []
  formErrors.title = ''
  dialogVisible.value = true
}
function openEdit(task: Task) {
  editingTask.value = task
  taskForm.title = task.title; taskForm.description = task.description || ''; taskForm.priority = task.priority
  taskForm.status = task.status; taskForm.assignee = task.assignee || ''
  taskForm.dueDate = task.due_date ? task.due_date.slice(0, 19) : ''
  taskForm.tags = [...(task.tags || [])]
  formErrors.title = ''
  dialogVisible.value = true
}
async function handleSave() {
  if (!taskForm.title.trim()) { formErrors.title = '标题不能为空'; return }
  saving.value = true
  try {
    const data: any = { title: taskForm.title, description: taskForm.description, priority: taskForm.priority, due_date: taskForm.dueDate || undefined, assignee: taskForm.assignee, tags: taskForm.tags }
    if (editingTask.value) {
      await store.updateTask(editingTask.value.id, { ...data, status: taskForm.status })
      ElMessage.success('任务已更新')
    } else {
      await store.addTask(data)
      ElMessage.success('任务已创建')
    }
    dialogVisible.value = false
  } catch { ElMessage.error('操作失败') }
  finally { saving.value = false }
}
async function handleDelete() {
  if (!editingTask.value) return
  try {
    await ElMessageBox.confirm('确定删除此任务？', '确认', { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' })
    await store.removeTask(editingTask.value.id)
    dialogVisible.value = false
    ElMessage.success('任务已删除')
  } catch {}
}

// ── Stats ──
const statCards = computed(() => {
  const tasks = store.tasks
  return [
    { key: 'total', label: '总任务数', icon: '📋', value: tasks.length, bg: 'var(--el-color-primary-light-9)', iconBg: 'var(--el-color-primary)' },
    { key: 'todo', label: '待处理', icon: '📥', value: tasks.filter(t => t.status === 'todo').length, bg: 'var(--el-color-primary-light-9)', iconBg: 'var(--el-color-primary)' },
    { key: 'prog', label: '进行中', icon: '⚡', value: tasks.filter(t => t.status === 'in_progress').length, bg: 'var(--el-color-warning-light-9)', iconBg: 'var(--el-color-warning)' },
    { key: 'done', label: '已完成', icon: '✅', value: tasks.filter(t => t.status === 'done').length, bg: 'var(--el-color-success-light-9)', iconBg: 'var(--el-color-success)' },
  ]
})

const statusBarOption = computed(() => {
  const { textPrimary, textRegular, textSecondary } = useChartTheme()
  const tasks = store.tasks
  const counts = {
    todo: tasks.filter(t => t.status === 'todo').length,
    in_progress: tasks.filter(t => t.status === 'in_progress').length,
    done: tasks.filter(t => t.status === 'done').length,
  }
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '8%', bottom: '3%', top: '18%', containLabel: true },
    xAxis: { type: 'category', data: ['待处理', '进行中', '已完成'], axisLabel: { fontSize: 11, color: textRegular.value }, axisTick: { show: false } },
    yAxis: { type: 'value', minInterval: 1, axisLabel: { fontSize: 10, color: textSecondary.value }, splitLine: { lineStyle: { color: 'var(--el-border-color-lighter)' } } },
    series: [{
      type: 'bar',
      data: [
        { value: counts.todo, itemStyle: { color: '#667eea', borderRadius: [6,6,0,0] } },
        { value: counts.in_progress, itemStyle: { color: '#e6a23c', borderRadius: [6,6,0,0] } },
        { value: counts.done, itemStyle: { color: '#67c23a', borderRadius: [6,6,0,0] } },
      ],
      barWidth: 40,
      label: { show: true, position: 'top', fontSize: 14, fontWeight: 700, color: textPrimary.value },
    }],
  }
})

const priorityPieOption = computed(() => {
  const { textRegular, bgColor } = useChartTheme()
  const tasks = store.tasks
  const counts = {
    low: tasks.filter(t => t.priority === 'low').length,
    medium: tasks.filter(t => t.priority === 'medium').length,
    high: tasks.filter(t => t.priority === 'high').length,
  }
  return {
    tooltip: { trigger: 'item', formatter: '{b}: {c} 个 ({d}%)' },
    legend: { bottom: 0, textStyle: { fontSize: 11, color: textRegular.value }, itemWidth: 10, itemHeight: 10 },
    series: [{
      type: 'pie',
      radius: ['50%', '75%'],
      center: ['50%', '45%'],
      avoidLabelOverlap: false,
      itemStyle: { borderRadius: 6, borderColor: bgColor.value, borderWidth: 3 },
      label: { show: false },
      emphasis: { label: { show: true, fontSize: 14, fontWeight: 'bold' } },
      data: [
        { value: counts.low, name: '低优先级', itemStyle: { color: '#67c23a' } },
        { value: counts.medium, name: '中优先级', itemStyle: { color: '#e6a23c' } },
        { value: counts.high, name: '高优先级', itemStyle: { color: '#f56c6c' } },
      ],
    }],
  }
})

onMounted(() => store.fetchTasks())</script>

<style scoped>
.search-toolbar {
  --el-component-size: 36px;
}
.search-toolbar :deep(.el-input__wrapper),
.search-toolbar :deep(.el-select__wrapper) {
  border-radius: 8px;
}
.search-toolbar :deep(.el-button) {
  border-radius: 8px;
}
.task-dialog :deep(.el-input__wrapper),
.task-dialog :deep(.el-select__wrapper),
.task-dialog :deep(.el-textarea__inner) {
  border-radius: 8px;
}
.task-dialog :deep(.el-button) {
  border-radius: 8px;
}
</style>

