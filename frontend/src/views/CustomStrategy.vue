<template>
  <div class="custom-strategy">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>自定义策略管理</span>
          <el-button type="primary" @click="handleCreate">创建新策略</el-button>
        </div>
      </template>

      <!-- 策略列表 -->
      <el-table :data="strategyList" style="width: 100%" v-loading="loading">
        <el-table-column prop="name" label="策略名称" width="200" />
        <el-table-column prop="description" label="描述" />
        <el-table-column prop="username" label="创建人" width="120">
          <template #default="{ row }">
            <el-tag :type="row.is_system ? 'info' : ''" size="small">{{ row.is_system ? '系统' : row.username }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button link type="success" size="small" @click="handleBacktest(row)">回测</el-button>
            <el-button link type="primary" size="small" @click="handleView(row)">查看</el-button>
            <el-button v-if="canEdit(row)" link type="primary" size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button v-if="canDelete(row)" link type="danger" size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="95%"
      :close-on-click-modal="false"
      @close="handleDialogClose"
    >
      <el-form :model="formData" label-width="120px">
        <el-form-item label="策略名称" required>
          <el-input v-model="formData.name" placeholder="请输入策略名称" maxlength="100" />
        </el-form-item>

        <el-form-item label="策略描述">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="2"
            placeholder="请输入策略简短描述"
            maxlength="500"
          />
        </el-form-item>

        <el-form-item label="详细说明">
          <el-input
            v-model="formData.detailed_description"
            type="textarea"
            :rows="4"
            placeholder="请输入策略详细说明（策略原理、使用方法等）"
          />
        </el-form-item>

        <el-form-item label="策略代码" required class="code-form-item">
          <div class="code-editor-wrapper">
            <div class="editor-toolbar">
              <el-button size="small" @click="insertTemplate">插入模板</el-button>
              <el-button size="small" @click="showReferenceDialog = true">参考已有策略</el-button>
              <el-button size="small" @click="handleValidate" :loading="validating">验证代码</el-button>
              <span v-if="validationResult" class="validation-result" :class="validationResult.valid ? 'success' : 'error'">
                {{ validationResult.valid ? '✓ 验证通过' : '✗ 验证失败' }}
              </span>
            </div>
            <CodeEditor
              v-model="formData.code"
              :dark-mode="isDark"
              height="500px"
              placeholder="请输入策略代码..."
            />
            <div v-if="validationResult && !validationResult.valid" class="validation-errors">
              <div v-for="(error, index) in validationResult.errors" :key="index" class="error-item">
                {{ error }}
              </div>
            </div>
            <div v-if="validationResult && validationResult.warnings.length > 0" class="validation-warnings">
              <div v-for="(warning, index) in validationResult.warnings" :key="index" class="warning-item">
                ⚠ {{ warning }}
              </div>
            </div>
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">保存</el-button>
      </template>
    </el-dialog>

    <!-- 参考策略对话框 -->
    <el-dialog
      v-model="showReferenceDialog"
      title="参考已有策略"
      width="90%"
    >
      <div v-loading="referenceLoading">
        <el-alert
          title="提示"
          type="info"
          :closable="false"
          style="margin-bottom: 16px;"
        >
          选择已有策略查看其代码，可以作为创建新策略的参考。点击"查看代码"可查看完整代码，然后可以复制到编辑器中。
        </el-alert>

        <!-- 筛选器 -->
        <div style="margin-bottom: 16px;">
          <el-radio-group v-model="strategyFilter" @change="handleFilterChange">
            <el-radio-button value="all">全部策略</el-radio-button>
            <el-radio-button value="system">系统策略</el-radio-button>
            <el-radio-button value="custom">自定义策略</el-radio-button>
          </el-radio-group>
        </div>

        <el-table
          :data="filteredStrategyList"
          style="width: 100%"
          max-height="400"
          @row-click="handleReferenceSelect"
        >
          <el-table-column prop="name" label="策略名称" width="200" />
          <el-table-column prop="description" label="描述" />
          <el-table-column label="类型" width="100">
            <template #default="{ row }">
              <el-tag :type="row.is_system ? 'success' : 'info'" size="small">
                {{ row.is_system ? '系统策略' : '自定义策略' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="180">
            <template #default="{ row }">
              {{ row.is_system ? '-' : row.created_at }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click.stop="handleReferenceSelect(row)">查看代码</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <template #footer>
        <el-button @click="showReferenceDialog = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 参考策略代码查看对话框 -->
    <el-dialog
      v-model="showReferenceCodeDialog"
      :title="`参考策略：${referenceStrategy?.name || ''}`"
      width="90%"
    >
      <div v-if="referenceStrategy">
        <el-descriptions :column="2" border style="margin-bottom: 16px;">
          <el-descriptions-item label="策略名称">{{ referenceStrategy.name }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ referenceStrategy.created_at }}</el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">{{ referenceStrategy.description || '无' }}</el-descriptions-item>
        </el-descriptions>

        <el-divider>策略代码</el-divider>
        <div class="reference-code-wrapper">
          <CodeEditor
            :model-value="referenceStrategyCode"
            :dark-mode="isDark"
            readonly
            height="500px"
          />
        </div>
      </div>

      <template #footer>
        <el-button @click="showReferenceCodeDialog = false">关闭</el-button>
        <el-button type="primary" @click="useReferenceCode">使用此代码</el-button>
      </template>
    </el-dialog>

    <!-- 查看对话框 -->
    <el-dialog
      v-model="viewDialogVisible"
      title="策略详情"
      width="95%"
    >
      <div v-if="viewStrategy">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="策略名称">{{ viewStrategy.name }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ viewStrategy.created_at }}</el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">{{ viewStrategy.description || '无' }}</el-descriptions-item>
          <el-descriptions-item label="详细说明" :span="2">
            <div style="white-space: pre-wrap;">{{ viewStrategy.detailed_description || '无' }}</div>
          </el-descriptions-item>
        </el-descriptions>

        <el-divider>策略代码</el-divider>
        <CodeEditor
          :model-value="viewStrategy.code"
          :dark-mode="isDark"
          readonly
          height="500px"
        />
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useDark } from '@vueuse/core'
import { customStrategyAPI, type CustomStrategyInfo, type CustomStrategyDetail, type CustomStrategyCreate, type CustomStrategyUpdate } from '@/api/customStrategy'
import { strategyAPI, type StrategyInfo } from '@/api/strategy'
import apiClient from '@/api/client'
import CodeEditor from '@/components/CodeEditor.vue'
import { useAuthStore } from '@/stores/auth'

const isDark = useDark()
const router = useRouter()
const authStore = useAuthStore()

const canEdit = (row: CustomStrategyInfo) => {
  if (row.is_system) return false
  return authStore.user?.role === 'admin' || row.user_id === authStore.user?.id
}

const canDelete = (row: CustomStrategyInfo) => {
  if (row.is_system) return false
  return authStore.user?.role === 'admin' || row.user_id === authStore.user?.id
}

// 策略列表
const strategyList = ref<CustomStrategyInfo[]>([])
const systemStrategyList = ref<StrategyInfo[]>([])
const allStrategyList = ref<Array<CustomStrategyInfo | StrategyInfo>>([])
const loading = ref(false)

// 对话框
const dialogVisible = ref(false)
const viewDialogVisible = ref(false)
const showReferenceDialog = ref(false)
const showReferenceCodeDialog = ref(false)
const dialogTitle = computed(() => editingStrategy.value ? '编辑策略' : '创建策略')
const editingStrategy = ref<CustomStrategyInfo | null>(null)
const viewStrategy = ref<CustomStrategyDetail | null>(null)
const referenceStrategy = ref<CustomStrategyInfo | null>(null)
const referenceStrategyCode = ref('')
const referenceLoading = ref(false)
const strategyFilter = ref<'all' | 'system' | 'custom'>('all')
const filteredStrategyList = computed(() => {
  if (strategyFilter.value === 'all') {
    return allStrategyList.value
  } else if (strategyFilter.value === 'system') {
    return allStrategyList.value.filter(s => s.is_system)
  } else {
    return allStrategyList.value.filter(s => !s.is_system)
  }
})

// 表单数据
// 表单数据
const formData = ref<CustomStrategyCreate>({
  name: '',
  description: '',
  detailed_description: '',
  code: '',
  parameter_descriptions: {},
})

// 验证
const validating = ref(false)
const validationResult = ref<any>(null)

// 提交
const submitting = ref(false)

// 策略代码模板
const strategyTemplate = `"""自定义策略模板"""

import pandas as pd
from typing import Any
from src.strategy.base import BaseStrategy

class MyCustomStrategy(BaseStrategy):
    """
    自定义策略
    
    策略说明：
    - 在这里描述你的策略逻辑
    """
    
    def __init__(self, param1: int = 10, param2: float = 0.5):
        """
        初始化策略
        
        Args:
            param1: 参数1说明
            param2: 参数2说明
        """
        super().__init__(
            name="My Custom Strategy",
            description="自定义策略描述",
            detailed_description="策略详细说明",
            parameter_descriptions={
                "param1": "参数1说明",
                "param2": "参数2说明",
            }
        )
        self.param1 = param1
        self.param2 = param2
    
    def analyze(
        self,
        data: pd.DataFrame,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        执行策略分析
        
        Args:
            data: 股票数据 DataFrame，包含以下列：
                - date: 日期
                - open: 开盘价
                - close: 收盘价
                - high: 最高价
                - low: 最低价
                - volume: 成交量
                - amount: 成交额
                - pct_chg: 涨跌幅
                - change: 涨跌额
                - turnover: 换手率
            **kwargs: 其他参数
        
        Returns:
            分析结果 DataFrame，必须包含 date 列，建议包含 signal 列（1=买入，-1=卖出，0=持有）
        """
        result = data.copy()
        
        # 在这里实现你的策略逻辑
        # 示例：简单的移动平均策略
        result['ma'] = result['close'].rolling(window=self.param1).mean()
        result['signal'] = 0
        
        # 当收盘价上穿均线时买入
        result.loc[result['close'] > result['ma'], 'signal'] = 1
        # 当收盘价下穿均线时卖出
        result.loc[result['close'] < result['ma'], 'signal'] = -1
        
        return result
`

// 加载策略列表
const loadStrategyList = async () => {
  loading.value = true
  try {
    // 加载自定义策略
    const customResponse = await customStrategyAPI.getList()
    strategyList.value = customResponse.data.strategies
    
    // 加载系统策略
    const systemResponse = await strategyAPI.listStrategies()
    systemStrategyList.value = systemResponse.strategies.filter(s => s.is_system)
    
    // 合并策略列表（系统策略在前）
    allStrategyList.value = [
      ...systemStrategyList.value.map(s => ({
        id: 0, // 系统策略没有ID，使用0
        user_id: 0,
        username: 'System',
        name: s.name,
        description: s.description,
        detailed_description: s.detailed_description || '',
        parameter_descriptions: s.parameter_descriptions || {},
        is_public: true,
        is_system: true,
        created_at: '',
        updated_at: null,
      })) as CustomStrategyInfo[],
      ...strategyList.value.map(s => ({
        ...s,
        is_system: false,
      })),
    ]
  } catch (error: any) {
    ElMessage.error('加载策略列表失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

// 创建策略
const handleCreate = () => {
  editingStrategy.value = null
  formData.value = {
    name: '',
    description: '',
    detailed_description: '',
    code: strategyTemplate,
    parameter_descriptions: {},
  }
  validationResult.value = null
  dialogVisible.value = true
}

// 编辑策略
const handleEdit = async (strategy: CustomStrategyInfo) => {
  try {
    const response = await customStrategyAPI.getDetail(strategy.id)
    const detail = response.data
    
    editingStrategy.value = strategy
    formData.value = {
      name: detail.name,
      description: detail.description,
      detailed_description: detail.detailed_description,
      code: detail.code,
      parameter_descriptions: detail.parameter_descriptions,
    }
    validationResult.value = null
    dialogVisible.value = true
  } catch (error: any) {
    ElMessage.error('加载策略详情失败: ' + (error.response?.data?.detail || error.message))
  }
}

// 查看策略
const handleView = async (strategy: CustomStrategyInfo) => {
  try {
    const response = await customStrategyAPI.getDetail(strategy.id)
    viewStrategy.value = response.data
    viewDialogVisible.value = true
  } catch (error: any) {
    ElMessage.error('加载策略详情失败: ' + (error.response?.data?.detail || error.message))
  }
}

// 删除策略
const handleDelete = async (strategy: CustomStrategyInfo) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除策略 "${strategy.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    await customStrategyAPI.delete(strategy.id)
    ElMessage.success('删除成功')
    loadStrategyList()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败: ' + (error.response?.data?.detail || error.message))
    }
  }
}

// 跳转回测
const handleBacktest = (strategy: CustomStrategyInfo) => {
  router.push({
    name: 'StrategyAnalysis',
    query: {
      strategy_name: strategy.name
    }
  })
}

// 插入模板
const insertTemplate = () => {
  formData.value.code = strategyTemplate
  ElMessage.info('已插入策略模板')
}

// 验证代码
const handleValidate = async () => {
  if (!formData.value.code.trim()) {
    ElMessage.warning('请先输入策略代码')
    return
  }
  
  validating.value = true
  try {
    const response = await customStrategyAPI.validate({
      code: formData.value.code,
      test_data: true,
    })
    validationResult.value = response.data
    
    if (response.data.valid) {
      ElMessage.success('代码验证通过')
      // 如果验证通过且返回了策略名称和描述，自动填充
      if (response.data.strategy_name && !formData.value.name) {
        formData.value.name = response.data.strategy_name
      }
      if (response.data.strategy_description && !formData.value.description) {
        formData.value.description = response.data.strategy_description
      }
    } else {
      ElMessage.error('代码验证失败，请查看错误信息')
    }
  } catch (error: any) {
    ElMessage.error('验证失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    validating.value = false
  }
}

// 提交表单
const handleSubmit = async () => {
  if (!formData.value.name.trim()) {
    ElMessage.warning('请输入策略名称')
    return
  }
  
  if (!formData.value.code.trim()) {
    ElMessage.warning('请输入策略代码')
    return
  }
  
  // 先验证代码
  await handleValidate()
  if (validationResult.value && !validationResult.value.valid) {
    ElMessage.warning('请先修复代码错误')
    return
  }
  
  submitting.value = true
  try {
    if (editingStrategy.value) {
      // 更新策略
      const updateData: CustomStrategyUpdate = {
        name: formData.value.name,
        description: formData.value.description,
        detailed_description: formData.value.detailed_description,
        code: formData.value.code,
        parameter_descriptions: formData.value.parameter_descriptions,
      }
      await customStrategyAPI.update(editingStrategy.value.id, updateData)
      ElMessage.success('更新成功')
    } else {
      // 创建策略
      await customStrategyAPI.create(formData.value)
      ElMessage.success('创建成功')
    }
    
    dialogVisible.value = false
    loadStrategyList()
  } catch (error: any) {
    ElMessage.error('保存失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    submitting.value = false
  }
}

// 关闭对话框
const handleDialogClose = () => {
  formData.value = {
    name: '',
    description: '',
    detailed_description: '',
    code: '',
    parameter_descriptions: {},
  }
  validationResult.value = null
  editingStrategy.value = null
}

// 选择参考策略
const handleReferenceSelect = async (strategy: CustomStrategyInfo | StrategyInfo) => {
  referenceLoading.value = true
  try {
    // 判断是系统策略还是自定义策略
    if ('is_system' in strategy && strategy.is_system) {
      // 系统策略：通过策略API获取代码
      const response = await apiClient.get(`/api/strategy/${strategy.name}/code`)
      referenceStrategy.value = {
        id: 0,
        user_id: 0,
        name: strategy.name,
        description: strategy.description,
        detailed_description: strategy.detailed_description || '',
        parameter_descriptions: strategy.parameter_descriptions || {},
        is_public: false,
        is_system: true,
        created_at: '',
        updated_at: null,
      } as CustomStrategyInfo
      referenceStrategyCode.value = response.data.code
    } else {
      // 自定义策略：通过自定义策略API获取代码
      const customStrategy = strategy as CustomStrategyInfo
      const response = await customStrategyAPI.getDetail(customStrategy.id)
      referenceStrategy.value = customStrategy
      referenceStrategyCode.value = response.data.code
    }
    showReferenceCodeDialog.value = true
    showReferenceDialog.value = false
  } catch (error: any) {
    ElMessage.error('加载策略代码失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    referenceLoading.value = false
  }
}

// 使用参考代码
const useReferenceCode = () => {
  if (referenceStrategyCode.value) {
    formData.value.code = referenceStrategyCode.value
    showReferenceCodeDialog.value = false
    ElMessage.success('已复制策略代码到编辑器')
  }
}

// 筛选变化处理
const handleFilterChange = () => {
  // 筛选逻辑已在 computed 中处理，这里可以添加其他逻辑
}

onMounted(() => {
  loadStrategyList()
})
</script>

<style scoped lang="scss">
.custom-strategy {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  :deep(.code-form-item) {
    .el-form-item__content {
      width: 100%;
    }
  }

  .code-editor-wrapper {
    border: 1px solid #dcdfe6;
    border-radius: 4px;
    overflow: hidden;
    width: 100%;
    max-width: 100%;

    .editor-toolbar {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 8px;
      background: #f5f7fa;
      border-bottom: 1px solid #dcdfe6;

      .validation-result {
        margin-left: auto;
        font-size: 14px;

        &.success {
          color: #67c23a;
        }

        &.error {
          color: #f56c6c;
        }
      }
    }

    .code-editor {
      width: 100%;
      min-height: 400px;
      padding: 12px;
      font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
      font-size: 14px;
      line-height: 1.6;
      border: none;
      outline: none;
      resize: both;
      background: #fafafa;
      color: #333;
      box-sizing: border-box;
    }

    .validation-errors {
      padding: 8px 12px;
      background: #fef0f0;
      border-top: 1px solid #fde2e2;

      .error-item {
        color: #f56c6c;
        font-size: 13px;
        margin: 4px 0;
      }
    }

    .validation-warnings {
      padding: 8px 12px;
      background: #fdf6ec;
      border-top: 1px solid #faecd8;

      .warning-item {
        color: #e6a23c;
        font-size: 13px;
        margin: 4px 0;
      }
    }
  }

  .code-viewer {
    background: #f5f7fa;
    padding: 16px;
    border-radius: 4px;
    overflow-x: auto;
    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
    font-size: 13px;
    line-height: 1.6;
    max-height: 500px;
    overflow-y: auto;
    color: #333;
  }

  .reference-code-wrapper {
    border: 1px solid #dcdfe6;
    border-radius: 4px;
    overflow: hidden;
  }

  .reference-code-viewer {
    background: #f5f7fa;
    padding: 16px;
    margin: 0;
    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
    font-size: 13px;
    line-height: 1.6;
    max-height: 500px;
    overflow-x: auto;
    overflow-y: auto;
    white-space: pre;
    tab-size: 2;
    color: #333;
  }
}

// Dark Mode Styles
html.dark .custom-strategy {
  .code-editor-wrapper {
    border-color: #4c4d4f;

    .editor-toolbar {
      background: #2d2d2d;
      border-bottom-color: #4c4d4f;
    }

    .code-editor {
      background: #1e1e1e;
      color: #d4d4d4;
    }
    
    .validation-errors {
      background: #2b1d1d;
      border-top-color: #442b2b;
    }
    
    .validation-warnings {
      background: #2b251d;
      border-top-color: #443b2b;
    }
  }

  .code-viewer, 
  .reference-code-viewer {
    background: #1e1e1e;
    color: #d4d4d4;
    border: 1px solid #4c4d4f;
  }
  
  .reference-code-wrapper {
    border-color: #4c4d4f;
  }
}
</style>
