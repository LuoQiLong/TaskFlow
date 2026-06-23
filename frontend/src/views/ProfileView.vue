<template>
  <div style="min-height:calc(100vh - 64px);display:flex;align-items:flex-start;justify-content:center;padding:40px 20px;background:transparent">
    <div style="width:100%;max-width:480px">
      <h2 style="font-size:22px;font-weight:700;color:var(--el-text-color-primary);margin:0 0 24px">个人设置</h2>

      <el-card style="border-radius:12px;margin-bottom:16px" :body-style="{ padding:'24px', display:'flex', alignItems:'center', gap:'20px' }">
        <div style="position:relative;cursor:pointer" @click="triggerUpload" title="点击更换头像">
          <el-avatar v-if="auth.user?.avatar_url" :src="auth.user.avatar_url" :size="72" style="font-size:28px"/>
          <el-avatar v-else :size="72" style="font-size:28px;background:linear-gradient(135deg,#6366f1,#8b5cf6)">
            {{ (auth.user?.display_name || auth.user?.email || 'U')[0].toUpperCase() }}
          </el-avatar>
          <div style="position:absolute;bottom:0;right:0;width:24px;height:24px;border-radius:50%;background:var(--el-color-primary);display:flex;align-items:center;justify-content:center;border:2px solid var(--el-bg-color)">
            <el-icon size="12" color="#fff"><EditPen /></el-icon>
          </div>
        </div>
        <div>
          <div style="font-size:16px;font-weight:700;color:var(--el-text-color-primary)">{{ auth.user?.display_name || auth.user?.email }}</div>
          <div style="font-size:12px;color:var(--el-text-color-secondary);margin-top:2px">{{ auth.user?.role === 'admin' ? '管理员' : '普通用户' }}</div>
        </div>
        <input ref="fileInput" type="file" accept="image/*" style="display:none" @change="onFileChange"/>
      </el-card>

      <el-card style="border-radius:12px" :body-style="{ padding:'24px' }">
        <el-alert v-if="successMsg" :title="successMsg" type="success" show-icon :closable="false" style="margin-bottom:16px"/>
        <el-alert v-if="errorMsg" :title="errorMsg" type="error" show-icon :closable="false" style="margin-bottom:16px"/>
        <el-form label-position="top">
          <el-form-item label="显示名称">
            <el-input v-model="form.display_name" placeholder="输入显示名称" size="large" :prefix-icon="UserFilled"/>
          </el-form-item>
          <el-form-item label="新密码（不修改请留空）">
            <el-input v-model="form.password" type="password" placeholder="至少6位" show-password size="large"/>
          </el-form-item>
          <el-button type="primary" size="large" :loading="saving" @click="handleSave"
            style="width:100%;background:linear-gradient(135deg,#6366f1,#8b5cf6);border:none;border-radius:10px;height:44px">
            保存修改
          </el-button>
        </el-form>
      </el-card>
    </div>

    <!-- Crop Dialog -->
    <el-dialog v-model="cropVisible" title="裁剪头像" width="480px" destroy-on-close @opened="onCropOpened">
      <div style="text-align:center">
        <div ref="cropWrap"
          style="width:320px;height:320px;margin:0 auto;position:relative;overflow:hidden;background:#222;border-radius:4px;cursor:move"
          @mousedown.prevent="startDrag"
          @mousemove.prevent="onDrag"
          @mouseup="endDrag"
          @mouseleave="endDrag"
          @touchstart.prevent="startDrag"
          @touchmove.prevent="onDrag"
          @touchend="endDrag">
          <img ref="cropImg" :src="cropSrc"
            :style="{ position:'absolute', left: imgLeft+'px', top: imgTop+'px', width: imgW+'px', height: imgH+'px', pointerEvents:'none' }"/>
          <!-- Bright area overlay -->
          <div style="position:absolute;inset:0;pointer-events:none;box-shadow:0 0 0 999px rgba(0,0,0,0.6);border-radius:2px"/>
        </div>
        <p style="font-size:12px;color:var(--el-text-color-secondary);margin-top:8px">拖拽图片调整裁剪区域，中间方形为最终头像</p>
      </div>
      <template #footer>
        <el-button @click="cropVisible = false">取消</el-button>
        <el-button type="primary" @click="doCrop" :loading="cropping">确认裁剪</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { EditPen, UserFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { updateProfile, uploadAvatar } from '@/api/auth'

const auth = useAuthStore()

const form = reactive({ display_name: auth.user?.display_name || '', password: '' })
const saving = ref(false)
const successMsg = ref('')
const errorMsg = ref('')
const fileInput = ref<HTMLInputElement>()

function triggerUpload() { fileInput.value?.click() }

// ── Crop state ──
const cropVisible = ref(false)
const cropSrc = ref('')
const cropImg = ref<HTMLImageElement>()
const cropWrap = ref<HTMLDivElement>()
const cropping = ref(false)
const imgLeft = ref(0), imgTop = ref(0), imgW = ref(0), imgH = ref(0)

let cropFile: File | null = null
let naturalW = 0, naturalH = 0
let scale = 1
let dragging = false
let dragStartX = 0, dragStartY = 0
let startLeft = 0, startTop = 0

function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  if (file.size > 5 * 1024 * 1024) { ElMessage.warning('图片不能超过 5MB'); return }
  cropFile = file
  cropSrc.value = URL.createObjectURL(file)
  cropVisible.value = true
  input.value = ''
}

function onCropOpened() {
  const img = cropImg.value
  if (!img) return
  naturalW = img.naturalWidth
  naturalH = img.naturalHeight
  // Fit image so shorter side fills 320px
  scale = 320 / Math.min(naturalW, naturalH)
  imgW.value = naturalW * scale
  imgH.value = naturalH * scale
  // Center in the 320x320 frame
  imgLeft.value = (320 - imgW.value) / 2
  imgTop.value = (320 - imgH.value) / 2
}

function startDrag(e: MouseEvent | TouchEvent) {
  dragging = true
  const pos = 'touches' in e ? e.touches[0] : e
  dragStartX = pos.clientX
  dragStartY = pos.clientY
  startLeft = imgLeft.value
  startTop = imgTop.value
}

function onDrag(e: MouseEvent | TouchEvent) {
  if (!dragging) return
  const pos = 'touches' in e ? e.touches[0] : e
  const dx = pos.clientX - dragStartX
  const dy = pos.clientY - dragStartY
  // Allow drag within bounds: image edges can't go past container center
  const maxL = 0, maxT = 0
  const minL = 320 - imgW.value, minT = 320 - imgH.value
  imgLeft.value = Math.max(minL, Math.min(maxL, startLeft + dx))
  imgTop.value = Math.max(minT, Math.min(maxT, startTop + dy))
}

function endDrag() { dragging = false }

async function doCrop() {
  const img = cropImg.value
  if (!img || !cropFile) return
  cropping.value = true
  try {
    // Calculate source rect in natural coords (center 320x320 of container → natural image)
    const srcX = (-imgLeft.value) / scale
    const srcY = (-imgTop.value) / scale
    const srcW = 320 / scale
    const srcH = 320 / scale
    const canvas = document.createElement('canvas')
    canvas.width = 256
    canvas.height = 256
    const ctx = canvas.getContext('2d')!
    ctx.drawImage(img, srcX, srcY, srcW, srcH, 0, 0, 256, 256)
    const blob = await new Promise<Blob>((resolve) => canvas.toBlob((b) => resolve(b!), 'image/jpeg', 0.9))
    const croppedFile = new File([blob], 'avatar.jpg', { type: 'image/jpeg' })
    const res = await uploadAvatar(croppedFile)
    if (auth.user) { auth.user.avatar_url = res.avatar_url + '?t=' + Date.now(); auth.save() }
    ElMessage.success('头像已更新')
    cropVisible.value = false
  } catch { ElMessage.error('上传失败') }
  finally { cropping.value = false }
}

async function handleSave() {
  successMsg.value = ''; errorMsg.value = ''
  saving.value = true
  try {
    const data: any = {}
    if (form.display_name !== (auth.user?.display_name || '')) data.display_name = form.display_name || null
    if (form.password) data.password = form.password
    if (Object.keys(data).length === 0) { saving.value = false; return }
    await updateProfile(data)
    if (data.display_name !== undefined && auth.user) { auth.user.display_name = data.display_name; auth.save() }
    form.password = ''
    successMsg.value = '个人资料已更新'
    setTimeout(() => { successMsg.value = '' }, 3000)
  } catch (e: any) {
    errorMsg.value = e.response?.data?.detail || '保存失败'
  } finally { saving.value = false }
}
</script>
