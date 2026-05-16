<template>
  <v-container fluid class="pa-0 d-flex flex-column align-center">
    <div class="table-wrapper mt-4">
      <div class="d-flex justify-space-between align-center mb-4">
        <h1 class="text-h4">登记处理</h1>
      </div>

      <!-- 使用封装后的通用表格组件 -->
      <app-data-table :headers="headers" :items="registers" :total-items="totalRegisters" :loading="loading"
        v-model:page="currentPage" v-model:items-per-page="itemsPerPage" show-search show-filter search-label="搜索用户名"
        @update:options="loadRegisters" @reset="loadRegisters">

        <!-- 自定义槽位：跑步APP -->
        <template v-slot:item.app="{ item }">
          {{ item.registration_info?.['跑步APP'] || '-' }}
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

        <!-- 自定义槽位：登记信息 -->
        <template v-slot:item.details="{ item }">
          <v-btn variant="text" size="small" color="primary" @click="openDetailsDialog(item)">查看信息</v-btn>
        </template>

        <!-- 自定义槽位：操作 -->
        <template v-slot:item.actions="{ item }">
          <v-menu location="bottom">
            <template v-slot:activator="{ props }">
              <v-btn icon="mdi-dots-vertical" variant="text" size="small" v-bind="props"></v-btn>
            </template>
            <v-list density="compact">
              <v-list-item @click="handleView(item)">查看详情</v-list-item>
              <v-menu location="right">
                <template v-slot:activator="{ props }">
                  <v-list-item v-bind="props" append-icon="mdi-chevron-right">更新状态</v-list-item>
                </template>
                <v-list density="compact">
                  <v-list-item @click="updateStatus(item, 'approved')" class="text-success">已处理</v-list-item>
                  <v-list-item @click="openReject(item)" class="text-error">驳回</v-list-item>
                  <v-list-item @click="updateStatus(item, 'pending')">未处理</v-list-item>
                </v-list>
              </v-menu>
              <v-divider></v-divider>
              <v-list-item @click="confirmDelete(item)" class="text-error">
                删除记录
              </v-list-item>
            </v-list>
          </v-menu>
        </template>
      </app-data-table>
    </div>

    <!-- 登记信息详情 Dialog -->
    <v-dialog v-model="detailsDialog.show" max-width="600">
      <v-card class="pa-2">
        <v-card-title>登记信息 - {{ detailsDialog.item?.username }}</v-card-title>
        <v-card-text>
          <v-table density="compact" border>
            <thead>
              <tr>
                <th class="text-left">字段</th>
                <th class="text-left">内容</th>
              </tr>
            </thead>
            <tbody>
                <tr v-for="row in detailFields" :key="row.key">
                  <td>{{ row.key }}</td>
                  <td>{{ row.value }}</td>
                </tr>
            </tbody>
          </v-table>
          <v-alert v-if="detailsDialog.item?.reject_reason" type="error" variant="tonal" class="mt-3" density="compact">
            <strong>驳回原因：</strong>{{ detailsDialog.item.reject_reason }}
          </v-alert>
        </v-card-text>
        <v-card-actions>
          <v-btn variant="text" size="small" prepend-icon="mdi-content-copy" @click="copyDetailText">复制为文本</v-btn>
          <v-spacer></v-spacer>
          <v-btn variant="tonal" @click="detailsDialog.show = false">关闭</v-btn>
        </v-card-actions>
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
  max-width: 1000px;
  overflow-x: auto;
}
</style>

<script lang="ts" setup>
import { ref, reactive, computed, onMounted } from 'vue'
import AppDataTable from '@/components/AppDataTable.vue'
import { ApiUrl } from '@/config/api-url'
import { ajax } from '@/api/ajax'
import { cookie } from '@/api/cookie'
// 类型定义
interface RegistrationItem {
  id: string
  username: string
  created_at: string
  status: 'pending' | 'approved' | 'rejected'
  registration_info?: any
  reject_reason?: string
  app?: string
}

// 状态管理
const registers = ref<RegistrationItem[]>([])
const loading = ref(false)
const totalRegisters = ref(0)
const itemsPerPage = ref(20)
const currentPage = ref(1)
const detailsDialog = reactive({ show: false, item: null as RegistrationItem | null })
const deleteDialog = reactive({ show: false, item: null as RegistrationItem | null })
const rejectDialog = reactive({ show: false, item: null as RegistrationItem | null, reason: '' })

const snackbar = reactive({ show: false, text: '', color: 'success' })
const fieldOrder = ref<string[]>([])

const detailFields = computed(() => {
  const info = detailsDialog.item?.registration_info
  if (!info) return []
  const keys = Object.keys(info)
  const order = ['跑步APP', ...fieldOrder.value]
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

async function loadFieldOrder() {
  try {
    const res = await ajax<any[]>('/api/fields')
    if (res.code === 200) {
      fieldOrder.value = res.data.map((f: any) => f.label)
    }
  } catch (err) { /* ignore */ }
}

onMounted(() => {
  loadFieldOrder()
})

function openDetailsDialog(item: RegistrationItem) {
  detailsDialog.item = item
  detailsDialog.show = true
}

function confirmDelete(item: RegistrationItem) {
  deleteDialog.item = item
  deleteDialog.show = true
}

// 配置化表头
const headers = [
  { title: '用户名', key: 'username', searchable: true, filterable: true },
  { title: '跑步APP', key: 'app', sortable: false, filterable: true },
  { title: '登记信息', key: 'details', sortable: false },
  { title: '创建时间', key: 'created_at', sortable: true },
  { title: '登记状态', key: 'status', sortable: true, filterable: true },
  { title: '操作', key: 'actions', sortable: false },
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

// 事件处理
function handleView(item: RegistrationItem) {
  openDetailsDialog(item)
}

async function copyDetailText() {
  const item = detailsDialog.item
  if (!item?.registration_info) return
  const info = item.registration_info
  const keys = Object.keys(info)
  const order = ['跑步APP', ...fieldOrder.value]
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

  try {
    const res = await ajax(`${ApiUrl.GET_REGISTRATIONS}?page=${page}&page_size=${pageSize}`, {
      method: 'GET',
      headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
    })
    if (res.code === 200) {
      registers.value = res.data.items.map((item: any) => ({
        ...item,
        app: item.registration_info?.['跑步APP'] || ''
      }))
      totalRegisters.value = res.data.total
    }
  } catch (err) {
    showMsg('加载登记数据失败', 'error')
  } finally {
    loading.value = false
  }
}

</script>
