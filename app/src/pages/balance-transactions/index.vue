<template>
  <v-container fluid class="pa-0 d-flex flex-column align-center">
    <div class="table-wrapper mt-4">
      <h1 class="text-h4 mb-4">余额流水</h1>

      <app-data-table
        :headers="headers"
        :items="items"
        :total-items="total"
        :loading="loading"
        :client-side="false"
        show-search show-filter
        search-label="搜索备注"
        v-model:page="page"
        v-model:items-per-page="pageSize"
        @update:options="loadData"
      >
        <template v-slot:item.app_name="{ item }">
          <div class="d-flex align-center ga-2">
            <v-avatar v-if="item.app_icon" size="22" rounded>
              <v-img :src="item.app_icon" cover></v-img>
            </v-avatar>
            <v-icon v-else size="18" color="grey">mdi-apps</v-icon>
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
      </app-data-table>
    </div>
  </v-container>
</template>

<style scoped>
.table-wrapper { width: 90%; }
</style>

<script lang="ts" setup>
import { ref, onMounted } from 'vue'
import { ajax } from '@/api/ajax'
import { cookie } from '@/api/cookie'
import { ApiUrl } from '@/config/api-url'
import AppDataTable from '@/components/AppDataTable.vue'

const items = ref<any[]>([])
const total = ref(0)
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)

const headers = [
  { title: 'APP', key: 'app_name' },
  { title: '类型', key: 'type', filterable: true },
  { title: '金额变化', key: 'amount' },
  { title: '余额', key: 'balance_after' },
  { title: '备注', key: 'note', searchable: true },
  { title: '时间', key: 'created_at' }
]

async function loadData(options: any = {}) {
  if (options.page) page.value = options.page
  if (options.itemsPerPage) pageSize.value = options.itemsPerPage
  loading.value = true
  try {
    const res = await ajax<any>(
      `${ApiUrl.GET_USER_BALANCE_TRANSACTIONS}?page=${page.value}&page_size=${pageSize.value}`,
      { headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` } }
    )
    if (res.code === 200 && res.data) {
      items.value = res.data.items || []
      total.value = res.data.total || 0
    }
  } catch (e) { /* ignore */ }
  finally { loading.value = false }
}

onMounted(() => { loadData() })
</script>
