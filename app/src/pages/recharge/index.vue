<template>
  <div class="recharge-page px-3 px-sm-6 py-4 py-sm-6 d-flex flex-column align-center">
    <div class="table-wrapper" style="width: 90%;">
      <div class="d-flex justify-space-between align-center mb-4">
        <h1 class="text-h5 text-sm-h4">充值申请</h1>
        <v-btn color="primary" prepend-icon="mdi-plus" @click="openDialog">新建申请</v-btn>
      </div>

      <app-data-table
        :headers="headers"
        :items="recharges"
        :total-items="recharges.length"
        :loading="loading"
        client-side
      >
        <template v-slot:item.app_balance_mode="{ item }">
          {{ item.app_balance_mode === 'mileage' ? '公里数' : item.app_balance_mode === 'count' ? '次数' : '-' }}
        </template>
        <template v-slot:item.status="{ item }">
          <v-chip size="small" :color="item.status === 'approved' ? 'success' : item.status === 'rejected' ? 'error' : 'warning'">
            {{ item.status === 'approved' ? '已通过' : item.status === 'rejected' ? '已驳回' : '待审核' }}
          </v-chip>
        </template>
        <template v-slot:item.reject_reason="{ item }">
          <span v-if="item.reject_reason" class="text-error">{{ item.reject_reason }}</span>
          <span v-else class="text-grey">-</span>
        </template>
        <template v-slot:item.created_at="{ item }">
          {{ formatDate(item.created_at) }}
        </template>
      </app-data-table>
    </div>

    <v-dialog v-model="dialog.show" max-width="450" persistent>
      <v-card class="pa-4">
        <v-card-title>新建充值申请</v-card-title>
        <v-card-text>
          <v-autocomplete v-model="dialog.appUid" :items="runningApps" item-title="name" item-value="uid"
            label="选择跑步APP" variant="outlined" density="comfortable" class="mb-3"
            :item-props="(item: any) => item.icon ? { prependAvatar: item.icon } : {}" />
          <div v-if="dialog.appUid" class="mb-3 text-body-2 text-medium-emphasis">
            余额模式：{{ selectedAppMode || '未设置' }}
          </div>
          <v-text-field v-model.number="dialog.amount" label="充值数量" type="number" variant="outlined"
            density="comfortable" class="mb-3" :rules="[v => !!v || '必填', v => v > 0 || '必须大于0']" />
          <v-textarea v-model="dialog.reason" label="申请原因" variant="outlined" rows="2" density="comfortable" />
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="tonal" @click="dialog.show = false">取消</v-btn>
          <v-btn color="primary" variant="flat" :loading="submitting" :disabled="!dialog.appUid || !dialog.amount" @click="submit">
            提交申请
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-snackbar v-model="snackbar.show" :color="snackbar.color" timeout="3000">
      {{ snackbar.text }}
    </v-snackbar>
  </div>
</template>

<style scoped>
.table-wrapper { overflow-x: auto; }
.recharge-page { max-height: 100%; overflow-y: auto; }
.recharge-page::-webkit-scrollbar { display: none; }
</style>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ajax } from '@/api/ajax'
import { cookie } from '@/api/cookie'
import { ApiUrl } from '@/config/api-url'
import type { BalanceRecharge, RunningApp } from '@/config/api-type'
import AppDataTable from '@/components/AppDataTable.vue'

const recharges = ref<BalanceRecharge[]>([])
const runningApps = ref<RunningApp[]>([])
const loading = ref(false)
const submitting = ref(false)
const dialog = reactive({ show: false, appUid: '', amount: 0, reason: '' })
const snackbar = reactive({ show: false, text: '', color: 'success' })

const selectedAppMode = computed(() => {
  const a = runningApps.value.find(a => a.uid === dialog.appUid)
  if (a?.balance_mode === 'mileage') return '公里数'
  if (a?.balance_mode === 'count') return '次数'
  return ''
})

const headers = [
  { title: 'APP', key: 'app_name' },
  { title: '充值量', key: 'amount' },
  { title: '模式', key: 'app_balance_mode' },
  { title: '原因', key: 'reason' },
  { title: '状态', key: 'status' },
  { title: '驳回原因', key: 'reject_reason' },
  { title: '时间', key: 'created_at' },
]

function showMsg(t: string, c = 'success') { snackbar.text = t; snackbar.color = c; snackbar.show = true }
function formatDate(iso: string) { return iso ? new Date(iso).toLocaleString('zh-CN') : '-' }

async function loadApps() {
  try {
    const res = await ajax<RunningApp[]>(ApiUrl.GET_PUBLIC_RUNNING_APPS)
    if (res.code === 200) runningApps.value = res.data
  } catch (e) { /* ignore */ }
}

async function loadRecharges() {
  loading.value = true
  try {
    const res = await ajax<BalanceRecharge[]>(ApiUrl.GET_MY_RECHARGES, {
      headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
    })
    if (res.code === 200) recharges.value = res.data
  } catch (e) { /* ignore */ }
  finally { loading.value = false }
}

function openDialog() {
  dialog.appUid = ''
  dialog.amount = 0
  dialog.reason = ''
  dialog.show = true
}

async function submit() {
  submitting.value = true
  try {
    const res = await ajax(ApiUrl.CREATE_RECHARGE, {
      method: 'POST',
      body: { app_uid: dialog.appUid, amount: dialog.amount, reason: dialog.reason },
      headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
    })
    if (res.code === 200) { showMsg('充值申请已提交'); dialog.show = false; loadRecharges() }
    else showMsg(res.msg, 'error')
  } catch (e) { showMsg('提交失败', 'error') }
  finally { submitting.value = false }
}

onMounted(() => { loadApps(); loadRecharges() })
</script>
