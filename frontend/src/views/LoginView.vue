<template>
  <div style="min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;background:var(--el-bg-color-page);position:relative;overflow:hidden">
    <!-- 左上角 紫色光晕 -->
    <div style="position:absolute;top:-200px;left:-200px;width:800px;height:800px;border-radius:50%;background:radial-gradient(circle, rgba(139,92,246,0.12) 0%, transparent 60%);pointer-events:none"/>
    <!-- 右下角 蓝色光晕 -->
    <div style="position:absolute;bottom:-180px;right:-180px;width:700px;height:700px;border-radius:50%;background:radial-gradient(circle, rgba(59,130,246,0.12) 0%, transparent 60%);pointer-events:none"/>

    <!-- Logo 在卡片外面 -->
    <div style="text-align:center;margin-bottom:24px;position:relative;z-index:1">
      <div style="width:52px;height:52px;border-radius:12px;background:linear-gradient(135deg,#8b5cf6,#6366f1);display:inline-flex;align-items:center;justify-content:center;margin-bottom:12px;box-shadow:0 8px 24px rgba(99,102,241,0.3)">
        <el-icon size="26" color="#fff"><List /></el-icon>
      </div>
      <h1 style="font-size:26px;font-weight:700;color:var(--el-text-color-primary);margin:0;letter-spacing:-0.5px">TaskFlow</h1>
      <p style="font-size:13px;color:var(--el-text-color-secondary);margin:4px 0 0">简洁高效的任务管理看板</p>
    </div>

    <!-- 卡片 -->
    <el-card style="width:420px;border-radius:16px;box-shadow:var(--el-box-shadow-light);position:relative;z-index:1" :body-style="{ padding: '36px 36px 28px' }">
      <!-- Tabs -->
      <div style="display:flex;background:var(--el-fill-color-light);border-radius:10px;padding:4px;margin-bottom:24px">
        <div v-for="t in tabs" :key="t.key"
          @click="activeTab = t.key"
          :style="{
            flex:1, textAlign:'center', padding:'9px 0', borderRadius:'8px', cursor:'pointer',
            fontSize:'14px', fontWeight:600, transition:'all 0.25s',
            background: activeTab === t.key ? 'var(--el-bg-color)' : 'transparent',
            color: activeTab === t.key ? '#6366f1' : '#909399',
            boxShadow: activeTab === t.key ? 'var(--el-box-shadow-light)' : 'none'
          }"
        >{{ t.label }}</div>
      </div>

      <el-alert v-if="auth.error" :title="auth.error" type="error" show-icon :closable="false" style="margin-bottom:16px"/>

      <!-- Login -->
      <el-form v-if="activeTab==='login'" @submit.prevent="handleLogin" :model="loginForm" label-position="top">
        <el-form-item label="邮箱" :error="loginErrors.email">
          <el-input v-model="loginForm.email" placeholder="请输入邮箱" :prefix-icon="Message" size="large"/>
        </el-form-item>
        <el-form-item label="密码" :error="loginErrors.password">
          <el-input v-model="loginForm.password" type="password" placeholder="请输入密码" :prefix-icon="Lock" show-password size="large"/>
        </el-form-item>
        <el-button type="primary" native-type="submit" size="large" :loading="auth.isLoading"
          style="width:100%;background:linear-gradient(135deg,#6366f1,#8b5cf6);border:none;border-radius:10px;height:44px;font-size:15px;font-weight:600">
          登 录
        </el-button>
        <div style="text-align:right;margin-top:12px">
          <el-button link type="primary" @click="router.push('/forgot-password')">忘记密码？</el-button>
        </div>
      </el-form>

      <!-- Register -->
      <el-form v-else @submit.prevent="handleRegister" :model="registerForm" label-position="top">
        <el-form-item label="邮箱" :error="regErrors.email">
          <el-input v-model="registerForm.email" placeholder="请输入邮箱" :prefix-icon="Message" size="large"/>
        </el-form-item>
        <el-form-item label="密码" :error="regErrors.password">
          <el-input v-model="registerForm.password" type="password" placeholder="至少6位密码" :prefix-icon="Lock" show-password size="large"/>
        </el-form-item>
        <el-form-item label="确认密码" :error="regErrors.confirm">
          <el-input v-model="registerForm.confirm" type="password" placeholder="再次输入密码" :prefix-icon="Lock" show-password size="large"/>
        </el-form-item>
        <el-button type="primary" native-type="submit" size="large" :loading="auth.isLoading"
          style="width:100%;background:linear-gradient(135deg,#6366f1,#8b5cf6);border:none;border-radius:10px;height:44px;font-size:15px;font-weight:600">
          注 册
        </el-button>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { Message, Lock } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

const tabs = [{ key: 'login', label: '登录' }, { key: 'register', label: '注册' }]
const activeTab = ref('login')

const loginForm = reactive({ email: '', password: '' })
const loginErrors = reactive({ email: '', password: '' })

async function handleLogin() {
  loginErrors.email = ''; loginErrors.password = ''
  if (!loginForm.email) { loginErrors.email = '请输入邮箱'; return }
  if (!loginForm.password) { loginErrors.password = '请输入密码'; return }
  try { await auth.login(loginForm.email, loginForm.password); router.push('/app/kanban') } catch {}
}

const registerForm = reactive({ email: '', password: '', confirm: '' })
const regErrors = reactive({ email: '', password: '', confirm: '' })

async function handleRegister() {
  regErrors.email = ''; regErrors.password = ''; regErrors.confirm = ''
  if (!registerForm.email) { regErrors.email = '请输入邮箱'; return }
  if (!registerForm.password) { regErrors.password = '请输入密码'; return }
  if (registerForm.password.length < 6) { regErrors.password = '密码至少6位'; return }
  if (registerForm.password !== registerForm.confirm) { regErrors.confirm = '两次密码不一致'; return }
  try { await auth.register(registerForm.email, registerForm.password); router.push('/app/kanban') } catch {}
}
</script>
