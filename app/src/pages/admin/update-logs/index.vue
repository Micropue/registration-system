<template>
  <v-container fluid class="pa-0 d-flex flex-column align-center">
    <div class="table-wrapper mt-4">
      <h1 class="text-h4 mb-4">更新日志</h1>

      <app-data-table
        :headers="headers"
        :items="items"
        :total-items="totalItems"
        :loading="loading"
        :page="page"
        :items-per-page="itemsPerPage"
        show-search
        search-label="搜索提交信息..."
        @update:options="onOptionsChange"
      >
        <template v-slot:item.commit_hash="{ item }">
          <code class="text-caption">{{ item.commit_hash?.slice(0, 7) }}</code>
        </template>
        <template v-slot:item.commit_date="{ item }">
          {{ formatDate(item.commit_date) }}
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

interface UpdateLog {
  uid: string
  commit_hash: string
  commit_message: string
  commit_date: string
  created_at: string
}

const items = ref<UpdateLog[]>([])
const totalItems = ref(0)
const loading = ref(false)
const page = ref(1)
const itemsPerPage = ref(20)
const snackbar = reactive({ show: false, text: '', color: 'success' })

const headers = [
  { title: '提交哈希', key: 'commit_hash', sortable: false },
  { title: '提交信息', key: 'commit_message', searchable: true },
  { title: '提交时间', key: 'commit_date', sortable: false },
]

function showMsg(t: string, c = 'success') { snackbar.text = t; snackbar.color = c; snackbar.show = true }
function formatDate(iso: string) { return iso ? new Date(iso).toLocaleString('zh-CN') : '-' }

async function loadLogs() {
  loading.value = true
  try {
    const params = new URLSearchParams({ page: String(page.value), page_size: String(itemsPerPage.value) })
    const res = await ajax<{ items: UpdateLog[], total: number }>(`${ApiUrl.GET_UPDATE_LOGS}?${params}`, {
      headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
    })
    if (res.code === 200) {
      items.value = res.data.items
      totalItems.value = res.data.total
    }
  } catch (e) { /* ignore */ }
  finally { loading.value = false }
}

function onOptionsChange(opts: { page: number; itemsPerPage: number }) {
  page.value = opts.page
  itemsPerPage.value = opts.itemsPerPage
  loadLogs()
}

onMounted(loadLogs)
</script>
