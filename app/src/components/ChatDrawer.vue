<template>
  <v-navigation-drawer
    location="right"
    width="420"
    temporary
    :model-value="chatStore.isOpen"
    @update:model-value="(v: boolean) => { if (!v) chatStore.close() }"
  >
    <template v-if="chatStore.isOpen">
      <div class="d-flex flex-column fill-height">
        <v-toolbar density="compact" color="primary" class="chat-toolbar">
          <v-icon start size="20" class="ml-1">mdi-chat-processing</v-icon>
          <v-toolbar-title class="text-body-2">{{ chatStore.title }}</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon="mdi-close" variant="text" size="small" @click="chatStore.close()"></v-btn>
        </v-toolbar>

        <div class="chat-body flex-1-1 overflow-hidden" v-if="chatStore.registrationUid">
          <RegistrationChat
            :key="chatStore.registrationUid"
            ref="chatComp"
            :registration-uid="chatStore.registrationUid"
            :is-admin-view="chatStore.isAdminView"
            :current-username="chatStore.currentUsername"
          >
            <template v-if="!chatStore.isAdminView" #quickActions>
              <v-btn size="x-small" variant="tonal" color="primary" rounded prepend-icon="mdi-file-document-outline"
                @click="showRegPick = true">发送登记信息</v-btn>
              <v-btn size="x-small" variant="tonal" color="secondary" rounded prepend-icon="mdi-message-text-outline"
                @click="showFbPick = true">发送工单</v-btn>
            </template>
          </RegistrationChat>
        </div>
        <div v-else class="flex-1-1 d-flex flex-column align-center justify-center text-medium-emphasis">
          <v-icon size="48" class="mb-3">mdi-chat-outline</v-icon>
          <div class="text-body-2">选择一个登记开始沟通</div>
        </div>
      </div>
    </template>

    <!-- 登记信息选择 Dialog -->
    <v-dialog v-model="showRegPick" max-width="420">
      <v-card class="rounded-lg">
        <v-card-title class="pa-4 pb-1 text-body-1">选择要发送的登记信息</v-card-title>
        <v-card-text class="pa-4 pt-1">
          <div v-if="regList.length === 0" class="text-center pa-6 text-medium-emphasis">暂无登记记录</div>
          <v-radio-group v-else v-model="pickedReg" hide-details>
            <v-radio v-for="r in regList" :key="r.id" :value="r.id" class="mb-2">
              <template #label>
                <div>
                  <div class="text-body-2 font-weight-medium">{{ r.app || '登记记录' }}</div>
                  <div class="text-caption text-medium-emphasis">{{ formatDate(r.created_at) }}</div>
                </div>
              </template>
            </v-radio>
          </v-radio-group>
        </v-card-text>
        <v-card-actions class="pa-4 pt-0">
          <v-spacer></v-spacer>
          <v-btn variant="text" size="small" @click="showRegPick = false">取消</v-btn>
          <v-btn variant="flat" rounded color="primary" size="small" :disabled="!pickedReg" @click="sendPickedReg">发送</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 工单选择 Dialog -->
    <v-dialog v-model="showFbPick" max-width="420">
      <v-card class="rounded-lg">
        <v-card-title class="pa-4 pb-1 text-body-1">选择要发送的工单</v-card-title>
        <v-card-text class="pa-4 pt-1">
          <div v-if="fbList.length === 0" class="text-center pa-6 text-medium-emphasis">暂无工单记录</div>
          <v-radio-group v-else v-model="pickedFb" hide-details>
            <v-radio v-for="f in fbList" :key="f.id" :value="f.id" class="mb-2">
              <template #label>
                <div>
                  <div class="text-body-2 font-weight-medium">{{ f.title }}</div>
                  <div class="d-flex align-center ga-2 mt-1">
                    <v-chip size="x-small" :color="statusColor(f.status)" variant="flat">{{ statusText(f.status) }}</v-chip>
                    <span class="text-caption text-medium-emphasis">{{ formatDate(f.created_at) }}</span>
                  </div>
                </div>
              </template>
            </v-radio>
          </v-radio-group>
        </v-card-text>
        <v-card-actions class="pa-4 pt-0">
          <v-spacer></v-spacer>
          <v-btn variant="text" size="small" @click="showFbPick = false">取消</v-btn>
          <v-btn variant="flat" rounded color="primary" size="small" :disabled="!pickedFb" @click="sendPickedFb">发送</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-navigation-drawer>
</template>

<style scoped>
.chat-toolbar {
  border-bottom: 1px solid rgba(255,255,255,.15) !important;
}
.chat-body {
  flex: 1 1 0;
  min-height: 0;
  overflow: hidden;
}
</style>

<script lang="ts" setup>
import { ref, watch } from 'vue'
import RegistrationChat from '@/components/RegistrationChat.vue'
import { useChatStore } from '@/stores/chat'
import { ajax } from '@/api/ajax'
import { cookie } from '@/api/cookie'
import { ApiUrl } from '@/config/api-url'

const chatStore = useChatStore()
const chatComp = ref<InstanceType<typeof RegistrationChat> | null>(null)
const showRegPick = ref(false)
const showFbPick = ref(false)
const pickedReg = ref('')
const pickedFb = ref('')
const regList = ref<any[]>([])
const fbList = ref<any[]>([])
const token = cookie.get('token') || ''

function formatDate(iso: string) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('zh-CN')
}

function statusText(s: string) {
  const m: Record<string, string> = { resolved: '已处理', rejected: '已驳回', pending: '待处理', approved: '已通过' }
  return m[s] || s
}

function statusColor(s: string) {
  const m: Record<string, string> = { resolved: 'success', rejected: 'error', pending: 'warning', approved: 'success' }
  return m[s] || 'grey'
}

async function loadRegList() {
  try {
    const res = await ajax<any>(`${ApiUrl.GET_USER_REGISTRATIONS}?page=1&page_size=50`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (res.code === 200) {
      regList.value = (res.data.items || []).map((r: any) => ({
        id: r.id, app: (r.data || r.registration_info || {})['跑步APP'] || '登记记录',
        created_at: r.created_at, data: r.data || r.registration_info
      }))
    }
  } catch (err) { /* ignore */ }
}

async function loadFbList() {
  try {
    const res = await ajax<any>(`${ApiUrl.GET_USER_FEEDBACKS}?page=1&page_size=50`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (res.code === 200) {
      fbList.value = res.data.items || []
    }
  } catch (err) { /* ignore */ }
}

function sendPickedReg() {
  const r = regList.value.find((r: any) => r.id === pickedReg.value)
  if (!r) return
  const data = r.data || {}
  const text = Object.entries(data).map(([k, v]: [string, any]) => `${k}：${v ?? ''}`).join('\n')
  chatComp.value?.sendMessage(`【登记信息】${r.app}\n${text}`, 'registration_card')
  showRegPick.value = false
  pickedReg.value = ''
}

function sendPickedFb() {
  const f = fbList.value.find((f: any) => f.id === pickedFb.value)
  if (!f) return
  chatComp.value?.sendMessage(`【工单】${f.title}\n标题：${f.title}\n状态：${statusText(f.status)}\n内容：${f.content || ''}`, 'feedback_card')
  showFbPick.value = false
  pickedFb.value = ''
}

watch(showRegPick, (v) => { if (v) { pickedReg.value = ''; loadRegList() } })
watch(showFbPick, (v) => { if (v) { pickedFb.value = ''; loadFbList() } })
</script>
