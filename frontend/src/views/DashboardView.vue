<template>
  <div style="padding:24px;background:var(--el-bg-color-page);min-height:100vh" v-loading="loading">
    <el-tabs v-if="!loading" v-model="activeTab" class="dashboard-tabs">
      <el-tab-pane name="kanban">
        <template #label>
          <span class="tab-label">📋 任务看板</span>
        </template>
        <!-- Stat cards -->
        <el-row :gutter="16" style="margin-bottom:20px">
          <el-col :span="6" v-for="card in statCards" :key="card.key">
            <el-card shadow="hover" :body-style="{ padding:'20px', display:'flex', alignItems:'center', gap:'12px' }"
              :style="{ background: card.bg, borderRadius:'12px', border:'none' }">
              <div :style="{ width:'44px',height:'44px',borderRadius:'10px',background:card.iconBg,display:'flex',alignItems:'center',justifyContent:'center',fontSize:'20px' }">{{ card.icon }}</div>
              <div>
                <div style="font-size:24px;font-weight:800;color:var(--el-text-color-primary);line-height:1.2">{{ card.value }}</div>
                <div style="font-size:13px;color:var(--el-text-color-secondary);font-weight:500">{{ card.label }}</div>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <!-- Charts row 1 -->
        <el-row :gutter="16" style="margin-bottom:16px">
          <el-col :span="12">
            <el-card shadow="never" style="border-radius:12px">
              <template #header><span style="font-weight:700;font-size:14px">任务状态分布</span></template>
              <div v-if="hasKanbanData" style="height:280px"><v-chart :option="statusBarOption" style="height:280px" autoresize /></div>
              <div v-else class="chart-empty"><span class="empty-icon">📊</span><span>暂无任务数据</span><span class="empty-hint">创建任务后将在此显示</span></div>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card shadow="never" style="border-radius:12px">
              <template #header><span style="font-weight:700;font-size:14px">优先级分布</span></template>
              <div v-if="hasKanbanData" style="height:280px"><v-chart :option="priorityPieOption" style="height:280px" autoresize /></div>
              <div v-else class="chart-empty"><span class="empty-icon">🍩</span><span>暂无任务数据</span><span class="empty-hint">创建任务后将在此显示</span></div>
            </el-card>
          </el-col>
        </el-row>

        <!-- Charts row 2 -->
        <el-row :gutter="16">
          <el-col :span="24">
            <el-card shadow="never" style="border-radius:12px">
              <template #header><span style="font-weight:700;font-size:14px">任务创建趋势（近30天）</span></template>
              <div v-if="hasKanbanData" style="height:300px"><v-chart :option="trendLineOption" style="height:300px" autoresize /></div>
              <div v-else class="chart-empty"><span class="empty-icon">📈</span><span>暂无任务数据</span><span class="empty-hint">创建任务后将在此显示</span></div>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>

      <el-tab-pane name="work-weekly">
        <template #label>
          <span class="tab-label">📆 工作周报</span>
        </template>
        <!-- Month toolbar -->
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:20px">
          <div style="display:flex;align-items:baseline;gap:10px">
            <span style="font-size:22px;font-weight:700;color:var(--el-text-color-primary)">{{ dashYear }}年{{ dashMonth }}月</span>
            <span style="font-size:13px;color:var(--el-text-color-secondary)">工作周报统计</span>
          </div>
          <div style="display:flex;align-items:center;gap:12px">
            <el-radio-group v-model="quickMonth" @change="onQuickMonth">
              <el-radio-button value="current">本月</el-radio-button>
              <el-radio-button value="last">上月</el-radio-button>
            </el-radio-group>
            <el-date-picker
              v-model="customMonth"
              type="month"
              placeholder="选择月份"
              format="YYYY-MM"
              value-format="YYYY-MM"
              @change="onCustomMonth"
            />
          </div>
        </div>

        <!-- Summary cards -->
        <div style="display:flex;gap:16px;margin-bottom:16px">
          <el-card shadow="hover" :body-style="{ padding:'20px', textAlign:'center' }" style="flex:1;border-radius:12px;border:none;background:var(--el-color-primary-light-9)">
            <div style="font-size:13px;color:var(--el-text-color-secondary);margin-bottom:4px">总工时</div>
            <div style="font-size:24px;font-weight:800;color:var(--el-color-primary)">{{ dashData?.summary?.total_hours ?? 0 }}<span style="font-size:13px">h</span></div>
          </el-card>
          <el-card shadow="hover" :body-style="{ padding:'20px', textAlign:'center' }" style="flex:1;border-radius:12px;border:none;background:var(--el-color-success-light-9)">
            <div style="font-size:13px;color:var(--el-text-color-secondary);margin-bottom:4px">任务工时</div>
            <div style="font-size:24px;font-weight:800;color:var(--el-color-success)">{{ dashData?.summary?.task_hours ?? 0 }}<span style="font-size:13px">h</span></div>
          </el-card>
          <el-card shadow="hover" :body-style="{ padding:'20px', textAlign:'center' }" style="flex:1;border-radius:12px;border:none;background:var(--el-color-danger-light-9)">
            <div style="font-size:13px;color:var(--el-text-color-secondary);margin-bottom:4px">工单工时</div>
            <div style="font-size:24px;font-weight:800;color:var(--el-color-danger)">{{ dashData?.summary?.work_order_hours ?? 0 }}<span style="font-size:13px">h</span></div>
          </el-card>
          <el-card shadow="hover" :body-style="{ padding:'20px', textAlign:'center' }" style="flex:1;border-radius:12px;border:none;background:var(--el-color-warning-light-9)">
            <div style="font-size:13px;color:var(--el-text-color-secondary);margin-bottom:4px">饱和度</div>
            <div style="font-size:24px;font-weight:800;color:var(--el-color-warning)">{{ dashData?.summary?.saturation_pct ?? 0 }}<span style="font-size:13px">%</span></div>
          </el-card>
          <el-card shadow="hover" :body-style="{ padding:'20px', textAlign:'center' }" style="flex:1;border-radius:12px;border:none;background:var(--el-color-danger-light-9)">
            <div style="font-size:13px;color:var(--el-text-color-secondary);margin-bottom:4px">超出工时</div>
            <div style="font-size:24px;font-weight:800;color:var(--el-color-danger)">{{ overtimeHours }}<span style="font-size:13px">h</span></div>
          </el-card>
        </div>

        <!-- Row 1: 项目工时分布 + 任务vs工单占比 -->
        <el-row :gutter="16" style="margin-bottom:16px">
          <el-col :span="12">
            <el-card shadow="never" style="border-radius:12px">
              <template #header><span style="font-weight:700;font-size:14px">项目工时分布</span></template>
              <div v-if="hasProjectHours" style="height:300px"><v-chart :option="projectHoursBarOption" style="height:300px" autoresize /></div>
              <div v-else class="chart-empty"><span class="empty-icon">📊</span><span>暂无项目工时数据</span><span class="empty-hint">记录工时后将在此显示</span></div>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card shadow="never" style="border-radius:12px">
              <template #header><span style="font-weight:700;font-size:14px">任务 vs 工单工时占比</span></template>
              <div v-if="hasTypeData" style="height:300px"><v-chart :option="typePieOption" style="height:300px" autoresize /></div>
              <div v-else class="chart-empty"><span class="empty-icon">🍩</span><span>暂无工时数据</span><span class="empty-hint">记录工时后将在此显示</span></div>
            </el-card>
          </el-col>
        </el-row>

        <!-- Row 2: 超期任务统计 + 标签分布 -->
        <el-row :gutter="16" style="margin-bottom:16px">
          <el-col :span="12">
            <el-card shadow="never" style="border-radius:12px">
              <template #header><span style="font-weight:700;font-size:14px">超期任务统计</span></template>
              <div v-if="hasOverdue" style="height:300px"><v-chart :option="overdueBarOption" style="height:300px" autoresize /></div>
              <div v-else class="chart-empty"><span class="empty-icon">✅</span><span>暂无超期任务</span><span class="empty-hint">太棒了，所有任务都在计划内</span></div>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card shadow="never" style="border-radius:12px">
              <template #header><span style="font-weight:700;font-size:14px">标签分布</span></template>
              <div v-if="hasTags" style="height:300px"><v-chart :option="tagPieOption" style="height:300px" autoresize /></div>
              <div v-else class="chart-empty"><span class="empty-icon">🏷️</span><span>暂无标签数据</span><span class="empty-hint">为任务添加标签后将在此显示</span></div>
            </el-card>
          </el-col>
        </el-row>

        <!-- Row 3: 周饱和度趋势 + 任务创建趋势 -->
        <el-row :gutter="16" style="margin-bottom:16px">
          <el-col :span="12">
            <el-card shadow="never" style="border-radius:12px">
              <template #header><span style="font-weight:700;font-size:14px">周饱和度趋势（近12周）</span></template>
              <v-chart :option="saturationTrendOption" style="height:300px" autoresize />
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card shadow="never" style="border-radius:12px">
              <template #header><span style="font-weight:700;font-size:14px">任务创建趋势（近12周）</span></template>
              <v-chart :option="creationTrendOption" style="height:300px" autoresize />
            </el-card>
          </el-col>
        </el-row>

        <!-- Row 4: 月度工时汇总 (full width) -->
        <el-row :gutter="16">
          <el-col :span="24">
            <el-card shadow="never" style="border-radius:12px">
              <template #header><span style="font-weight:700;font-size:14px">月度工时汇总</span></template>
              <v-chart :option="weeklyStackOption" style="height:300px" autoresize />
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useChartTheme } from '@/composables/useChartTheme'
import { use } from 'echarts/core'
import { BarChart, PieChart, LineChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, LegendComponent, GridComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import VChart from 'vue-echarts'
import { getOverviewStats, getTrendStats } from '@/api/stats'
import { getDashboardStats, type DashboardStats } from '@/api/work-stats'

use([BarChart, PieChart, LineChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent, CanvasRenderer])

// ── Tab state ──
const activeTab = ref('work-weekly')
const loading = ref(true)

// ── Kanban tab data ──
const overview = ref<any>(null)
const trend = ref<any[]>([])

// ── Work-weekly tab data ──
const dashData = ref<DashboardStats | null>(null)
const now = new Date()
const dashYear = ref(now.getFullYear())
const dashMonth = ref(now.getMonth() + 1)
const customMonth = ref<string | null>(null)

const quickMonth = ref('current')

function setMonth(y: number, m: number) {
  dashYear.value = y
  dashMonth.value = m
  fetchDashboard()
}

function onQuickMonth(val: string) {
  customMonth.value = null
  if (val === 'current') {
    setMonth(now.getFullYear(), now.getMonth() + 1)
  } else {
    const d = new Date(now.getFullYear(), now.getMonth() - 1, 1)
    setMonth(d.getFullYear(), d.getMonth() + 1)
  }
}

function onCustomMonth(val: string | null) {
  if (!val) return
  quickMonth.value = ''
  const [y, m] = val.split('-').map(Number)
  setMonth(y, m)
}

// ── Data fetching ──
async function fetchKanban() {
  try {
    const [ov, tr] = await Promise.all([getOverviewStats(), getTrendStats(30)])
    overview.value = ov
    trend.value = tr
  } catch {}
}

async function fetchDashboard() {
  try {
    const d = await getDashboardStats(dashYear.value, dashMonth.value)
    dashData.value = d
  } catch {}
}

onMounted(async () => {
  await Promise.all([fetchKanban(), fetchDashboard()])
  loading.value = false
})

watch(activeTab, (tab) => {
  if (tab === 'kanban' && !overview.value) fetchKanban()
  if (tab === 'work-weekly' && !dashData.value) fetchDashboard()
})

// ═══════════════════════════════════════
//  Kanban charts (existing, unchanged)
// ═══════════════════════════════════════

const chart = useChartTheme()
const hasKanbanData = computed(() => (overview.value?.total ?? 0) > 0)

const statCards = computed(() => [
  { key:'total', label:'总任务数', icon:'📋', value: overview.value?.total??0, bg:'var(--el-color-primary-light-9)', iconBg:'var(--el-color-primary)' },
  { key:'todo', label:'待处理', icon:'📥', value: overview.value?.status_counts?.todo??0, bg:'var(--el-color-primary-light-9)', iconBg:'var(--el-color-primary)' },
  { key:'prog', label:'进行中', icon:'⚡', value: overview.value?.status_counts?.in_progress??0, bg:'var(--el-color-warning-light-9)', iconBg:'var(--el-color-warning)' },
  { key:'done', label:'已完成', icon:'✅', value: overview.value?.status_counts?.done??0, bg:'var(--el-color-success-light-9)', iconBg:'var(--el-color-success)' },
])

const statusBarOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: '3%', right: '8%', bottom: '3%', containLabel: true },
  xAxis: { type: 'category', data: ['待处理', '进行中', '已完成'], axisLabel: { color: chart.textRegular.value } },
  yAxis: { type: 'value', minInterval: 1, axisLabel: { color: chart.textSecondary.value } },
  series: [{
    type: 'bar',
    data: [
      { value: overview.value?.status_counts?.todo ?? 0, itemStyle: { color: '#667eea', borderRadius: [6,6,0,0] } },
      { value: overview.value?.status_counts?.in_progress ?? 0, itemStyle: { color: '#e6a23c', borderRadius: [6,6,0,0] } },
      { value: overview.value?.status_counts?.done ?? 0, itemStyle: { color: '#67c23a', borderRadius: [6,6,0,0] } },
    ],
    barWidth: 50,
    label: { show: true, position: 'top', fontSize: 14, fontWeight: 700, color: chart.textPrimary.value },
  }],
}))

const priorityPieOption = computed(() => ({
  tooltip: { trigger: 'item', formatter: '{b}: {c} 个 ({d}%)' },
  legend: { bottom: 0, textStyle: { color: chart.textRegular.value, fontSize: 12 } },
  series: [{
    type: 'pie',
    radius: ['50%', '75%'],
    center: ['50%', '45%'],
    avoidLabelOverlap: false,
    itemStyle: { borderRadius: 6, borderColor: chart.bgColor.value, borderWidth: 3 },
    label: { show: false },
    emphasis: { label: { show: true, fontSize: 16, fontWeight: 'bold' } },
    data: [
      { value: overview.value?.priority_counts?.low ?? 0, name: '低优先级', itemStyle: { color: '#67c23a' } },
      { value: overview.value?.priority_counts?.medium ?? 0, name: '中优先级', itemStyle: { color: '#e6a23c' } },
      { value: overview.value?.priority_counts?.high ?? 0, name: '高优先级', itemStyle: { color: '#f56c6c' } },
    ],
  }],
}))

const trendLineOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: '3%', right: '5%', bottom: '3%', containLabel: true },
  xAxis: {
    type: 'category',
    data: trend.value.map((d: any) => d.date.slice(5)),
    axisLabel: { color: chart.textSecondary.value, fontSize: 11, rotate: 45 },
  },
  yAxis: { type: 'value', minInterval: 1, axisLabel: { color: chart.textSecondary.value } },
  series: [{
    type: 'line',
    data: trend.value.map((d: any) => d.count),
    smooth: true,
    lineStyle: { color: '#667eea', width: 3 },
    itemStyle: { color: '#667eea' },
    areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(102,126,234,0.25)' }, { offset: 1, color: 'rgba(102,126,234,0.02)' }] } },
    symbol: 'circle',
    symbolSize: 6,
  }],
}))

// ═══════════════════════════════════════
//  Work-Weekly charts
// ═══════════════════════════════════════

const TAG_COLORS = ['#6366f1', '#f56c6c', '#67c23a', '#e6a23c', '#8b5cf6', '#06b6d4', '#ec4899', '#f97316', '#14b8a6', '#a855f7']

const hasProjectHours = computed(() => (dashData.value?.project_hours ?? []).length > 0)
const hasTypeData = computed(() => {
  const tb = dashData.value?.type_breakdown
  return (tb?.task_hours ?? 0) > 0 || (tb?.work_order_hours ?? 0) > 0
})
const hasOverdue = computed(() => (dashData.value?.overdue_by_project ?? []).length > 0)
const hasTags = computed(() => (dashData.value?.tag_distribution ?? []).length > 0)

const overtimeHours = computed(() => {
  const total = dashData.value?.summary?.total_hours ?? 0
  const target = dashData.value?.period?.monthly_target ?? 0
  return Math.max(0, Math.round((total - target) * 10) / 10)
})

// Chart: 项目工时分布 (horizontal bar)
const projectHoursBarOption = computed(() => {
  const data = (dashData.value?.project_hours ?? []).slice(0, 10)
  return {
    tooltip: { trigger: 'axis', formatter: (p: any) => `${p[0].name}: ${p[0].value}h` },
    grid: { left: '3%', right: '12%', bottom: '3%', containLabel: true },
    xAxis: { type: 'value', axisLabel: { color: chart.textSecondary.value, formatter: '{value}h' } },
    yAxis: { type: 'category', data: data.map(d => d.project_name).reverse(), axisLabel: { color: chart.textRegular.value, fontSize: 11 }, inverse: true },
    series: [{
      type: 'bar',
      data: data.map(d => ({ value: d.hours, itemStyle: { color: d.project_color, borderRadius: [0, 6, 6, 0] } })).reverse(),
      barWidth: 20,
      label: { show: true, position: 'right', fontSize: 12, color: chart.textRegular.value, formatter: '{c}h' },
    }],
  }
})

// Chart: 任务 vs 工单工时占比 (donut)
const typePieOption = computed(() => {
  const tb = dashData.value?.type_breakdown
  const data = [
    { value: tb?.task_hours ?? 0, name: '任务', itemStyle: { color: '#6366f1' } },
    { value: tb?.work_order_hours ?? 0, name: '工单', itemStyle: { color: '#f56c6c' } },
  ]
  return {
    tooltip: { trigger: 'item', formatter: '{b}: {c}h ({d}%)' },
    legend: { bottom: 0, textStyle: { color: chart.textRegular.value, fontSize: 12 } },
    series: [{
      type: 'pie',
      radius: ['55%', '80%'],
      center: ['50%', '45%'],
      avoidLabelOverlap: false,
      itemStyle: { borderRadius: 6, borderColor: chart.bgColor.value, borderWidth: 3 },
      label: { show: false },
      emphasis: { label: { show: true, fontSize: 16, fontWeight: 'bold' } },
      data,
    }],
  }
})

// Chart: 超期任务统计 (bar)
const overdueBarOption = computed(() => {
  const data = dashData.value?.overdue_by_project ?? []
  return {
    tooltip: { trigger: 'axis', formatter: (p: any) => `${p[0].name}: ${p[0].value} 个超期任务` },
    grid: { left: '3%', right: '8%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: data.map(d => d.project_name), axisLabel: { color: chart.textRegular.value, fontSize: 11, rotate: data.length > 5 ? 30 : 0 } },
    yAxis: { type: 'value', minInterval: 1, axisLabel: { color: chart.textSecondary.value } },
    series: [{
      type: 'bar',
      data: data.map(d => ({ value: d.overdue_count, itemStyle: { color: d.project_color, borderRadius: [6, 6, 0, 0] } })),
      barWidth: 40,
      label: { show: true, position: 'top', fontSize: 14, fontWeight: 700, color: '#f56c6c' },
    }],
  }
})

// Chart: 标签分布 (donut)
const tagPieOption = computed(() => {
  const data = dashData.value?.tag_distribution ?? []
  return {
    tooltip: { trigger: 'item', formatter: '{b}: {c}h ({d}%)' },
    legend: { bottom: 0, textStyle: { color: chart.textRegular.value, fontSize: 11 } },
    series: [{
      type: 'pie',
      radius: ['45%', '72%'],
      center: ['50%', '45%'],
      avoidLabelOverlap: false,
      itemStyle: { borderRadius: 4, borderColor: chart.bgColor.value, borderWidth: 2 },
      label: { show: false },
      emphasis: { label: { show: true, fontSize: 13, fontWeight: 'bold' } },
      data: data.map((d, i) => ({ value: d.hours, name: d.tag, itemStyle: { color: TAG_COLORS[i % TAG_COLORS.length] } })),
    }],
  }
})

// Chart: 周饱和度趋势 (line)
const saturationTrendOption = computed(() => {
  const data = dashData.value?.saturation_trend ?? []
  return {
    tooltip: { trigger: 'axis', formatter: (p: any) => `${p[0].axisValue}: ${p[0].value}% (${dashData.value?.saturation_trend?.[p[0].dataIndex]?.total_hours ?? 0}h)` },
    grid: { left: '3%', right: '5%', bottom: '3%', containLabel: true },
    xAxis: {
      type: 'category',
      data: data.map(d => d.week_start.slice(5)),
      axisLabel: { color: chart.textSecondary.value, fontSize: 10, rotate: 45 },
    },
    yAxis: { type: 'value', axisLabel: { color: chart.textSecondary.value, formatter: '{value}%' } },
    series: [{
      type: 'line',
      data: data.map(d => d.saturation_pct),
      smooth: true,
      lineStyle: { color: '#6366f1', width: 2.5 },
      itemStyle: { color: '#6366f1' },
      areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(99,102,241,0.2)' }, { offset: 1, color: 'rgba(99,102,241,0.02)' }] } },
      symbol: 'circle',
      symbolSize: 6,
      markLine: {
        silent: true,
        data: [{ yAxis: 100, lineStyle: { color: '#e6a23c', type: 'dashed', width: 1.5 }, label: { formatter: '100%', fontSize: 10, color: '#e6a23c' } }],
      },
    }],
  }
})

// Chart: 任务创建趋势 (line)
const creationTrendOption = computed(() => {
  const data = dashData.value?.creation_trend ?? []
  return {
    tooltip: { trigger: 'axis', formatter: (p: any) => `${p[0].axisValue}: 创建 ${p[0].value} 个任务` },
    grid: { left: '3%', right: '5%', bottom: '3%', containLabel: true },
    xAxis: {
      type: 'category',
      data: data.map(d => d.week_start.slice(5)),
      axisLabel: { color: chart.textSecondary.value, fontSize: 10, rotate: 45 },
    },
    yAxis: { type: 'value', minInterval: 1, axisLabel: { color: chart.textSecondary.value } },
    series: [{
      type: 'line',
      data: data.map(d => d.count),
      smooth: true,
      lineStyle: { color: '#8b5cf6', width: 2.5 },
      itemStyle: { color: '#8b5cf6' },
      areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(139,92,246,0.2)' }, { offset: 1, color: 'rgba(139,92,246,0.02)' }] } },
      symbol: 'circle',
      symbolSize: 6,
    }],
  }
})

// Chart: 月度工时汇总 (stacked bar)
const weeklyStackOption = computed(() => {
  const data = dashData.value?.weekly_breakdown ?? []
  return {
    tooltip: { trigger: 'axis', formatter: (p: any) => `${p[0].axisValue}<br/>${p.map((s: any) => `${s.seriesName}: ${s.value}h`).join('<br/>')}` },
    legend: { bottom: 0, textStyle: { color: chart.textRegular.value, fontSize: 12 } },
    grid: { left: '3%', right: '5%', bottom: '10%', containLabel: true },
    xAxis: { type: 'category', data: data.map(d => d.week_start.slice(5)), axisLabel: { color: chart.textSecondary.value, fontSize: 11 } },
    yAxis: { type: 'value', axisLabel: { color: chart.textSecondary.value, formatter: '{value}h' } },
    series: [
      {
        name: '任务',
        type: 'bar',
        stack: 'total',
        data: data.map(d => d.task_hours),
        itemStyle: { color: '#6366f1', borderRadius: 0 },
        barWidth: 40,
        label: { show: true, position: 'inside', fontSize: 11, color: '#fff' },
      },
      {
        name: '工单',
        type: 'bar',
        stack: 'total',
        data: data.map(d => d.work_order_hours),
        itemStyle: { color: '#f56c6c', borderRadius: [6, 6, 0, 0] },
        label: { show: true, position: 'inside', fontSize: 11, color: '#fff' },
      },
    ],
  }
})
</script>

<style scoped>
.dashboard-tabs :deep(.el-tabs__header) {
  margin-bottom: 20px;
}
.dashboard-tabs :deep(.el-tabs__nav-wrap::after) {
  height: 1px;
  background-color: var(--el-border-color-light);
}
.dashboard-tabs :deep(.el-tabs__item) {
  font-size: 15px;
  font-weight: 600;
  padding: 0 24px;
  height: 42px;
  line-height: 42px;
  color: var(--el-text-color-regular);
}
.dashboard-tabs :deep(.el-tabs__item.is-active) {
  color: var(--el-color-primary);
}
.dashboard-tabs :deep(.el-tabs__active-bar) {
  height: 3px;
  border-radius: 2px;
}
.tab-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.chart-empty {
  height: 300px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--el-text-color-placeholder);
  font-size: 13px;
  gap: 6px;
}
.empty-icon {
  font-size: 32px;
  opacity: 0.5;
  margin-bottom: 4px;
}
.empty-hint {
  font-size: 12px;
  opacity: 0.7;
}
</style>
