<template>
  <v-container fluid class="pa-0 d-flex flex-column align-center">
    <div class="table-wrapper mt-4">
      <div class="d-flex justify-space-between align-center mb-4">
        <h1 class="text-h4">账户管理</h1>
        <v-btn color="primary" @click="dialog = true" prepend-icon="mdi-plus">新建账户</v-btn>
      </div>

      <v-expansion-panels class="mb-4">
        <v-expansion-panel elevation="0" border>
          <v-expansion-panel-title>
            <div class="d-flex align-center">
              <v-icon icon="mdi-filter-outline" class="me-2" color="primary"></v-icon>
              <span class="text-primary font-weight-bold">数据筛选</span>
            </div>
          </v-expansion-panel-title>
          <v-expansion-panel-text>
            <v-row class="mt-1">
              <v-col cols="12" md="3">
                <v-select
                  v-model="filterType"
                  :items="['全部', '管理员', '普通']"
                  label="账户类型筛选"
                  variant="outlined"
                  density="compact"
                  hide-details
                  @update:model-value="loadUsers()"
                ></v-select>
              </v-col>
            </v-row>
          </v-expansion-panel-text>
        </v-expansion-panel>
      </v-expansion-panels>
      
      <v-card class="elevation-0" border>
        <v-data-table-server 
          :headers="headers" 
          :items="users" 
          :loading="loading" 
          v-model:page="currentPage"
          v-model:items-per-page="itemsPerPage" 
          :items-length="totalUsers" 
          items-per-page-text="每页行数"
          page-text="{0}-{1} 共 {2}" 
          :items-per-page-options="[
            { value: 10, title: '10' },
            { value: 20, title: '20' },
            { value: 50, title: '50' },
            { value: -1, title: '全部' }
          ]"
          @update:options="loadUsers" 
          class="elevation-0"
        >
          <template v-slot:item.type="{ item }">
            <v-chip :color="item.type === 'admin' ? 'primary' : 'grey'" size="small">
              {{ item.type === 'admin' ? '管理员' : '普通' }}
            </v-chip>
          </template>
          <template v-slot:item.register_time="{ item }">
            {{ formatDate(item.register_time) }}
          </template>
          <template v-slot:item.last_login_time="{ item }">
            {{ formatDate(item.last_login_time) }}
          </template>
          <template v-slot:item.actions="{ item }">
            <v-menu location="bottom">
              <template v-slot:activator="{ props }">
                <v-btn icon="mdi-dots-vertical" variant="text" size="small" v-bind="props"></v-btn>
              </template>
              <v-list density="compact">
                <v-list-item @click="handleAction('修改', item)">修改</v-list-item>
                <v-list-item @click="handleAction('删除', item)" class="text-error">删除</v-list-item>
                <v-list-item @click="handleAction('查找工单', item)">查找工单</v-list-item>
                <v-list-item @click="handleAction('强制下线', item)">强制下线</v-list-item>
                <v-list-item @click="handleAction('登记检查', item)">登记检查</v-list-item>
              </v-list>
            </v-menu>
          </template>
        </v-data-table-server>
      </v-card>
    </div>

    <!-- 新建账户 Dialog -->
    <v-dialog v-model="dialog" max-width="500">
      <v-card class="pa-4">
        <v-card-title>新建账户</v-card-title>
        <v-card-text>
          <v-form ref="formRef" @submit.prevent="createAccount">
            <v-text-field 
              v-model="newUsername" 
              label="用户名" 
              variant="outlined" 
              :rules="[v => !!v || '用户名必填', v => v.length <= 20 || '用户名不能超过20位']"
              hide-details="auto"
              class="mb-4"
              required
            ></v-text-field>
            <v-text-field 
              v-model="newPassword" 
              label="密码" 
              type="password" 
              variant="outlined" 
              :rules="[v => !!v || '密码必填', v => (v.length >= 6 && v.length <= 16) || '密码需6-16位', v => /^[A-Za-z0-9-]+$/.test(v) || '仅支持字母、数字和短横线']"
              hide-details="auto"
              class="mb-4"
              required
            ></v-text-field>
            <v-select 
              v-model="newType" 
              :items="[{ title: '普通', value: 'default' }, { title: '管理员', value: 'admin' }]" 
              label="账户类型"
              variant="outlined"
              density="compact"
              class="compact-select"
              hide-details="auto"
            ></v-select>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="tonal" @click="dialog = false">取消</v-btn>
          <v-btn color="primary" variant="flat" :loading="loading" @click="createAccount">提交</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 全局提示栏 -->
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

.table-wrapper :deep(.v-card) {
  width: 100% !important;
  overflow-x: auto;
}

.table-wrapper :deep(.v-data-table) {
  width: 100% !important;
  min-width: 800px;
}

.table-wrapper :deep(th) {
  white-space: nowrap !important;
}
</style>

<style>
.compact-select .v-field__input,
.compact-select .v-field__label {
  font-size: 0.85rem !important;
}
</style>

<script lang="ts" setup>
import { ref, reactive, onMounted } from 'vue'
import { ajax } from '@/api/ajax'
import { cookie } from '@/api/cookie'
import { ApiUrl } from '@/config/api-url'
import { getErrorMessage } from '@/config/error-msg'
import type { UserItem } from '@/config/api-type'

interface PaginatedUsers {
  total: number;
  page: number;
  page_size: number;
  items: UserItem[];
}

const users = ref<UserItem[]>([])
const loading = ref(false)
const totalUsers = ref(0)
const itemsPerPage = ref(20)
const currentPage = ref(1)
const dialog = ref(false)
const formRef = ref<any>(null)
const newUsername = ref('')
const newPassword = ref('')
const newType = ref('default')
const filterType = ref('全部')

const snackbar = reactive({
  show: false,
  text: '',
  color: 'success'
})

function showMsg(text: string, color: string = 'success') {
  snackbar.text = text
  snackbar.color = color
  snackbar.show = true
}

function handleAction(action: string, user: UserItem) {
  showMsg(`执行操作: ${action} - ${user.username}`)
}

const headers = [
  { title: '用户名', key: 'username' },
  { title: '活跃会话', key: 'session_count', sortable: true },
  { title: '类型', key: 'type', sortable: false },
  { title: '注册时间', key: 'register_time', sortable: true },
  { title: '最后登录', key: 'last_login_time', sortable: true },
  { title: '登录IP', key: 'login_ip', sortable: false },
  { title: '登录设备', key: 'login_device', sortable: false },
  { title: '操作', key: 'actions', sortable: false },
]

function formatDate(isoString: string | null) {
  if (!isoString) return '-'
  const date = new Date(isoString)
  return date.getFullYear() + '-' + 
         String(date.getMonth() + 1).padStart(2, '0') + '-' + 
         String(date.getDate()).padStart(2, '0') + ' ' + 
         String(date.getHours()).padStart(2, '0') + ':' + 
         String(date.getMinutes()).padStart(2, '0') + ':' + 
         String(date.getSeconds()).padStart(2, '0')
}

async function createAccount() {
  const { valid } = await formRef.value.validate()
  if (!valid) return

  loading.value = true
  try {
    const res = await ajax(ApiUrl.CREATE_USER, {
      method: 'POST',
      body: {
        username: newUsername.value,
        password: newPassword.value,
        type: newType.value
      },
      headers: {
        'Authorization': `Bearer ${cookie.get('token') || ''}`
      }
    })

    if (res.code === 200) {
      dialog.value = false
      newUsername.value = ''
      newPassword.value = ''
      showMsg('账户创建成功')
      loadUsers()
    } else {
      showMsg(res.msg || getErrorMessage(res.code, '创建失败'), 'error')
    }
  } catch (err) {
    console.error('Failed to create account', err)
    showMsg('请求失败，请稍后再试', 'error')
  } finally {
    loading.value = false
  }
}

async function loadUsers(options: any = { page: 1, itemsPerPage: 20, sortBy: [] }) {
  const page = options.page || currentPage.value
  const pageSize = options.itemsPerPage || itemsPerPage.value
  const sortBy = options.sortBy?.[0]
  
  const roleMap: Record<string, string> = { '管理员': 'admin', '普通': 'default' }
  const typeParam = roleMap[filterType.value] || ''

  let url = `${ApiUrl.GET_USERS}?page=${page}&page_size=${pageSize}`
  if (sortBy) {
    url += `&sort_by=${sortBy.key}&order=${sortBy.order}`
  }
  if (typeParam) {
    url += `&type=${typeParam}`
  }

  loading.value = true
  currentPage.value = page
  itemsPerPage.value = pageSize

  try {
    const res = await ajax<PaginatedUsers>(url, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${cookie.get('token') || ''}`
      }
    })

    if (res.code === 200) {
      users.value = res.data.items
      totalUsers.value = res.data.total
    }
  } catch (err) {
    console.error('Failed to load users', err)
  } finally {
    loading.value = false
  }
}
onMounted(() => {
  loadUsers()
})
</script>
