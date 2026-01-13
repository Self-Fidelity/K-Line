<template>
  <div class="side-menu">
    <div class="logo-container">
      <h2 v-if="!isCollapse">K-Line Quant</h2>
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
        <el-menu-item index="/strategy/batch">批量扫描</el-menu-item>
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
      color: v.$text-primary;
      margin: 0;
      font-size: 18px;
      white-space: nowrap;
      transition: color 0.3s;
    }
  }

  .el-menu-vertical {
    border-right: none;
    flex: 1;
    overflow-y: auto;
    background-color: transparent; // Let parent handle bg
    
    &:not(.el-menu--collapse) {
      width: 240px;
    }
  }
}
</style>
