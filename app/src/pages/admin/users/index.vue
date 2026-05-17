<template>
  <v-container fluid class="pa-0 d-flex flex-column align-center">
    <div class="table-wrapper mt-4">
      <v-row align="center" class="mb-4">
        <v-col cols="12" sm="auto">
          <h1 class="text-h4">账户管理</h1>
        </v-col>
        <v-col cols="12" sm class="d-flex flex-wrap ga-2 justify-sm-end">
          <v-btn color="secondary" variant="tonal" @click="bulkDialog.show = true" prepend-icon="mdi-file-upload">批量新增</v-btn>
          <v-btn color="primary" @click="dialog = true" prepend-icon="mdi-plus">新建账户</v-btn>
        </v-col>
      </v-row>

      <!-- 使用封装后的通用表格组件 -->
      <app-data-table :headers="headers" :items="users" :total-items="totalUsers" :loading="loading"
        v-model:page="currentPage" v-model:items-per-page="itemsPerPage" show-search show-filter
        search-label="搜索用户名/IP/设备" @update:options="loadUsers" @reset="loadUsers">
        <!-- 自定义槽位：类型 -->
        <template v-slot:item.type="{ item }">
          <v-chip :color="item.type === 'admin' ? 'primary' : 'grey'" size="small">
            {{ item.type === 'admin' ? '管理员' : '普通' }}
          </v-chip>
        </template>

        <!-- 自定义槽位：注册时间 -->
        <template v-slot:item.register_time="{ item }">
          {{ formatDate(item.register_time) }}
        </template>

        <!-- 自定义槽位：最后登录 -->
        <template v-slot:item.last_login_time="{ item }">
          {{ formatDate(item.last_login_time) }}
        </template>

        <template v-slot:item.login_device="{ item }">
          <span class="text-caption" :title="item.login_device">{{ formatUA(item.login_device) }}</span>
        </template>

        <!-- 自定义槽位：操作 -->
        <template v-slot:item.actions="{ item }">
          <div class="d-flex ga-1">
            <v-btn variant="tonal" rounded color="primary" @click="handleAction('修改', item)">修改</v-btn>
            <v-btn variant="tonal" rounded color="error" :disabled="isCurrentUser(item)" @click="handleAction('删除', item)">删除</v-btn>
            <v-btn variant="tonal" rounded @click="handleAction('查找工单', item)" v-if="item.type !== 'admin'">查找工单</v-btn>
            <v-btn variant="tonal" rounded color="warning" @click="handleAction('强制下线', item)">强制下线</v-btn>
          </div>
        </template>
      </app-data-table>
    </div>

    <!-- 新建账户 Dialog -->
    <v-dialog v-model="dialog" max-width="500">
      <v-card class="pa-4">
        <v-card-title>新建账户</v-card-title>
        <v-card-text>
          <v-form ref="formRef" @submit.prevent="createAccount">
            <v-text-field v-model="newUsername" label="用户名" variant="outlined"
              :rules="[v => !!v || '用户名必填', v => v.length <= 20 || '用户名不能超过20位']" hide-details="auto" class="mb-4"
              required></v-text-field>
            <v-text-field v-model="newPassword" label="密码" type="password" variant="outlined"
              :rules="[v => !!v || '密码必填', v => (v.length >= 6 && v.length <= 16) || '密码需6-16位', v => /^[A-Za-z0-9-]+$/.test(v) || '仅支持字母、数字和短横线']"
              hide-details="auto" class="mb-4" required></v-text-field>
            <v-select v-model="newType" :items="[{ title: '普通', value: 'default' }, { title: '管理员', value: 'admin' }]"
              label="账户类型" variant="outlined" density="compact" class="compact-select" hide-details="auto"></v-select>
            <div class="text-caption text-grey mt-1">创建后不可修改账户类型</div>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="tonal" @click="dialog = false">取消</v-btn>
          <v-btn color="primary" variant="flat" :loading="loading" @click="createAccount">提交</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 批量新增账户 Dialog -->
    <v-dialog v-model="bulkDialog.show" max-width="600">
      <v-card class="pa-4">
        <v-card-title>批量新增账户</v-card-title>
        <v-card-text>
          <div class="mb-4">
            <div class="text-subtitle-2 mb-2">1. 下载样板文件</div>
            <v-btn variant="outlined" size="small" prepend-icon="mdi-download" @click="downloadTemplate">下载 Excel 样板</v-btn>
          </div>
          <div class="mb-4">
            <div class="text-subtitle-2 mb-2">2. 格式要求</div>
            <v-list density="compact">
              <v-list-item prepend-icon="mdi-check-circle" title="第一行为表头：用户名、密码、类型"></v-list-item>
              <v-list-item prepend-icon="mdi-check-circle" title="用户名：1-20位字符"></v-list-item>
              <v-list-item prepend-icon="mdi-check-circle" title="密码：6-16位，支持字母、数字、短横线"></v-list-item>
              <v-list-item prepend-icon="mdi-check-circle" title="类型：admin (管理员) 或 default (普通用户)"></v-list-item>
            </v-list>
          </div>
          <div class="mb-4">
            <div class="text-subtitle-2 mb-2">3. 上传文件</div>
            <v-file-input v-model="bulkDialog.file" label="选择 Excel 文件" variant="outlined" density="compact"
              accept=".xlsx, .xls" prepend-icon="mdi-microsoft-excel" hide-details :loading="bulkDialog.isParsing"></v-file-input>
          </div>

          <!-- 预览与编辑区域 -->
          <v-expand-transition>
            <div v-if="bulkDialog.parsedAccounts.length" class="mb-4">
              <div class="d-flex justify-space-between align-center mb-2">
                <div class="text-subtitle-2">4. 预览与编辑 (共 {{ bulkDialog.parsedAccounts.length }} 条)</div>
                <v-btn variant="text" size="small" color="error" @click="bulkDialog.parsedAccounts = []">清空列表</v-btn>
              </div>
              <v-card border flat class="preview-list">
                <v-table density="compact">
                  <thead>
                    <tr>
                      <th class="text-left text-no-wrap" style="width: 35%">用户名</th>
                      <th class="text-left text-no-wrap" style="width: 35%">密码</th>
                      <th class="text-left text-no-wrap" style="width: 20%">类型</th>
                      <th style="width: 10%"></th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(acc, index) in bulkDialog.parsedAccounts" :key="index" :class="{'bg-green-lighten-5': acc.status === 'success', 'bg-red-lighten-5': acc.status === 'error'}">
                      <td class="pa-1">
                        <v-text-field v-model="acc.username" density="compact" hide-details variant="solo-filled" flat class="compact-input editable-cell"></v-text-field>
                      </td>
                      <td class="pa-1">
                        <v-text-field v-model="acc.password" density="compact" hide-details variant="solo-filled" flat class="compact-input editable-cell"></v-text-field>
                      </td>
                      <td class="pa-1">
                        <v-select v-model="acc.type" :items="['default', 'admin']" density="compact" hide-details variant="solo-filled" flat class="compact-input editable-cell"></v-select>
                      </td>
                      <td class="pa-1 text-center">
                        <v-btn icon="mdi-delete-outline" variant="text" size="x-small" color="error" @click="bulkDialog.parsedAccounts.splice(index, 1)"></v-btn>
                      </td>
                    </tr>
                  </tbody>
                </v-table>
              </v-card>
            </div>
          </v-expand-transition>

          <!-- 导入结果展示 -->
          <v-expand-transition>
            <div v-if="bulkDialog.result" class="mt-4 pa-4 bg-grey-lighten-4 rounded">
              <div class="text-subtitle-1 font-weight-bold mb-2">导入结果</div>
              <div class="d-flex gap-4 mb-2">
                <span class="text-success">成功: {{ bulkDialog.result.success_count }}</span>
                <span class="text-error">失败: {{ bulkDialog.result.errors.length }}</span>
                <span>总计: {{ bulkDialog.result.total_count }}</span>
              </div>
              <v-divider v-if="bulkDialog.result.errors.length" class="my-2"></v-divider>
              <div v-if="bulkDialog.result.errors.length" style="max-height: 150px; overflow-y: auto;">
                <div v-for="(err, i) in bulkDialog.result.errors" :key="i" class="text-caption text-error">
                  {{ err }}
                </div>
              </div>
            </div>
          </v-expand-transition>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="tonal" @click="bulkDialog.show = false; bulkDialog.result = null">取消</v-btn>
          <v-btn color="primary" variant="flat" :loading="loading" :disabled="!bulkDialog.file" @click="handleBulkUpload">
            开始导入
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 修改账户 Dialog -->
    <v-dialog v-model="editDialog.show" max-width="500">
      <v-card class="pa-4">
        <v-card-title>修改账户</v-card-title>
        <v-card-text>
          <v-form ref="editFormRef" @submit.prevent="updateAccount">
            <v-text-field v-model="editDialog.username" label="用户名" variant="outlined"
              :rules="[v => !!v || '用户名必填', v => v.length <= 20 || '用户名不能超过20位']" hide-details="auto" class="mb-4"
              required></v-text-field>
            <v-text-field v-model="editDialog.password" label="新密码 (留空则不修改)" type="password" variant="outlined"
              :rules="[v => !v || (v.length >= 6 && v.length <= 16) || '密码需6-16位', v => !v || /^[A-Za-z0-9-]+$/.test(v) || '仅支持字母、数字和短横线']"
              hide-details="auto" class="mb-4"></v-text-field>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="tonal" @click="editDialog.show = false">取消</v-btn>
          <v-btn color="primary" variant="flat" :loading="loading" @click="updateAccount">保存</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 删除确认 Dialog -->
    <v-dialog v-model="confirmDialog.show" max-width="400">
      <v-card>
        <v-card-title class="text-h5 pa-4">确认删除</v-card-title>
        <v-card-text class="pa-4 pt-0">
          您确定要删除账户 <strong>{{ confirmDialog.username }}</strong> 吗？此操作不可撤销。
        </v-card-text>
        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="confirmDialog.show = false">取消</v-btn>
          <v-btn color="error" variant="flat" :loading="loading" @click="confirmDelete">确认删除</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 强制下线确认 Dialog -->
    <v-dialog v-model="logoutDialog.show" max-width="400">
      <v-card>
        <v-card-title class="text-h5 pa-4">确认强制下线</v-card-title>
        <v-card-text class="pa-4 pt-0">
          您确定要将账户 <strong>{{ logoutDialog.username }}</strong> 强制下线吗？该用户的所有当前活跃会话都将被清除。
        </v-card-text>
        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="logoutDialog.show = false">取消</v-btn>
          <v-btn color="warning" variant="flat" :loading="loading" @click="confirmForceLogout">确认下线</v-btn>
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
}

.compact-select .v-field__input,
.compact-select .v-field__label {
  font-size: 0.9em !important;
}

.preview-list {
  max-height: 300px;
  overflow-y: auto;
  overflow-x: auto;
}

.preview-list :deep(table) {
  min-width: 450px !important;
}

.compact-input :deep(.v-field__input) {
  padding-top: 4px !important;
  padding-bottom: 4px !important;
  min-height: 32px !important;
  font-size: 0.85rem !important;
}

.editable-cell :deep(.v-field) {
  border-radius: 4px !important;
  background-color: rgba(0, 0, 0, 0.03) !important;
  transition: background-color 0.2s;
}

.editable-cell:hover :deep(.v-field) {
  background-color: rgba(0, 0, 0, 0.06) !important;
}

.editable-cell :deep(.v-field__outline) {
  display: none;
}
</style>

<script lang="ts" setup>
import { ref, reactive, watch } from 'vue'
import { useRouter } from 'vue-router'
import * as XLSX from 'xlsx'
import { ajax } from '@/api/ajax'
import { cookie } from '@/api/cookie'
import { ApiUrl } from '@/config/api-url'
import { getErrorMessage } from '@/config/error-msg'
import type { UserItem } from '@/config/api-type'
import AppDataTable from '@/components/AppDataTable.vue'
import { useAppStore } from '@/stores/app'

interface PaginatedUsers { total: number; page: number; page_size: number; items: UserItem[]; }

const appStore = useAppStore()
const router = useRouter()
const users = ref<UserItem[]>([])
const loading = ref(false)
const totalUsers = ref(0)
const itemsPerPage = ref(20)
const currentPage = ref(1)
const dialog = ref(false)
const bulkDialog = reactive({ 
  show: false, 
  file: null as File | null, 
  parsedAccounts: [] as any[],
  isParsing: false,
  result: null as any 
})
const editDialog = reactive({ show: false, uid: '', username: '', password: '' })
const confirmDialog = reactive({ show: false, uid: '', username: '' })
const logoutDialog = reactive({ show: false, uid: '', username: '' })
const formRef = ref<any>(null)
const editFormRef = ref<any>(null)
const newUsername = ref('')
const newPassword = ref('')
const newType = ref('default')

const snackbar = reactive({ show: false, text: '', color: 'success' })
function showMsg(text: string, color: string = 'success') {
  snackbar.text = text
  snackbar.color = color
  snackbar.show = true
}

function isCurrentUser(user: UserItem) {
  return appStore.userInfo?.username === user.username
}

watch(() => bulkDialog.file, (newFile) => {
  if (newFile) {
    parseFile(newFile)
  } else {
    bulkDialog.parsedAccounts = []
    bulkDialog.result = null
  }
})

function parseFile(file: File) {
  bulkDialog.isParsing = true
  bulkDialog.result = null
  const reader = new FileReader()
  reader.onload = (e: any) => {
    try {
      const data = e.target.result
      const workbook = XLSX.read(data, { type: 'binary' })
      const sheetName = workbook.SheetNames[0]
      const sheet = workbook.Sheets[sheetName]
      const rows = XLSX.utils.sheet_to_json(sheet, { header: 1 }) as any[][]
      
      // 过滤空行并映射为对象
      bulkDialog.parsedAccounts = rows.slice(1)
        .filter(row => row.length > 0 && row[0])
        .map(row => ({
          username: String(row[0] || ''),
          password: String(row[1] || ''),
          type: String(row[2] || 'default'),
          status: 'pending' as 'pending' | 'success' | 'error',
          errorMsg: ''
        }))
    } catch (err) {
      showMsg('文件解析失败', 'error')
    } finally {
      bulkDialog.isParsing = false
    }
  }
  reader.readAsBinaryString(file)
}

function handleAction(action: string, user: UserItem) {
  if (action === '修改') {
    editDialog.uid = user.uid
    editDialog.username = user.username
    editDialog.password = ''
    editDialog.show = true
  } else if (action === '删除') {
    if (isCurrentUser(user)) {
      showMsg('无法删除当前登录的账户', 'error')
      return
    }
    confirmDialog.uid = user.uid
    confirmDialog.username = user.username
    confirmDialog.show = true
  } else if (action === '强制下线') {
    logoutDialog.uid = user.uid
    logoutDialog.username = user.username
    logoutDialog.show = true
  } else if (action === '查找工单') {
    router.push({ path: '/admin/feedbacks', query: { username: user.username } })
  }
}

async function confirmDelete() {
  await deleteAccount(confirmDialog.uid)
  confirmDialog.show = false
}

async function confirmForceLogout() {
  await forceLogout(logoutDialog.uid)
  logoutDialog.show = false
}

function downloadTemplate() {
  const data = [
    ['用户名', '密码', '类型'],
    ['testuser', 'password123', 'default'],
    ['adminuser', 'secret456', 'admin']
  ]
  const ws = XLSX.utils.aoa_to_sheet(data)
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, "用户导入模板")
  XLSX.writeFile(wb, "用户导入样板.xlsx")
}

async function handleBulkUpload() {
  if (!bulkDialog.parsedAccounts.length) return
  
  loading.value = true
  bulkDialog.result = { success_count: 0, total_count: bulkDialog.parsedAccounts.length, errors: [] }
  
  for (let i = 0; i < bulkDialog.parsedAccounts.length; i++) {
    const acc = bulkDialog.parsedAccounts[i]
    acc.status = 'pending'
    
    try {
      const res = await ajax(ApiUrl.CREATE_USER, {
        method: 'POST',
        body: { username: acc.username, password: acc.password, type: acc.type },
        headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
      })
      
      if (res.code === 200) {
        acc.status = 'success'
        bulkDialog.result.success_count++
      } else {
        acc.status = 'error'
        acc.errorMsg = res.msg || '创建失败'
        bulkDialog.result.errors.push(`第 ${i + 2} 行 (${acc.username}): ${acc.errorMsg}`)
      }
    } catch (err) {
      acc.status = 'error'
      acc.errorMsg = '网络错误'
      bulkDialog.result.errors.push(`第 ${i + 2} 行 (${acc.username}): 网络请求失败`)
    }
  }
  
  if (bulkDialog.result.success_count > 0) {
    showMsg(`批量导入完成，成功 ${bulkDialog.result.success_count} 个`)
    loadUsers()
  }
  loading.value = false
}

async function updateAccount() {
  const { valid } = await editFormRef.value.validate()
  if (!valid) return
  loading.value = true
  try {
    const res = await ajax(`${ApiUrl.UPDATE_USER}/${editDialog.uid}`, {
      method: 'PATCH',
      body: { username: editDialog.username, password: editDialog.password || undefined },
      headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
    })
    if (res.code === 200) {
      editDialog.show = false
      showMsg('账户修改成功')
      loadUsers()
    } else {
      showMsg(res.msg || '修改失败', 'error')
    }
  } catch (err) {
    showMsg('请求失败，请稍后再试', 'error')
  } finally {
    loading.value = false
  }
}

async function forceLogout(uid: string) {
  loading.value = true
  try {
    const res = await ajax(`${ApiUrl.FORCE_LOGOUT}/${uid}/force-logout`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
    })
    if (res.code === 200) {
      showMsg('该账户已强制下线')
      loadUsers()
    } else {
      showMsg(res.msg || '强制下线失败', 'error')
    }
  } catch (err) {
    showMsg('请求失败，请稍后再试', 'error')
  } finally {
    loading.value = false
  }
}

async function deleteAccount(uid: string) {
  loading.value = true
  try {
    const res = await ajax(`${ApiUrl.DELETE_USER}/${uid}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
    })
    if (res.code === 200) {
      showMsg('账户删除成功')
      loadUsers()
    } else {
      showMsg(res.msg || getErrorMessage(res.code, '删除失败'), 'error')
    }
  } catch (err) {
    showMsg('请求失败，请稍后再试', 'error')
  } finally {
    loading.value = false
  }
}

// 配置化表头
const headers = [
  { title: '用户名', key: 'username', searchable: true, filterable: true },
  { title: '活跃会话', key: 'session_count', sortable: true },
  { title: '类型', key: 'type', sortable: false, filterable: true, filterFormatter: (v: string) => v === 'admin' ? '管理员' : '普通' },
  { title: '登录IP', key: 'login_ip', sortable: false, searchable: true, filterable: true },
  { title: '登录设备', key: 'login_device', sortable: false, searchable: true, filterable: true },
  { title: '操作', key: 'actions', sortable: false },
  { title: '注册时间', key: 'register_time', sortable: true, filterable: true, filterFormatter: (v: string) => formatDate(v) },
  { title: '最后登录', key: 'last_login_time', sortable: true, filterable: true, filterFormatter: (v: string) => formatDate(v) },
]

function formatDate(isoString: string | null) {
  if (!isoString) return '-'
  const date = new Date(isoString)
  return date.getFullYear() + '-' + String(date.getMonth() + 1).padStart(2, '0') + '-' + String(date.getDate()).padStart(2, '0') + ' ' + String(date.getHours()).padStart(2, '0') + ':' + String(date.getMinutes()).padStart(2, '0') + ':' + String(date.getSeconds()).padStart(2, '0')
}

function formatUA(ua: string | null): string {
  if (!ua) return '-'
  const parts: string[] = []
  if (/Windows/i.test(ua)) parts.push('Windows')
  else if (/Mac/i.test(ua)) parts.push('Mac')
  else if (/Linux/i.test(ua) && !/Android/i.test(ua)) parts.push('Linux')
  if (/iPhone/i.test(ua)) parts.push('iPhone')
  else if (/iPad/i.test(ua)) parts.push('iPad')
  else if (/Android/i.test(ua)) parts.push('Android')
  if (/Edg\//i.test(ua)) parts.push('Edge')
  else if (/Chrome/i.test(ua) && !/Edg\//i.test(ua)) parts.push('Chrome')
  else if (/Safari/i.test(ua) && !/Chrome/i.test(ua)) parts.push('Safari')
  else if (/Firefox/i.test(ua)) parts.push('Firefox')
  return parts.length > 0 ? parts.join(' / ') : ua.slice(0, 50)
}

async function createAccount() {
  const { valid } = await formRef.value.validate()
  if (!valid) return
  loading.value = true
  try {
    const res = await ajax(ApiUrl.CREATE_USER, {
      method: 'POST',
      body: { username: newUsername.value, password: newPassword.value, type: newType.value },
      headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
    })
    if (res.code === 200) {
      dialog.value = false
      newUsername.value = ''; newPassword.value = ''
      showMsg('账户创建成功')
      loadUsers()
    } else {
      showMsg(res.msg || getErrorMessage(res.code, '创建失败'), 'error')
    }
  } catch (err) {
    showMsg('请求失败，请稍后再试', 'error')
  } finally { loading.value = false }
}

async function loadUsers(options: any = { page: 1, itemsPerPage: 20, sortBy: [] }) {
  const page = options.page || currentPage.value
  const pageSize = options.itemsPerPage || itemsPerPage.value
  const sortBy = options.sortBy?.[0]

  let url = `${ApiUrl.GET_USERS}?page=${page}&page_size=${pageSize}`
  if (sortBy) url += `&sort_by=${sortBy.key}&order=${sortBy.order}`

  loading.value = true
  currentPage.value = page
  itemsPerPage.value = pageSize

  try {
    const res = await ajax<PaginatedUsers>(url, {
      method: 'GET',
      headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
    })
    if (res.code === 200) {
      users.value = res.data.items
      totalUsers.value = res.data.total
    }
  } catch (err) {
    console.error('Failed to load users', err)
  } finally { loading.value = false }
}
</script>
