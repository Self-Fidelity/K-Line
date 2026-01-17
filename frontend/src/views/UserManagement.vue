<template>
  <div class="user-management">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>用户管理</span>
          <div>
            <el-button type="success" @click="handleCreate" style="margin-right: 10px">添加用户</el-button>
            <el-button type="primary" @click="fetchUsers">刷新列表</el-button>
          </div>
        </div>
      </template>

      <el-table :data="users" v-loading="loading" style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" width="150" />
        <el-table-column prop="email" label="邮箱" width="200" />
        <el-table-column prop="role" label="角色" width="120">
          <template #default="{ row }">
            <el-tag :type="row.role === 'admin' ? 'danger' : 'info'">{{ row.role }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'">
              {{ row.is_active ? '激活' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="注册时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="200">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button 
              link 
              type="danger" 
              size="small" 
              @click="handleDelete(row)"
              :disabled="row.id === currentUserId"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建用户对话框 -->
    <el-dialog
      v-model="createDialogVisible"
      title="添加新用户"
      width="500px"
    >
      <el-form :model="createForm" label-width="100px">
        <el-form-item label="用户名" required>
          <el-input v-model="createForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="邮箱" required>
          <el-input v-model="createForm.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="密码" required>
          <el-input v-model="createForm.password" placeholder="请输入密码" show-password />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="createForm.role">
            <el-option label="普通用户" value="user" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="createDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitCreate" :loading="submitting">创建</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 编辑用户对话框 -->
    <el-dialog
      v-model="dialogVisible"
      title="编辑用户"
      width="500px"
    >
      <el-form :model="editForm" label-width="100px">
        <el-form-item label="用户名">
          <el-input v-model="editForm.username" disabled />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="editForm.email" disabled />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="editForm.role">
            <el-option label="普通用户" value="user" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-switch
            v-model="editForm.is_active"
            active-text="激活"
            inactive-text="禁用"
          />
        </el-form-item>
        <el-form-item label="密码">
            <el-input v-model="editForm.password" placeholder="留空则不修改" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitEdit" :loading="submitting">保存</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { userAPI, type UserUpdateParams, type UserCreateParams } from '@/api/users'
import type { UserInfo } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const currentUserId = computed(() => authStore.user?.id)

const users = ref<UserInfo[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const createDialogVisible = ref(false) // 新增：创建用户对话框
const submitting = ref(false)

const editForm = ref({
  id: 0,
  username: '',
  email: '',
  role: 'user',
  is_active: true,
  password: ''
})

const createForm = ref<UserCreateParams>({
  username: '',
  email: '',
  password: '',
  role: 'user',
  max_watchlist_count: 50
})

const fetchUsers = async () => {
  loading.value = true
  try {
    users.value = await userAPI.listUsers()
  } catch (error: any) {
    ElMessage.error('获取用户列表失败')
  } finally {
    loading.value = false
  }
}

const handleCreate = () => {
  createForm.value = {
    username: '',
    email: '',
    password: '',
    role: 'user',
    max_watchlist_count: 50
  }
  createDialogVisible.value = true
}

const submitCreate = async () => {
  if (!createForm.value.username || !createForm.value.password || !createForm.value.email) {
    ElMessage.warning('请填写必填项')
    return
  }
  submitting.value = true
  try {
    await userAPI.createUser(createForm.value)
    ElMessage.success('用户创建成功')
    createDialogVisible.value = false
    fetchUsers()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '创建失败')
  } finally {
    submitting.value = false
  }
}

const handleEdit = (user: UserInfo) => {
  editForm.value = {
    id: user.id,
    username: user.username,
    email: user.email,
    role: user.role,
    is_active: user.is_active,
    password: ''
  }
  dialogVisible.value = true
}

const submitEdit = async () => {
  submitting.value = true
  try {
    const updateData: UserUpdateParams = {
      role: editForm.value.role,
      is_active: editForm.value.is_active
    }
    if (editForm.value.password) {
        updateData.password = editForm.value.password
    }
    
    await userAPI.updateUser(editForm.value.id, updateData)
    ElMessage.success('用户更新成功')
    dialogVisible.value = false
    fetchUsers()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '更新失败')
  } finally {
    submitting.value = false
  }
}

const handleDelete = (user: UserInfo) => {
  ElMessageBox.confirm(
    `确定要删除用户 "${user.username}" 吗？此操作不可恢复。`,
    '警告',
    {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(async () => {
    try {
      await userAPI.deleteUser(user.id)
      ElMessage.success('用户已删除')
      fetchUsers()
    } catch (error: any) {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  })
}

const formatDateTime = (dateStr: string) => {
  return new Date(dateStr).toLocaleString()
}

onMounted(() => {
  fetchUsers()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
