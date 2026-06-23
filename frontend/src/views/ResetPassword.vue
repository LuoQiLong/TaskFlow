<template>
  <div style="min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;background:var(--el-bg-color-page);position:relative;overflow:hidden">
    <!-- 左上角 紫色光晕 -->
    <div style="position:absolute;top:-200px;left:-200px;width:800px;height:800px;border-radius:50%;background:radial-gradient(circle, rgba(139,92,246,0.12) 0%, transparent 60%);pointer-events:none"/>
    <!-- 右下角 蓝色光晕 -->
    <div style="position:absolute;bottom:-180px;right:-180px;width:700px;height:700px;border-radius:50%;background:radial-gradient(circle, rgba(59,130,246,0.12) 0%, transparent 60%);pointer-events:none"/>

    <!-- Logo -->
    <div style="text-align:center;margin-bottom:24px;position:relative;z-index:1">
      <div style="width:52px;height:52px;border-radius:12px;background:linear-gradient(135deg,#8b5cf6,#6366f1);display:inline-flex;align-items:center;justify-content:center;margin-bottom:12px;box-shadow:0 8px 24px rgba(99,102,241,0.3)">
        <el-icon size="26" color="#fff"><Lock /></el-icon>
      </div>
      <h1 style="font-size:26px;font-weight:700;color:var(--el-text-color-primary);margin:0;letter-spacing:-0.5px">TaskFlow</h1>
      <p style="font-size:13px;color:var(--el-text-color-secondary);margin:4px 0 0">重置密码</p>
    </div>

    <!-- 卡片 -->
    <el-card style="width:420px;border-radius:16px;box-shadow:var(--el-box-shadow-light);position:relative;z-index:1" :body-style="{ padding: '36px 36px 28px' }">

      <!-- 成功提示 -->
      <div v-if="successMessage" style="text-align:center">
        <span style="font-size:48px">✅</span>
        <h2 style="font-size:18px;font-weight:700;color:var(--el-text-color-primary);margin:8px 0 4px">密码重置成功</h2>
        <p style="font-size:14px;color:var(--el-text-color-secondary);margin:0 0 24px">{{ successMessage }}</p>
        <el-button type="primary" size="large" @click="router.push('/login')"
          style="width:100%;background:linear-gradient(135deg,#6366f1,#8b5cf6);border:none;border-radius:10px;height:44px;font-size:15px;font-weight:600">
          前往登录
        </el-button>
      </div>

      <!-- 重置表单 -->
      <div v-else>
        <h2 style="font-size:18px;font-weight:700;color:var(--el-text-color-primary);margin:0 0 4px">设置新密码</h2>
        <p style="font-size:13px;color:var(--el-text-color-secondary);margin:0 0 24px">输入重置码和新密码</p>

        <el-alert v-if="errorMessage" :title="errorMessage" type="error" show-icon :closable="false" style="margin-bottom:16px"/>

        <el-form @submit.prevent="handleReset" label-position="top">
          <el-form-item label="重置码" :error="errors.token">
            <el-input v-model="form.token" placeholder="粘贴重置码" :prefix-icon="Key" size="large"/>
          </el-form-item>
          <el-form-item label="新密码" :error="errors.newPassword">
            <el-input v-model="form.newPassword" type="password" placeholder="至少6位新密码" :prefix-icon="Lock" show-password size="large"/>
          </el-form-item>
          <el-form-item label="确认密码" :error="errors.confirm">
            <el-input v-model="form.confirm" type="password" placeholder="再次输入新密码" :prefix-icon="Lock" show-password size="large"/>
          </el-form-item>
          <el-button type="primary" native-type="submit" size="large" :loading="isLoading"
            style="width:100%;background:linear-gradient(135deg,#6366f1,#8b5cf6);border:none;border-radius:10px;height:44px;font-size:15px;font-weight:600">
            重置密码
          </el-button>
        </el-form>
      </div>

      <!-- 返回登录 -->
      <div style="text-align:center;margin-top:16px">
        <el-button link type="primary" @click="router.push('/login')">返回登录</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Lock, Key } from '@element-plus/icons-vue'
import { resetPassword } from '@/api/auth'

const router = useRouter()
const route = useRoute()

const form = reactive({ token: '', newPassword: '', confirm: '' })
const errors = reactive({ token: '', newPassword: '', confirm: '' })
const isLoading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

onMounted(() => {
  const queryToken = route.query.token
  if (queryToken && typeof queryToken === 'string') {
    form.token = queryToken
  }
})

async function handleReset() {
  errors.token = ''; errors.newPassword = ''; errors.confirm = ''; errorMessage.value = ''
  if (!form.token) { errors.token = '请输入重置码'; return }
  if (!form.newPassword) { errors.newPassword = '请输入新密码'; return }
  if (form.newPassword.length < 6) { errors.newPassword = '密码至少6位'; return }
  if (form.newPassword !== form.confirm) { errors.confirm = '两次密码不一致'; return }

  isLoading.value = true
  try {
    await resetPassword(form.token, form.newPassword)
    successMessage.value = '请使用新密码重新登录'
  } catch (e: any) {
    errorMessage.value = e.response?.data?.detail || '重置失败，请稍后重试'
  } finally {
    isLoading.value = false
  }
}
</script>
