<template>
  <div class="feedback-page px-3 px-sm-6 py-4 py-sm-6" style="max-width: 800px; margin: 0 auto;">
    <div class="d-flex justify-space-between align-center mb-4">
      <h1 class="text-h5 text-sm-h4">工单反馈</h1>
      <v-btn color="primary" prepend-icon="mdi-plus" @click="openNewDialog">新建工单</v-btn>
    </div>

    <div v-if="loading && feedbacks.length === 0" class="d-flex justify-center py-8">
      <v-progress-circular indeterminate color="primary"></v-progress-circular>
    </div>

    <div v-else-if="feedbacks.length === 0" class="text-center py-8 text-medium-emphasis">
      <v-icon size="40" class="mb-2">mdi-inbox-outline</v-icon>
      <div>暂无工单</div>
    </div>

    <div v-else>
      <div v-for="item in feedbacks" :key="item.id"
        class="feedback-card pa-4 mb-3 rounded-lg" @click="openDetail(item.id)">
        <div class="d-flex align-center ga-3 mb-1">
          <span class="text-body-1 font-weight-bold">{{ item.title }}</span>
          <v-badge v-if="item.reply_count > 0 && !viewedIds.has(item.id)" :content="item.reply_count" color="error" inline></v-badge>
          <v-chip :color="getStatusColor(item.status)" size="x-small">{{ getStatusText(item.status) }}</v-chip>
        </div>
        <div class="text-caption text-medium-emphasis">{{ formatDate(item.created_at) }}</div>
        <div class="text-body-2 mt-2 text-medium-emphasis" style="white-space: pre-wrap; max-height: 60px; overflow: hidden;">{{ item.content }}</div>
      </div>

      <div class="text-center py-4" v-if="hasMore">
        <v-btn variant="tonal" :loading="loadingMore" @click="loadMore">加载更多</v-btn>
      </div>
    </div>

    <!-- 工单详情 Dialog -->
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
                {{ reply.is_admin ? '管理员' : '我' }}
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

    <!-- 新建工单 Dialog -->
    <v-dialog v-model="newDialog.show" max-width="500">
      <v-card class="pa-4">
        <v-card-title>新建工单</v-card-title>
        <v-card-text>
          <v-form ref="newFormRef" v-model="newFormValid">
            <v-text-field v-model="newDialog.title" label="标题" variant="outlined"
              :rules="[v => !!v || '标题必填']" hide-details="auto" class="mb-4"></v-text-field>
            <v-textarea v-model="newDialog.content" label="内容" variant="outlined"
              :rules="[v => !!v || '内容必填']" rows="4" hide-details="auto"></v-textarea>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="tonal" @click="newDialog.show = false">取消</v-btn>
          <v-btn color="primary" variant="flat" :loading="newLoading" :disabled="!newFormValid" @click="createFeedback">提交</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-snackbar v-model="snackbar.show" :color="snackbar.color" timeout="3000">
      {{ snackbar.text }}
    </v-snackbar>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ajax } from '@/api/ajax'
import { cookie } from '@/api/cookie'
import { ApiUrl } from '@/config/api-url'

interface FeedbackItem {
  id: string
  title: string
  content: string
  status: string
  created_at: string
  reply_count: number
}

interface FeedbackDetail {
  id: string
  username: string
  title: string
  content: string
  status: string
  created_at: string
  replies: { id: string; content: string; is_admin: boolean; created_at: string }[]
}

const feedbacks = ref<FeedbackItem[]>([])
const loading = ref(false)
const loadingMore = ref(false)
const page = ref(1)
const hasMore = ref(false)
const replyLoading = ref(false)
const newLoading = ref(false)
const newFormValid = ref(false)
const newFormRef = ref<any>(null)

const newDialog = reactive({ show: false, title: '', content: '' })
const detailDialog = reactive({ show: false, data: null as FeedbackDetail | null, replyContent: '' })
const viewedIds = reactive(new Set<string>())

const snackbar = reactive({ show: false, text: '', color: 'success' })
function showMsg(text: string, color: string = 'success') {
  snackbar.text = text; snackbar.color = color; snackbar.show = true
}

function getStatusColor(s: string) {
  return s === 'resolved' ? 'success' : s === 'rejected' ? 'error' : 'warning'
}
function getStatusText(s: string) {
  return s === 'resolved' ? '已处理' : s === 'rejected' ? '已驳回' : '待处理'
}
function formatDate(iso: string) {
  if (!iso) return '-'
  return new Date(iso).toLocaleString('zh-CN')
}

async function loadFeedbacks(reset = false) {
  if (reset) { page.value = 1; feedbacks.value = [] }
  loading.value = true
  try {
    const res = await ajax<any>(`${ApiUrl.GET_USER_FEEDBACKS}?page=${page.value}&page_size=20`, {
      headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
    })
    if (res.code === 200) {
      if (reset) feedbacks.value = res.data.items
      else feedbacks.value.push(...res.data.items)
      hasMore.value = feedbacks.value.length < res.data.total
    }
  } catch (err) { showMsg('加载失败', 'error') }
  finally { loading.value = false; loadingMore.value = false }
}

function loadMore() {
  page.value++
  loadingMore.value = true
  loadFeedbacks()
}

async function openDetail(id: string) {
  viewedIds.add(id)
  try {
    const res = await ajax<FeedbackDetail>(`${ApiUrl.GET_FEEDBACK_DETAIL}/${id}`, {
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
      method: 'POST',
      body: { content: detailDialog.replyContent },
      isFormData: true,
      headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
    })
    if (res.code === 200) {
      showMsg('回复成功')
      detailDialog.replyContent = ''
      openDetail(detailDialog.data.id)
    } else showMsg(res.msg, 'error')
  } catch (err) { showMsg('回复失败', 'error') }
  finally { replyLoading.value = false }
}

function openNewDialog() {
  newDialog.title = ''; newDialog.content = ''; newDialog.show = true
  newFormValid.value = false; newFormRef.value?.resetValidation()
}

async function createFeedback() {
  const { valid } = await newFormRef.value.validate()
  if (!valid) return
  newLoading.value = true
  try {
    const res = await ajax(ApiUrl.CREATE_FEEDBACK, {
      method: 'POST',
      body: { title: newDialog.title, content: newDialog.content },
      isFormData: true,
      headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
    })
    if (res.code === 200) {
      newDialog.show = false
      showMsg('工单已提交')
      loadFeedbacks(true)
    } else showMsg(res.msg, 'error')
  } catch (err) { showMsg('提交失败', 'error') }
  finally { newLoading.value = false }
}

onMounted(() => loadFeedbacks(true))
</script>

<style scoped lang="scss">
.feedback-page { max-height: 100%; overflow-y: auto; }
.feedback-page::-webkit-scrollbar { display: none; }
.feedback-card {
  background: #fff;
  cursor: pointer;
  transition: box-shadow 0.2s;
  &:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
}
</style>
