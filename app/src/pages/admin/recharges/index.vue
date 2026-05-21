<template>
  <v-container fluid class="pa-0 d-flex flex-column align-center">
    <div class="table-wrapper mt-4">
      <h1 class="text-h4 mb-4">充值审批</h1>

      <app-data-table
        :headers="headers"
        :items="recharges"
        :total-items="recharges.length"
        :loading="loading"
        client-side
        show-search show-filter
        search-label="搜索申请人/APP"
      >
        <template v-slot:item.app_balance_mode="{ item }">
          {{ item.app_balance_mode === 'mileage' ? '公里数' : item.app_balance_mode === 'count' ? '次数' : '-' }}
        </template>
        <template v-slot:item.status="{ item }">
          <v-chip size="small" :color="statusColor(item.status)">{{ statusText(item.status) }}</v-chip>
        </template>
        <template v-slot:item.created_at="{ item }">
          {{ formatDate(item.created_at) }}
        </template>
        <template v-slot:item.actions="{ item }">
          <div class="d-flex ga-1" v-if="item.status === 'pending'">
            <v-btn variant="tonal" rounded size="small" color="success" @click="process(item.id, 'approved')">通过</v-btn>
            <v-btn variant="tonal" rounded size="small" color="error" @click="openReject(item)">驳回</v-btn>
          </div>
        </template>
      </app-data-table>
    </div>

    <v-dialog v-model="rejectDialog.show" max-width="400">
      <v-card class="pa-4">
        <v-card-title>驳回充值申请</v-card-title>
        <v-card-text>
          <v-textarea v-model="rejectDialog.reason" label="驳回原因" variant="outlined" rows="2" hide-details></v-textarea>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="tonal" @click="rejectDialog.show = false">取消</v-btn>
          <v-btn color="error" variant="flat" @click="doReject">确认驳回</v-btn>
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
import { ajax } from '@/api/ajax'
import { cookie } from '@/api/cookie'
import { ApiUrl } from '@/config/api-url'
import type { BalanceRecharge } from '@/config/api-type'
import AppDataTable from '@/components/AppDataTable.vue'

const recharges = ref<BalanceRecharge[]>([])
const loading = ref(false)
const rejectDialog = reactive({ show: false, uid: '', reason: '' })
const snackbar = reactive({ show: false, text: '', color: 'success' })

const headers = [
  { title: '申请人', key: 'username', searchable: true },
  { title: 'APP', key: 'app_name', searchable: true, filterable: true },
  { title: '充值量', key: 'amount', sortable: true },
  { title: '模式', key: 'app_balance_mode', filterable: true },
  { title: '原因', key: 'reason', searchable: true },
  { title: '状态', key: 'status', sortable: true, filterable: true },
  { title: '时间', key: 'created_at', sortable: true },
  { title: '操作', key: 'actions', sortable: false },
]

function showMsg(t: string, c = 'success') { snackbar.text = t; snackbar.color = c; snackbar.show = true }
function formatDate(iso: string) { return iso ? new Date(iso).toLocaleString('zh-CN') : '-' }
function statusColor(s: string) { return s === 'approved' ? 'success' : s === 'rejected' ? 'error' : 'warning' }
function statusText(s: string) { return s === 'approved' ? '已通过' : s === 'rejected' ? '已驳回' : '待处理' }

async function loadRecharges() {
  loading.value = true
  try {
    const res = await ajax<BalanceRecharge[]>(ApiUrl.GET_ALL_RECHARGES, {
      headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
    })
    if (res.code === 200) recharges.value = res.data
  } catch (e) { /* ignore */ }
  finally { loading.value = false }
}

async function process(uid: string, status: string) {
  try {
    const res = await ajax(`${ApiUrl.PROCESS_RECHARGE}/${uid}/process`, {
      method: 'POST',
      body: { status },
      headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
    })
    if (res.code === 200) { showMsg('已处理'); loadRecharges() }
    else showMsg(res.msg, 'error')
  } catch (e) { showMsg('操作失败', 'error') }
}

function openReject(item: BalanceRecharge) {
  rejectDialog.uid = item.id
  rejectDialog.reason = ''
  rejectDialog.show = true
}

async function doReject() {
  try {
    const res = await ajax(`${ApiUrl.PROCESS_RECHARGE}/${rejectDialog.uid}/process`, {
      method: 'POST',
      body: { status: 'rejected', reject_reason: rejectDialog.reason },
      headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
    })
    if (res.code === 200) { rejectDialog.show = false; showMsg('已驳回'); loadRecharges() }
    else showMsg(res.msg, 'error')
  } catch (e) { showMsg('操作失败', 'error') }
}

onMounted(loadRecharges)
</script>
