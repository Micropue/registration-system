<template>
  <v-container fluid class="pa-0 d-flex flex-column align-center">
    <div class="table-wrapper mt-4">
      <div class="d-flex align-center mb-4">
        <h1 class="text-h4">用户余额管理 - {{ appName }}</h1>
      </div>

      <app-data-table
        :headers="headers"
        :items="items"
        :total-items="total"
        :loading="loading"
        :client-side="false"
        show-search show-filter
        search-label="搜索用户名"
        v-model:page="page"
        v-model:items-per-page="pageSize"
        @update:options="loadData"
      >
        <template v-slot:item.username="{ item }">
          <div class="d-flex align-center ga-2">
            <span class="font-weight-bold">{{ item.username }}</span>
            <v-chip v-if="item.group_name" size="x-small" variant="flat"
              :color="item.group_name === '超级管理员' ? '#B71C1C' : item.group_name === '未分配' ? '#6B7280' : '#D32F2F'">
              {{ item.group_name }}
            </v-chip>
            <v-chip v-if="item.is_delegated" size="x-small" color="warning">已链接</v-chip>
          </div>
          <div v-if="item.is_delegated && item.delegated_to_name" class="text-caption text-grey">
            余额由 {{ item.delegated_to_name }} 管理
          </div>
        </template>
        <template v-slot:item.updated_at="{ item }">
          {{ formatDate(item.updated_at) }}
        </template>
        <template v-slot:item.actions="{ item }">
          <div class="d-flex ga-1">
            <v-btn variant="tonal" rounded size="x-small" color="success"
              @click="openAdjust(item, true)">增加余额</v-btn>
            <v-btn variant="tonal" rounded size="x-small" color="error"
              @click="openAdjust(item, false)">减少余额</v-btn>
            <v-tooltip v-if="item.is_delegated" text="该用户余额已链接到上级，增减将作用于上级余额">
              <template v-slot:activator="{ props }">
                <v-icon v-bind="props" size="16" color="warning">mdi-link-variant</v-icon>
              </template>
            </v-tooltip>
          </div>
        </template>
      </app-data-table>
    </div>

    <v-dialog v-model="adjustDialog.show" max-width="400">
      <v-card class="pa-4">
        <v-card-title>{{ adjustDialog.isIncrease ? '增加余额' : '减少余额' }} - {{ adjustDialog.username }}</v-card-title>
        <v-card-text>
           <div class="text-subtitle-2 mb-2">
            当前余额: {{ adjustDialog.currentBalance }}
            <v-chip v-if="balanceMode" size="x-small" class="ml-1" :color="balanceMode === 'mileage' ? 'primary' : 'green'">
              {{ balanceMode === 'mileage' ? '公里' : '次' }}
            </v-chip>
          </div>
          <v-text-field v-model.number="adjustDialog.amount" label="调整数额" type="number" variant="outlined" density="comfortable"
            :rules="[v => v > 0 || '请输入正数']" hide-details class="mb-3" :min="0.01" step="0.01"></v-text-field>
          <v-text-field v-model="adjustDialog.note" label="备注" variant="outlined" density="comfortable" hide-details></v-text-field>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="tonal" @click="adjustDialog.show = false">取消</v-btn>
          <v-btn :color="adjustDialog.isIncrease ? 'success' : 'error'" variant="flat" :loading="adjusting" @click="doAdjust">
            {{ adjustDialog.isIncrease ? '确认增加' : '确认减少' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-snackbar v-model="snackbar.show" :color="snackbar.color" timeout="3000">
      {{ snackbar.text }}
    </v-snackbar>
  </v-container>
</template>

<style scoped>
.table-wrapper { width: 90%; }
</style>

<script lang="ts" setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ajax } from '@/api/ajax'
import { cookie } from '@/api/cookie'
import { ApiUrl } from '@/config/api-url'
import AppDataTable from '@/components/AppDataTable.vue'

const route = useRoute()
const appUid = route.params.appUid as string

const items = ref<any[]>([])
const total = ref(0)
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const appName = ref('')
const balanceMode = ref('')

const adjustDialog = reactive({
  show: false,
  isIncrease: true,
  userUid: '',
  username: '',
  currentBalance: 0,
  amount: 0,
  note: ''
})
const adjusting = ref(false)

function formatDate(iso: string) {
  if (!iso) return '-'
  return new Date(iso).toLocaleString('zh-CN')
}

const snackbar = reactive({ show: false, text: '', color: 'success' })

const headers = [
  { title: '用户名', key: 'username', searchable: true, filterable: true },
  { title: '当前余额', key: 'balance' },
  { title: '更新时间', key: 'updated_at' },
  { title: '操作', key: 'actions', sortable: false }
]

async function loadApps() {
  try {
    const res = await ajax<any[]>(ApiUrl.GET_RUNNING_APPS, {
      headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
    })
    if (res.code === 200) {
      const app = res.data.find((a: any) => a.uid === appUid)
      if (app) {
        appName.value = app.name
        balanceMode.value = app.balance_mode || ''
      }
    }
  } catch (e) { /* ignore */ }
}

async function loadData(options: any = {}) {
  if (options.page) page.value = options.page
  if (options.itemsPerPage) pageSize.value = options.itemsPerPage
  loading.value = true
  try {
    const res = await ajax<any>(
      `${ApiUrl.GET_APP_USER_BALANCES}/${appUid}/users-balance?page=${page.value}&page_size=${pageSize.value}`,
      { headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` } }
    )
    if (res.code === 200 && res.data) {
      items.value = res.data.items || []
      total.value = res.data.total || 0
    }
  } catch (e) { /* ignore */ }
  finally { loading.value = false }
}

function openAdjust(item: any, isIncrease: boolean) {
  adjustDialog.userUid = item.user_uid
  adjustDialog.username = item.username
  adjustDialog.currentBalance = item.balance
  adjustDialog.isIncrease = isIncrease
  adjustDialog.amount = 0
  adjustDialog.note = ''
  adjustDialog.show = true
}

async function doAdjust() {
  if (!adjustDialog.amount || adjustDialog.amount <= 0) return
  adjusting.value = true
  try {
    const realAmount = adjustDialog.isIncrease ? adjustDialog.amount : -adjustDialog.amount
    const res = await ajax(`${ApiUrl.ADJUST_APP_USER_BALANCE}/${appUid}/users/${adjustDialog.userUid}/balance`, {
      method: 'PATCH',
      body: { amount: realAmount, note: adjustDialog.note || (adjustDialog.isIncrease ? '管理员手动增加余额' : '管理员手动减少余额') },
      headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
    })
    if (res.code === 200) {
      snackbar.text = '余额已调整'
      snackbar.color = 'success'
      snackbar.show = true
      adjustDialog.show = false
      loadData()
    } else {
      snackbar.text = res.msg || '操作失败'
      snackbar.color = 'error'
      snackbar.show = true
    }
  } catch (e) {
    snackbar.text = '操作失败'
    snackbar.color = 'error'
    snackbar.show = true
  } finally {
    adjusting.value = false
  }
}

onMounted(() => {
  loadApps()
  loadData()
})
</script>
