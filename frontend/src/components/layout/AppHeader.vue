<template>
  <div class="app-header">
    <div class="left-panel">
      <el-button link @click="$emit('toggle-collapse')">
        <el-icon :size="20"><Expand v-if="isCollapse" /><Fold v-else /></el-icon>
      </el-button>
      <el-breadcrumb separator="/">
        <template v-for="(matched, index) in route.matched" :key="index">
          <el-breadcrumb-item v-if="matched.meta.title">
            {{ matched.meta.title }}
          </el-breadcrumb-item>
        </template>
      </el-breadcrumb>
    </div>

    <div class="right-panel">
      <!-- Right panel content removed as requested -->
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { Fold, Expand } from '@element-plus/icons-vue'

defineProps<{
  isCollapse: boolean
}>()

defineEmits(['toggle-collapse'])

const route = useRoute()
const currentRouteName = computed(() => route.meta.title || route.name)
</script>

<style lang="scss" scoped>
.app-header {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 10px;

  .left-panel {
    display: flex;
    align-items: center;
    gap: 15px;
  }

  .right-panel {
    display: flex;
    align-items: center;
    gap: 20px;
    
    .status-item {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 14px;
      color: #909399;
    }
  }
}
</style>
