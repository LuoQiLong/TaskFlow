<template>
  <div class="login-bg" style="min-height:100vh;display:flex;align-items:center;justify-content:center">
    <el-card style="width:420px;border-radius:16px" :body-style="{ padding: '40px' }">
      <div style="text-align:center;margin-bottom:24px">
        <h2>创建账号</h2>
        <p style="color:var(--el-text-color-secondary);font-size:14px">开始管理你的任务</p>
      </div>
      <el-form @submit.prevent="handleSubmit" :model="form">
        <el-form-item label="邮箱" :error="errors.email">
          <el-input v-model="form.email" placeholder="请输入邮箱" size="large"/>
        </el-form-item>
        <el-form-item label="密码" :error="errors.password">
          <el-input v-model="form.password" type="password" placeholder="至少6位" size="large" show-password/>
        </el-form-item>
        <el-form-item label="确认密码" :error="errors.confirm">
          <el-input v-model="form.confirm" type="password" placeholder="再次输入" size="large" show-password/>
        </el-form-item>
        <el-button type="primary" native-type="submit" size="large" :loading="auth.isLoading" style="width:100%">注册</el-button>
      </el-form>
      <div style="text-align:center;margin-top:16px">
        <el-button link type="primary" @click="$router.push('/login')">已有账号？登录</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
const router = useRouter(); const auth = useAuthStore()
const form = reactive({ email: '', password: '', confirm: '' })
const errors = reactive({ email: '', password: '', confirm: '' })

async function handleSubmit() {
  errors.email = ''; errors.password = ''; errors.confirm = ''
  if (!form.email) { errors.email = '请输入邮箱'; return }
  if (!form.password || form.password.length < 6) { errors.password = '密码至少6位'; return }
  if (form.password !== form.confirm) { errors.confirm = '两次密码不一致'; return }
  try { await auth.register(form.email, form.password); router.push('/app/kanban') } catch {}
}
</script>
