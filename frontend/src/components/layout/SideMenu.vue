<template>
  <div class="side-menu">
    <div class="logo-container">
      <h2 v-if="!isCollapse">K-Line Daily</h2>
      <h2 v-else>K</h2>
    </div>
    
    <el-menu
      :default-active="activeMenu"
      class="el-menu-vertical"
      :collapse="isCollapse"
      router
    >
      <el-menu-item index="/">
        <el-icon><DataBoard /></el-icon>
        <template #title>仪表盘</template>
      </el-menu-item>

      <el-sub-menu index="data">
        <template #title>
          <el-icon><Coin /></el-icon>
          <span>数据中心</span>
        </template>
        <el-menu-item index="/data/manage">数据管理</el-menu-item>
        <el-menu-item index="/data/update">数据更新</el-menu-item>
      </el-sub-menu>

      <el-sub-menu index="strategy">
        <template #title>
          <el-icon><TrendCharts /></el-icon>
          <span>策略实验室</span>
        </template>
        <el-menu-item index="/strategy/analysis">单策略分析</el-menu-item>
        <el-menu-item index="/strategy/compare">策略对比</el-menu-item>
        <el-menu-item index="/strategy/aggregation">策略聚合</el-menu-item>

        <el-menu-item index="/strategy/custom">自定义策略</el-menu-item>
        <el-menu-item index="/strategy/optimize">参数优化</el-menu-item>
      </el-sub-menu>

      <el-menu-item index="/chart">
        <el-icon><Histogram /></el-icon>
        <template #title>K线复盘</template>
      </el-menu-item>

    </el-menu>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { DataBoard, Coin, TrendCharts, Histogram } from '@element-plus/icons-vue'

defineProps<{
  isCollapse: boolean
}>()

const route = useRoute()
const activeMenu = computed(() => route.path)
</script>

<style lang="scss" scoped>
@use '@/styles/variables' as v;

.side-menu {
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: v.$bg-secondary;
  border-right: 1px solid v.$border-color;
  transition: background-color 0.3s, border-color 0.3s;

  .logo-container {
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-bottom: 1px solid v.$border-color;
    transition: border-color 0.3s;

    h2 {
      font-size: 18px;
      font-weight: 700;
      white-space: nowrap;
      background: linear-gradient(135deg, #409eff, #67c23a);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }
  }
}

// ── 菜单项目增强 ──
:deep(.el-menu) {
  border-right: none;
  background: transparent;

  // 选中项——左侧发光条 + 渐变背景
  .el-menu-item.is-active {
    position: relative;
    background: linear-gradient(90deg, rgba(64,158,255,0.12), transparent) !important;
    color: var(--el-color-primary) !important;
    font-weight: 600;

    &::before {
      content: '';
      position: absolute;
      left: 0;
      top: 8px;
      bottom: 8px;
      width: 3px;
      background: var(--el-color-primary);
      border-radius: 0 3px 3px 0;
    }
  }

  // 悬停效果
  .el-menu-item:hover {
    background: rgba(64,158,255,0.06) !important;
  }

  // 子菜单标题
  .el-sub-menu__title:hover {
    background: rgba(64,158,255,0.04) !important;
  }

  // 子菜单展开箭头动画
  .el-sub-menu__icon-arrow {
    transition: transform 0.3s ease;
  }
  .el-sub-menu.is-opened .el-sub-menu__icon-arrow {
    transform: rotate(180deg);
  }

  // 子菜单内边距
  .el-menu--inline .el-menu-item {
    padding-left: 56px !important;
  }
}
</style>
