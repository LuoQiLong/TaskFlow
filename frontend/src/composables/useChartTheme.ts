import { ref, watch } from 'vue'

// Reactive CSS variable reader for ECharts
const textPrimary = ref('')
const textRegular = ref('')
const textSecondary = ref('')
const textPlaceholder = ref('')
const bgColor = ref('')
const borderLight = ref('')
const fillLight = ref('')
const borderLighter = ref('')

function readVars() {
  const root = document.documentElement
  const style = getComputedStyle(root)
  textPrimary.value = style.getPropertyValue('--el-text-color-primary').trim() || '#303133'
  textRegular.value = style.getPropertyValue('--el-text-color-regular').trim() || '#606266'
  textSecondary.value = style.getPropertyValue('--el-text-color-secondary').trim() || '#909399'
  textPlaceholder.value = style.getPropertyValue('--el-text-color-placeholder').trim() || '#c0c4cc'
  bgColor.value = style.getPropertyValue('--el-bg-color').trim() || '#ffffff'
  borderLight.value = style.getPropertyValue('--el-border-color-light').trim() || '#e4e7ed'
  fillLight.value = style.getPropertyValue('--el-fill-color-light').trim() || '#f0f0f0'
  borderLighter.value = style.getPropertyValue('--el-border-color-lighter').trim() || '#ebeef5'
}

// Read once on init
readVars()

// Watch for dark class changes
if (typeof MutationObserver !== 'undefined') {
  const observer = new MutationObserver(() => readVars())
  observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] })
}

// Also watch for localStorage theme changes
watch(() => localStorage.getItem('theme'), () => {
  // Small delay to let Element Plus update CSS vars
  setTimeout(readVars, 100)
})

export function useChartTheme() {
  return { textPrimary, textRegular, textSecondary, textPlaceholder, bgColor, borderLight, fillLight, borderLighter }
}
