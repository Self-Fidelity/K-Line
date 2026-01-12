<template>
  <el-container class="main-layout">
    <el-aside :width="isCollapse ? '64px' : '240px'" class="aside-container">
      <SideMenu :is-collapse="isCollapse" />
    </el-aside>
    
    <el-container>
      <el-header height="60px" class="header-container">
        <AppHeader :is-collapse="isCollapse" @toggle-collapse="toggleCollapse" />
      </el-header>
      
      <el-main class="main-content">
        <router-view v-slot="{ Component }">
          <transition name="fade-transform" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import SideMenu from '../components/layout/SideMenu.vue'
import AppHeader from '../components/layout/AppHeader.vue'

const isCollapse = ref(false)

const toggleCollapse = () => {
  isCollapse.value = !isCollapse.value
}
</script>

<style lang="scss" scoped>
@use '@/styles/variables' as v;

.main-layout {
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}

.aside-container {
  // Background handled by component inside, but good to set base
  background-color: v.$bg-secondary;
  transition: width 0.3s, background-color 0.3s;
  overflow: hidden;
}

.header-container {
  padding: 0;
  background-color: v.$bg-secondary;
  border-bottom: 1px solid v.$border-color;
  transition: background-color 0.3s, border-color 0.3s;
}

.main-content {
  background-color: v.$bg-primary;
  padding: 20px;
  overflow-y: auto;
  transition: background-color 0.3s;
}

/* Transitions */
.fade-transform-enter-active,
.fade-transform-leave-active {
  transition: opacity 0.3s, transform 0.3s;
}

.fade-transform-enter-from {
  opacity: 0;
  transform: translateX(-20px);
}

.fade-transform-leave-to {
  opacity: 0;
  transform: translateX(20px);
}
</style>
