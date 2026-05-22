<template>
  <v-container fluid class="pa-0 d-flex flex-column align-center">
    <div class="table-wrapper mt-4">
      <div class="d-flex justify-space-between align-center mb-2">
        <h1 class="text-h4">订单处理</h1>
      </div>

      <div class="d-flex flex-wrap ga-2 mb-4">
        <v-badge
          :content="totalPending"
          color="error"
          offset-x="-6"
          offset-y="-6"
          :model-value="totalPending > 0"
        >
          <v-btn
            :to="{ path: '/admin/registers', query: route.query }"
            :variant="!selectedApp ? 'tonal' : 'text'"
            :color="!selectedApp ? 'primary' : ''"
            rounded
            size="small"
          >
            全部订单
          </v-btn>
        </v-badge>
        <v-badge
          v-for="app in runningApps"
          :key="app.id"
          :content="appStats[app.name]?.pending || 0"
          color="error"
          offset-x="-6"
          offset-y="-6"
          :model-value="(appStats[app.name]?.pending || 0) > 0"
        >
          <v-btn
            :to="{ path: `/admin/registers/${encodeURIComponent(app.name)}`, query: route.query }"
            :variant="selectedApp === app.name ? 'tonal' : 'text'"
            :color="selectedApp === app.name ? 'primary' : ''"
            rounded
            size="small"
          >
            <v-avatar v-if="app.icon" size="20" rounded class="me-1">
              <v-img :src="app.icon" cover></v-img>
            </v-avatar>
            <span class="color-dot" :style="{ backgroundColor: app.accent_color || '#1976D2' }"></span>
            {{ app.name }}
          </v-btn>
        </v-badge>
      </div>

      <!-- 使用封装后的通用表格组件 -->
      <app-data-table :headers="headers" :items="registers" :total-items="totalRegisters" :loading="loading"
        v-model:page="currentPage" v-model:items-per-page="itemsPerPage" show-search show-filter search-label="搜索用户名"
        @update:options="loadRegisters" @reset="loadRegisters"
        :row-props="({ item }: any) => item.status !== 'pending' ? { class: 'row-processed' } : {}">

        <!-- 自定义槽位：跑步APP -->
        <template v-slot:item.app="{ item }">
          <div class="d-flex align-center ga-1 app-name-cell">
            <v-avatar v-if="getAppInfo(item.app)?.icon" size="22" rounded>
              <v-img :src="getAppInfo(item.app)?.icon" cover></v-img>
            </v-avatar>
            <span class="color-dot" :style="{ backgroundColor: getAppInfo(item.app)?.accent_color || '#1976D2' }"></span>
            <span class="font-weight-bold text-body-2 text-no-wrap">{{ item.app }}</span>
          </div>
        </template>

        <!-- 自定义槽位：模板 -->
        <template v-slot:item.template_name="{ item }">
          <span class="text-body-2">{{ item.template_name || '-' }}</span>
        </template>

        <!-- 自定义槽位：跑量 -->
        <template v-slot:item.amount="{ item }">
          <span v-if="item.amount != null" class="font-weight-bold text-primary">{{ item.amount }}{{ getAmountUnit(item.app) }}</span>
          <span v-else class="text-grey">-</span>
        </template>

        <!-- 自定义槽位：创建时间 -->
        <template v-slot:item.created_at="{ item }">
          {{ formatDate(item.created_at) }}
        </template>

        <!-- 自定义槽位：登记状态 -->
        <template v-slot:item.status="{ item }">
          <v-chip :color="getStatusColor(item.status)" size="small">
            {{ getStatusText(item.status) }}
          </v-chip>
        </template>

        <!-- 自定义槽位：优先级 -->
        <template v-slot:item.priority="{ item }">
          <v-chip :color="getPriorityColor(item.priority)" size="small" variant="tonal">
            {{ getPriorityText(item.priority) }}
          </v-chip>
        </template>

        <!-- 自定义槽位：客户信息 -->
        <template v-slot:item.details="{ item }">
          <v-btn variant="text" size="small" color="primary" @click="openDetailsDialog(item)">查看信息</v-btn>
        </template>

        <!-- 自定义槽位：操作 -->
        <template v-slot:item.actions="{ item }">
          <div class="d-flex ga-1">
            <v-badge :model-value="chatUnreadCount(item.id) > 0" :content="chatUnreadCount(item.id)" color="error" offset-x="-4" offset-y="-4">
              <v-btn variant="tonal" rounded color="primary" @click="openDetailsDialog(item)">聊天</v-btn>
            </v-badge>
            <v-btn variant="tonal" rounded color="success" @click="updateStatus(item, 'approved')">已处理</v-btn>
            <v-btn variant="tonal" rounded color="error" @click="openReject(item)">驳回</v-btn>
            <v-btn variant="tonal" rounded color="warning" @click="updateStatus(item, 'pending')">未处理</v-btn>
            <v-btn variant="tonal" rounded color="error" @click="confirmDelete(item)">删除记录</v-btn>
          </div>
        </template>
      </app-data-table>
    </div>

    <!-- 客户信息详情 Dialog（集成聊天） -->
    <v-dialog v-model="detailsDialog.show" max-width="1100">
      <v-card v-if="detailsDialog.item" class="detail-card">
        <v-card-title class="d-flex align-center pa-4 pb-0">
          客户信息 - {{ detailsDialog.item?.username }}
          <v-spacer></v-spacer>
          <v-chip :color="getPriorityColor(detailsDialog.item?.priority || 'low')" size="small" variant="tonal" class="me-2">
            {{ getPriorityText(detailsDialog.item?.priority || 'low') }}
          </v-chip>
          <v-btn variant="text" size="small" @click="handleDetailsClose">关闭</v-btn>
        </v-card-title>

        <div class="detail-body">
          <div class="detail-info-panel">
            <v-card-text class="pa-4 pt-2">
              <v-table density="compact" border>
                <thead>
                  <tr><th class="text-left">字段</th><th class="text-left">内容</th></tr>
                </thead>
                <tbody>
                  <tr v-if="detailsDialog.item?.amount != null">
                    <td class="font-weight-bold text-primary">跑量</td>
                    <td class="font-weight-bold text-primary">{{ detailsDialog.item.amount }}{{ getAmountUnit(detailsDialog.item.app) }}</td>
                  </tr>
                  <tr v-for="row in detailFields" :key="row.key">
                    <td class="font-weight-bold">{{ row.key }}</td>
                    <td>
                      {{ row.value }}
                      <v-btn v-if="isAccountField(row.key)" icon="mdi-content-copy" variant="text" density="compact" size="x-small" color="primary" class="ms-1" @click="copyFieldValue(row.key, row.value)"></v-btn>
                    </td>
                  </tr>
                </tbody>
              </v-table>
              <v-alert v-if="detailsDialog.item?.reject_reason" type="error" variant="tonal" class="mt-3" density="compact">
                <strong>驳回原因：</strong>{{ detailsDialog.item.reject_reason }}
              </v-alert>
            </v-card-text>
            <v-card-actions class="pa-4 pt-0">
              <v-btn variant="text" size="small" prepend-icon="mdi-content-copy" @click="copyDetailText">复制为文本</v-btn>
            </v-card-actions>
          </div>

          <div class="detail-chat-panel">
            <RegistrationChat
              v-if="detailsDialog.item?.id"
              :registration-uid="detailsDialog.item.id"
              :is-admin-view="true"
              :current-username="appStore.userInfo?.username || ''"
            />
          </div>
        </div>
      </v-card>
    </v-dialog>

    <!-- 删除确认 Dialog -->
    <v-dialog v-model="deleteDialog.show" max-width="400">
      <v-card>
        <v-card-title class="text-h5">确认删除</v-card-title>
        <v-card-text>
          确定要删除用户 <b>{{ deleteDialog.item?.username }}</b> 的登记记录吗？此操作不可撤销。
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="deleteDialog.show = false">取消</v-btn>
          <v-btn color="error" variant="elevated" @click="handleDelete" :loading="loading">确认删除</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 驳回原因 Dialog -->
    <v-dialog v-model="rejectDialog.show" max-width="450">
      <v-card>
        <v-card-title class="text-h5 pa-4">驳回登记</v-card-title>
        <v-card-text class="pa-4 pt-0">
          <v-textarea v-model="rejectDialog.reason" label="驳回原因" variant="outlined"
            placeholder="请填写驳回原因，用户将看到此内容"
            rows="3" hide-details auto-grow></v-textarea>
        </v-card-text>
        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="rejectDialog.show = false">取消</v-btn>
          <v-btn color="error" variant="flat" :loading="loading" @click="confirmReject">确认驳回</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-snackbar v-model="snackbar.show" :color="snackbar.color" timeout="3000">
      {{ snackbar.text }}
    </v-snackbar>
  </v-container>
</template>

<style scoped>
.table-wrapper {
  width: 90%;
  overflow-x: auto;
}
:deep(.row-processed) { opacity: 0.5; }
.color-dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 5px; vertical-align: middle; flex-shrink: 0; }
.app-name-cell { min-width: 120px; white-space: nowrap; }

.detail-card {
  overflow: hidden;
  display: flex;
  flex-direction: column;
  max-height: 85vh;
}
.detail-body {
  display: flex;
  flex: 1;
  min-height: 0;
}
.detail-info-panel {
  flex: 0 0 45%;
  max-width: 45%;
  display: flex;
  flex-direction: column;
  border-right: 1px solid rgba(0,0,0,0.08);
  overflow-y: auto;
}
.detail-chat-panel {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

@media (max-width: 768px) {
  .detail-body {
    flex-direction: column;
  }
  .detail-info-panel {
    flex: 0 0 auto;
    max-width: 100%;
    border-right: none;
    border-bottom: 1px solid rgba(0,0,0,0.08);
    max-height: 250px;
  }
  .detail-chat-panel {
    flex: 1;
    min-height: 350px;
  }
}
</style>

<script lang="ts" setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppDataTable from '@/components/AppDataTable.vue'
import RegistrationChat from '@/components/RegistrationChat.vue'
import { ApiUrl } from '@/config/api-url'
import { ajax } from '@/api/ajax'
import { cookie } from '@/api/cookie'
import type { RunningApp } from '@/config/api-type'
import { useAppStore } from '@/stores/app'
import { useChatStore } from '@/stores/chat'
// 类型定义
interface RegistrationItem {
  id: string
  username: string
  created_at: string
  status: 'pending' | 'approved' | 'rejected'
  registration_info?: any
  reject_reason?: string
  app?: string
  priority?: string
  template_uid?: string
  amount?: number | null
}

// 状态管理
const route = useRoute()
const router = useRouter()
const appStore = useAppStore()
const chatStore = useChatStore()

const runningApps = ref<RunningApp[]>([])
const appStats = ref<Record<string, { pending: number }>>({})
const selectedApp = computed(() => decodeURIComponent(route.params.appName as string || ''))
const totalPending = computed(() => Object.values(appStats.value).reduce((sum, s) => sum + s.pending, 0))

const registers = ref<RegistrationItem[]>([])
const loading = ref(false)
const totalRegisters = ref(0)
const itemsPerPage = ref(20)
const currentPage = ref(1)
const detailsDialog = reactive({ show: false, item: null as RegistrationItem | null })
const deleteDialog = reactive({ show: false, item: null as RegistrationItem | null })
const rejectDialog = reactive({ show: false, item: null as RegistrationItem | null, reason: '' })

const snackbar = reactive({ show: false, text: '', color: 'success' })
const templateFieldOrder = ref<string[]>([])

const detailFields = computed(() => {
  const info = detailsDialog.item?.registration_info
  if (!info) return []
  const keys = Object.keys(info)
  const order = ['跑步APP', ...templateFieldOrder.value]
  return keys
    .map(k => ({ key: k, value: _formatVal(info[k]) }))
    .sort((a, b) => {
      const ai = order.indexOf(a.key)
      const bi = order.indexOf(b.key)
      if (ai === -1 && bi === -1) return a.key.localeCompare(b.key)
      if (ai === -1) return 1
      if (bi === -1) return -1
      return ai - bi
    })
})

function _formatVal(val: any): string {
  if (val === null || val === undefined) return '-'
  if (Array.isArray(val)) return val.join(', ')
  return String(val)
}

function showMsg(text: string, color: string = 'success') {
  snackbar.text = text
  snackbar.color = color
  snackbar.show = true
}

async function loadRunningApps() {
  try {
    const res = await ajax<RunningApp[]>(ApiUrl.GET_RUNNING_APPS, {
      headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
    })
    if (res.code === 200) runningApps.value = res.data
  } catch (err) { /* ignore */ }
}

async function loadStats() {
  try {
    const res = await ajax<{ app: string; pending: number }[]>(ApiUrl.REGISTRATION_STATS, {
      headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
    })
    if (res.code === 200) {
      const map: Record<string, { pending: number }> = {}
      for (const s of res.data) {
        map[s.app] = { pending: s.pending }
      }
      appStats.value = map
    }
  } catch (err) { /* ignore */ }
}

async function loadTemplateFieldOrder(appName: string, templateUid: string) {
  const app = runningApps.value.find(a => a.name === appName)
  if (!app || !templateUid) { templateFieldOrder.value = []; return }
  try {
    const res = await ajax<any[]>(`/api/admin/settings/running-apps/${app.uid}/templates`, {
      headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
    })
    if (res.code === 200) {
      const tpl = (res.data || []).find((t: any) => t.uid === templateUid)
      if (tpl?.fields) {
        templateFieldOrder.value = tpl.fields.map((f: any) => f.label)
        return
      }
    }
  } catch (err) { /* ignore */ }
  templateFieldOrder.value = []
}

onMounted(async () => {
  await loadRunningApps()
  await loadStats()
  if (runningApps.value.length > 0) {
    if (selectedApp.value && !runningApps.value.find(a => a.name === selectedApp.value) && !route.query.chat) {
      router.replace({ path: `/admin/registers/${encodeURIComponent(runningApps.value[0].name)}`, query: route.query })
      return
    }
  }
  await loadRegisters()
  openChatFromQuery()
})

watch(selectedApp, () => {
  currentPage.value = 1
  loadRegisters()
})

function openDetailsDialog(item: RegistrationItem) {
  detailsDialog.item = item
  detailsDialog.show = true
  chatStore.clearUnreadCount(item.id)
  if (item.app && item.template_uid) {
    loadTemplateFieldOrder(item.app, item.template_uid)
  }
}

function handleDetailsClose() {
  detailsDialog.show = false
  if (route.query.chat) {
    router.replace({ query: { ...route.query, chat: undefined } })
  }
}

function openChatFromQuery() {
  const chatId = route.query.chat
  if (chatId && typeof chatId === 'string') {
    const item = registers.value.find(r => String(r.id) === String(chatId))
    if (item) openDetailsDialog(item)
  }
}

watch(() => route.query.chat, () => {
  openChatFromQuery()
})

function chatUnreadCount(id: string) {
  return chatStore.chatUnreadCounts[id] || 0
}

function getAppInfo(appName: string) {
  return runningApps.value.find(a => a.name === appName)
}

function getAmountUnit(appName: string | undefined): string {
  if (!appName) return ''
  const app = runningApps.value.find(a => a.name === appName)
  if (app?.balance_mode === 'mileage') return ' 公里'
  if (app?.balance_mode === 'count') return ' 次'
  return ''
}

function confirmDelete(item: RegistrationItem) {
  deleteDialog.item = item
  deleteDialog.show = true
}

// 配置化表头
const headers = [
  { title: '用户名', key: 'username', searchable: true, filterable: true },
  { title: '跑步APP', key: 'app', sortable: true, filterable: true },
  { title: '模板', key: 'template_name', sortable: true },
  { title: '跑量', key: 'amount', sortable: true },
  { title: '客户信息', key: 'details', sortable: false },
  { title: '登记状态', key: 'status', sortable: true, filterable: true },
  { title: '优先级', key: 'priority', sortable: true, filterable: true },
  { title: '操作', key: 'actions', sortable: false },
  { title: '创建时间', key: 'created_at', sortable: true },
]

// 工具函数
function formatDate(isoString: string) {
  if (!isoString) return '-'
  const date = new Date(isoString)
  return date.toLocaleString()
}

function getStatusColor(status: string) {
  switch (status) {
    case 'approved': return 'success'
    case 'rejected': return 'error'
    default: return 'warning'
  }
}

function getStatusText(status: string) {
  switch (status) {
    case 'approved': return '已通过'
    case 'rejected': return '已拒绝'
    default: return '待处理'
  }
}

function getPriorityColor(priority: string) {
  switch (priority) {
    case 'high': return 'error'
    case 'medium': return 'warning'
    default: return 'grey'
  }
}

function getPriorityText(priority: string) {
  switch (priority) {
    case 'high': return '高'
    case 'medium': return '中'
    default: return '低'
  }
}

// 事件处理
async function copyDetailText() {
  const item = detailsDialog.item
  if (!item?.registration_info) return
  const info = item.registration_info
  const keys = Object.keys(info)
  const order = ['跑步APP', ...templateFieldOrder.value]
  const sorted = [...keys].sort((a, b) => {
    const ai = order.indexOf(a)
    const bi = order.indexOf(b)
    if (ai === -1 && bi === -1) return a.localeCompare(b)
    if (ai === -1) return 1
    if (bi === -1) return -1
    return ai - bi
  })
  const text = sorted.map(k => `${k}：${info[k] ?? ''}`).join('\n')
  try {
    await navigator.clipboard.writeText(text)
    showMsg('已复制到剪贴板')
  } catch {
    showMsg('复制失败', 'error')
  }
}

function isAccountField(key: string): boolean {
  const lower = key.toLowerCase()
  return lower.includes('账号') || lower.includes('密码') || lower.includes('account') || lower.includes('password')
}

async function copyFieldValue(key: string, value: string) {
  try {
    await navigator.clipboard.writeText(value)
    showMsg(`已复制：${key}`)
  } catch {
    showMsg('复制失败', 'error')
  }
}

function openReject(item: RegistrationItem) {
  rejectDialog.item = item
  rejectDialog.reason = ''
  rejectDialog.show = true
}

async function confirmReject() {
  if (!rejectDialog.item) return
  loading.value = true
  try {
    const res = await ajax(`${ApiUrl.UPDATE_REGISTRATION_STATUS}/${rejectDialog.item.id}/status`, {
      method: 'POST',
      body: { status: 'rejected', reject_reason: rejectDialog.reason },
      isFormData: true,
      headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
    })
    if (res.code === 200) {
      rejectDialog.item.status = 'rejected'
      showMsg(`已驳回 ${rejectDialog.item.username} 的登记`)
      rejectDialog.show = false
      loadRegisters()
    } else {
      showMsg(res.msg || '驳回失败', 'error')
    }
  } catch (err) {
    showMsg('请求失败', 'error')
  } finally {
    loading.value = false
  }
}

async function updateStatus(item: RegistrationItem, status: RegistrationItem['status']) {
  loading.value = true
  try {
    const res = await ajax(`${ApiUrl.UPDATE_REGISTRATION_STATUS}/${item.id}/status`, {
      method: 'POST',
      body: { status },
      isFormData: true,
      headers: { 
        'Authorization': `Bearer ${cookie.get('token') || ''}`
      }
    })
    if (res.code === 200) {
      item.status = status
      showMsg(`已更新 ${item.username} 的状态为: ${getStatusText(status)}`)
      loadRegisters()
    } else {
      showMsg(res.msg || '状态更新失败', 'error')
    }
  } catch (err) {
    showMsg('请求失败', 'error')
  } finally {
    loading.value = false
  }
}

async function handleDelete() {
  if (!deleteDialog.item) return
  
  loading.value = true
  try {
    const res = await ajax(`${ApiUrl.DELETE_REGISTRATION}/${deleteDialog.item.id}`, {
      method: 'DELETE',
      headers: { 
        'Authorization': `Bearer ${cookie.get('token') || ''}`
      }
    })
    if (res.code === 200) {
      showMsg(`已成功删除 ${deleteDialog.item.username} 的登记记录`)
      deleteDialog.show = false
      loadRegisters()
    } else {
      showMsg(res.msg || '删除失败', 'error')
    }
  } catch (err) {
    showMsg('请求失败', 'error')
  } finally {
    loading.value = false
  }
}

// 加载数据
async function loadRegisters(options: any = { page: 1, itemsPerPage: 20 }) {
  const page = options.page || currentPage.value
  const pageSize = options.itemsPerPage || itemsPerPage.value

  loading.value = true
  currentPage.value = page
  itemsPerPage.value = pageSize

  let url = `${ApiUrl.GET_REGISTRATIONS}?page=${page}&page_size=${pageSize}`
  if (selectedApp.value) {
    url += `&running_app=${encodeURIComponent(selectedApp.value)}`
  }
  const username = route.query.username as string || ''
  if (username) {
    url += `&username=${encodeURIComponent(username)}`
  }
  if (options.sortBy && options.sortBy.length > 0) {
    url += `&sort_by=${encodeURIComponent(options.sortBy[0].key)}&order=${options.sortBy[0].order}`
  }

  try {
    const res = await ajax(url, {
      method: 'GET',
      headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
    })
    if (res.code === 200) {
      registers.value = res.data.items.map((item: any) => ({
        ...item,
        app: item.registration_info?.['跑步APP'] || '',
        amount: item.amount ?? null
      }))
      totalRegisters.value = res.data.total
      loadStats()
    }
  } catch (err) {
    showMsg('加载登记数据失败', 'error')
  } finally {
    loading.value = false
  }
}

</script>
