<template>
  <el-container style="height:100vh">
    <el-header height="64px" style="background:var(--el-bg-color);border-bottom:1px solid var(--el-border-color-light);display:flex;align-items:center;justify-content:space-between;padding:0 24px;box-shadow:var(--el-box-shadow-lighter)">
      <div style="display:flex;align-items:center;gap:20px">
        <div @click="router.push('/app/work-weekly')" style="display:flex;align-items:center;gap:8px;cursor:pointer">
          <img src="/logo_taskflow.png" alt="TaskFlow" style="height:32px" />
          <span style="font-size:18px;font-weight:700;color:var(--el-text-color-primary)">TaskFlow</span>
        </div>
        <div style="display:flex;gap:4px;background:var(--el-fill-color-light);border-radius:8px;padding:3px">
          <button v-for="item in navItems" :key="item.path" @click="$router.push(item.path)"
            :style="{ padding:'8px 18px', border:'none', borderRadius:'6px', cursor:'pointer', fontSize:'14px', fontWeight:600, transition:'all 0.2s',
              background: isActive(item.path) ? 'var(--el-bg-color)' : 'transparent',
              color: isActive(item.path) ? '#6366f1' : 'var(--el-text-color-secondary)',
              boxShadow: isActive(item.path) ? 'var(--el-box-shadow-light)' : 'none' }">
            <span style="margin-right:4px">{{ item.icon }}</span>{{ item.label }}
          </button>
        </div>
      </div>
      <div style="display:flex;align-items:center;gap:12px">
        <!-- Admin scope switcher -->
        <el-select v-if="auth.isAdmin" :model-value="scope.targetUserId" @change="onScopeChange"
          class="scope-select" size="default" placeholder="👤 我自己" filterable>
          <el-option :value="0" label="👤 我自己"/>
          <el-option :value="-1" label="👥 全部用户"/>
          <el-option-group v-if="otherUsers.length" label="— 切换至指定用户 —">
            <el-option v-for="u in otherUsers" :key="u.id" :value="u.id"
              :label="(u.display_name || u.email) + ' (' + u.email + ')'"/>
          </el-option-group>
        </el-select>
        <!-- Admin: users management -->
        <button v-if="auth.isAdmin" @click="$router.push('/app/admin/users')"
          :style="{ padding:'6px 14px', border:'none', borderRadius:'8px', cursor:'pointer', fontSize:'13px', fontWeight:600,
            background: isActive('/app/admin/users') ? 'var(--el-color-primary-light-9)' : 'transparent',
            color: isActive('/app/admin/users') ? '#6366f1' : 'var(--el-text-color-secondary)' }">
          👥 用户管理
        </button>
        <el-button circle @click="toggleDark">
          <el-icon><Moon v-if="isDark" /><Sunny v-else /></el-icon>
        </el-button>
        <div @click="$router.push('/app/profile')"
          style="display:flex;align-items:center;background:var(--el-fill-color-light);border-radius:22px;padding:3px 12px 3px 3px;cursor:pointer"
          title="个人设置">
          <el-avatar v-if="auth.user?.avatar_url" :src="auth.user.avatar_url" :size="30"/>
          <el-avatar v-else :size="30" :style="{ background: 'linear-gradient(135deg,#6366f1,#8b5cf6)', fontSize:'14px', fontWeight:700 }">
            {{ (auth.user?.display_name || auth.user?.email || '?')[0].toUpperCase() }}
          </el-avatar>
          <span style="font-size:14px;color:var(--el-text-color-regular);padding:0 8px;font-weight:600">{{ auth.user?.display_name || auth.user?.email }}</span>
        </div>
        <el-button circle @click="auth.logout();$router.push('/login')" title="退出登录">
          <el-icon><SwitchButton /></el-icon>
        </el-button>
      </div>
    </el-header>
    <el-main style="padding:0;background:var(--el-bg-color-page);position:relative;overflow-y:auto">
      <!-- 左上角 紫色光晕 -->
      <div style="position:absolute;top:-200px;left:-200px;width:800px;height:800px;border-radius:50%;background:radial-gradient(circle, rgba(139,92,246,0.10) 0%, transparent 60%);pointer-events:none;z-index:0"/>
      <!-- 右下角 蓝色光晕 -->
      <div style="position:absolute;bottom:-180px;right:-180px;width:700px;height:700px;border-radius:50%;background:radial-gradient(circle, rgba(59,130,246,0.10) 0%, transparent 60%);pointer-events:none;z-index:0"/>
      <div style="position:relative;z-index:1;min-height:calc(100vh - 64px)">
        <router-view />
      </div>
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Moon, Sunny, SwitchButton } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { useScopeStore } from '@/stores/scope'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const scope = useScopeStore()
const isDark = ref(false)

const navItems = [
  { path: '/app/kanban', label: '任务看板', icon: '📋' },
  { path: '/app/dashboard', label: '数据图表', icon: '📊' },
  { path: '/app/work-weekly', label: '工作周报', icon: '📆' },
]

const otherUsers = computed(() => scope.allUsers.filter(u => u.id !== auth.user?.id))

function isActive(path: string) { return route.path === path }

function onScopeChange(val: number) {
  scope.setScope(val)
  router.go(0)
}

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

onMounted(async () => {
  await auth.fetchProfile()
  if (auth.isAdmin) {
    await scope.loadAllUsers()
  }
})
</script>

<style scoped>
.scope-select {
  width: 170px;
}
.scope-select :deep(.el-input__wrapper) {
  border-radius: 10px;
  background: var(--el-color-primary-light-9);
  border-color: var(--el-color-primary-light-5);
  box-shadow: none;
  transition: all 0.25s;
}
.scope-select :deep(.el-input__wrapper:hover) {
  border-color: var(--el-color-primary);
  background: var(--el-color-primary-light-8);
}
.scope-select :deep(.el-input__inner) {
  font-weight: 600;
  color: var(--el-color-primary);
}
</style>
