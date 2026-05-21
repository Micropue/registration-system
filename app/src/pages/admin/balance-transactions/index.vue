<template>
  <v-container fluid class="pa-0 d-flex flex-column align-center">
    <div class="table-wrapper mt-4">
      <h1 class="text-h4 mb-4">余额流水</h1>

      <app-data-table
        :headers="headers"
        :items="transactions"
        :total-items="totalTransactions"
        :loading="loading"
        v-model:page="currentPage"
        v-model:items-per-page="itemsPerPage"
        show-search show-filter
        search-label="搜索备注/关联ID"
        @update:options="loadTransactions"
        @reset="loadTransactions"
      >
        <template v-slot:item.type="{ item }">
          <v-chip size="small" :color="item.type === 'recharge' ? 'success' : item.type === 'deduction' ? 'error' : 'warning'">
            {{ item.type === 'recharge' ? '充值' : item.type === 'deduction' ? '减少' : '撤销' }}
          </v-chip>
        </template>
        <template v-slot:item.amount="{ item }">
          <span :class="item.type === 'recharge' || item.type === 'reversal' ? 'text-success' : 'text-error'" class="font-weight-bold">
            {{ item.type === 'reversal' ? '+' : item.type === 'recharge' ? '+' : '-' }}{{ item.amount }}
          </span>
        </template>
        <template v-slot:item.created_at="{ item }">
          {{ formatDate(item.created_at) }}
        </template>
      </app-data-table>
    </div>

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
import { ajax } from '@/api/ajax'
import { cookie } from '@/api/cookie'
import { ApiUrl } from '@/config/api-url'
import AppDataTable from '@/components/AppDataTable.vue'

interface TransactionItem {
  id: string; app_uid: string; app_name: string; type: string; amount: number;
  balance_after: number; related_uid: string; related_type: string;
  note: string; created_at: string
}

const transactions = ref<TransactionItem[]>([])
const loading = ref(false)
const totalTransactions = ref(0)
const currentPage = ref(1)
const itemsPerPage = ref(20)
const snackbar = reactive({ show: false, text: '', color: 'success' })

const headers = [
  { title: 'APP', key: 'app_name', filterable: true },
  { title: '类型', key: 'type', filterable: true },
  { title: '变动量', key: 'amount', sortable: true },
  { title: '变动后余额', key: 'balance_after', sortable: true },
  { title: '关联', key: 'related_uid', searchable: true },
  { title: '备注', key: 'note', searchable: true },
  { title: '时间', key: 'created_at', sortable: true },
]

function showMsg(t: string, c = 'success') { snackbar.text = t; snackbar.color = c; snackbar.show = true }
function formatDate(iso: string) { return iso ? new Date(iso).toLocaleString('zh-CN') : '-' }

async function loadTransactions(options: any = { page: 1, itemsPerPage: 20 }) {
  loading.value = true
  const page = options.page || currentPage.value
  const pageSize = options.itemsPerPage || itemsPerPage.value
  currentPage.value = page
  itemsPerPage.value = pageSize
  try {
    const res = await ajax<any>(`${ApiUrl.GET_BALANCE_TRANSACTIONS}?page=${page}&page_size=${pageSize}`, {
      headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
    })
    if (res.code === 200) {
      transactions.value = res.data.items
      totalTransactions.value = res.data.total
    }
  } catch (e) { /* ignore */ }
  finally { loading.value = false }
}

onMounted(() => { loadTransactions() })
</script>
