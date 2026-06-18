import * as XLSX from 'xlsx-js-style'
import type { WorkItem } from '@/api/work-items'
import type { WeeklyStats, MonthlyStats, TrendPoint } from '@/api/work-stats'

// ── Helpers ──

const TYPE_MAP: Record<string, string> = { task: '任务', work_order: '工单' }
const STATUS_MAP: Record<string, string> = { todo: '待处理', in_progress: '进行中', done: '已完成' }
const PRIORITY_MAP: Record<string, string> = { high: '高', medium: '中', low: '低' }

// Theme colors
const HEADER_FILL = '3271AE'       // muted blue header bg
const HEADER_FONT = 'FFFFFF'       // white text
const ZEBRA_EVEN = 'F1F5F9'       // light slate for even rows
const ZEBRA_ODD = 'FFFFFF'        // white for odd rows
const SUMMARY_FILL = 'FFF7ED'     // soft orange summary
const SECTION_FILL = 'F1F5F9'     // light slate section headers (Sheet2)

function fmtDate(d?: string | null): string {
  if (!d) return ''
  return d.slice(0, 10)
}

function isOverdue(item: WorkItem): boolean {
  if (!item.end_date || item.status === 'done') return false
  return new Date() > new Date(item.end_date)
}

// ── Styling helpers ──

function headerStyle() {
  return {
    fill: { fgColor: { rgb: HEADER_FILL } },
    font: { color: { rgb: HEADER_FONT }, bold: true, sz: 10 },
    alignment: { horizontal: 'center', vertical: 'center' },
    border: {
      top: { style: 'thin', color: { rgb: 'D4D4D8' } },
      bottom: { style: 'thin', color: { rgb: 'D4D4D8' } },
      left: { style: 'thin', color: { rgb: 'D4D4D8' } },
      right: { style: 'thin', color: { rgb: 'D4D4D8' } },
    },
  }
}

function dataStyle(isEven: boolean) {
  return {
    fill: { fgColor: { rgb: isEven ? ZEBRA_EVEN : ZEBRA_ODD } },
    font: { sz: 10 },
    border: {
      top: { style: 'thin', color: { rgb: 'E5E7EB' } },
      bottom: { style: 'thin', color: { rgb: 'E5E7EB' } },
      left: { style: 'thin', color: { rgb: 'E5E7EB' } },
      right: { style: 'thin', color: { rgb: 'E5E7EB' } },
    },
  }
}

function summaryStyle() {
  return {
    fill: { fgColor: { rgb: SUMMARY_FILL } },
    font: { bold: true, sz: 10 },
    border: {
      top: { style: 'thin', color: { rgb: 'E5E7EB' } },
      bottom: { style: 'thin', color: { rgb: 'E5E7EB' } },
      left: { style: 'thin', color: { rgb: 'E5E7EB' } },
      right: { style: 'thin', color: { rgb: 'E5E7EB' } },
    },
  }
}

function sectionStyle() {
  return {
    fill: { fgColor: { rgb: SECTION_FILL } },
    font: { bold: true, sz: 11 },
    alignment: { horizontal: 'left', vertical: 'center' },
  }
}

function labelStyle() {
  return {
    font: { bold: true, sz: 10 },
    fill: { fgColor: { rgb: 'F8FAFC' } },
    border: {
      right: { style: 'thin', color: { rgb: 'E5E7EB' } },
    },
  }
}

function valueStyle() {
  return {
    font: { sz: 10 },
    fill: { fgColor: { rgb: 'FFFFFF' } },
  }
}

// Apply styles to a sheet row-by-row
function styleHeaders(sheet: XLSX.WorkSheet, colCount: number) {
  const cols = colNumToLetters(colCount)
  for (let c = 0; c < colCount; c++) {
    const addr = cols[c] + '1'
    if (sheet[addr]) sheet[addr].s = headerStyle()
  }
}

function styleDataRows(sheet: XLSX.WorkSheet, startRow: number, endRow: number, colCount: number) {
  const cols = colNumToLetters(colCount)
  for (let r = startRow; r <= endRow; r++) {
    const isEven = (r - startRow) % 2 === 1
    for (let c = 0; c < colCount; c++) {
      const addr = cols[c] + String(r)
      if (sheet[addr]) sheet[addr].s = dataStyle(isEven)
    }
  }
}

function styleRow(sheet: XLSX.WorkSheet, row: number, colCount: number, sty: object) {
  const cols = colNumToLetters(colCount)
  for (let c = 0; c < colCount; c++) {
    const addr = cols[c] + String(row)
    if (sheet[addr]) sheet[addr].s = sty
  }
}

function colNumToLetters(count: number): string[] {
  const result: string[] = []
  for (let i = 0; i < count; i++) {
    let n = i
    let s = ''
    do {
      s = String.fromCharCode(65 + (n % 26)) + s
      n = Math.floor(n / 26) - 1
    } while (n >= 0)
    result.push(s)
  }
  return result
}

function autoColWidth(sheet: XLSX.WorkSheet, colCount: number) {
  sheet['!cols'] = Array.from({ length: colCount }, () => ({ wch: 14 }))
}

// ── Sheet 1: 工作项清单 ──

function buildSheet1(
  items: WorkItem[],
  projectNameMap: Map<number, string>,
  itemHoursMap: Map<number, number>,
): XLSX.WorkSheet {
  const headers = ['序号', '项目', '类型', '标题', '状态', '优先级', '预估工时(h)', '已记录工时(h)', '开始时间', '结束时间', '截止日期', '标签', '是否超期']
  const colCount = headers.length

  const rows: (string | number)[][] = [headers]

  let totalEstimated = 0
  let totalLogged = 0

  for (let i = 0; i < items.length; i++) {
    const item = items[i]
    const logged = itemHoursMap.get(item.id) || 0
    totalEstimated += item.estimated_hours || 0
    totalLogged += logged
    rows.push([
      i + 1,
      projectNameMap.get(item.project_id) || `项目#${item.project_id}`,
      TYPE_MAP[item.type] || item.type,
      item.title,
      STATUS_MAP[item.status] || item.status,
      PRIORITY_MAP[item.priority] || item.priority,
      item.estimated_hours ?? '',
      logged || '',
      fmtDate(item.start_date),
      fmtDate(item.end_date),
      fmtDate(item.due_date),
      (item.tags || []).join(', '),
      isOverdue(item) ? '是' : '否',
    ])
  }

  // Empty separator + summary row
  rows.push([''])
  rows.push(['合计', '', '', `${items.length} 项`, '', '', totalEstimated || '', totalLogged || '', '', '', '', '', ''])

  const sheet = XLSX.utils.aoa_to_sheet(rows)

  // Apply styles
  styleHeaders(sheet, colCount)                          // Row 1: dark slate header
  if (items.length > 0) {
    styleDataRows(sheet, 2, 1 + items.length, colCount)  // Data rows: zebra
  }
  styleRow(sheet, 1 + items.length + 2, colCount, summaryStyle()) // Summary row

  autoColWidth(sheet, colCount)
  if (sheet['!cols']) sheet['!cols'][3] = { wch: 40 }   // wider title column
  return sheet
}

// ── Sheet 2: 工时摘要 ──

function buildSheet2(
  periodLabel: string,
  viewMode: 'week' | 'month',
  stats: WeeklyStats | MonthlyStats | null,
): XLSX.WorkSheet {
  const rows: (string | number)[][] = []
  let rowIdx = 0

  // Title
  rows.push(['报告周期', periodLabel])
  rows.push(['视图模式', viewMode === 'week' ? '周视图' : '月视图'])
  rows.push([])

  if (stats) {
    const target = 'weekly_target' in stats ? stats.weekly_target : stats.monthly_target

    rows.push(['── 饱和度 ──'])
    rows.push(['总工时', `${stats.total_hours}h`])
    rows.push(['目标工时', `${target}h`])
    rows.push(['饱和度', `${stats.saturation_pct}%`])
    rows.push(['剩余工时', `${stats.remaining_hours}h`])
    rows.push([])

    rows.push(['── 类型分布 ──'])
    rows.push(['任务工时', `${stats.task_hours}h`])
    rows.push(['工单工时', `${stats.work_order_hours}h`])
    rows.push([])

    if (stats.project_breakdown.length > 0) {
      rows.push(['── 项目分布 ──'])
      rows.push(['项目名称', '工时', '占比'])
      const total = stats.total_hours || 1
      for (const p of stats.project_breakdown) {
        rows.push([p.project_name, `${p.hours}h`, `${Math.round((p.hours / total) * 100)}%`])
      }
      rows.push([])
    }

    if (viewMode === 'month' && 'weekly_breakdown' in stats && stats.weekly_breakdown?.length) {
      rows.push(['── 周度明细 ──'])
      rows.push(['周起始', '总工时', '任务工时', '工单工时'])
      for (const w of stats.weekly_breakdown) {
        rows.push([fmtDate(w.week_start), `${w.total_hours}h`, `${w.task_hours}h`, `${w.work_order_hours}h`])
      }
      rows.push([])
    }
  } else {
    rows.push(['(无统计数据)'])
  }

  const sheet = XLSX.utils.aoa_to_sheet(rows)

  // Apply styles to Sheet2
  let r = 1
  while (r <= rows.length) {
    const rowData = rows[r - 1]
    if (rowData.length === 0) { r++; continue }

    const firstCell = String(rowData[0] ?? '')

    if (firstCell.startsWith('──')) {
      // Section header
      styleRow(sheet, r, 3, sectionStyle())
    } else if (rowData.length >= 2 && rowData[1] === '工时' && !rowData[0].toString().startsWith('项目')) {
      // Sub-table header (项目名称 / 工时 / 占比, 周起始 / 总工时 / ...)
      styleRow(sheet, r, 3, {
        fill: { fgColor: { rgb: 'F0F0FF' } },
        font: { bold: true, sz: 10 },
        border: {
          bottom: { style: 'thin', color: { rgb: 'D4D4D8' } },
        },
      })
    } else if (firstCell === '报告周期' || firstCell === '视图模式') {
      styleRow(sheet, r, 2, labelStyle())
      // Value cell
      const bAddr = colNumToLetters(2)[1] + String(r)
      if (sheet[bAddr]) sheet[bAddr].s = valueStyle()
    } else if (['总工时', '目标工时', '饱和度', '剩余工时', '任务工时', '工单工时'].includes(firstCell as string)) {
      styleRow(sheet, r, 2, labelStyle())
      const bAddr = colNumToLetters(2)[1] + String(r)
      if (sheet[bAddr]) sheet[bAddr].s = valueStyle()
    }
    r++
  }

  autoColWidth(sheet, 4)
  return sheet
}

// ── Sheet 3: 趋势数据 ──

function buildSheet3(trendData: TrendPoint[]): XLSX.WorkSheet {
  const headers = ['周起始', '周结束', '已记录工时', '计划工时', '总工时', '饱和度%']
  const colCount = headers.length

  const rows: (string | number)[][] = [headers]

  for (const t of trendData) {
    rows.push([
      fmtDate(t.week_start),
      fmtDate(t.week_end),
      t.logged_hours != null ? `${t.logged_hours}h` : '',
      t.planned_hours != null ? `${t.planned_hours}h` : '',
      t.total_hours != null ? `${t.total_hours}h` : '',
      t.saturation_pct != null ? `${t.saturation_pct}%` : '',
    ])
  }

  const sheet = XLSX.utils.aoa_to_sheet(rows)

  // Apply styles
  styleHeaders(sheet, colCount)                         // Row 1: purple header
  if (trendData.length > 0) {
    styleDataRows(sheet, 2, 1 + trendData.length, colCount) // Data rows: zebra
  }

  autoColWidth(sheet, colCount)
  return sheet
}

// ── Main export ──

export interface ExportData {
  periodLabel: string
  viewMode: 'week' | 'month'
  items: WorkItem[]
  projectNameMap: Map<number, string>
  itemHoursMap: Map<number, number>
  currentStats: WeeklyStats | MonthlyStats | null
  trendData: TrendPoint[]
}

export function exportWorkWeekly(data: ExportData): void {
  const wb = XLSX.utils.book_new()

  const sheet1 = buildSheet1(data.items, data.projectNameMap, data.itemHoursMap)
  const sheet2 = buildSheet2(data.periodLabel, data.viewMode, data.currentStats)
  const sheet3 = buildSheet3(data.trendData)

  XLSX.utils.book_append_sheet(wb, sheet1, '工作项清单')
  XLSX.utils.book_append_sheet(wb, sheet2, '工时摘要')
  XLSX.utils.book_append_sheet(wb, sheet3, '趋势数据')

  let filename: string
  if (data.viewMode === 'week') {
    const match = data.periodLabel.match(/第(\d+)周/)
    const weekNum = match ? match[1] : ''
    filename = `工作周报_第${weekNum}周.xlsx`
  } else {
    filename = `工作月报_${data.periodLabel.replace(/\//g, '-')}.xlsx`
  }

  XLSX.writeFile(wb, filename)
}
