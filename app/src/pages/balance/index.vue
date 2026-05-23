<template>
  <v-container fluid class="pa-0 d-flex flex-column align-center">
    <div class="table-wrapper mt-4">
      <h1 class="text-h4 mb-4">余额查看</h1>
      <app-data-table
        :headers="headers"
        :items="balances"
        :total-items="balances.length"
        :loading="loading"
        clientSide
        show-search show-filter
        search-label="搜索APP名称"
      >
        <template v-slot:item.app_name="{ item }">
          <div class="d-flex align-center ga-2">
            <v-avatar v-if="item.icon" size="28" rounded>
              <v-img :src="item.icon" cover></v-img>
            </v-avatar>
            <v-icon v-else size="20" color="grey">mdi-run-fast</v-icon>
            {{ item.app_name }}
          </div>
        </template>
        <template v-slot:item.balance_mode="{ item }">
          <v-chip size="small" :color="item.balance_mode === 'mileage' ? 'blue' : item.balance_mode === 'count' ? 'green' : 'grey'">
            {{ item.balance_mode === 'mileage' ? '公里数' : item.balance_mode === 'count' ? '次数' : '未设置' }}
          </v-chip>
        </template>
        <template v-slot:item.actions="{ item }">
          <div class="d-flex ga-1">
            <v-btn variant="tonal" rounded size="small" color="primary" @click="goRecharge(item)">充值申请</v-btn>
            <v-btn variant="tonal" rounded size="small" color="secondary" @click="openFlow(item)">查看流水</v-btn>
          </div>
        </template>
      </app-data-table>
    </div>

    <v-dialog v-model="flowDialog.show" max-width="800">
      <v-card class="pa-4">
        <v-card-title class="d-flex align-center ga-2">
          <v-avatar v-if="flowDialog.icon" size="28" rounded>
            <v-img :src="flowDialog.icon" cover></v-img>
          </v-avatar>
          余额流水 - {{ flowDialog.appName }}
        </v-card-title>
        <v-card-text>
          <v-data-table-server
            :headers="flowHeaders"
            :items="flowItems"
            :items-length="flowTotal"
            :loading="flowLoading"
            v-model:page="flowPage"
            v-model:items-per-page="flowPageSize"
            @update:options="loadFlow"
            density="compact"
          >
            <template v-slot:item.app_name="{ item }">
              <div class="d-flex align-center ga-2">
                <v-avatar v-if="item.app_icon" size="22" rounded>
                  <v-img :src="item.app_icon" cover></v-img>
                </v-avatar>
                {{ item.app_name }}
              </div>
            </template>
            <template v-slot:item.type="{ item }">
              <v-chip size="x-small" :color="item.type === 'recharge' ? 'success' : item.type === 'deduction' ? 'error' : 'warning'">
                {{ item.type === 'recharge' ? '充值' : item.type === 'deduction' ? '扣费' : '撤销' }}
              </v-chip>
            </template>
            <template v-slot:item.amount="{ item }">
              <span :class="item.type === 'deduction' ? 'text-error' : 'text-success'">
                {{ item.type === 'deduction' ? '-' : '+' }}{{ item.amount }}
              </span>
            </template>
            <template v-slot:item.created_at="{ item }">
              {{ new Date(item.created_at).toLocaleString('zh-CN') }}
            </template>
          </v-data-table-server>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="tonal" @click="flowDialog.show = false">关闭</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<style scoped>
.table-wrapper { width: 90%; }
</style>

<script lang="ts" setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ajax } from '@/api/ajax'
import { cookie } from '@/api/cookie'
import { ApiUrl } from '@/config/api-url'
import type { UserBalance, BalanceTransaction } from '@/config/api-type'
import AppDataTable from '@/components/AppDataTable.vue'

const router = useRouter()

const balances = ref<UserBalance[]>([])
const loading = ref(false)

const headers = [
  { title: 'APP名称', key: 'app_name', searchable: true, filterable: true },
  { title: '余额类型', key: 'balance_mode' },
  { title: '当前余额', key: 'balance' },
  { title: '操作', key: 'actions', sortable: false }
]

const flowDialog = reactive({ show: false, appUid: '', appName: '', icon: '' })
const flowItems = ref<BalanceTransaction[]>([])
const flowTotal = ref(0)
const flowLoading = ref(false)
const flowPage = ref(1)
const flowPageSize = ref(20)

const flowHeaders = [
  { title: 'APP', key: 'app_name' },
  { title: '类型', key: 'type' },
  { title: '金额', key: 'amount' },
  { title: '余额', key: 'balance_after' },
  { title: '备注', key: 'note' },
  { title: '时间', key: 'created_at' }
]

async function loadBalances() {
  loading.value = true
  try {
    const res = await ajax<UserBalance[]>(ApiUrl.GET_USER_BALANCES, {
      headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
    })
    if (res.code === 200) balances.value = res.data
  } catch (e) { /* ignore */ }
  finally { loading.value = false }
}

function goRecharge(item: UserBalance) {
  router.push({ path: '/recharge', query: { app_uid: item.app_uid } })
}

function openFlow(item: UserBalance) {
  flowDialog.appUid = item.app_uid
  flowDialog.appName = item.app_name
  flowDialog.icon = item.icon || ''
  flowDialog.show = true
  flowPage.value = 1
  loadFlow()
}

async function loadFlow() {
  flowLoading.value = true
  try {
    const res = await ajax<any>(
      `${ApiUrl.GET_USER_BALANCE_TRANSACTIONS}?app_uid=${flowDialog.appUid}&page=${flowPage.value}&page_size=${flowPageSize.value}`,
      { headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` } }
    )
    if (res.code === 200 && res.data) {
      flowItems.value = res.data.items || []
      flowTotal.value = res.data.total || 0
    }
  } catch (e) { /* ignore */ }
  finally { flowLoading.value = false }
}

onMounted(() => { loadBalances() })
</script>
