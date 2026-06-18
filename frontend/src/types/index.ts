export const STATUS_MAP: Record<string, string> = {
  todo: '待处理',
  in_progress: '进行中',
  done: '已完成',
  archived: '已归档',
}
export const PRIORITY_MAP: Record<string, string> = {
  low: '低优先级',
  medium: '中优先级',
  high: '高优先级',
}
export const STATUS_OPTIONS = Object.entries(STATUS_MAP).map(([v, l]) => ({ value: v, label: l }))
export const PRIORITY_OPTIONS = Object.entries(PRIORITY_MAP).map(([v, l]) => ({ value: v, label: l }))
