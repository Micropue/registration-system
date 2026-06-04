<template>
  <div class="registration-chat">
    <div class="chat-messages" ref="msgContainer">
      <div v-if="messages.length === 0" class="chat-empty">
        <div class="empty-icon-wrapper">
          <v-icon size="48" color="primary" class="mb-2">mdi-message-processing-outline</v-icon>
        </div>
        <div class="text-body-2 font-weight-medium text-medium-emphasis mt-4">暂无消息记录</div>
        <div class="text-caption text-disabled mt-1">在下方输入内容开始沟通吧</div>
      </div>

      <div v-for="msg in messages" :key="msg.id"
        :class="['chat-bubble-wrapper', msg.username === currentUsername ? 'is-self' : 'is-other']">

        <!-- 聊天气泡 -->
        <div :class="['chat-bubble', msg.msg_type && msg.msg_type !== 'text' ? 'is-card' : '']">
          <!-- 头部信息：名字与时间 -->
          <div class="chat-meta">
            <span class="user-name">{{ msg.username }}</span>
            <span class="msg-time">{{ formatTime(msg.created_at) }}</span>
          </div>

          <!-- 登记卡片 -->
          <div v-if="msg.msg_type === 'registration_card'" class="chat-card reg-card">
            <div class="chat-card-icon reg-icon">
              <v-icon size="22">mdi-file-document-outline</v-icon>
            </div>
            <div class="chat-card-body">
              <div class="card-title">客户信息</div>
              <div class="card-text">{{ msg.message }}</div>
            </div>
          </div>

          <!-- 反馈/工单卡片 -->
          <div v-else-if="msg.msg_type === 'feedback_card'" class="chat-card fb-card">
            <div class="chat-card-icon fb-icon">
              <v-icon size="22">mdi-ticket-confirmation-outline</v-icon>
            </div>
            <div class="chat-card-body">
              <div class="card-title">工单信息</div>
              <div class="card-text">{{ msg.message }}</div>
            </div>
          </div>

          <!-- 普通文本消息 -->
          <div v-else class="chat-text">{{ msg.message }}</div>
        </div>
      </div>
    </div>

    <div v-if="$slots.quickActions" class="d-flex ga-1 px-1">
      <slot name="quickActions"></slot>
    </div>

    <!-- 底部输入区 -->
    <div class="chat-input-area">
      <div class="chat-input-row">
        <v-textarea v-model="input" density="compact" variant="solo-filled" flat
          placeholder="输入消息... (Enter 发送，Shift+Enter 换行)" hide-details auto-grow
          class="chat-input" @keydown.enter.exact.prevent="send"></v-textarea>
        <v-btn icon="mdi-send" variant="flat" color="primary" size="40" elevation="2" @click="send"
          :disabled="!input.trim()" :loading="sending" class="send-btn"></v-btn>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, watch, nextTick, onBeforeUnmount } from 'vue'
import { ajax } from '@/api/ajax'
import { cookie } from '@/api/cookie'
import { ApiUrl } from '@/config/api-url'
import { useChatStore } from '@/stores/chat'

const props = defineProps<{
  registrationUid: string
  isAdminView?: boolean
  currentUsername?: string
}>()

const messages = ref<any[]>([])
const input = ref('')
const sending = ref(false)
const msgContainer = ref<HTMLElement>()
let ws: WebSocket | null = null

const token = cookie.get('token') || ''

function formatTime(iso: string) {
  if (!iso) return ''
  return new Date(iso).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

function scrollBottom() {
  nextTick(() => {
    if (msgContainer.value) {
      msgContainer.value.scrollTop = msgContainer.value.scrollHeight
    }
  })
}

const chatStore = useChatStore()

async function loadHistory() {
  try {
    const res = await ajax<any[]>(`${ApiUrl.REGISTRATION_CHAT}/${props.registrationUid}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (res.code === 200) {
      messages.value = res.data
      scrollBottom()
      chatStore.clearUnreadCount(props.registrationUid)
    }
  } catch (err) { /* ignore */ }
}

function connectWs() {
  if (!props.registrationUid || !token) return
  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = location.host
  ws = new WebSocket(`${protocol}//${host}/ws/chat/${props.registrationUid}?token=${token}`)
  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      messages.value.push(data)
      scrollBottom()
    } catch (e) { /* ignore */ }
  }
  ws.onclose = () => {
    setTimeout(() => {
      if (props.registrationUid) connectWs()
    }, 3000)
  }
}

async function send() {
  if (!input.value.trim() || !ws || ws.readyState !== WebSocket.OPEN) return
  sending.value = true
  try {
    ws.send(JSON.stringify({ message: input.value.trim(), type: 'text' }))
    input.value = ''
  } catch (err) { /* ignore */ }
  finally { sending.value = false }
}

function sendMessage(text: string, type: string = 'text') {
  if (!ws || ws.readyState !== WebSocket.OPEN) return
  ws.send(JSON.stringify({ message: text, type }))
}

watch(() => props.registrationUid, (val) => {
  if (val) {
    messages.value = []
    loadHistory()
    connectWs()
  }
}, { immediate: true })

onBeforeUnmount(() => {
  if (ws) {
    ws.onclose = null
    ws.close()
    ws = null
  }
})

defineExpose({ sendMessage })
</script>

<style scoped>
/* 全局容器 */
.registration-chat {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  background-color: rgb(var(--v-theme-surface));
  border-radius: 12px;
}

/* 消息列表区 */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  padding: 16px 12px;
  scroll-behavior: smooth;
}

/* 滚动条 */
.chat-messages::-webkit-scrollbar {
  width: 6px;
}

.chat-messages::-webkit-scrollbar-track {
  background: transparent;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: rgba(var(--v-theme-on-surface), 0.15);
  border-radius: 8px;
}

/* 空状态 */
.chat-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  opacity: 0.8;
  animation: fadeIn 0.5s ease;
}

.empty-icon-wrapper {
  background: rgb(var(--v-theme-surface-variant));
  padding: 16px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 气泡外层 */
.chat-bubble-wrapper {
  display: flex;
  flex-direction: column;
  margin-bottom: 16px;
  width: 100%;
  animation: fadeInUp 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
}

/* 核心气泡 */
.chat-bubble {
  position: relative;
  padding: 10px 14px;
  border-radius: 18px;
  max-width: 85%;
  word-break: break-word;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.04);
}

/* 别人发的消息 */
.is-other {
  align-items: flex-start;
}

.is-other .chat-bubble {
  background-color: rgb(var(--v-theme-background));
  border-top-left-radius: 4px;
  color: rgb(var(--v-theme-on-background));
}

.is-other .chat-meta {
  color: rgba(var(--v-theme-on-background), 0.6);
}

/* 自己发的消息 */
.is-self {
  align-items: flex-end;
}

.is-self .chat-bubble {
  background: linear-gradient(135deg, #2196F3 0%, #1565C0 100%);
  border-top-right-radius: 4px;
  color: #FFFFFF;
  box-shadow: 0 4px 10px rgba(21, 101, 192, 0.2);
}

.is-self .chat-meta {
  color: rgba(255, 255, 255, 0.8);
  justify-content: flex-end;
}

/* 卡片类型 */
.chat-bubble.is-card {
  padding: 0;
  background: transparent !important;
  box-shadow: none !important;
  max-width: 90%;
}

/* 元信息 */
.chat-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.75rem;
  margin-bottom: 4px;
  font-weight: 500;
}

.msg-time {
  font-weight: 400;
  font-size: 0.7rem;
}

/* 文本消息 */
.chat-text {
  font-size: 0.9rem;
  line-height: 1.5;
  letter-spacing: 0.3px;
  white-space: pre-wrap;
}

/* 卡片 */
.chat-card {
  display: flex;
  gap: 12px;
  background: rgb(var(--v-theme-background));
  border-radius: 16px;
  padding: 14px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(0, 0, 0, 0.04);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.chat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08);
}

.is-self .chat-card {
  border: 1px solid rgba(33, 150, 243, 0.2);
}

.chat-card-icon {
  flex-shrink: 0;
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.reg-icon {
  background: linear-gradient(135deg, #E3F2FD, #BBDEFB);
  color: #1976D2;
}

.fb-icon {
  background: linear-gradient(135deg, #FFF3E0, #FFE0B2);
  color: #F57C00;
}

.chat-card-body {
  flex: 1;
  min-width: 0;
}

.card-title {
  font-size: 0.85rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-background));
  margin-bottom: 6px;
}

.chat-card .card-text {
  white-space: pre-wrap;
  color: rgba(var(--v-theme-on-background), 0.7);
  font-size: 0.8rem;
  line-height: 1.5;
  max-height: 150px;
  overflow-y: auto;
  padding-right: 4px;
  scrollbar-width: thin;
}

.chat-card .card-text::-webkit-scrollbar {
  width: 4px;
}

.chat-card .card-text::-webkit-scrollbar-thumb {
  background: rgba(var(--v-theme-on-background), 0.15);
  border-radius: 4px;
}

/* 输入区 */
.chat-input-area {
  flex-shrink: 0;
  padding: 8px 12px;
  background: rgb(var(--v-theme-background));
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-bottom-left-radius: 12px;
  border-bottom-right-radius: 12px;
  overflow: hidden;
}

.chat-input-row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.chat-input {
  flex: 1;
  min-width: 0;
}

.chat-input :deep(.v-field__input) {
  padding-top: 9px !important;
  padding-bottom: 9px !important;
  font-size: 0.9rem;
  line-height: 1.4;
  overflow-y: auto !important;
}

.send-btn {
  flex-shrink: 0;
  margin-top: 2px;
  border-radius: 50% !important;
  transition: transform 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
}

.send-btn:hover:not(:disabled) {
  transform: scale(1.1) rotate(-5deg);
}

@keyframes fadeInUp {
  0% {
    opacity: 0;
    transform: translateY(12px);
  }

  100% {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeIn {
  0% {
    opacity: 0;
  }

  100% {
    opacity: 1;
  }
}
</style>