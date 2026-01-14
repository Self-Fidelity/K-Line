<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <div class="logo-icon">
          <el-icon><TrendCharts /></el-icon>
        </div>
        <h2>K-Line Daily</h2>
        <p>On beta Testing</p>
      </div>
      
      <el-form 
        :model="loginForm" 
        :rules="rules" 
        ref="loginFormRef" 
        @submit.prevent="handleLogin"
        class="login-form"
        size="large"
      >
        <el-form-item prop="username">
          <el-input 
            v-model="loginForm.username" 
            placeholder="用户名" 
            :prefix-icon="User"
          />
        </el-form-item>
        
        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            :type="showPassword ? 'text' : 'password'"
            placeholder="密码"
            :prefix-icon="Lock"
            @keyup.enter="handleLogin"
          >
            <template #suffix>
              <el-icon
                class="password-icon"
                @click="showPassword = !showPassword"
                style="cursor: pointer"
              >
                <View v-if="showPassword" />
                <Hide v-else />
              </el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-button 
          type="primary" 
          :loading="loading" 
          @click="handleLogin" 
          class="login-button"
        >
          登 录
        </el-button>
      </el-form>
      
      <div class="login-footer">
        <span>© 2026 K-Line Daily. All rights reserved.</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { View, Hide, User, Lock, TrendCharts } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const loginFormRef = ref<FormInstance>()
const loading = ref(false)
const showPassword = ref(false)

const loginForm = reactive({
  username: '',
  password: '',
})

const rules = reactive<FormRules>({
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
})

const handleLogin = async () => {
  if (!loginFormRef.value) return

  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        await authStore.login(loginForm.username, loginForm.password)
        ElMessage.success('登录成功')
        router.push('/')
      } catch (error: any) {
        ElMessage.error(error.response?.data?.detail || '登录失败，请检查用户名和密码')
      } finally {
        loading.value = false
      }
    }
  })
}
</script>

<style scoped lang="scss">
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: #0f0f0f;
  background-image: 
    radial-gradient(at 0% 0%, rgba(45, 45, 45, 0.3) 0px, transparent 50%),
    radial-gradient(at 100% 100%, rgba(33, 150, 243, 0.1) 0px, transparent 50%);
}

.login-box {
  width: 400px;
  background: #1e1e1e;
  border-radius: 16px;
  padding: 40px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
  border: 1px solid #333;
  
  .login-header {
    text-align: center;
    margin-bottom: 40px;
    
    .logo-icon {
      width: 64px;
      height: 64px;
      background: linear-gradient(135deg, #2196f3 0%, #1976d2 100%);
      border-radius: 16px;
      display: flex;
      align-items: center;
      justify-content: center;
      margin: 0 auto 20px;
      color: white;
      font-size: 32px;
      box-shadow: 0 4px 12px rgba(33, 150, 243, 0.3);
    }

    h2 {
      margin: 0;
      color: #e0e0e0;
      font-size: 24px;
      font-weight: 600;
    }
    
    p {
      margin: 8px 0 0;
      color: #808080;
      font-size: 14px;
    }
  }

  .login-form {
    :deep(.el-input__wrapper) {
      background-color: #2d2d2d;
      box-shadow: none;
      border: 1px solid #404040;
      
      &:hover, &.is-focus {
        border-color: #2196f3;
      }
      
      input {
        color: #e0e0e0;
        &::placeholder {
          color: #606060;
        }
      }
    }
    
    .login-button {
      width: 100%;
      margin-top: 10px;
      font-weight: 600;
      letter-spacing: 1px;
      height: 44px;
      background: linear-gradient(90deg, #2196f3 0%, #1976d2 100%);
      border: none;
      
      &:hover {
        opacity: 0.9;
        transform: translateY(-1px);
      }
      
      &:active {
        transform: translateY(0);
      }
    }
  }

  .login-footer {
    margin-top: 30px;
    text-align: center;
    color: #404040;
    font-size: 12px;
  }
}
</style>
