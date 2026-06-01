<template>
  <v-container fluid class="pa-0 d-flex flex-column align-center">
    <div class="table-wrapper mt-4">
      <h1 class="text-h4 mb-4">通知中心</h1>
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
        <template v-slot:item.is_read="{ item }">
          <v-icon size="18" :color="item.is_read ? 'grey' : 'primary'">
            {{ item.is_read ? 'mdi-check-circle-outline' : 'mdi-circle' }}
          </v-icon>
        </template>
        <template v-slot:item.title="{ item }">
          <div class="d-flex align-center ga-2">
            <span :class="!item.is_read ? 'font-weight-bold' : ''">{{ item.title }}</span>
          </div>
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
import { useAppStore } from '@/stores/app'

const router = useRouter()
const appStore = useAppStore()

const notifications = ref<any[]>([])
const loading = ref(false)
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)

const headers = [
  { title: '状态', key: 'is_read', width: 60 },
  { title: '标题', key: 'title', searchable: true },
  { title: '内容', key: 'content', searchable: true },
  { title: '时间', key: 'created_at' },
  { title: '操作', key: 'actions', width: 80 }
]

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

async function handleClick(n: any) {
  if (!n.is_read) {
    try {
      await ajax(`/api/notifications/${n.id}/read`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
      })
      n.is_read = true
    } catch (e) { /* ignore */ }
  }
  const userInfo = appStore.userInfo
  const isAdmin = userInfo?.type !== 'default'
  if (n.type === 'new_registration') {
    if (isAdmin) {
      router.push({ path: '/admin/registers', query: n.reference_id ? { chat: n.reference_id } : {} })
    }
  }
  else if (n.type === 'registration_rejected') {
    router.push({ path: '/sign', query: n.reference_id ? { chat: n.reference_id } : {} })
  }
  else if (n.type === 'registration_approved') {
    router.push({ path: '/sign', query: n.reference_id ? { chat: n.reference_id } : {} })
  }
  else if (n.type === 'chat_message') {
    const targetPath = isAdmin ? '/admin/registers' : '/sign'
    router.push({ path: targetPath, query: n.reference_id ? { chat: n.reference_id } : {} })
  }
  else if (n.type === 'feedback_replied' || n.type === 'new_feedback' || n.type === 'feedback_status') {
    const targetPath = isAdmin ? '/admin/feedbacks' : '/feedback'
    router.push({ path: targetPath, query: n.reference_id ? { id: n.reference_id } : {} })
  }
  else if (n.type === 'recharge_processed') {
    router.push('/recharge')
  }
}

onMounted(() => {
  loadNotifications()
})
</script>
