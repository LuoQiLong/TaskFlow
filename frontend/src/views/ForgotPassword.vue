<template>
  <div style="min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;background:var(--el-bg-color-page);position:relative;overflow:hidden">
    <!-- 左上角 紫色光晕 -->
    <div style="position:absolute;top:-200px;left:-200px;width:800px;height:800px;border-radius:50%;background:radial-gradient(circle, rgba(139,92,246,0.12) 0%, transparent 60%);pointer-events:none"/>
    <!-- 右下角 蓝色光晕 -->
    <div style="position:absolute;bottom:-180px;right:-180px;width:700px;height:700px;border-radius:50%;background:radial-gradient(circle, rgba(59,130,246,0.12) 0%, transparent 60%);pointer-events:none"/>

    <!-- Logo -->
    <div style="text-align:center;margin-bottom:24px;position:relative;z-index:1">
      <div style="width:52px;height:52px;border-radius:12px;background:linear-gradient(135deg,#8b5cf6,#6366f1);display:inline-flex;align-items:center;justify-content:center;margin-bottom:12px;box-shadow:0 8px 24px rgba(99,102,241,0.3)">
        <el-icon size="26" color="#fff"><List /></el-icon>
      </div>
      <h1 style="font-size:26px;font-weight:700;color:var(--el-text-color-primary);margin:0;letter-spacing:-0.5px">TaskFlow</h1>
      <p style="font-size:13px;color:var(--el-text-color-secondary);margin:4px 0 0">找回密码</p>
    </div>

    <!-- 卡片 -->
    <el-card style="width:420px;border-radius:16px;box-shadow:var(--el-box-shadow-light);position:relative;z-index:1" :body-style="{ padding: '36px 36px 28px' }">

      <!-- Step 1: 输入邮箱 -->
      <div v-if="!emailSent">
        <h2 style="font-size:18px;font-weight:700;color:var(--el-text-color-primary);margin:0 0 4px">忘记密码？</h2>
        <p style="font-size:13px;color:var(--el-text-color-secondary);margin:0 0 24px">输入注册邮箱，我们将发送重置码到您的邮箱</p>

        <el-alert v-if="errorMessage" :title="errorMessage" type="error" show-icon :closable="false" style="margin-bottom:16px"/>

        <el-form @submit.prevent="handleForgot" label-position="top">
          <el-form-item label="邮箱" :error="errors.email">
            <el-input v-model="form.email" placeholder="请输入邮箱" :prefix-icon="Message" size="large"/>
          </el-form-item>
          <el-button type="primary" native-type="submit" size="large" :loading="isLoading"
            style="width:100%;background:linear-gradient(135deg,#6366f1,#8b5cf6);border:none;border-radius:10px;height:44px;font-size:15px;font-weight:600">
            发送重置码
          </el-button>
        </el-form>
      </div>

      <!-- Step 2: 邮件已发送 -->
      <div v-else>
        <div style="text-align:center;margin-bottom:20px">
          <span style="font-size:48px">📧</span>
          <h2 style="font-size:18px;font-weight:700;color:var(--el-text-color-primary);margin:8px 0 4px">邮件已发送</h2>
          <p style="font-size:13px;color:var(--el-text-color-secondary);margin:0 0 16px">
            重置码已发送至 <b>{{ form.email }}</b><br/>
            请在 15 分钟内查收邮件
          </p>
        </div>

        <el-alert type="info" :closable="false" style="margin-bottom:16px">
          <template #title>
            没有收到？请检查垃圾邮件箱，或确认邮箱地址是否正确
          </template>
        </el-alert>

        <el-button type="primary" size="large" @click="router.push('/reset-password')"
          style="width:100%;background:linear-gradient(135deg,#6366f1,#8b5cf6);border:none;border-radius:10px;height:44px;font-size:15px;font-weight:600">
          我已收到，去重置密码
        </el-button>
      </div>

      <!-- 返回登录 -->
      <div style="text-align:center;margin-top:16px">
        <el-button link type="primary" @click="router.push('/login')">返回登录</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { Message, List } from '@element-plus/icons-vue'
import { forgotPassword } from '@/api/auth'

const router = useRouter()

const form = reactive({ email: '' })
const errors = reactive({ email: '' })
const isLoading = ref(false)
const errorMessage = ref('')
const emailSent = ref(false)

async function handleForgot() {
  errors.email = ''; errorMessage.value = ''
  if (!form.email) { errors.email = '请输入邮箱'; return }
  isLoading.value = true
  try {
    await forgotPassword(form.email)
    emailSent.value = true
  } catch (e: any) {
    errorMessage.value = e.response?.data?.detail || '请求失败，请稍后重试'
  } finally {
    isLoading.value = false
  }
}
</script>
