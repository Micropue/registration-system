<template>
  <v-app style="height: 100%">
    <!-- 左侧导航栏 (桌面端响应式固定，移动端为抽屉) -->
    <v-navigation-drawer
      v-model="sideOpen"
      app
      width="260"
      elevation="0"
      class="border-e"
    >
      <!-- 用户信息 -->
      <div v-if="user" class="py-3 d-flex align-center px-4">
        <v-avatar size="32" color="primary" class="me-3">
          <span class="text-white font-weight-bold text-body-2">{{ user.username.charAt(0).toUpperCase() }}</span>
        </v-avatar>
        <div>
          <div class="text-body-2 font-weight-bold">{{ user.username }}</div>
          <div class="text-caption text-grey">{{ user.type === 'admin' ? '管理员' : '普通用户' }}</div>
        </div>
      </div>
      <div v-else-if="!isAuthChecking" class="pa-4">
        <v-btn color="primary" variant="flat" to="/login" class="rounded-pill" block elevation="0" size="small">
          登录
        </v-btn>
      </div>

      <v-divider></v-divider>

      <!-- 导航菜单 -->
      <v-list nav density="compact" class="pa-2">
        <v-list-item
          v-for="item in displayFunctions"
          :key="item.to"
          :prepend-icon="item.icon"
          :title="item.title"
          :to="item.to"
          rounded="xl"
          active-color="primary"
          class="mb-1"
        ></v-list-item>
      </v-list>

      <template v-slot:append v-if="user">
        <div class="pa-2">
          <v-btn
            prepend-icon="mdi-logout"
            color="error"
            variant="tonal"
            class="rounded-pill"
            size="small"
            block
            @click="handleLogout"
          >
            退出登录
          </v-btn>
        </div>
      </template>
    </v-navigation-drawer>

    <!-- 顶部导航栏 -->
    <v-app-bar app color="rgba(255, 255, 255, 0.8)" flat class="px-3 px-md-6 border-b"
      style="backdrop-filter: blur(12px);">
      <v-container class="d-flex align-center pa-0" fluid>
        <v-app-bar-nav-icon class="me-1" @click="toggleSidebar"></v-app-bar-nav-icon>

        <div class="d-flex align-center cursor-pointer" @click="router.push('/')">
          <v-avatar size="36" class="me-2">
            <v-img src="@/assets/logo.jpg"></v-img>
          </v-avatar>
          <span class="text-h6 font-weight-bold color-primary d-none d-sm-flex">
            哆啦A梦（校园跑版）
          </span>
        </div>

        <v-spacer></v-spacer>

        <div class="d-flex align-center">
          <v-fade-transition>
            <v-progress-circular v-if="isPageLoading" indeterminate color="primary" size="20" width="2"
              class="me-4"></v-progress-circular>
          </v-fade-transition>

          <template v-if="user">
            <v-btn color="error" variant="tonal" class="rounded-pill px-4 font-weight-bold"
              size="small" @click="handleLogout">
              退出登录
            </v-btn>
          </template>
          <v-btn v-else-if="!isAuthChecking" color="primary" variant="flat" to="/login"
            class="rounded-pill px-6 font-weight-bold" elevation="0">
            登录
          </v-btn>
          <v-btn v-else color="primary" variant="flat" class="rounded-pill px-6 font-weight-bold" elevation="0"
            disabled loading>
            检测中
          </v-btn>
        </div>
      </v-container>
    </v-app-bar>

    <v-main class="bg-grey-lighten-4 overflow-y-auto" style="height: 100%;">
      <div class="main-gradient-bg"></div>
      <RouterView />
    </v-main>
  </v-app>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useDisplay } from 'vuetify'
import { checkLoginStatus } from '@/api/auth'
import { cookie } from '@/api/cookie'
import { functions } from '@/config/functions'
import { useAppStore } from '@/stores/app'
import type { CheckLoginData } from '@/config/api-type'

const router = useRouter()
const route = useRoute()
const appStore = useAppStore()
const { mdAndUp } = useDisplay()
const sideOpen = ref(false)
const user = ref<CheckLoginData | null>(null)
const isAuthChecking = ref(true)

const isPageLoading = computed(() => appStore.isPageLoading)

const displayFunctions = computed(() => {
  if (!user.value) return []
  return functions.filter(item => {
    const targetRole = item.role || 'default'
    return user.value?.type === targetRole
  })
})

async function fetchUser() {
  isAuthChecking.value = true
  user.value = await checkLoginStatus()
  appStore.setUserInfo(user.value)
  isAuthChecking.value = false
}

function toggleSidebar() {
  sideOpen.value = !sideOpen.value
}

function handleLogout() {
  cookie.remove('token')
  user.value = null
  appStore.setUserInfo(null)
  router.push('/login')
}

onMounted(() => {
  fetchUser()
  if (mdAndUp.value) {
    sideOpen.value = true
  }
})
watch(() => route.path, fetchUser)
</script>

<style>
html, body, #app {
  height: 100%;
}

.logo-text {
  font-size: 16px !important;
}

.color-primary {
  color: #1867C0;
}

.bg-gradient-overlay {
  background: linear-gradient(to top, rgba(0, 0, 0, 0.8) 0%, transparent 100%);
  width: 100%;
}

.main-gradient-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 400px;
  background: linear-gradient(180deg, rgba(24, 103, 192, 0.08) 0%, rgba(255, 255, 255, 0) 100%);
  pointer-events: none;
}

:deep(.v-navigation-drawer__content) {
  overflow-y: auto;
}

:deep(.v-list-item--active) {
  background: rgba(24, 103, 192, 0.1) !important;
  color: #1867C0 !important;
}

.gap-2 {
  gap: 8px;
}

.cursor-pointer {
  cursor: pointer;
}

.border-md {
  border-width: 2px !important;
  border-style: solid;
}
</style>
