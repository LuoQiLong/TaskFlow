<template>
  <div style="padding:24px 28px;background:transparent;min-height:calc(100vh - 64px)">
    <!-- Header -->
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:20px">
      <div>
        <h2 style="font-size:22px;font-weight:700;color:var(--el-text-color-primary);margin:0">👥 用户管理</h2>
        <p style="font-size:13px;color:var(--el-text-color-secondary);margin:4px 0 0">管理系统中的所有用户账号</p>
      </div>
    </div>

    <!-- Stats cards -->
    <el-row :gutter="16" style="margin-bottom:20px">
      <el-col :span="6">
        <div class="stat-card total">
          <div class="stat-card-icon">👥</div>
          <div class="stat-card-body">
            <div class="stat-card-value">{{ users.length }}</div>
            <div class="stat-card-label">总用户</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card admin">
          <div class="stat-card-icon">🛡️</div>
          <div class="stat-card-body">
            <div class="stat-card-value">{{ users.filter(u=>u.role==='admin').length }}</div>
            <div class="stat-card-label">管理员</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card active">
          <div class="stat-card-icon">✅</div>
          <div class="stat-card-body">
            <div class="stat-card-value">{{ users.filter(u=>u.is_active).length }}</div>
            <div class="stat-card-label">已启用</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card disabled">
          <div class="stat-card-icon">🚫</div>
          <div class="stat-card-body">
            <div class="stat-card-value">{{ users.filter(u=>!u.is_active).length }}</div>
            <div class="stat-card-label">已禁用</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- Toolbar -->
    <div class="admin-toolbar">
      <el-input v-model="search" placeholder="搜索邮箱或显示名称..." clearable size="large"
        style="width:280px" @input="onSearch" :prefix-icon="Search"/>
      <el-select v-model="roleFilter" placeholder="全部角色" clearable size="large" style="width:150px" @change="onSearch">
        <el-option v-for="r in ROLE_OPTIONS" :key="r.value" :label="r.label" :value="r.value"/>
      </el-select>
      <el-select v-model="activeFilter" placeholder="全部状态" clearable size="large" style="width:140px" @change="onSearch">
        <el-option label="已启用" :value="true"/>
        <el-option label="已禁用" :value="false"/>
      </el-select>
      <span style="margin-left:auto;font-size:13px;color:var(--el-text-color-secondary);font-weight:500">
        显示 {{ filteredUsers.length }} / {{ users.length }} 人
      </span>
    </div>

    <!-- Table -->
    <el-card class="users-card" :body-style="{ padding:0 }">
      <el-table :data="filteredUsers" style="width:100%" :row-class-name="rowClass">
        <el-table-column label="用户" min-width="260">
          <template #default="{ row }">
            <div style="display:flex;align-items:center;gap:12px;padding:4px 0">
              <el-avatar v-if="row.avatar_url" :src="row.avatar_url" :size="42"/>
              <el-avatar v-else :size="42" class="avatar-default">
                {{ (row.display_name || row.email)[0].toUpperCase() }}
              </el-avatar>
              <div>
                <div style="font-size:14px;font-weight:600;color:var(--el-text-color-primary);line-height:1.3">
                  {{ row.display_name || row.email?.split('@')[0] }}
                </div>
                <div style="font-size:12px;color:var(--el-text-color-secondary)">{{ row.email }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="角色" width="110" align="center">
          <template #default="{ row }">
            <span class="role-badge" :class="row.role">
              {{ row.role === 'admin' ? '🛡️ 管理员' : '👤 普通用户' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <span class="status-dot" :class="row.is_active ? 'on' : 'off'"/>
            {{ row.is_active ? '启用' : '禁用' }}
          </template>
        </el-table-column>
        <el-table-column label="注册时间" width="140">
          <template #default="{ row }">
            <span style="font-size:13px;color:var(--el-text-color-secondary)">
              {{ row.created_at?.slice(0, 10) || '-' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <div style="display:flex;gap:6px">
              <el-button size="small" class="action-btn edit" @click="openEdit(row)">
                <el-icon style="margin-right:3px"><EditPen /></el-icon>编辑
              </el-button>
              <el-button size="small" class="action-btn reset" @click="handleResetPwd(row)">
                <el-icon style="margin-right:3px"><Key /></el-icon>重置
              </el-button>
              <el-button size="small" class="action-btn del" @click="handleDelete(row)"
                :disabled="row.id === auth.user?.id">
                <el-icon style="margin-right:3px"><Delete /></el-icon>
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Edit Dialog -->
    <el-dialog v-model="editVisible" width="440px" destroy-on-close class="admin-dialog">
      <template #header>
        <div style="display:flex;align-items:center;gap:10px">
          <div class="dialog-icon-box">
            <el-icon color="#fff" size="18"><EditPen /></el-icon>
          </div>
          <span style="font-size:17px;font-weight:700;color:var(--el-text-color-primary)">编辑用户</span>
        </div>
      </template>
      <el-form v-if="editUser" label-position="top">
        <el-form-item label="显示名称">
          <el-input v-model="editForm.display_name" size="large" placeholder="输入显示名称"/>
        </el-form-item>
        <el-form-item label="角色">
          <el-radio-group v-model="editForm.role" size="large" style="width:100%">
            <el-radio-button value="member" style="flex:1">👤 普通用户</el-radio-button>
            <el-radio-button value="admin" style="flex:1">🛡️ 管理员</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="账号状态">
          <el-switch v-model="editForm.is_active"
            :active-text="editForm.is_active ? '已启用' : '已禁用'"
            :active-value="true" :inactive-value="false"
            size="large"/>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false" size="large">取消</el-button>
        <el-button type="primary" @click="handleSaveEdit" :loading="saving" size="large"
          style="background:linear-gradient(135deg,#6366f1,#8b5cf6);border:none">保存</el-button>
      </template>
    </el-dialog>

    <!-- Reset Password Dialog -->
    <el-dialog v-model="resetVisible" width="420px" destroy-on-close class="admin-dialog">
      <template #header>
        <div style="display:flex;align-items:center;gap:10px">
          <div class="dialog-icon-box reset-icon">
            <el-icon color="#fff" size="18"><Key /></el-icon>
          </div>
          <span style="font-size:17px;font-weight:700;color:var(--el-text-color-primary)">重置密码</span>
        </div>
      </template>
      <div style="text-align:center">
        <el-avatar v-if="resetUser?.avatar_url" :src="resetUser.avatar_url" :size="56"/>
        <el-avatar v-else :size="56" class="avatar-default" style="font-size:20px">
          {{ (resetUser?.display_name || resetUser?.email || '?')[0].toUpperCase() }}
        </el-avatar>
        <div style="font-size:15px;font-weight:700;color:var(--el-text-color-primary);margin:10px 0 4px">
          {{ resetUser?.display_name || resetUser?.email }}
        </div>
        <div style="font-size:13px;color:var(--el-text-color-secondary);margin-bottom:20px">
          设置一个新密码替换旧密码
        </div>
        <el-input v-model="resetPwd" type="password" placeholder="至少6位新密码" show-password size="large"/>
      </div>
      <template #footer>
        <el-button @click="resetVisible = false" size="large">取消</el-button>
        <el-button type="primary" @click="handleConfirmReset" :loading="saving" size="large"
          style="background:linear-gradient(135deg,#f56c6c,#e6a23c);border:none">确认重置</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, EditPen, Key, Delete } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { fetchUsers, updateUser, adminResetPassword, deleteUser, type UserListItem } from '@/api/admin'
import { ROLE_MAP, ROLE_OPTIONS } from '@/types'

const auth = useAuthStore()
const router = useRouter()

if (!auth.isAdmin) { router.replace('/app/kanban') }

const users = ref<UserListItem[]>([])
const search = ref('')
const roleFilter = ref('')
const activeFilter = ref<boolean | null>(null)
const saving = ref(false)

const filteredUsers = computed(() => {
  let list = users.value
  if (search.value) {
    const kw = search.value.toLowerCase()
    list = list.filter(u => u.email.toLowerCase().includes(kw) || (u.display_name || '').toLowerCase().includes(kw))
  }
  if (roleFilter.value) list = list.filter(u => u.role === roleFilter.value)
  if (activeFilter.value !== null && activeFilter.value !== '') list = list.filter(u => u.is_active === activeFilter.value)
  return list
})

function rowClass({ row }: any) {
  if (!row.is_active) return 'row-disabled'
  return ''
}

async function loadUsers() {
  try {
    const params: any = {}
    if (search.value) params.search = search.value
    if (roleFilter.value) params.role = roleFilter.value
    if (activeFilter.value !== null && activeFilter.value !== '') params.is_active = activeFilter.value
    users.value = await fetchUsers(params)
  } catch {}
}
function onSearch() { loadUsers() }

// Edit
const editVisible = ref(false)
const editUser = ref<UserListItem | null>(null)
const editForm = ref({ display_name: '', role: 'member', is_active: true })
function openEdit(row: UserListItem) {
  editUser.value = row
  editForm.value = { display_name: row.display_name || '', role: row.role, is_active: row.is_active }
  editVisible.value = true
}
async function handleSaveEdit() {
  if (!editUser.value) return
  saving.value = true
  try {
    await updateUser(editUser.value.id, editForm.value)
    ElMessage.success('用户信息已更新')
    editVisible.value = false
    loadUsers()
  } catch { ElMessage.error('操作失败') }
  finally { saving.value = false }
}

// Reset password
const resetVisible = ref(false)
const resetUser = ref<UserListItem | null>(null)
const resetPwd = ref('')
function handleResetPwd(row: UserListItem) {
  resetUser.value = row
  resetPwd.value = '123456'
  resetVisible.value = true
}
async function handleConfirmReset() {
  if (!resetUser.value || resetPwd.value.length < 6) { ElMessage.warning('密码至少6位'); return }
  saving.value = true
  try {
    await adminResetPassword(resetUser.value.id, resetPwd.value)
    ElMessage.success('密码已重置为 ' + resetPwd.value)
    resetVisible.value = false
  } catch { ElMessage.error('操作失败') }
  finally { saving.value = false }
}

// Delete
async function handleDelete(row: UserListItem) {
  if (row.id === auth.user?.id) { ElMessage.warning('不能删除自己的账号'); return }
  try {
    await ElMessageBox.confirm(
      `确定要删除用户「${row.display_name || row.email}」吗？此操作不可恢复。`,
      '确认删除',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消', confirmButtonClass: 'el-button--danger' }
    )
    await deleteUser(row.id)
    ElMessage.success('已删除')
    loadUsers()
  } catch {}
}

onMounted(() => { loadUsers() })
</script>

<style scoped>
/* Stats cards */
.stat-card {
  background: var(--el-bg-color);
  border-radius: 12px;
  padding: 18px 20px;
  display: flex;
  align-items: center;
  gap: 14px;
  border: 1px solid var(--el-border-color-light);
  transition: all 0.2s;
}
.stat-card:hover { transform: translateY(-2px); box-shadow: var(--el-box-shadow-light); }
.stat-card-icon { font-size: 28px; line-height: 1; }
.stat-card-body { flex: 1; }
.stat-card-value { font-size: 26px; font-weight: 800; color: var(--el-text-color-primary); line-height: 1.1; }
.stat-card-label { font-size: 12px; color: var(--el-text-color-secondary); font-weight: 500; margin-top: 2px; }
.stat-card.total .stat-card-icon { color: #6366f1; }
.stat-card.admin .stat-card-icon { color: #e6a23c; }
.stat-card.active .stat-card-icon { color: #67c23a; }
.stat-card.disabled .stat-card-icon { color: #f56c6c; }

/* Toolbar */
.admin-toolbar {
  background: var(--el-bg-color);
  border-radius: 12px;
  padding: 16px 20px;
  margin-bottom: 16px;
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
  border: 1px solid var(--el-border-color-light);
}

/* Table card */
.users-card {
  border-radius: 12px;
  border: 1px solid var(--el-border-color-light);
  overflow: hidden;
}

/* Avatar */
.avatar-default {
  background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
  font-weight: 700;
  color: #fff;
}

/* Role badge */
.role-badge {
  font-size: 12px;
  padding: 4px 12px;
  border-radius: 20px;
  font-weight: 600;
  white-space: nowrap;
}
.role-badge.admin {
  background: #fef0f0;
  color: #f56c6c;
  border: 1px solid #fbc4c4;
}
.role-badge.member {
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  border: 1px solid var(--el-color-primary-light-5);
}

/* Status dot */
.status-dot {
  display: inline-block;
  width: 8px; height: 8px;
  border-radius: 50%;
  margin-right: 6px;
  vertical-align: middle;
}
.status-dot.on { background: #67c23a; box-shadow: 0 0 0 3px rgba(103,194,58,0.2); }
.status-dot.off { background: #f56c6c; box-shadow: 0 0 0 3px rgba(245,108,108,0.2); }

/* Action buttons */
.action-btn {
  border-radius: 6px !important;
  font-weight: 500;
  font-size: 12px;
  border: none !important;
}
.action-btn.edit { background: var(--el-color-primary-light-9) !important; color: var(--el-color-primary) !important; }
.action-btn.edit:hover { background: var(--el-color-primary) !important; color: #fff !important; }
.action-btn.reset { background: var(--el-color-warning-light-9) !important; color: var(--el-color-warning) !important; }
.action-btn.reset:hover { background: var(--el-color-warning) !important; color: #fff !important; }
.action-btn.del { background: var(--el-color-danger-light-9) !important; color: var(--el-color-danger) !important; }
.action-btn.del:hover { background: var(--el-color-danger) !important; color: #fff !important; }

/* Disabled row */
:deep(.row-disabled) {
  opacity: 0.55;
  background: var(--el-fill-color-lighter) !important;
}

/* Dialog */
.admin-dialog :deep(.el-input__wrapper),
.admin-dialog :deep(.el-select__wrapper) {
  border-radius: 8px;
}
.dialog-icon-box {
  width: 36px; height: 36px;
  border-radius: 10px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  display: flex; align-items: center; justify-content: center;
}
.dialog-icon-box.reset-icon {
  background: linear-gradient(135deg, #f56c6c, #e6a23c);
}
</style>
