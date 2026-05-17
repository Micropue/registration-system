<template>
  <v-container fluid class="pa-0 d-flex flex-column align-center">
    <div class="table-wrapper mt-4">
      <div class="d-flex justify-space-between align-center mb-4">
        <h1 class="text-h4">工单处理</h1>
      </div>

      <app-data-table
        :headers="headers" :items="feedbacks" :total-items="totalFeedbacks" :loading="loading"
        v-model:page="currentPage" v-model:items-per-page="itemsPerPage"
        show-search show-filter search-label="搜索标题/用户名"
        @update:options="loadFeedbacks" @reset="loadFeedbacks"
        :row-props="({ item }: any) => item.status !== 'pending' ? { class: 'row-processed' } : {}"
      >
        <template v-slot:item.status="{ item }">
          <v-chip :color="getStatusColor(item.status)" size="small">{{ getStatusText(item.status) }}</v-chip>
        </template>
        <template v-slot:item.created_at="{ item }">
          {{ formatDate(item.created_at) }}
        </template>
        <template v-slot:item.actions="{ item }">
          <div class="d-flex ga-1">
            <v-btn variant="tonal" rounded color="primary" @click="openDetail(item)">查看/回复</v-btn>
            <v-btn variant="tonal" rounded color="success" @click="updateStatus(item, 'resolved')">已处理</v-btn>
            <v-btn variant="tonal" rounded color="error" @click="updateStatus(item, 'rejected')">驳回</v-btn>
            <v-btn variant="tonal" rounded color="warning" @click="updateStatus(item, 'pending')">待处理</v-btn>
            <v-btn variant="tonal" rounded color="error" @click="confirmDelete(item)">删除</v-btn>
          </div>
        </template>
      </app-data-table>
    </div>

    <!-- 工单详情 + 回复 Dialog -->
    <v-dialog v-model="detailDialog.show" max-width="650" scrollable>
      <v-card v-if="detailDialog.data" class="pa-4">
        <v-card-title class="d-flex align-center">
          <span class="text-h6">{{ detailDialog.data.title }}</span>
          <v-spacer></v-spacer>
          <v-chip :color="getStatusColor(detailDialog.data.status)" size="small">{{ getStatusText(detailDialog.data.status) }}</v-chip>
        </v-card-title>
        <v-card-subtitle>{{ detailDialog.data.username }} · {{ formatDate(detailDialog.data.created_at) }}</v-card-subtitle>
        <v-divider class="my-2"></v-divider>
        <v-card-text>
          <div class="pa-3 rounded bg-grey-lighten-4 mb-4" style="white-space: pre-wrap;">{{ detailDialog.data.content }}</div>

          <div class="text-subtitle-2 mb-2">回复 ({{ detailDialog.data.replies?.length || 0 }})</div>
          <div v-for="reply in detailDialog.data.replies" :key="reply.id"
            class="pa-3 mb-2 rounded" :class="reply.is_admin ? 'bg-blue-lighten-5' : 'bg-grey-lighten-4'">
            <div class="d-flex align-center ga-2 mb-1">
              <v-chip size="x-small" :color="reply.is_admin ? 'primary' : 'grey'">
                {{ reply.is_admin ? '管理员' : '用户' }}
              </v-chip>
              <span class="text-caption text-medium-emphasis">{{ formatDate(reply.created_at) }}</span>
            </div>
            <div style="white-space: pre-wrap;">{{ reply.content }}</div>
          </div>

          <v-textarea v-model="detailDialog.replyContent" label="输入回复..." variant="outlined"
            rows="2" auto-grow hide-details class="mt-2" density="compact"></v-textarea>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="tonal" @click="detailDialog.show = false">关闭</v-btn>
          <v-btn color="primary" variant="flat" :loading="replyLoading" :disabled="!detailDialog.replyContent" @click="submitReply">
            发送回复
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 删除确认 -->
    <v-dialog v-model="deleteDialog.show" max-width="400">
      <v-card>
        <v-card-title class="text-h5 pa-4">确认删除</v-card-title>
        <v-card-text class="pa-4 pt-0">确定要删除工单「{{ deleteDialog.title }}」吗？</v-card-text>
        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="deleteDialog.show = false">取消</v-btn>
          <v-btn color="error" variant="flat" :loading="loading" @click="handleDelete">确认删除</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-snackbar v-model="snackbar.show" :color="snackbar.color" timeout="3000">
      {{ snackbar.text }}
    </v-snackbar>
  </v-container>
</template>

<style scoped>
.table-wrapper { width: 90%; max-width: 1100px; }
:deep(.row-processed) { opacity: 0.5; }
</style>

<script lang="ts" setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import AppDataTable from '@/components/AppDataTable.vue'
import { ApiUrl } from '@/config/api-url'
import { ajax } from '@/api/ajax'
import { cookie } from '@/api/cookie'

const route = useRoute()

interface FeedbackItem {
  id: string; username: string; title: string; content: string; status: string; created_at: string
}
interface FeedbackDetail {
  id: string; username: string; title: string; content: string; status: string; created_at: string
  replies: { id: string; content: string; is_admin: boolean; created_at: string }[]
}

const feedbacks = ref<FeedbackItem[]>([])
const loading = ref(false)
const replyLoading = ref(false)
const totalFeedbacks = ref(0)
const itemsPerPage = ref(20)
const currentPage = ref(1)

const detailDialog = reactive({ show: false, data: null as FeedbackDetail | null, replyContent: '' })
const deleteDialog = reactive({ show: false, id: '', title: '' })
const snackbar = reactive({ show: false, text: '', color: 'success' })
function showMsg(text: string, color: string = 'success') {
  snackbar.text = text; snackbar.color = color; snackbar.show = true
}

const headers = [
  { title: '标题', key: 'title', searchable: true },
  { title: '用户', key: 'username', searchable: true, filterable: true },
  { title: '状态', key: 'status', sortable: true, filterable: true },
  { title: '操作', key: 'actions', sortable: false },
  { title: '创建时间', key: 'created_at', sortable: true },
]

function getStatusColor(s: string) { return s === 'resolved' ? 'success' : s === 'rejected' ? 'error' : 'warning' }
function getStatusText(s: string) { return s === 'resolved' ? '已处理' : s === 'rejected' ? '已驳回' : '待处理' }
function formatDate(iso: string) { return iso ? new Date(iso).toLocaleString('zh-CN') : '-' }

async function loadFeedbacks(options: any = { page: 1, itemsPerPage: 20 }) {
  const page = options.page || currentPage.value
  const pageSize = options.itemsPerPage || itemsPerPage.value
  loading.value = true; currentPage.value = page; itemsPerPage.value = pageSize
  const username = route.query.username as string || ''
  let url = `${ApiUrl.ADMIN_GET_FEEDBACKS}?page=${page}&page_size=${pageSize}`
  if (username) url += `&username=${encodeURIComponent(username)}`
  try {
    const res = await ajax(url, {
      headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
    })
    if (res.code === 200) {
      feedbacks.value = res.data.items
      totalFeedbacks.value = res.data.total
    }
  } catch (err) { showMsg('加载失败', 'error') } finally { loading.value = false }
}

async function openDetail(item: FeedbackItem) {
  try {
    const res = await ajax<FeedbackDetail>(`${ApiUrl.GET_FEEDBACK_DETAIL}/${item.id}`, {
      headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
    })
    if (res.code === 200) {
      detailDialog.data = res.data
      detailDialog.replyContent = ''
      detailDialog.show = true
    }
  } catch (err) { showMsg('加载失败', 'error') }
}

async function submitReply() {
  if (!detailDialog.data || !detailDialog.replyContent) return
  replyLoading.value = true
  try {
    const res = await ajax(`${ApiUrl.REPLY_FEEDBACK}/${detailDialog.data.id}/reply`, {
      method: 'POST', body: { content: detailDialog.replyContent }, isFormData: true,
      headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
    })
    if (res.code === 200) {
      showMsg('回复成功'); detailDialog.replyContent = ''
      openDetail(detailDialog.data as any)
    } else showMsg(res.msg, 'error')
  } catch (err) { showMsg('回复失败', 'error') } finally { replyLoading.value = false }
}

async function updateStatus(item: FeedbackItem, status: string) {
  loading.value = true
  try {
    const res = await ajax(`${ApiUrl.ADMIN_UPDATE_FEEDBACK_STATUS}/${item.id}/status`, {
      method: 'POST', body: { status }, isFormData: true,
      headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
    })
    if (res.code === 200) { showMsg('状态已更新'); loadFeedbacks() }
    else showMsg(res.msg, 'error')
  } catch (err) { showMsg('请求失败', 'error') } finally { loading.value = false }
}

function confirmDelete(item: FeedbackItem) {
  deleteDialog.id = item.id
  deleteDialog.title = item.title
  deleteDialog.show = true
}

async function handleDelete() {
  loading.value = true
  try {
    const res = await ajax(`${ApiUrl.ADMIN_GET_FEEDBACKS}/${deleteDialog.id}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
    })
    if (res.code === 200) { deleteDialog.show = false; showMsg('已删除'); loadFeedbacks() }
    else showMsg(res.msg, 'error')
  } catch (err) { showMsg('请求失败', 'error') } finally { loading.value = false }
}
</script>
