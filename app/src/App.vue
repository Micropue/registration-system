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
          :exact="item.exact"
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
            <v-menu v-model="notifMenuOpen" location="bottom end" :close-on-content-click="false" min-width="320">
              <template v-slot:activator="{ props: menuProps }">
                <v-badge :model-value="unreadCount > 0" :content="unreadCount" color="error" overlap>
                  <v-btn icon="mdi-bell-outline" variant="text" size="small" v-bind="menuProps"
                    @click="openNotifications"></v-btn>
                </v-badge>
              </template>
              <v-list density="compact" max-height="400" style="overflow-y: auto;">
                <div class="d-flex justify-space-between align-center pa-2">
                  <span class="text-subtitle-2 font-weight-bold">消息</span>
                  <v-btn v-if="unreadCount > 0" variant="text" size="x-small" @click="markAllRead">全部已读</v-btn>
                </div>
                <v-divider></v-divider>
                <div v-if="notifications.length === 0" class="pa-4 text-center text-grey">暂无消息</div>
                <v-list-item v-for="n in notifications" :key="n.id" :class="!n.is_read ? 'bg-primary-lighten-5' : ''"
                  @click="handleNotificationClick(n)" density="compact" class="mb-1">
                  <template v-slot:prepend>
                    <v-icon size="18" :color="n.is_read ? 'grey' : 'primary'">mdi-circle</v-icon>
                  </template>
                  <v-list-item-title class="text-body-2">{{ n.title }}</v-list-item-title>
                  <v-list-item-subtitle class="text-caption">{{ n.content }}</v-list-item-subtitle>
                  <template v-slot:append>
                    <span class="text-caption text-grey">{{ formatNotifDate(n.created_at) }}</span>
                  </template>
                </v-list-item>
              </v-list>
            </v-menu>
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
import { ref, onMounted, watch, computed, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useDisplay } from 'vuetify'
import { checkLoginStatus } from '@/api/auth'
import { cookie } from '@/api/cookie'
import { ajax } from '@/api/ajax'
import { functions } from '@/config/functions'
import { useAppStore } from '@/stores/app'
import { useChatStore } from '@/stores/chat'
import type { CheckLoginData } from '@/config/api-type'

const router = useRouter()
const route = useRoute()
const { mobile } = useDisplay()
const appStore = useAppStore()
const chatStore = useChatStore()
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
  if (user.value) {
  }
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

const unreadCount = ref(0)
const notifications = ref<any[]>([])
const notifMenuOpen = ref(false)
let notifTimer: any = null

async function fetchNotifications() {
  if (!user.value) return
  try {
    const [countRes, listRes] = await Promise.all([
      ajax<any>('/api/notifications/unread-count', { headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` } }),
      ajax<any[]>('/api/notifications', { headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` } })
    ])
    if (countRes.code === 200) unreadCount.value = countRes.data.count
    if (listRes.code === 200) {
      notifications.value = listRes.data
      const counts: Record<string, number> = {}
      for (const n of listRes.data) {
        if (n.type === 'chat_message' && !n.is_read && n.reference_id) {
          counts[n.reference_id] = (counts[n.reference_id] || 0) + 1
        }
      }
      chatStore.setUnreadCounts(counts)
    }
  } catch (e) { /* ignore */ }
}

function openNotifications() {
  fetchNotifications()
}

async function markAllRead() {
  try {
    await ajax('/api/notifications/read-all', {
      method: 'POST', headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
    })
    unreadCount.value = 0
    notifications.value = notifications.value.map((n: any) => ({ ...n, is_read: true }))
  } catch (e) { /* ignore */ }
}

async function handleNotificationClick(n: any) {
  if (!n.is_read) {
    try {
      await ajax(`/api/notifications/${n.id}/read`, {
        method: 'POST', headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
      })
      n.is_read = true
      unreadCount.value = Math.max(0, unreadCount.value - 1)
    } catch (e) { /* ignore */ }
  }
  const isAdmin = user.value?.type === 'admin'
  if (n.type === 'new_registration') {
    router.push({ path: '/admin/registers', query: n.reference_id ? { chat: n.reference_id } : {} })
  }
  else if (n.type === 'registration_rejected') {
    router.push({ path: '/sign', query: n.reference_id ? { chat: n.reference_id } : {} })
  }
  else if (n.type === 'chat_message') {
    const targetPath = isAdmin ? '/admin/registers' : '/sign'
    if (n.reference_id) {
      router.push({ path: targetPath, query: { chat: n.reference_id } })
    } else {
      router.push(targetPath)
    }
  }
  else if (n.type === 'feedback_replied' || n.type === 'new_feedback' || n.type === 'feedback_status') {
    const targetPath = isAdmin ? '/admin/feedbacks' : '/feedback'
    if (n.reference_id) {
      router.push({ path: targetPath, query: { id: n.reference_id } })
    } else {
      router.push(targetPath)
    }
  }
  notifMenuOpen.value = false
}

function formatNotifDate(iso: string) {
  if (!iso) return ''
  const d = new Date(iso)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  return d.toLocaleDateString('zh-CN')
}

onMounted(() => {
  fetchUser()
  if (mdAndUp.value) {
    sideOpen.value = true
  }
  notifTimer = setInterval(fetchNotifications, 30000)
  setTimeout(fetchNotifications, 2000)
})

onUnmounted(() => {
  if (notifTimer) clearInterval(notifTimer)
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

:deep(.v-navigation-drawer .v-list-item) {
  font-size: 14px;
}
:deep(.v-navigation-drawer .v-list-item .v-list-item-title) {
  font-size: 14px;
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
