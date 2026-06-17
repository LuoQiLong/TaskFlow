<template>
  <div style="display:flex;flex-direction:column;height:calc(100vh - 64px);background:#f9fbfc">
    <!-- Toolbar -->
    <div class="search-toolbar" style="background:var(--el-bg-color);padding:20px 28px;border-bottom:1px solid var(--el-border-color-light);display:flex;gap:12px;align-items:center;flex-wrap:wrap">
      <el-input v-model="searchText" placeholder="搜索任务..." :prefix-icon="Search" clearable style="width:500px" size="large" @clear="searchText=''" @input="onSearch"/>
      <el-select v-model="filters.tag" placeholder="标签" clearable style="width:110px" size="large" @change="onFilterChange('tag', $event)">
        <el-option v-for="t in allTags" :key="t" :label="t" :value="t"/>
      </el-select>
      <el-select v-model="filters.status" placeholder="状态" clearable style="width:110px" size="large" @change="onFilterChange('status', $event)">
        <el-option v-for="o in statusOptions" :key="o.value" :label="o.label" :value="o.value"/>
      </el-select>
      <el-select v-model="filters.priority" placeholder="优先级" clearable style="width:110px" size="large" @change="onFilterChange('priority', $event)">
        <el-option v-for="o in priorityOptions" :key="o.value" :label="o.label" :value="o.value"/>
      </el-select>
      <div style="width:500px;flex-shrink:0"><el-date-picker v-model="dateRange" type="daterange" range-separator="至" start-placeholder="开始" end-placeholder="结束" format="YYYY-MM-DD" value-format="YYYY-MM-DD" size="large" style="width:100%" @change="onDateChange"/></div>
      <el-button v-if="hasFilters" @click="clearFilters" size="small" text style="color:#909399;font-size:12px" :icon="Close">清除</el-button>
    </div>

    <!-- Kanban Board + Stats -->
    <div style="flex:1;display:flex;gap:0;overflow:hidden">
      <!-- Kanban columns -->
      <div style="flex:1;display:flex;gap:20px;padding:20px 28px;overflow-x:auto;min-height:0" v-loading="store.isLoading">
        <div v-for="col in columns" :key="col.key"
          :style="{ flex: 1, minWidth: '260px', maxWidth: '380px', background: col.bg, borderRadius: '18px', display: 'flex', flexDirection: 'column', border: '1px solid #e4e7ed' }"
          @dragover.prevent @drop="onDrop($event, col.key)">
          <div style="display:flex;align-items:center;justify-content:space-between;padding:16px 18px;background:rgba(255,255,255,0.6)">
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
              style="background:var(--el-bg-color);border-radius:14px;padding:16px;cursor:grab;box-shadow:0 1px 4px rgba(0,0,0,0.06);transition:all 0.2s;border-left:4px solid"
              :style="{ borderLeftColor: priorityColor(task.priority) }"
              @click="openEdit(task)">
              <div style="font-size:14px;font-weight:600;color:var(--el-text-color-primary);margin-bottom:8px;word-break:break-word;line-height:1.5">{{ task.title }}</div>
              <div v-if="task.description" style="font-size:12px;color:var(--el-text-color-secondary);margin-bottom:8px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden">{{ task.description }}</div>
              <!-- Tags row -->
              <div v-if="(task.tags||[]).length" style="display:flex;gap:4px;flex-wrap:wrap;margin-bottom:10px">
                <span v-for="t in (task.tags||[])" :key="t" style="background:#eef4ff;color:#6169ee;font-size:12px;padding:2px 10px;border-radius:8px;font-weight:500">#{{ t }}</span>
              </div>
              <!-- Meta row -->
              <div style="display:flex;align-items:center;gap:5px;flex-wrap:wrap">
                <span :style="{ fontSize:'11px',padding:'1px 8px',borderRadius:'8px',fontWeight:600,background:priorityBg(task.priority),color:priorityColor(task.priority),border:`1px solid ${priorityColor(task.priority)}` }">{{ priorityMap[task.priority] }}</span>
                <span v-if="task.due_date" :style="{ fontSize:'12px', color: isOverdue(task) ? '#f56c6c' : 'var(--el-text-color-secondary)' }">📅 {{ formatDate(task.due_date) }}</span>
                <span v-if="task.assignee" style="font-size:12px;color:var(--el-text-color-secondary);margin-left:auto">👤 {{ task.assignee }}</span>
              </div>
            </div>
            <div v-if="colTasks(col.key).length===0" style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;color:#c0c4cc;font-size:13px;padding:24px">
              <span style="font-size:32px;margin-bottom:8px;opacity:0.5">{{ col.emptyIcon }}</span>
              <span>暂无任务</span>
              <span style="font-size:12px;margin-top:4px">点击 + 添加</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Right Stats Panel -->
      <div style="width:370px;flex-shrink:0;background:var(--el-bg-color);border-left:1px solid var(--el-border-color-light);overflow-y:auto;padding:20px">
        <h3 style="font-size:16px;font-weight:700;color:var(--el-text-color-primary);margin-bottom:18px">📊 数据概览</h3>
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
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Close, EditPen, Plus, Document, PriceTag, Flag, List, User, Calendar } from '@element-plus/icons-vue'
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
  { key: 'todo', label: '待处理', bg: 'linear-gradient(180deg, #eef2ff, #f3e8ff)', dotColor: '#667eea', emptyIcon: '📥' },
  { key: 'in_progress', label: '进行中', bg: 'linear-gradient(180deg, #fffbeb, #fef3c7)', dotColor: '#e6a23c', emptyIcon: '⚡' },
  { key: 'done', label: '已完成', bg: 'linear-gradient(180deg, #ecfdf5, #d1fae5)', dotColor: '#67c23a', emptyIcon: '🎉' },
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
const filters = reactive({ tag: '', status: '', priority: '' })
function onFilterChange(key: string, val: string) { store.setFilter(key as any, val) }
const hasFilters = computed(() => !!(filters.tag || filters.status || filters.priority || dateRange.value || searchText.value))
function clearFilters() {
  filters.tag = ''; filters.status = ''; filters.priority = ''; dateRange.value = null; searchText.value = ''
  store.clearFilters()
}

function colTasks(status: string) {
  return store.tasks.filter(t => t.status === status).sort((a, b) => a.column_order - b.column_order)
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
    { key: 'total', label: '总任务数', icon: '📋', value: tasks.length, bg: 'linear-gradient(135deg,#eef2ff,#e0e7ff)', iconBg: '#667eea' },
    { key: 'todo', label: '待处理', icon: '📥', value: tasks.filter(t => t.status === 'todo').length, bg: 'linear-gradient(135deg,#eef2ff,#f3e8ff)', iconBg: '#8b5cf6' },
    { key: 'prog', label: '进行中', icon: '⚡', value: tasks.filter(t => t.status === 'in_progress').length, bg: 'linear-gradient(135deg,#fffbeb,#fef3c7)', iconBg: '#e6a23c' },
    { key: 'done', label: '已完成', icon: '✅', value: tasks.filter(t => t.status === 'done').length, bg: 'linear-gradient(135deg,#ecfdf5,#d1fae5)', iconBg: '#67c23a' },
  ]
})

const statusBarOption = computed(() => {
  const tasks = store.tasks
  const counts = {
    todo: tasks.filter(t => t.status === 'todo').length,
    in_progress: tasks.filter(t => t.status === 'in_progress').length,
    done: tasks.filter(t => t.status === 'done').length,
  }
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '8%', bottom: '3%', top: '18%', containLabel: true },
    xAxis: { type: 'category', data: ['待处理', '进行中', '已完成'], axisLabel: { fontSize: 11, color: '#606266' }, axisTick: { show: false } },
    yAxis: { type: 'value', minInterval: 1, axisLabel: { fontSize: 10, color: '#909399' }, splitLine: { lineStyle: { color: 'var(--el-border-color-lighter)' } } },
    series: [{
      type: 'bar',
      data: [
        { value: counts.todo, itemStyle: { color: '#667eea', borderRadius: [6,6,0,0] } },
        { value: counts.in_progress, itemStyle: { color: '#e6a23c', borderRadius: [6,6,0,0] } },
        { value: counts.done, itemStyle: { color: '#67c23a', borderRadius: [6,6,0,0] } },
      ],
      barWidth: 40,
      label: { show: true, position: 'top', fontSize: 14, fontWeight: 700, color: '#303133' },
    }],
  }
})

const priorityPieOption = computed(() => {
  const tasks = store.tasks
  const counts = {
    low: tasks.filter(t => t.priority === 'low').length,
    medium: tasks.filter(t => t.priority === 'medium').length,
    high: tasks.filter(t => t.priority === 'high').length,
  }
  return {
    tooltip: { trigger: 'item', formatter: '{b}: {c} 个 ({d}%)' },
    legend: { bottom: 0, textStyle: { fontSize: 11, color: '#606266' }, itemWidth: 10, itemHeight: 10 },
    series: [{
      type: 'pie',
      radius: ['50%', '75%'],
      center: ['50%', '45%'],
      avoidLabelOverlap: false,
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 3 },
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

onMounted(() => store.fetchTasks())
watch(() => store.filters, () => store.fetchTasks(), { deep: true })
</script>

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
