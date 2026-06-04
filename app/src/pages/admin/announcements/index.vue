<template>
  <v-container fluid class="pa-4">
    <div class="mb-4">
      <div class="d-flex align-center">
        <v-icon color="primary" size="28" class="mr-2">mdi-bullhorn-outline</v-icon>
        <h1 class="text-h4 mt-0 mb-0">公告</h1>
      </div>
    </div>

    <div class="d-flex justify-end mb-4">
      <v-btn color="primary" elevation="2" prepend-icon="mdi-plus" @click="openCreateDialog">新建公告</v-btn>
    </div>

    <v-timeline v-if="announcements.length > 0" side="end" density="compact" line-thickness="2" line-color="primary">
      <v-timeline-item
        v-for="ann in announcements"
        :key="ann.uid"
        dot-color="primary"
        size="x-small"
      >
        <div class="mb-1 d-flex align-center flex-wrap ga-2">
          <span class="text-subtitle-1 font-weight-bold">{{ ann.title }}</span>
          <v-chip v-if="!ann.is_published" size="x-small" color="grey" variant="tonal">草稿</v-chip>
          <v-chip v-else size="x-small" color="success" variant="tonal">已发布</v-chip>
        </div>
        <v-card variant="outlined" rounded="lg" class="mb-2">
          <v-card-text class="text-body-2" style="white-space: pre-wrap; line-height: 1.7;">
            {{ ann.content }}
          </v-card-text>
          <v-divider></v-divider>
          <v-card-actions class="pa-2">
            <span class="text-caption text-medium-emphasis">{{ ann.publisher_name }} · {{ formatDate(ann.create_time) }}</span>
            <v-spacer></v-spacer>
            <v-btn v-if="!ann.is_published" variant="tonal" rounded size="small" color="success" @click="doPublish(ann.uid)">发布</v-btn>
            <v-btn v-else variant="tonal" rounded size="small" color="grey" @click="doUnpublish(ann.uid)">取消发布</v-btn>
            <v-btn variant="tonal" rounded size="small" color="primary" class="ml-1" @click="openEditDialog(ann)">编辑</v-btn>
            <v-btn variant="tonal" rounded size="small" color="error" class="ml-1" @click="confirmDelete(ann)">删除</v-btn>
          </v-card-actions>
        </v-card>
      </v-timeline-item>
    </v-timeline>
    <div v-else-if="!loading" class="text-center py-8 text-grey text-body-1">暂无公告</div>

    <v-progress-linear v-if="loading" indeterminate color="primary"></v-progress-linear>

    <!-- 创建/编辑 Dialog -->
    <v-dialog v-model="editDialog.show" max-width="560">
      <v-card rounded="lg">
        <v-card-title class="d-flex align-center">
          <v-icon color="primary" class="mr-2">{{ editDialog.isEdit ? 'mdi-pencil-box' : 'mdi-plus-box' }}</v-icon>
          {{ editDialog.isEdit ? '编辑公告' : '新建公告' }}
        </v-card-title>
        <v-card-text>
          <v-text-field
            v-model="editDialog.title"
            label="标题"
            variant="outlined"
            density="comfortable"
            hide-details
            class="mb-3"
          ></v-text-field>
          <v-textarea
            v-model="editDialog.content"
            label="内容"
            variant="outlined"
            density="comfortable"
            rows="6"
            hide-details
          ></v-textarea>
        </v-card-text>
        <v-card-actions class="pa-4 pt-0">
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="editDialog.show = false">取消</v-btn>
          <v-btn color="primary" variant="flat" :loading="saving" @click="doSave">保存</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 删除确认 Dialog -->
    <v-dialog v-model="deleteDialog.show" max-width="400">
      <v-card rounded="lg">
        <v-card-title class="d-flex align-center text-error pa-4 pb-2">
          <v-icon color="error" class="mr-2">mdi-alert-circle</v-icon>
          确认删除公告
        </v-card-title>
        <v-card-text class="pa-4 pt-0">
          确定要删除公告 <strong>{{ deleteDialog.item?.title }}</strong> 吗？此操作不可撤销。
        </v-card-text>
        <v-card-actions class="pa-4 pt-0">
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="deleteDialog.show = false">取消</v-btn>
          <v-btn color="error" variant="flat" @click="doDelete">确认删除</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-snackbar v-model="snackbar.show" :color="snackbar.color" timeout="3000">
      {{ snackbar.text }}
    </v-snackbar>
  </v-container>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ajax } from '@/api/ajax'
import { cookie } from '@/api/cookie'

const announcements = ref<any[]>([])
const loading = ref(false)
const saving = ref(false)
const snackbar = reactive({ show: false, text: '', color: 'success' })
const deleteDialog = reactive({ show: false, item: null as any })
const editDialog = reactive({ show: false, isEdit: false, uid: '', title: '', content: '' })

const authHeaders = () => ({ 'Authorization': `Bearer ${cookie.get('token') || ''}` })

function showMsg(text: string, color: string = 'success') {
  snackbar.text = text
  snackbar.color = color
  snackbar.show = true
}

function formatDate(iso: string) {
  if (!iso) return ''
  return new Date(iso).toLocaleString('zh-CN')
}

async function loadAnnouncements() {
  loading.value = true
  try {
    const res = await ajax<any[]>('/api/admin/announcements', { headers: authHeaders() })
    if (res.code === 200) announcements.value = res.data || []
  } catch { /* ignore */ }
  finally { loading.value = false }
}

function openCreateDialog() {
  editDialog.isEdit = false
  editDialog.uid = ''
  editDialog.title = ''
  editDialog.content = ''
  editDialog.show = true
}

function openEditDialog(ann: any) {
  editDialog.isEdit = true
  editDialog.uid = ann.uid
  editDialog.title = ann.title
  editDialog.content = ann.content
  editDialog.show = true
}

async function doSave() {
  if (!editDialog.title.trim()) {
    showMsg('请输入标题', 'error')
    return
  }
  saving.value = true
  try {
    const body = { title: editDialog.title.trim(), content: editDialog.content }
    let res
    if (editDialog.isEdit) {
      res = await ajax(`/api/admin/announcements/${editDialog.uid}`, {
        method: 'PUT', body, headers: authHeaders()
      })
    } else {
      res = await ajax('/api/admin/announcements', {
        method: 'POST', body, headers: authHeaders()
      })
    }
    if (res.code === 200) {
      editDialog.show = false
      showMsg(editDialog.isEdit ? '已更新' : '已创建')
      loadAnnouncements()
    } else {
      showMsg(res.msg || '操作失败', 'error')
    }
  } catch {
    showMsg('请求失败', 'error')
  } finally {
    saving.value = false
  }
}

async function doPublish(uid: string) {
  try {
    const res = await ajax(`/api/admin/announcements/${uid}/publish`, {
      method: 'POST', headers: authHeaders()
    })
    if (res.code === 200) {
      showMsg('已发布')
      loadAnnouncements()
    } else {
      showMsg(res.msg || '操作失败', 'error')
    }
  } catch { showMsg('请求失败', 'error') }
}

async function doUnpublish(uid: string) {
  try {
    const res = await ajax(`/api/admin/announcements/${uid}/unpublish`, {
      method: 'POST', headers: authHeaders()
    })
    if (res.code === 200) {
      showMsg('已取消发布')
      loadAnnouncements()
    } else {
      showMsg(res.msg || '操作失败', 'error')
    }
  } catch { showMsg('请求失败', 'error') }
}

function confirmDelete(ann: any) {
  deleteDialog.show = true
  deleteDialog.item = ann
}

async function doDelete() {
  if (!deleteDialog.item) return
  try {
    const res = await ajax(`/api/admin/announcements/${deleteDialog.item.uid}`, {
      method: 'DELETE', headers: authHeaders()
    })
    if (res.code === 200) {
      deleteDialog.show = false
      showMsg('已删除')
      loadAnnouncements()
    } else {
      showMsg(res.msg || '操作失败', 'error')
    }
  } catch { showMsg('请求失败', 'error') }
}

onMounted(() => {
  loadAnnouncements()
})
</script>
