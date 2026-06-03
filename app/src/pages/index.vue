<template>
  <v-container fluid class="pa-0 d-flex flex-column align-center">
    <div class="table-wrapper mt-4">
      <h1 class="text-h4 mb-4">待处理</h1>
      <app-data-table
        :headers="headers"
        :items="notifications"
        :total-items="total"
        :loading="loading"
        :client-side="false"
        show-search search-label="搜索通知"
        v-model:page="page"
        v-model:items-per-page="pageSize"
        @update:options="loadNotifications"
      >
        <template v-slot:item.type="{ item }">
          <v-icon size="20" :color="typeColor(item.type)">{{ typeIcon(item.type) }}</v-icon>
        </template>
        <template v-slot:item.created_at="{ item }">
          {{ formatDate(item.created_at) }}
        </template>
        <template v-slot:item.actions="{ item }">
          <v-btn variant="tonal" rounded size="small" color="primary" @click="handleClick(item)">查看</v-btn>
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
import { useRouter } from 'vue-router'
import { ajax } from '@/api/ajax'
import { cookie } from '@/api/cookie'
import AppDataTable from '@/components/AppDataTable.vue'

const router = useRouter()

const notifications = ref<any[]>([])
const loading = ref(false)
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)

const headers = [
  { title: '类型', key: 'type', width: 60 },
  { title: '标题', key: 'title', searchable: true },
  { title: '内容', key: 'content', searchable: true },
  { title: '时间', key: 'created_at' },
  { title: '操作', key: 'actions', width: 80 }
]

function typeIcon(type: string) {
  if (type === 'pending_registration') return 'mdi-file-document-outline'
  if (type === 'pending_feedback') return 'mdi-message-text-outline'
  if (type === 'pending_recharge') return 'mdi-cash-plus'
  return 'mdi-circle'
}

function typeColor(type: string) {
  if (type === 'pending_registration') return 'primary'
  if (type === 'pending_feedback') return 'warning'
  if (type === 'pending_recharge') return 'success'
  return 'grey'
}

function formatDate(iso: string) {
  if (!iso) return ''
  const d = new Date(iso)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  return d.toLocaleString('zh-CN')
}

async function loadNotifications() {
  loading.value = true
  try {
    const token = cookie.get('token') || ''
    const res = await ajax<any>(`/api/notifications?page=${page.value}&page_size=${pageSize.value}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (res.code === 200 && res.data) {
      notifications.value = res.data.items || []
      total.value = res.data.total || 0
    }
  } catch (e) { /* ignore */ }
  finally { loading.value = false }
}

function handleClick(n: any) {
  if (n.type === 'pending_registration') {
    router.push({ path: '/admin/registers', query: n.reference_id ? { chat: n.reference_id } : {} })
  }
  else if (n.type === 'pending_feedback') {
    router.push({ path: '/admin/feedbacks', query: n.reference_id ? { id: n.reference_id } : {} })
  }
  else if (n.type === 'pending_recharge') {
    router.push('/admin/recharges')
  }
}

onMounted(() => {
  loadNotifications()
})
</script>
