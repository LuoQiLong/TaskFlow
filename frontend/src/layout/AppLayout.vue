<template>
  <el-container style="height:100vh">
    <el-header height="64px" style="background:var(--el-bg-color);border-bottom:1px solid var(--el-border-color-light);display:flex;align-items:center;justify-content:space-between;padding:0 24px;box-shadow:0 1px 4px rgba(0,0,0,0.04)">
      <div style="display:flex;align-items:center;gap:20px">
        <div style="display:flex;align-items:center;gap:8px">
          <div style="width:32px;height:32px;border-radius:8px;background:linear-gradient(135deg,#6366f1,#8b5cf6);display:flex;align-items:center;justify-content:center">
            <el-icon color="#fff" size="18"><List /></el-icon>
          </div>
          <span style="font-size:18px;font-weight:700;color:var(--el-text-color-primary)">TaskFlow</span>
        </div>
        <div style="display:flex;gap:4px;background:var(--el-fill-color-light);border-radius:8px;padding:3px">
          <button v-for="item in navItems" :key="item.path" @click="$router.push(item.path)"
            :style="{ padding:'8px 18px', border:'none', borderRadius:'6px', cursor:'pointer', fontSize:'14px', fontWeight:600, transition:'all 0.2s',
              background: isActive(item.path) ? 'var(--el-bg-color)' : 'transparent',
              color: isActive(item.path) ? '#6366f1' : 'var(--el-text-color-secondary)',
              boxShadow: isActive(item.path) ? '0 1px 3px rgba(0,0,0,0.06)' : 'none' }">
            <span style="margin-right:4px">{{ item.icon }}</span>{{ item.label }}
          </button>
        </div>
      </div>
      <div style="display:flex;align-items:center;gap:12px">
        <el-button circle @click="toggleDark">
          <el-icon><Moon v-if="isDark" /><Sunny v-else /></el-icon>
        </el-button>
        <div style="display:flex;align-items:center;background:var(--el-fill-color-light);border-radius:22px;padding:3px 12px 3px 3px;cursor:default">
          <el-avatar :size="30" :style="{ background: 'linear-gradient(135deg,#6366f1,#8b5cf6)', fontSize:'14px', fontWeight:700 }">
            {{ (auth.user?.email || '?')[0].toUpperCase() }}
          </el-avatar>
          <span style="font-size:14px;color:var(--el-text-color-regular);padding:0 8px;font-weight:600">{{ auth.user?.email }}</span>
        </div>
        <el-button circle @click="auth.logout();$router.push('/login')" title="退出登录">
          <el-icon><SwitchButton /></el-icon>
        </el-button>
      </div>
    </el-header>
    <el-main style="padding:0;background:var(--el-bg-color-page)">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { ref, watchEffect } from 'vue'
import { useRoute } from 'vue-router'
import { Moon, Sunny, SwitchButton } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const auth = useAuthStore()
const isDark = ref(false)

const navItems = [
  { path: '/app/kanban', label: '任务看板', icon: '📋' },
  { path: '/app/dashboard', label: '数据图表', icon: '📊' },
  { path: '/app/work-weekly', label: '工作周报', icon: '📆' },
]

function isActive(path: string) { return route.path === path }

// Dark mode
const stored = localStorage.getItem('theme')
if (stored === 'dark') {
  isDark.value = true
  document.documentElement.classList.add('dark')
}
function toggleDark() {
  isDark.value = !isDark.value
  document.documentElement.classList.toggle('dark', isDark.value)
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
}
</script>
