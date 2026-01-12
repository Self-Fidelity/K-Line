<template>
  <el-config-provider :locale="zhCn" :size="size">
  <router-view />
  </el-config-provider>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import { useDark } from '@vueuse/core'

const size = computed(() => 'default')

// Force Dark Mode
const isDark = useDark()
onMounted(() => {
  isDark.value = true
})
</script>

<style lang="scss">
// Global styles imported in main.ts
// Ensure full height for root div
#app {
  width: 100%;
  height: 100vh;
  margin: 0;
  padding: 0;
  overflow: hidden;
}
</style>
