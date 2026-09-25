<template>
  <div class="d-flex justify-center pa-4 chat-room-page">
    <v-card class="chat-shell" rounded="xl" elevation="0" border>
      <!-- 顶栏 -->
      <div class="d-flex align-center px-4 chat-toolbar">
        <div class="d-flex align-center">
          <v-icon color="primary" class="me-2">mdi-forum-outline</v-icon>
          <span class="font-weight-bold">全局聊天室</span>
          <v-chip v-if="wsConnected" size="x-small" color="success" variant="tonal" class="ms-2">
            <v-icon size="12" class="me-1">mdi-wifi</v-icon>已连接
          </v-chip>
          <v-chip v-else size="x-small" color="warning" variant="tonal" class="ms-2">
            连接中...
          </v-chip>
        </div>
        <v-spacer></v-spacer>
        <v-menu location="bottom end">
          <template v-slot:activator="{ props: menuProps }">
            <v-btn variant="text" size="small" v-bind="menuProps" class="text-none">
              <v-icon class="me-1" size="16">mdi-account-group</v-icon>
              在线 {{ onlineCount }}
            </v-btn>
          </template>
          <v-list density="compact" max-height="320" style="overflow-y: auto;" min-width="200">
            <v-list-subheader class="text-caption">在线用户列表</v-list-subheader>
            <v-list-item v-if="onlineList.length === 0" density="compact" disabled>
              暂无在线用户
            </v-list-item>
            <v-list-item v-for="u in onlineList" :key="u.uid" density="compact">
              <template v-slot:prepend>
                <v-avatar :color="isMe(u) ? 'primary' : 'grey-lighten-2'" size="28" class="me-2">
                  <span :class="isMe(u) ? 'text-white' : ''" class="text-caption font-weight-bold">{{ u.username.charAt(0).toUpperCase() }}</span>
                </v-avatar>
              </template>
              <v-list-item-title class="text-body-2">{{ u.username }}<span v-if="isMe(u)" class="text-grey"> (我)</span></v-list-item-title>
              <template v-slot:append>
                <v-icon v-if="u.is_admin" size="14" color="primary" title="管理员">mdi-shield-account</v-icon>
                <span v-else class="online-dot"></span>
              </template>
            </v-list-item>
          </v-list>
        </v-menu>
      </div>

      <v-divider></v-divider>

      <div class="d-flex chat-body">
        <!-- 消息列 -->
        <div class="chat-main">
          <!-- 置顶公告 -->
          <div v-if="pinnedMsg" class="pinned-banner">
            <div class="d-flex align-center">
              <v-icon size="16" color="warning" class="me-1">mdi-pin</v-icon>
              <span class="text-caption font-weight-bold text-warning me-2">群公告</span>
              <span class="text-caption text-grey">—— {{ pinnedMsg.username }}</span>
            </div>
            <div class="pinned-content mt-1">
              <span v-if="pinnedMsg.msg_type === 'image'" class="text-body-2">[图片消息]</span>
              <span v-else class="text-body-2">{{ pinnedMsg.message }}</span>
            </div>
            <div class="d-flex justify-end mt-1" v-if="isAdminUser">
              <v-btn size="x-small" variant="text" color="grey" @click="unpinMessage" class="text-none">
                <v-icon size="14" class="me-1">mdi-pin-off</v-icon>取消置顶
              </v-btn>
            </div>
          </div>

          <!-- 消息区 -->
          <div class="chat-messages" ref="msgContainer">
            <div v-if="loadingHistory" class="d-flex justify-center py-6">
              <v-progress-circular indeterminate size="24" color="primary"></v-progress-circular>
            </div>
            <div v-else>
              <div v-if="hasMore && messages.length > 0" class="d-flex justify-center py-2">
                <v-btn size="small" variant="tonal" color="primary" :loading="loadingOlder" @click="loadOlder">
                  <v-icon size="16" class="me-1">mdi-history</v-icon>
                  加载更早消息
                </v-btn>
              </div>
              <div v-if="messages.length === 0" class="chat-empty">
                <v-icon size="48" color="grey-lighten-1" class="mb-2">mdi-chat-outline</v-icon>
                <div class="text-body-2 font-weight-medium text-medium-emphasis">暂无消息记录</div>
                <div class="text-caption text-disabled mt-1">发条消息开始聊天吧</div>
              </div>
              <div v-for="(msg, idx) in messages" :key="msg.id">
                <div v-if="showDayDivider(idx)" class="day-divider">
                  <span>{{ formatDay(msg.created_at) }}</span>
                </div>
                <div :class="['msg-row', isSelf(msg) ? 'is-self' : 'is-other']">
                  <div class="msg-wrapper">
                    <div v-if="!isSelf(msg)" class="msg-meta">
                      <span class="msg-username" :class="{ 'admin-name': msg.is_admin }">
                        {{ msg.username }}<v-icon v-if="msg.is_admin" size="12" class="ms-1 mb-1" color="primary">mdi-shield-account</v-icon>
                      </span>
                      <span class="msg-time">{{ formatTime(msg.created_at) }}</span>
                    </div>
                    <div v-else class="msg-time text-end">{{ formatTime(msg.created_at) }}</div>

                    <div class="msg-bubble-row">
                      <div :class="['msg-bubble', isSelf(msg) ? 'bubble-self' : 'bubble-other']">
                        <!-- 撤回消息 -->
                        <div v-if="msg.is_recalled" class="recalled-msg">
                          <v-icon size="14" class="me-1">mdi-cancel</v-icon>消息已撤回
                        </div>
                        <!-- 图片消息 -->
                        <div v-else-if="msg.msg_type === 'image'" class="img-msg">
                          <v-img :src="msg.image_url" max-width="260" min-width="120" aspect-ratio="1.4"
                            class="rounded-lg cursor-pointer" cover @click="previewImage(msg.image_url)"></v-img>
                          <div v-if="msg.message" class="mt-1 img-caption">{{ msg.message }}</div>
                        </div>
                        <!-- 订单卡片消息 -->
                        <div v-else-if="msg.msg_type === 'registration_card'" class="reg-card-msg">
                          <div class="card-row" @click="openRegistration(cardData(msg))">
                            <v-icon color="primary" class="me-2">mdi-file-document-outline</v-icon>
                            <div class="card-body">
                              <div class="card-title">{{ cardData(msg).title || '订单信息' }}</div>
                              <div class="card-text text-truncate">{{ cardData(msg).summary || '查看订单详情' }}</div>
                            </div>
                            <v-btn icon="mdi-open-in-new" size="x-small" variant="text"></v-btn>
                          </div>
                        </div>
                        <!-- 文本消息 -->
                        <div v-else class="text-msg">{{ msg.message }}</div>
                      </div>
                      <!-- 操作按钮 -->
                      <div class="msg-hover-actions" v-if="!msg.is_recalled">
                        <v-btn v-if="pinnedMsg?.id === msg.id" icon size="x-small" variant="text" color="warning"
                          @click="unpinMessage" title="取消置顶">
                          <v-icon size="14">mdi-pin-off</v-icon>
                        </v-btn>
                        <v-btn v-else-if="isAdminUser" icon size="x-small" variant="text"
                          @click="pinMessage(msg.id)" title="设为群公告">
                          <v-icon size="14">mdi-pin</v-icon>
                        </v-btn>
                        <v-btn v-if="isSelf(msg)" icon size="x-small" variant="text"
                          @click="recallMessage(msg.id)" title="撤回">
                          <v-icon size="14">mdi-undo</v-icon>
                        </v-btn>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 输入区 -->
          <div class="chat-input-area">
            <div v-if="pendingImage" class="d-inline-flex align-center pending-img">
              <v-img :src="pendingImage" width="60" height="60" cover class="rounded me-2"></v-img>
              <v-btn icon="mdi-close-circle" size="x-small" variant="text" @click="clearPendingImage"></v-btn>
            </div>
            <div class="d-flex align-end">
              <input ref="fileInput" type="file" accept="image/png,image/jpeg,image/webp,image/gif,image/heic,image/heif"
                class="d-none" @change="onFileSelected" />
              <v-btn icon="mdi-image-outline" variant="text" class="me-1 mb-1" title="发送图片"
                @click="fileInput?.click()" :disabled="!wsReady || sending"></v-btn>
              <v-btn icon="mdi-file-document-outline" variant="text" class="me-1 mb-1" title="发送订单"
                @click="openOrderPicker" :disabled="!wsReady || sending || orderListLoading"></v-btn>
              <v-textarea v-model="input" density="compact" variant="solo-filled" flat auto-grow rows="1"
                hide-details class="chat-input" placeholder="输入消息...（Enter 发送，Shift+Enter 换行）"
                @keydown.enter.exact.prevent="send" :disabled="sending"></v-textarea>
              <v-btn icon="mdi-send" variant="flat" color="primary" size="42" elevation="2"
                class="send-btn ms-2 mb-1" @click="send" :disabled="!canSend || !wsReady" :loading="sending"></v-btn>
            </div>
            <div class="text-caption text-grey mt-1">
              <span>支持多行消息（Shift+Enter 换行）</span>
            </div>
          </div>
        </div>

        <!-- 右侧在线用户列（桌面端） -->
        <div class="online-panel d-none d-lg-flex">
          <div class="panel-title">
            <span>在线用户</span>
            <v-chip size="x-small" color="primary" variant="tonal">{{ onlineCount }}</v-chip>
          </div>
          <v-divider></v-divider>
          <div class="panel-list">
            <div v-if="onlineList.length === 0" class="pa-4 text-center text-grey text-caption">
              暂无在线用户
            </div>
            <div v-for="u in onlineList" :key="u.uid" class="d-flex align-center py-2 px-2 online-item">
              <v-avatar :color="isMe(u) ? 'primary' : 'grey-lighten-3'" size="30">
                <span :class="isMe(u) ? 'text-white' : 'text-grey-darken-1'" class="text-caption font-weight-bold">
                  {{ u.username.charAt(0).toUpperCase() }}
                </span>
              </v-avatar>
              <span class="text-body-2 ms-2 text-truncate">{{ u.username }}</span>
              <span v-if="isMe(u)" class="text-caption text-grey ms-1">（我）</span>
              <v-spacer></v-spacer>
              <v-icon v-if="u.is_admin" size="14" color="primary" title="管理员">mdi-shield-account</v-icon>
            </div>
          </div>
        </div>
      </div>
    </v-card>

    <!-- 图片预览弹窗 -->
    <v-dialog v-model="previewDialog" max-width="600" @click:outside="previewDialog = false">
      <v-img :src="previewUrl" max-height="80vh" contain class="rounded-lg"></v-img>
    </v-dialog>

    <!-- 选择订单弹窗 -->
    <v-dialog v-model="orderPickerShow" max-width="640">
      <v-card rounded="xl">
        <v-card-title class="d-flex align-center">
          <v-icon class="me-2" color="primary">mdi-file-document-outline</v-icon>
          <span class="text-h6 font-weight-bold">选择要发送的订单</span>
          <v-spacer></v-spacer>
          <v-btn icon="mdi-close" variant="text" size="small" @click="orderPickerShow = false"></v-btn>
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text class="pa-2" style="max-height: 400px; overflow-y: auto;">
          <div v-if="orderListLoading" class="d-flex justify-center py-8">
            <v-progress-circular indeterminate color="primary"></v-progress-circular>
          </div>
          <div v-else-if="orderList.length === 0" class="pa-6 text-center text-grey">
            暂无可发送的订单
          </div>
          <v-list-item v-for="o in orderList" :key="o.id" class="order-item rounded-lg mb-1"
            @click="sendRegistrationCard(o)">
            <template v-slot:prepend>
              <v-icon color="primary">mdi-file-document-outline</v-icon>
            </template>
            <v-list-item-title class="text-body-2 d-flex align-center">
              <span class="text-truncate">{{ orderSummary(o) }}</span>
            </v-list-item-title>
            <v-list-item-subtitle class="text-caption">
              {{ isAdminUser ? o.username : '' }} {{ formatDateTime(o.created_at) }}
              <v-chip size="x-small" :color="statusColor(o.status)" variant="tonal" class="ms-1">
                {{ statusText(o.status) }}
              </v-chip>
            </v-list-item-subtitle>
          </v-list-item>
        </v-card-text>
      </v-card>
    </v-dialog>

    <v-snackbar v-model="snackbar.show" :color="snackbar.color" timeout="3000" location="top center">
      {{ snackbar.text }}
    </v-snackbar>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, reactive, nextTick, onBeforeUnmount, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ajax } from '@/api/ajax'
import { cookie } from '@/api/cookie'
import { ApiUrl } from '@/config/api-url'
import { useAppStore } from '@/stores/app'

const router = useRouter()
const appStore = useAppStore()
const username = appStore.userInfo?.username || ''

const token = cookie.get('token') || ''

const messages = ref<any[]>([])
const input = ref('')
const sending = ref(false)
const loadingHistory = ref(false)
const loadingOlder = ref(false)
const hasMore = ref(false)
const msgContainer = ref<HTMLElement>()
const snackbar = reactive({ show: false, text: '', color: 'error' })

const onlineUsers = reactive<Record<string, any>>({})
const onlineList = computed(() => Object.values(onlineUsers) as any[])
const onlineCount = computed(() => onlineList.value.length)

const wsConnected = ref(false)
const wsReady = ref(false)
const pendingImage = ref('')
const pendingImageFile = ref<File | null>(null)
const fileInput = ref<HTMLInputElement>()
const previewDialog = ref(false)
const previewUrl = ref('')

const canSend = computed(() => input.value.trim() !== '' || !!pendingImageFile.value)
const pinnedMsg = ref<any>(null)

let ws: WebSocket | null = null
let reconnectTimer: any = null
let disposed = false

const isSelf = (msg: any) => msg.username === username
const isMe = (u: any) => u.username === username
const isAdminUser = computed(() => {
  const perms = appStore.userInfo?.permissions
  const v = perms?.['订单处理']
  return typeof v === 'object' && v !== null ? !!(v as any)['查看'] : !!v
})

function formatTime(iso: string) {
  if (!iso) return ''
  return new Date(iso).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', hour12: false })
}

function formatDay(iso: string) {
  const d = new Date(iso)
  const today = new Date()
  const sameDay = d.toDateString() === today.toDateString()
  return sameDay ? '今天' : d.toLocaleDateString('zh-CN', { month: 'long', day: 'numeric', weekday: 'short' })
}

function formatDateTime(iso: string) {
  if (!iso) return ''
  return new Date(iso).toLocaleString('zh-CN', { hour12: false })
}

function showDayDivider(idx: number) {
  if (idx === 0) return true
  const cur = new Date(messages.value[idx].created_at).toDateString()
  const prev = new Date(messages.value[idx - 1].created_at).toDateString()
  return cur !== prev
}

function showMsg(text: string, color = 'error') {
  snackbar.text = text
  snackbar.color = color
  snackbar.show = true
}

function scrollBottom() {
  nextTick(() => {
    if (msgContainer.value) {
      msgContainer.value.scrollTop = msgContainer.value.scrollHeight
    }
  })
}

async function loadHistory() {
  loadingHistory.value = true
  try {
    const res = await ajax<any>(ApiUrl.GET_GLOBAL_CHATS, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (res.code === 200 && res.data) {
      messages.value = res.data.items || []
      hasMore.value = !!res.data.has_more
    }
  } catch (e) { /* ignore */ }
  finally {
    loadingHistory.value = false
    scrollBottom()
  }
}

async function loadOlder() {
  if (loadingOlder.value || messages.value.length === 0) return
  loadingOlder.value = true
  const el = msgContainer.value
  const prevTop = el?.scrollTop || 0
  const prevHeight = el?.scrollHeight || 0
  try {
    const oldest = messages.value[0]
    const res = await ajax<any>(`${ApiUrl.GET_GLOBAL_CHATS}?before_id=${oldest.id}&limit=100`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (res.code === 200 && res.data?.items?.length) {
      messages.value = [...res.data.items, ...messages.value]
      hasMore.value = !!res.data.has_more
    } else {
      hasMore.value = false
    }
    nextTick(() => {
      // 顶部追加内容后保持原视口位置(仍显示同一批消息)
      if (el) el.scrollTop = el.scrollHeight - (prevHeight - prevTop)
    })
  } catch (e) { /* ignore */ }
  finally { loadingOlder.value = false }
}

function connectWs() {
  if (!token || disposed) return
  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
  ws = new WebSocket(`${protocol}//${location.host}/ws/global-chat?token=${token}`)
  ws.onopen = () => { wsConnected.value = true; wsReady.value = true }
  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      if (data.type === 'presence') {
        const map: Record<string, any> = {}
        for (const u of data.users || []) map[u.uid] = u
        Object.keys(onlineUsers).forEach(k => { if (!map[k]) delete onlineUsers[k] })
        Object.assign(onlineUsers, map)
      } else if (data.type === 'recall_message') {
        const msg = messages.value.find((m: any) => m.id === data.message_uid)
        if (msg) {
          msg.is_recalled = true
          setTimeout(() => {
            const idx = messages.value.findIndex((m: any) => m.id === data.message_uid)
            if (idx !== -1) messages.value.splice(idx, 1)
          }, 3000)
        }
      } else if (data.type === 'message') {
        if (!messages.value.some(m => m.id === data.id)) {
          messages.value.push(data)
          scrollBottom()
        }
      } else if (data.type === 'pin_update') {
        pinnedMsg.value = data.pinned || null
        if (data.by) showMsg(`${data.by} ${data.pinned ? '置顶了一条消息' : '取消了置顶'}`, 'info')
      } else if (data.type === 'error') {
        showMsg(data.message)
      }
    } catch (e) { /* ignore */ }
  }
  ws.onclose = () => {
    wsConnected.value = false
    wsReady.value = false
    if (!disposed) reconnectTimer = setTimeout(connectWs, 3000)
  }
  ws.onerror = () => { ws?.close() }
}

async function send() {
  const text = input.value.trim()
  if (!text && !pendingImageFile.value) return
  if (!ws || ws.readyState !== WebSocket.OPEN) return
  sending.value = true
  try {
    let imageUrl = ''
    if (pendingImageFile.value) {
      const res = await ajax<{ url: string }>('/api/upload/image', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: { file: pendingImageFile.value },
        isFormData: true
      })
      if (res.code !== 200 || !res.data?.url) {
        showMsg('图片上传失败')
        return
      }
      imageUrl = res.data.url
    }
    if (imageUrl) {
      ws.send(JSON.stringify({ msg_type: 'image', message: text, image_url: imageUrl }))
    } else {
      ws.send(JSON.stringify({ msg_type: 'text', message: text }))
    }
    input.value = ''
    clearPendingImage()
  } catch (e) { showMsg('发送失败') }
  finally { sending.value = false }
}

function onFileSelected(e: Event) {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  target.value = ''
  if (!file) return
  if (!file.type.startsWith('image/')) { showMsg('仅支持图片文件'); return }
  if (file.size > 1 * 1024 * 1024) { showMsg('图片大小不能超过 1MB'); return }
  pendingImageFile.value = file
  pendingImage.value = URL.createObjectURL(file)
}

function clearPendingImage() {
  if (pendingImage.value && pendingImage.value.startsWith('blob:')) URL.revokeObjectURL(pendingImage.value)
  pendingImage.value = ''
  pendingImageFile.value = null
}

function previewImage(url: string) {
  previewUrl.value = url
  previewDialog.value = true
}

/* ---- 订单卡片 ---- */

const orderPickerShow = ref(false)
const orderList = ref<any[]>([])
const orderListLoading = ref(false)

async function openOrderPicker() {
  orderPickerShow.value = true
  if (orderList.value.length > 0) return
  orderListLoading.value = true
  try {
    let items: any[] = []
    if (isAdminUser.value) {
      // 管理端列表默认只返回一次订单,需额外请求二次订单
      const base = '/api/admin/registrations'
      const [r1, r2] = await Promise.all([
        ajax<any>(`${base}?page=1&page_size=30`, { headers: { 'Authorization': `Bearer ${token}` } }),
        ajax<any>(`${base}?page=1&page_size=30&secondary=1`, { headers: { 'Authorization': `Bearer ${token}` } })
      ])
      items = [...(r1.code === 200 ? r1.data?.items || [] : []), ...(r2.code === 200 ? r2.data?.items || [] : [])]
    } else {
      const res = await ajax<any>('/api/registrations?page=1&page_size=30', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      items = res.code === 200 ? res.data?.items || [] : []
    }
    orderList.value = items.sort((a: any, b: any) => String(b.created_at).localeCompare(String(a.created_at)))
  } catch (e) { orderList.value = [] }
  finally { orderListLoading.value = false }
}

function orderSummary(o: any) {
  const data = o.data || {}
  const appName = data['应用'] || ''
  const keys = Object.keys(data).filter(k => k !== '应用' && !isImageVal(data[k])).slice(0, 2)
  const parts = keys.map(k => {
    const v = data[k]
    return Array.isArray(v) ? v.join('、') : String(v ?? '')
  }).filter(Boolean)
  return [appName, ...parts].join(' · ')
}

function isImageVal(v: any) {
  if (typeof v === 'string') return v.startsWith('/media/') || v.startsWith('http')
  if (Array.isArray(v)) return v.some(x => typeof x === 'string' && (x.startsWith('/media/') || x.startsWith('http')))
  return false
}

function statusText(status: string) {
  if (status === 'approved') return '已通过'
  if (status === 'rejected') return '已驳回'
  return '待处理'
}

function statusColor(status: string) {
  if (status === 'approved') return 'success'
  if (status === 'rejected') return 'error'
  return 'warning'
}

function sendRegistrationCard(o: any) {
  const payload = {
    registration_uid: o.id,
    title: `订单 #${String(o.id).slice(-8).toUpperCase()}`,
    username: o.username || username,
    created_at: o.created_at,
    status: o.status,
    amount: o.amount ?? null,
    summary: orderSummary(o),
    is_secondary: o.is_secondary || false
  }
  if (!ws || ws.readyState !== WebSocket.OPEN) return
  ws.send(JSON.stringify({ msg_type: 'registration_card', message: JSON.stringify(payload) }))
  orderPickerShow.value = false
}

function cardData(msg: any) {
  try {
    return JSON.parse(msg.message)
  } catch (e) {
    return { title: '订单信息', summary: msg.message }
  }
}

function openRegistration(card: any) {
  if (!card.registration_uid) return
  const path = isAdminUser.value ? '/admin/registers' : '/sign'
  const query: Record<string, any> = { chat: card.registration_uid }
  if (card.is_secondary) query.tab = 'secondary'
  router.push({ path, query })
}

async function recallMessage(messageUid: string) {
  if (!ws || ws.readyState !== WebSocket.OPEN) return
  ws.send(JSON.stringify({ type: 'recall_message', message_uid: messageUid }))
}

async function loadPinned() {
  try {
    const res = await ajax<any>('/api/global-chats/pinned', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (res.code === 200 && res.data && !Array.isArray(res.data)) {
      pinnedMsg.value = res.data
    } else {
      pinnedMsg.value = null
    }
  } catch (e) { /* ignore */ }
}

function pinMessage(messageUid: string) {
  if (!ws || ws.readyState !== WebSocket.OPEN) return
  ws.send(JSON.stringify({ msg_type: 'pin_message', message_uid: messageUid }))
}

function unpinMessage() {
  if (!ws || ws.readyState !== WebSocket.OPEN) return
  ws.send(JSON.stringify({ msg_type: 'unpin_message' }))
}

onMounted(() => {
  loadHistory()
  loadPinned()
  connectWs()
})

onBeforeUnmount(() => {
  disposed = true
  if (reconnectTimer) clearTimeout(reconnectTimer)
  if (ws) {
    ws.onclose = null
    ws.close()
    ws = null
  }
  clearPendingImage()
})
</script>

<style scoped>
.chat-room-page {
  height: calc(100vh - 100px);
}

.chat-shell {
  display: flex;
  flex-direction: column;
  width: 100%;
  max-width: 1100px;
  height: 100%;
  overflow: hidden;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.1);
}

.chat-toolbar {
  min-height: 52px;
}

.chat-body {
  flex: 1;
  min-height: 0;
}

.chat-main {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
  min-height: 0;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: rgb(var(--v-theme-background));
}

.chat-messages::-webkit-scrollbar {
  width: 6px;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: rgba(var(--v-theme-on-surface), 0.15);
  border-radius: 8px;
}

.chat-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  opacity: 0.7;
}

.day-divider {
  display: flex;
  justify-content: center;
  margin: 12px 0;
}

.day-divider span {
  font-size: 12px;
  color: rgb(var(--v-theme-on-surface), 0.4);
  background: rgb(var(--v-theme-surface));
  padding: 2px 12px;
  border-radius: 999px;
}

.msg-row {
  display: flex;
  margin-bottom: 12px;
}

.msg-row.is-self {
  justify-content: flex-end;
}

.msg-row.is-other {
  justify-content: flex-start;
}

.msg-wrapper {
  max-width: 78%;
  display: flex;
  flex-direction: column;
}

.msg-meta {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 3px;
  font-size: 12px;
  color: rgb(var(--v-theme-on-surface), 0.5);
}

.msg-username {
  font-weight: 600;
}

.msg-username.admin-name {
  color: #D32F2F;
}

.is-self .msg-time {
  align-self: flex-end;
  font-size: 11px;
  color: rgb(var(--v-theme-on-surface), 0.4);
  margin-bottom: 3px;
}

.is-other .msg-time {
  font-size: 11px;
}

.msg-bubble {
  padding: 9px 14px;
  border-radius: 16px;
  word-break: break-word;
  font-size: 14px;
  line-height: 1.55;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}

.is-other .msg-bubble {
  background: rgb(var(--v-theme-surface));
  border-top-left-radius: 4px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.07);
}

.is-self .msg-bubble {
  background: linear-gradient(135deg, #EF5350 0%, #C62828 100%);
  border-top-right-radius: 4px;
  color: #fff;
}

.text-msg {
  white-space: pre-wrap;
}

.img-caption {
  white-space: pre-wrap;
  font-size: 13px;
}

.cursor-pointer {
  cursor: pointer;
}

.reg-card-msg {
  min-width: 220px;
  max-width: 320px;
}

.card-row {
  display: flex;
  align-items: center;
  cursor: pointer;
}

.card-row:hover .card-title {
  color: #D32F2F;
}

.card-body {
  flex: 1;
  min-width: 0;
}

.card-title {
  font-weight: 600;
  font-size: 13px;
}

.card-text {
  font-size: 12px;
  color: rgb(var(--v-theme-on-surface), 0.6);
  max-width: 220px;
}

.chat-input-area {
  padding: 10px 12px 6px;
  background: rgb(var(--v-theme-surface));
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.07);
}

.pending-img {
  margin-bottom: 8px;
  border: 1px dashed rgba(var(--v-theme-on-surface), 0.2);
  border-radius: 8px;
  padding: 4px;
}

.chat-input {
  flex: 1;
}

.send-btn:hover:not(:disabled) {
  transform: scale(1.08);
}

.online-panel {
  width: 230px;
  flex-shrink: 0;
  flex-direction: column;
  border-left: 1px solid rgba(var(--v-theme-on-surface), 0.07);
}

.panel-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  font-size: 14px;
  font-weight: 600;
}

.panel-list {
  flex: 1;
  overflow-y: auto;
}

.online-item {
  border-radius: 8px;
}

.online-item:hover {
  background: rgba(var(--v-theme-on-surface), 0.04);
}

.online-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #4caf50;
  margin-left: 8px;
}

.order-item {
  background: rgb(var(--v-theme-background));
}

.msg-bubble-row {
  display: flex;
  align-items: flex-end;
  gap: 4px;
}

.msg-hover-actions {
  display: flex;
  gap: 0;
  flex-shrink: 0;
}

.msg-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 2px;
}

.recall-btn {
  min-width: 24px;
  min-height: 24px;
  width: 24px;
  height: 24px;
}

.recalled-msg {
  font-size: 13px;
  color: rgb(var(--v-theme-on-surface), 0.45);
  font-style: italic;
  display: flex;
  align-items: center;
}

.is-self .bubble-self:has(.recalled-msg) {
  background: rgba(var(--v-theme-on-surface), 0.05);
  color: rgb(var(--v-theme-on-surface), 0.45);
}

.pinned-banner {
  margin: 0 16px;
  padding: 10px 14px;
  background: linear-gradient(135deg, rgba(255, 193, 7, 0.06) 0%, rgba(255, 152, 0, 0.04) 100%);
  border: 1px solid rgba(255, 193, 7, 0.2);
  border-left: 3px solid rgb(var(--v-theme-warning));
  border-radius: 8px;
  flex-shrink: 0;
}

.pinned-content {
  color: rgb(var(--v-theme-on-surface), 0.8);
  line-height: 1.5;
  word-break: break-word;
  white-space: pre-wrap;
  max-height: 60px;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
