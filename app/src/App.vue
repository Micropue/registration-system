<template>
  <v-app style="height: 100%">
    <!-- 左侧导航栏 (桌面端响应式固定，移动端为抽屉) -->
    <v-navigation-drawer v-model="sideOpen" app width="260" elevation="0" class="border-e">
      <!-- 用户信息 -->
      <div v-if="user" class="py-3 d-flex align-center px-4 user-agent">
        <div class="background">
          <Prism style="height: 100%;" :intensity="3" :speed="1" :distort="5.3" />
        </div>
        <v-avatar size="32" class="me-3 avatar">
          <span class="text-white font-weight-bold text-body-2">{{ user.username.charAt(0).toUpperCase() }}</span>
        </v-avatar>
        <div>
          <div class="text-body-2 font-weight-bold">{{ user.username }}</div>
          <div class="text-caption text-grey">{{ user.group_name || '未分配' }}</div>
        </div>
      </div>
      <div v-else-if="!isAuthChecking" class="pa-4">
        <v-btn color="primary" variant="flat" to="/login" block elevation="0">
          登录
        </v-btn>
      </div>


      <!-- 导航菜单 -->
      <v-list nav density="compact" class="pa-2">
        <v-list-item v-for="item in mainFunctions" :key="item.to" :to="item.to" :exact="item.exact" rounded="xl" active-color="primary" class="mb-1">
          <template v-slot:prepend>
            <v-badge :model-value="(pendingCounts[item.title] || 0) > 0" :content="pendingCounts[item.title]" color="error" offset-x="4" offset-y="4" size="small" inline>
              <v-icon>{{ item.icon }}</v-icon>
            </v-badge>
          </template>
          <v-list-item-title>{{ item.title }}</v-list-item-title>
        </v-list-item>
        <v-divider v-if="bottomFunctions.length > 0" class="mt-2 mb-1"></v-divider>
        <v-list-item v-for="item in bottomFunctions" :key="item.to" :to="item.to" :exact="item.exact" rounded="xl" active-color="primary" class="mb-1">
          <template v-slot:prepend>
            <v-icon>{{ item.icon }}</v-icon>
          </template>
          <v-list-item-title>{{ item.title }}</v-list-item-title>
        </v-list-item>
      </v-list>
    </v-navigation-drawer>

    <!-- 顶部导航栏 -->
    <v-app-bar app flat class="px-3 px-md-6 border-b" style="backdrop-filter: blur(12px);">
      <v-container class="d-flex align-center pa-0" fluid>
        <v-app-bar-nav-icon class="me-1" @click="toggleSidebar"></v-app-bar-nav-icon>
        <div class="d-flex align-center cursor-pointer" @click="router.push('/')">
          <v-avatar size="36" class="me-2 ml-5">
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
            <!-- 待处理任务 -->
            <v-menu v-model="pendingMenuOpen" location="bottom end" :close-on-content-click="false" min-width="320">
              <template v-slot:activator="{ props: menuProps }">
                <v-badge :model-value="pendingTotalCount > 0" :content="pendingTotalCount" color="error" overlap>
                  <v-btn icon="mdi-clipboard-list-outline" variant="text" size="small" v-bind="menuProps"
                    @click="fetchPendingList"></v-btn>
                </v-badge>
              </template>
              <v-list density="compact" max-height="400" style="overflow-y: auto;">
                <div class="d-flex justify-space-between align-center pa-2">
                  <span class="text-subtitle-2 font-weight-bold">待处理任务</span>
                </div>
                <v-divider></v-divider>
                <div v-if="pendingList.length === 0" class="pa-4 text-center text-grey">暂无待处理任务</div>
                <v-list-item v-for="n in pendingList" :key="n.id"
                  @click="handlePendingClick(n)" density="compact" class="mb-1">
                  <template v-slot:prepend>
                    <v-icon size="18" :color="typeColor(n.type)">{{ typeIcon(n.type) }}</v-icon>
                  </template>
                  <v-list-item-title class="text-body-2">{{ n.title }}</v-list-item-title>
                  <v-list-item-subtitle class="text-caption">{{ n.content }}</v-list-item-subtitle>
                  <template v-slot:append>
                    <span class="text-caption text-grey">{{ formatNotifDate(n.created_at) }}</span>
                  </template>
                </v-list-item>
              </v-list>
            </v-menu>

            <!-- 通知消息 -->
            <v-menu v-model="notifMenuOpen" location="bottom end" :close-on-content-click="false" min-width="320">
              <template v-slot:activator="{ props: menuProps }">
                <v-badge :model-value="notifUnreadCount > 0" :content="notifUnreadCount" color="error" overlap>
                  <v-btn icon="mdi-bell-outline" variant="text" size="small" v-bind="menuProps"
                    @click="fetchNotifications"></v-btn>
                </v-badge>
              </template>
              <v-list density="compact" max-height="400" style="overflow-y: auto;">
                <div class="d-flex justify-space-between align-center pa-2">
                  <span class="text-subtitle-2 font-weight-bold">消息</span>
                  <v-btn v-if="notifUnreadCount > 0" variant="text" size="x-small" @click="markAllRead">全部已读</v-btn>
                </div>
                <v-divider></v-divider>
                <div v-if="notifList.length === 0" class="pa-4 text-center text-grey">暂无消息</div>
                <v-list-item v-for="n in notifList" :key="n.id" :class="!n.is_read ? 'bg-primary-lighten-5' : ''"
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
            <v-btn v-if="user && needRefresh" icon="mdi-update" variant="text" size="small" color="warning"
              class="me-1" @click="refreshApp" title="有新版本可用，点击更新">
            </v-btn>
            <v-btn v-else-if="user" icon="mdi-cellphone-arrow-down" variant="text" size="small"
              class="me-1" title="检查PWA更新" @click="checkForUpdate" :loading="isCheckingUpdate">
            </v-btn>
            <v-btn color="error" variant="tonal" class="rounded-pill px-4 font-weight-bold" size="small"
              @click="handleLogout">
              退出登录
            </v-btn>
          </template>
          <v-btn v-else-if="!isAuthChecking" color="primary" variant="flat" to="/login"
            class="rounded-pill px-6 font-weight-bold" elevation="0">
            登录
          </v-btn>
          <v-btn v-else color="primary" variant="flat" class="rounded-pill px-6 font-weight-bold" elevation="0" disabled
            loading>
            检测中
          </v-btn>
        </div>
      </v-container>
    </v-app-bar>

    <v-main class="overflow-y-auto" style="height: 100%;">
      <div class="main-gradient-bg"></div>
      <RouterView />
    </v-main>

    <v-overlay v-model="needRefresh" class="align-center justify-center" persistent scroll-strategy="block">
      <v-card rounded="xl" max-width="420" elevation="12" class="pa-8 text-center">
        <v-icon size="64" color="primary" class="mb-4">mdi-update</v-icon>
        <h2 class="text-h5 font-weight-bold mb-2">发现新版本</h2>
        <p class="text-body-1 text-medium-emphasis mb-6">检测到新版本可用，请更新后继续使用。</p>
        <v-btn color="primary" variant="flat" size="large" rounded="lg" block
          @click="refreshApp" class="font-weight-bold">
          立即更新
        </v-btn>
      </v-card>
    </v-overlay>

    <v-dialog v-model="announceDialog.show" max-width="520">
      <v-card rounded="xl" v-if="announceDialog.data">
        <v-card-title class="d-flex align-center pa-4">
          <v-icon color="primary" class="mr-2" size="28">mdi-bullhorn</v-icon>
          <span class="text-h6 font-weight-bold">{{ announceDialog.data.title }}</span>
          <v-spacer></v-spacer>
          <v-btn icon="mdi-close" variant="text" @click="announceDialog.show = false"></v-btn>
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text class="pa-4" style="white-space: pre-wrap; line-height: 1.8;">
          {{ announceDialog.data.content }}
        </v-card-text>
        <v-divider></v-divider>
        <v-card-actions class="pa-4">
          <span class="text-caption text-medium-emphasis">{{ announceDialog.data.publisher_name }} · {{ formatDate(announceDialog.data.create_time) }}</span>
          <v-spacer></v-spacer>
          <v-btn color="primary" variant="flat" rounded="lg" @click="announceDialog.show = false">我知道了</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-app>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed, onUnmounted, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useDisplay } from 'vuetify'
import { checkLoginStatus } from '@/api/auth'
import { cookie } from '@/api/cookie'
import { ajax } from '@/api/ajax'
import { functions } from '@/config/functions'
import { useAppStore } from '@/stores/app'
import { useChatStore } from '@/stores/chat'
import type { CheckLoginData } from '@/config/api-type'
import { useRegisterSW } from 'virtual:pwa-register/vue'
import Prism from './components/effect/prism.vue'

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

const ADMIN_PERM_KEYS = ['账户管理', '账户组管理', '订单处理', '工单处理', 'APP配置', '充值审批', '下属管理', '公告管理']

function hasAnyAdminPerm(permissions: Record<string, any> | undefined): boolean {
  if (!permissions) return false
  return ADMIN_PERM_KEYS.some(key => {
    const val = permissions[key]
    if (typeof val === 'object' && val !== null) return Object.values(val).some(Boolean)
    return !!val
  })
}

function hasPerm(permissions: Record<string, any> | undefined, key: string): boolean {
  if (!permissions) return false
  if (key.includes('.')) {
    const [parent, child] = key.split('.')
    const parentVal = permissions[parent]
    if (typeof parentVal === 'object' && parentVal !== null) return !!parentVal[child]
    return false
  }
  const val = permissions[key]
  if (typeof val === 'object' && val !== null) return Object.values(val).some(Boolean)
  return !!val
}

const PERM_MAP: Record<string, string> = {
  '/admin/groups': '账户组管理.查看',
  '/admin/recharges': '充值审批.查看',
  '/admin/users': '账户管理.查看',
  '/admin/registers': '订单处理.查看',
  '/admin/feedbacks': '工单处理.查看',
  '/admin/running-apps': 'APP配置.查看',
  '/admin/update-logs': 'APP配置.查看',
  '/admin/announcements': '公告管理.查看',
  '/admin/subordinates': '下属管理.查看',
  '/sign': '新建登记',
  '/feedback': '新建工单',
  '/recharge': '充值申请',
  '/balance': '余额查看',
  '/balance-transactions': '余额查看',
}

const displayFunctions = computed(() => {
  if (!user.value) return []
  const perms = user.value.permissions
  if (!perms || typeof perms !== 'object') return []

  return functions.filter(item => {
    const required = PERM_MAP[item.to]
    if (required) return hasPerm(perms, required)
    if (item.to === '/admin' && item.exact) return hasAnyAdminPerm(perms)
    if (item.role === 'default' || !item.role) return true
    return false
  })
})

const mainFunctions = computed(() => displayFunctions.value.filter(f => !f.group))
const bottomFunctions = computed(() => displayFunctions.value.filter(f => f.group === 'bottom'))

async function fetchUser() {
  isAuthChecking.value = true
  const prevUser = user.value
  user.value = await checkLoginStatus()
  appStore.setUserInfo(user.value)
  if (user.value && !prevUser) {
    fetchPendingCounts()
    setTimeout(connectNotifWs, 1000)
  }
  fetchNotifications()
  fetchLatestAnnouncement()
  isAuthChecking.value = false
}

function toggleSidebar() {
  sideOpen.value = !sideOpen.value
}

function handleLogout() {
  cookie.remove('token')
  user.value = null
  appStore.setUserInfo(null)
  notifList.value = []
  pendingList.value = []
  businessBadges.value = {}
  if (notifWs) { notifWs.close(); notifWs = null }
  if (reconnectTimer) { clearTimeout(reconnectTimer); reconnectTimer = null }
  router.push('/login')
}

const pendingList = ref<any[]>([])
const pendingMenuOpen = ref(false)
const notifList = ref<any[]>([])
const notifMenuOpen = ref(false)
const businessBadges = ref<Record<string, number>>({})
const pendingTotalCount = computed(() => {
  return Object.values(businessBadges.value).reduce((a, b) => a + b, 0)
})
const notifUnreadCount = computed(() => notifList.value.filter((n: any) => !n.is_read).length)
let notifWs: WebSocket | null = null
let reconnectTimer: any = null

function typeIcon(type: string) {
  if (type === 'pending_registration') return 'mdi-file-document-outline'
  if (type === 'pending_feedback') return 'mdi-message-text-outline'
  if (type === 'pending_recharge') return 'mdi-cash-plus'
  return 'mdi-circle'
}

function typeColor(type: string) {
  if (type === 'pending_registration') return 'primary'
  if (type === 'pending_feedback') return 'warning'
  if (type === 'pending_recharge') return 'success'
  return 'grey'
}

const pendingCounts = computed(() => {
  const isAdmin = user.value?.role !== 'default'
  const result: Record<string, number> = { '订单': 0, '工单反馈': 0, '充值申请': 0 }
  for (const n of notifList.value) {
    if (n.is_read) continue
    if (n.type === 'chat_message' || n.type === 'registration_approved' || n.type === 'registration_rejected') {
      result['订单']++
    } else if (n.type === 'feedback_replied' || n.type === 'feedback_status') {
      result['工单反馈']++
    } else if (n.type === 'recharge_approved' || n.type === 'recharge_rejected') {
      result['充值申请']++
    }
  }
  if (isAdmin) {
    result['订单处理'] = businessBadges.value['订单处理'] || 0
    result['工单处理'] = businessBadges.value['工单处理'] || 0
    result['充值审批'] = businessBadges.value['充值审批'] || 0
  }
  return result
})

function connectNotifWs() {
  const token = cookie.get('token')
  if (!token || !user.value) return
  if (notifWs && notifWs.readyState === WebSocket.OPEN) return
  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = location.host
  notifWs = new WebSocket(`${protocol}//${host}/ws/notifications?token=${token}`)
  notifWs.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      if (data.type === 'notification_update') {
        if (data.status === 'to_unread') {
          const exists = notifList.value.find((n: any) => n.id === data.id)
          if (!exists) {
            notifList.value.unshift({
              id: data.id, type: data.notif_type, title: data.title || '',
              content: data.content || '', reference_id: data.reference_id || '',
              is_read: false, created_at: data.created_at
            })
          }
        } else if (data.status === 'to_read') {
          const item = notifList.value.find((n: any) => n.id === data.id)
          if (item) item.is_read = true
        } else if (data.status === 'all_read') {
          notifList.value.forEach((n: any) => { n.is_read = true })
        }
      } else if (data.type === 'business_update') {
        const isAdmin = user.value?.role !== 'default'
        if (isAdmin) {
          businessBadges.value[data.key] = Math.max(0, (businessBadges.value[data.key] || 0) + (data.delta || 0))
        }
      } else if (data.type === 'chat_unread') {
        chatStore.incrementUnread(data.uid)
      }
    } catch (e) { /* ignore */ }
  }
  notifWs.onclose = () => {
    reconnectTimer = setTimeout(() => { fetchNotifications(); fetchPendingCounts(); connectNotifWs() }, 5000)
  }
  notifWs.onerror = () => {
    notifWs?.close()
  }
}

async function fetchNotifications() {
  if (!user.value) return
  try {
    const res = await ajax<any>('/api/notifications?page=1&page_size=20', {
      headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
    })
    if (res.code === 200 && res.data) {
      notifList.value = res.data.items || []
    }
  } catch (e) { /* ignore */ }
}

async function fetchPendingList() {
  if (!user.value) return
  try {
    const res = await ajax<any>('/api/pending-items', {
      headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
    })
    if (res.code === 200 && res.data) {
      pendingList.value = res.data.items || []
      if (res.data.counts) {
        businessBadges.value = res.data.counts
      }
    }
  } catch (e) { /* ignore */ }
}

async function fetchPendingCounts() {
  if (!user.value) return
  try {
    const res = await ajax<any>('/api/admin/dashboard/stats', {
      headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
    })
    if (res.code === 200 && res.data) {
      businessBadges.value = {
        '订单处理': res.data.pending_registrations || 0,
        '工单处理': (res.data.pending_feedbacks || 0) + (res.data.unread_feedbacks || 0),
        '充值审批': res.data.pending_recharges || 0,
      }
    }
  } catch (e) { /* ignore */ }
}

async function markAllRead() {
  try {
    await ajax('/api/notifications/read-all', {
      method: 'POST', headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
    })
    notifList.value.forEach((n: any) => { n.is_read = true })
  } catch (e) { /* ignore */ }
}

async function handleNotificationClick(n: any) {
  if (!n.is_read) {
    const item = notifList.value.find((x: any) => x.id === n.id)
    if (item) item.is_read = true
    try {
      await ajax(`/api/notifications/${n.id}/read`, {
        method: 'POST', headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
      })
    } catch (e) { /* ignore */ }
  }
  const isAdmin = user.value?.role !== 'default'
  if (n.type === 'chat_message') {
    const targetPath = isAdmin ? '/admin/registers' : '/sign'
    router.push({ path: targetPath, query: n.reference_id ? { chat: n.reference_id } : {} })
  }
  else if (n.type === 'registration_rejected' || n.type === 'registration_approved') {
    router.push({ path: '/sign', query: n.reference_id ? { chat: n.reference_id } : {} })
  }
  else if (n.type === 'feedback_replied' || n.type === 'feedback_status') {
    router.push({ path: '/feedback', query: n.reference_id ? { id: n.reference_id } : {} })
  }
  else if (n.type === 'recharge_approved' || n.type === 'recharge_rejected') {
    router.push('/recharge')
  }
  notifMenuOpen.value = false
}

function handlePendingClick(n: any) {
  if (n.type === 'pending_registration') {
    router.push({ path: '/admin/registers', query: n.reference_id ? { chat: n.reference_id } : {} })
  }
  else if (n.type === 'pending_feedback') {
    router.push({ path: '/admin/feedbacks', query: n.reference_id ? { id: n.reference_id } : {} })
  }
  else if (n.type === 'pending_recharge') {
    router.push('/admin/recharges')
  }
  pendingMenuOpen.value = false
}

function formatNotifDate(iso: string) {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleString('zh-CN', { hour12: false })
}

function formatDate(iso: string) {
  if (!iso) return ''
  return new Date(iso).toLocaleString('zh-CN')
}

const announceDialog = reactive({ show: false, data: null as any })

const announcedIds = ref<Set<string>>(new Set())
if (typeof localStorage !== 'undefined') {
  try {
    announcedIds.value = new Set(JSON.parse(localStorage.getItem('announced_ids') || '[]'))
  } catch { /* ignore */ }
}

async function fetchLatestAnnouncement() {
  try {
    const token = cookie.get('token') || ''
    const res = await ajax<any>('/api/announcements/latest')
    if (res.code === 200 && res.data) {
      if (!announcedIds.value.has(res.data.uid)) {
        announceDialog.data = res.data
        announceDialog.show = true
        announcedIds.value.add(res.data.uid)
        localStorage.setItem('announced_ids', JSON.stringify([...announcedIds.value]))
      }
    }
  } catch { /* ignore */ }
}

onMounted(async () => {
  await fetchUser()
  if (mdAndUp.value) {
    sideOpen.value = true
  }
})

onUnmounted(() => {
  if (reconnectTimer) clearTimeout(reconnectTimer)
  if (notifWs) notifWs.close()
})
watch(() => route.path, fetchUser)

watch(() => route.path, (path) => {
  const types: string[] = []
  if (path === '/sign' || path.startsWith('/sign?')) {
    types.push('chat_message', 'registration_approved', 'registration_rejected')
  } else if (path === '/feedback' || path.startsWith('/feedback?')) {
    types.push('feedback_replied', 'feedback_status')
  } else if (path === '/recharge' || path.startsWith('/recharge?')) {
    types.push('recharge_approved', 'recharge_rejected')
  } else if (path.startsWith('/admin/registers')) {
    types.push('chat_message', 'registration_approved', 'registration_rejected')
  } else if (path.startsWith('/admin/feedbacks')) {
    types.push('feedback_replied', 'feedback_status')
  } else if (path.startsWith('/admin/recharges')) {
    types.push('recharge_approved', 'recharge_rejected')
  }
  if (types.length > 0) {
    ajax('/api/notifications/read-by-types', {
      method: 'POST',
      body: { types },
      headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
    }).catch(() => {})
    for (const n of notifList.value) {
      if (!n.is_read && types.includes(n.type)) n.is_read = true
    }
  }
})

const { needRefresh, updateServiceWorker } = useRegisterSW()

const isCheckingUpdate = ref(false)

async function checkForUpdate() {
  isCheckingUpdate.value = true
  try {
    if ('serviceWorker' in navigator) {
      const reg = await navigator.serviceWorker.getRegistration()
      if (reg) {
        await reg.update()
        setTimeout(() => {
          if (reg.waiting) {
            reg.waiting.postMessage({ type: 'SKIP_WAITING' })
          }
          isCheckingUpdate.value = false
        }, 1000)
        return
      }
    }
  } catch (e) { /* ignore */ }
  isCheckingUpdate.value = false
}

function refreshApp() {
  updateServiceWorker()
}
</script>

<style>
html,
body,
#app {
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

.user-agent {
  position: relative;
  color: white;
  height: 60px;
  margin: 5px;
  overflow: hidden;
  border-radius: 8px;

  .avatar{
    background-color: rgba(185, 185, 185, 0.167);
    backdrop-filter: blur(2px);
  }
  .background {
    position: absolute;
    width: 100%;
    top: 0;
    left: 0;
    height: 100%;
    background-color: black;
    z-index: -1;
  }
}
</style>
