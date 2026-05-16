<template>
  <div class="sign-page px-3 px-sm-6 py-4 py-sm-6" style="max-width: 800px; margin: 0 auto;">
    <!-- 顶部操作区 -->
    <div class="d-flex justify-space-between align-center mb-4">
      <h1 class="text-h5 text-sm-h4">数据登记</h1>
      <v-btn v-if="!showForm" color="primary" size="default" prepend-icon="mdi-plus" @click="openNewDialog" class="text-none">
        新建登记
      </v-btn>
    </div>

    <!-- 正在登记表单 -->
    <v-expand-transition>
      <div v-if="showForm" class="form-section mb-4 pa-3 pa-sm-6 rounded-lg">
        <div class="d-flex align-center pb-2">
          <v-icon color="primary" size="24" class="me-2">mdi-run-fast</v-icon>
          <span class="text-h6 font-weight-bold">新建登记</span>
        </div>
        <div class="text-body-2 text-medium-emphasis pb-3">
          已选择：
          <v-chip size="x-small" color="primary" label>{{ selectedApp }}</v-chip>
        </div>
        <v-divider class="mb-4"></v-divider>

        <div v-if="isLoading" class="d-flex flex-column align-center py-6">
          <v-progress-circular indeterminate color="primary" size="40" width="4"></v-progress-circular>
        </div>

        <v-form v-else ref="formRef" v-model="isFormValid" @submit.prevent="submitForm">
          <v-row dense>
            <v-col v-for="field in formFields" :key="field.label" cols="12" class="mb-1">
              <template v-if="['text', 'textarea', 'number', 'date'].includes(field.type)">
                <v-textarea v-if="field.type === 'textarea'" v-model="formData[field.label]" :label="field.label"
                  :required="field.required" :rules="field.required ? [v => !!v || `${field.label}是必填项`] : []"
                  variant="outlined" density="comfortable" color="primary" rows="2" auto-grow></v-textarea>
                <v-text-field v-else v-model="formData[field.label]" :label="field.label" :type="field.type"
                  :required="field.required" :rules="field.required ? [v => !!v || `${field.label}是必填项`] : []"
                  variant="outlined" density="comfortable" color="primary"></v-text-field>
              </template>
              <template v-else-if="field.type === 'radio'">
                <div class="text-subtitle-2 mb-1 text-medium-emphasis">
                  {{ field.label }} <span v-if="field.required" class="text-error">*</span>
                </div>
                <v-radio-group v-model="formData[field.label]" :rules="field.required ? [v => !!v || '请选择一个选项'] : []"
                  inline color="primary" density="comfortable" class="mt-n2">
                  <v-radio v-for="opt in field.options" :key="opt.value" :label="opt.label" :value="opt.value"></v-radio>
                </v-radio-group>
              </template>
              <template v-else-if="field.type === 'select'">
                <v-select v-model="formData[field.label]" :items="field.options" item-title="label" item-value="value"
                  :label="field.label" :required="field.required" :rules="field.required ? [v => !!v || '请选择一个选项'] : []"
                  variant="outlined" density="comfortable" color="primary"></v-select>
              </template>
              <template v-else-if="field.type === 'checkbox'">
                <div class="text-subtitle-2 mb-1 text-medium-emphasis">
                  {{ field.label }} <span v-if="field.required" class="text-error">*</span>
                </div>
                <div class="d-flex flex-wrap gap-x-4 mt-n1">
                  <v-checkbox v-for="opt in field.options" :key="opt.value" v-model="formData[field.label]"
                    :label="opt.label" :value="opt.value"
                    :rules="field.required ? [v => (formData[field.label] && formData[field.label].length > 0) || '至少选择一项'] : []"
                    color="primary" density="compact" hide-details class="me-2"></v-checkbox>
                </div>
              </template>
              <template v-else-if="field.type.endsWith('-range')">
                <div class="text-subtitle-2 mb-1 text-medium-emphasis">
                  {{ field.label }} <span v-if="field.required" class="text-error">*</span>
                </div>
                <v-row dense>
                  <v-col cols="6">
                    <v-text-field v-model="formData[field.label][0]" label="开始" :type="field.type.replace('-range', '')"
                      variant="outlined" density="comfortable"
                      :rules="field.required ? [v => !!v || '必填'] : []"></v-text-field>
                  </v-col>
                  <v-col cols="6">
                    <v-text-field v-model="formData[field.label][1]" label="结束" :type="field.type.replace('-range', '')"
                      variant="outlined" density="comfortable"
                      :rules="field.required ? [v => !!v || '必填'] : []"></v-text-field>
                  </v-col>
                </v-row>
              </template>
            </v-col>
          </v-row>

          <div class="d-flex ga-2 mt-4">
            <v-btn variant="text" @click="cancelForm">取消</v-btn>
            <v-spacer></v-spacer>
            <v-btn color="primary" size="large" rounded="pill" class="font-weight-bold"
              :loading="isSubmitting" :disabled="!isFormValid || isLoading" @click="openConfirm">
              提交登记
            </v-btn>
          </div>
        </v-form>
      </div>
    </v-expand-transition>

    <!-- 选择APP的Dialog -->
    <v-dialog v-model="newDialog.show" max-width="500" persistent>
      <v-card class="pa-4">
        <v-card-title class="text-h5">新建登记</v-card-title>
        <v-card-text>
          <v-form ref="selectFormRef" v-model="selectFormValid" @submit.prevent="startNewRegistration">
            <v-autocomplete v-model="newDialog.app" :items="runningApps" item-title="name" item-value="name"
              label="搜索跑步APP" :rules="[v => !!v || '请选择跑步APP']"
              variant="outlined" density="comfortable" hide-no-data></v-autocomplete>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="tonal" @click="newDialog.show = false">取消</v-btn>
          <v-btn color="primary" variant="flat" :disabled="!selectFormValid" @click="startNewRegistration">
            下一步
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 确认提交对话框 -->
    <v-dialog v-model="confirmDialog" max-width="400">
      <v-card class="pa-4">
        <v-card-title class="text-h6">确认提交</v-card-title>
        <v-card-text>提交后登记信息将由管理员审核，确定提交吗？</v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="confirmDialog = false">取消</v-btn>
          <v-btn color="primary" variant="flat" :loading="isSubmitting" @click="submitForm">确认提交</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 重新提交对话框 -->
    <v-dialog v-model="resubmitDialog.show" max-width="500" persistent>
      <v-card class="pa-4">
        <v-card-title class="text-h5">重新提交登记</v-card-title>
        <v-card-text>
          <v-form ref="resubmitSelectFormRef" v-model="resubmitSelectValid">
            <v-autocomplete v-model="resubmitDialog.app" :items="runningApps" item-title="name" item-value="name"
              label="搜索跑步APP" :rules="[v => !!v || '请选择跑步APP']"
              variant="outlined" density="comfortable" hide-no-data></v-autocomplete>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="tonal" @click="resubmitDialog.show = false">取消</v-btn>
          <v-btn color="primary" variant="flat" :disabled="!resubmitSelectValid" @click="startResubmitForm">
            下一步
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 重新提交后的表单 -->
    <v-dialog v-model="resubmitFormDialog.show" max-width="700" persistent scrollable>
      <v-card class="pa-4">
        <v-card-title class="d-flex align-center">
          <span class="text-h5">重新提交登记</span>
          <v-spacer></v-spacer>
          <v-chip size="small" color="warning" label>{{ resubmitFormDialog.app }}</v-chip>
        </v-card-title>
        <v-divider class="mb-4"></v-divider>
        <v-card-text>
          <v-form ref="resubmitFormRef" v-model="resubmitFormValid">
            <v-row dense>
              <v-col v-for="field in formFields" :key="field.label" cols="12">
                <template v-if="['text', 'textarea', 'number', 'date'].includes(field.type)">
                  <v-textarea v-if="field.type === 'textarea'" v-model="resubmitFormDialog.data[field.label]" :label="field.label"
                    :required="field.required" :rules="field.required ? [v => !!v || `${field.label}是必填项`] : []"
                    variant="outlined" density="comfortable" color="primary" rows="2" auto-grow></v-textarea>
                  <v-text-field v-else v-model="resubmitFormDialog.data[field.label]" :label="field.label" :type="field.type"
                    :required="field.required" :rules="field.required ? [v => !!v || `${field.label}是必填项`] : []"
                    variant="outlined" density="comfortable" color="primary"></v-text-field>
                </template>
                <template v-else-if="field.type === 'radio'">
                  <div class="text-subtitle-2 mb-1">{{ field.label }} <span v-if="field.required" class="text-error">*</span></div>
                  <v-radio-group v-model="resubmitFormDialog.data[field.label]" :rules="field.required ? [v => !!v || '请选择一个选项'] : []"
                    inline color="primary" density="comfortable">
                    <v-radio v-for="opt in field.options" :key="opt.value" :label="opt.label" :value="opt.value"></v-radio>
                  </v-radio-group>
                </template>
                <template v-else-if="field.type === 'select'">
                  <v-select v-model="resubmitFormDialog.data[field.label]" :items="field.options" item-title="label" item-value="value"
                    :label="field.label" :required="field.required" :rules="field.required ? [v => !!v || '请选择一个选项'] : []"
                    variant="outlined" density="comfortable" color="primary"></v-select>
                </template>
              </v-col>
            </v-row>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="tonal" @click="resubmitFormDialog.show = false">取消</v-btn>
          <v-btn color="warning" variant="flat" :loading="isSubmitting" :disabled="!resubmitFormValid" @click="doResubmit">
            提交
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 登记历史 -->
    <h2 class="text-h6 font-weight-bold mb-3">登记历史</h2>

    <div v-if="historyLoading" class="d-flex justify-center py-8">
      <v-progress-circular indeterminate color="primary" size="32"></v-progress-circular>
    </div>
    <div v-else-if="registrations.length === 0" class="text-center py-8 text-medium-emphasis">
      <v-icon size="40" class="mb-2">mdi-inbox-outline</v-icon>
      <div class="text-body-2">暂无登记记录</div>
    </div>
    <div v-else>
      <div v-for="item in registrations" :key="item.id"
        class="history-item mb-2 pa-3 rounded-lg d-flex flex-wrap align-center ga-3">
        <div class="flex-grow-1" style="min-width: 0;">
          <div class="d-flex flex-wrap gap-x-4 gap-y-1">
            <span class="text-body-2">{{ item.data['跑步APP'] || '-' }}</span>
            <span class="text-caption text-medium-emphasis">{{ formatDate(item.created_at) }}</span>
          </div>
          <div v-if="item.status === 'rejected' && item.reject_reason" class="text-caption text-error mt-1">
            {{ item.reject_reason }}
          </div>
        </div>
        <v-chip :color="getStatusColor(item.status)" size="x-small" class="flex-shrink-0">
          {{ getStatusText(item.status) }}
        </v-chip>
        <div class="d-flex ga-1 flex-shrink-0">
          <v-btn variant="text" size="x-small" color="primary" @click="openDetailDialog(item)">查看</v-btn>
          <v-btn v-if="item.status === 'rejected'" variant="text" size="x-small" color="warning" @click="openResubmitDialog(item)">重新提交</v-btn>
        </div>
      </div>
      <div class="text-center py-4" v-if="hasMoreHistory">
        <v-btn variant="tonal" :loading="loadingMore" @click="loadMoreHistory">加载更多</v-btn>
      </div>
    </div>

    <!-- 详情查看对话框 -->
    <v-dialog v-model="detailDialog.show" max-width="500">
      <v-card class="pa-4">
        <v-card-title>登记详情</v-card-title>
        <v-card-text>
          <v-table density="compact">
            <tbody>
              <tr v-for="key in sortedDetailKeys" :key="key">
                <td class="font-weight-bold">{{ key }}</td>
                <td>{{ formatValue(detailDialog.data[key]) }}</td>
              </tr>
            </tbody>
          </v-table>
          <v-alert v-if="detailDialog.rejectReason" type="error" variant="tonal" class="mt-3" density="compact">
            <strong>驳回原因：</strong>{{ detailDialog.rejectReason }}
          </v-alert>
          <div class="mt-3">
            <v-chip :color="getStatusColor(detailDialog.status)" size="small">
              {{ getStatusText(detailDialog.status) }}
            </v-chip>
            <span class="text-caption text-grey ml-2">{{ formatDate(detailDialog.createdAt) }}</span>
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="tonal" @click="detailDialog.show = false">关闭</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-snackbar v-model="snackbar.show" :color="snackbar.color" timeout="3000">
      {{ snackbar.text }}
    </v-snackbar>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive, computed } from 'vue'
import { ajax } from '@/api/ajax'
import { cookie } from '@/api/cookie'
import { ApiUrl } from '@/config/api-url'


interface FormField {
  label: string
  type: string
  required: boolean
  default: any
  options: { label: string; value: any }[]
}

interface AppItem {
  id: number
  name: string
  normal_price: number
  morning_price: number
  note: string
}

interface RegistrationItem {
  id: string
  data: Record<string, any>
  created_at: string
  status: string
  reject_reason?: string
}

const isLoading = ref(true)
const historyLoading = ref(false)
const loadingMore = ref(false)
const historyPage = ref(1)
const hasMoreHistory = ref(false)
const isSubmitting = ref(false)
const isFormValid = ref(false)
const showForm = ref(false)
const confirmDialog = ref(false)

const formRef = ref<any>(null)
const selectFormRef = ref<any>(null)
const resubmitSelectFormRef = ref<any>(null)
const resubmitFormRef = ref<any>(null)

const formFields = ref<FormField[]>([])
const formData = reactive<Record<string, any>>({})
const runningApps = ref<AppItem[]>([])
const registrations = ref<RegistrationItem[]>([])
const selectedApp = ref('')

const selectFormValid = ref(false)
const resubmitSelectValid = ref(false)
const resubmitFormValid = ref(false)

const newDialog = reactive({ show: false, app: '' })

const resubmitDialog = reactive({ show: false, uid: '', app: '', oldData: {} as Record<string, any> })
const resubmitFormDialog = reactive({
  show: false,
  uid: '',
  app: '',
  data: {} as Record<string, any>
})

const detailDialog = reactive({
  show: false,
  data: {} as Record<string, any>,
  status: '',
  createdAt: '',
  rejectReason: ''
})

const sortedDetailKeys = computed(() => {
  const data = detailDialog.data
  const keys = Object.keys(data)
  const fieldOrder = ['跑步APP', ...formFields.value.map(f => f.label)]
  return keys.sort((a, b) => {
    const ai = fieldOrder.indexOf(a)
    const bi = fieldOrder.indexOf(b)
    if (ai === -1 && bi === -1) return a.localeCompare(b)
    if (ai === -1) return 1
    if (bi === -1) return -1
    return ai - bi
  })
})

const snackbar = reactive({ show: false, text: '', color: 'success' })
function showMsg(text: string, color: string = 'success') {
  snackbar.text = text
  snackbar.color = color
  snackbar.show = true
}

function getStatusColor(status: string) {
  switch (status) {
    case 'approved': return 'success'
    case 'rejected': return 'error'
    default: return 'warning'
  }
}

function getStatusText(status: string) {
  switch (status) {
    case 'approved': return '已处理'
    case 'rejected': return '已驳回'
    default: return '未处理'
  }
}

function formatDate(iso: string) {
  if (!iso) return '-'
  const d = new Date(iso)
  return d.toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

function formatValue(val: any): string {
  if (Array.isArray(val)) return val.join(', ')
  if (val === null || val === undefined) return '-'
  return String(val)
}

async function fetchConfig() {
  isLoading.value = true
  try {
    const [appsRes, fieldsRes] = await Promise.all([
      ajax<AppItem[]>(ApiUrl.GET_PUBLIC_RUNNING_APPS),
      ajax<FormField[]>('/api/fields')
    ])
    if (appsRes.code === 200) runningApps.value = appsRes.data
    if (fieldsRes.code === 200) formFields.value = fieldsRes.data
  } catch (err) {
    showMsg('获取配置失败', 'error')
  } finally {
    isLoading.value = false
  }
}

function initFormData() {
  formFields.value.forEach(field => {
    if (field.type === 'checkbox') {
      formData[field.label] = Array.isArray(field.default) ? [...field.default] : []
    } else if (field.type.endsWith('-range')) {
      formData[field.label] = (Array.isArray(field.default) && field.default.length === 2)
        ? [...field.default] : ['', '']
    } else {
      formData[field.label] = field.default || ''
    }
  })
}

function initResubmitFormData() {
  const data: Record<string, any> = {}
  formFields.value.forEach(field => {
    if (field.type === 'checkbox') {
      data[field.label] = Array.isArray(field.default) ? [...field.default] : []
    } else {
      data[field.label] = field.default || ''
    }
  })
  return data
}

function openNewDialog() {
  newDialog.app = ''
  newDialog.show = true
  selectFormValid.value = false
  selectFormRef.value?.resetValidation()
}

function startNewRegistration() {
  if (!newDialog.app) return
  selectedApp.value = newDialog.app
  newDialog.show = false
  initFormData()
  showForm.value = true
  formRef.value?.resetValidation()
  setTimeout(() => {
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }, 100)
}

function cancelForm() {
  showForm.value = false
  selectedApp.value = ''
}

function openConfirm() {
  formRef.value.validate().then((res: any) => {
    if (res.valid) confirmDialog.value = true
  })
}

async function submitForm() {
  isSubmitting.value = true
  const token = cookie.get('token')
  const submissionData = {
    跑步APP: selectedApp.value,
    ...formData
  }
  try {
    const res = await ajax('/api/registrations', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
      body: submissionData
    })
    if (res.code === 200) {
      confirmDialog.value = false
      showForm.value = false
      selectedApp.value = ''
      showMsg('登记提交成功')
      loadHistory(true)
    } else {
      showMsg(res.msg, 'error')
    }
  } catch (error) {
    showMsg('提交失败，请稍后再试', 'error')
  } finally {
    isSubmitting.value = false
  }
}

async function loadHistory(reset = false) {
  if (reset) { historyPage.value = 1; registrations.value = [] }
  historyLoading.value = true
  const token = cookie.get('token')
  try {
    const res = await ajax<any>(`${ApiUrl.GET_USER_REGISTRATIONS}?page=${historyPage.value}&page_size=20`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (res.code === 200) {
      if (reset) registrations.value = res.data.items
      else registrations.value.push(...res.data.items)
      hasMoreHistory.value = registrations.value.length < res.data.total
    }
  } catch (err) {
    console.error('Failed to load history', err)
  } finally {
    historyLoading.value = false
    loadingMore.value = false
  }
}

function loadMoreHistory() {
  historyPage.value++
  loadingMore.value = true
  loadHistory()
}

function openDetailDialog(item: RegistrationItem) {
  detailDialog.data = item.data
  detailDialog.status = item.status
  detailDialog.createdAt = item.created_at
  detailDialog.rejectReason = item.reject_reason || ''
  detailDialog.show = true
}

function openResubmitDialog(item: RegistrationItem) {
  resubmitDialog.uid = item.id
  resubmitDialog.app = item.data['跑步APP'] || ''
  resubmitDialog.oldData = { ...item.data }
  resubmitDialog.show = true
  resubmitSelectValid.value = false
  resubmitSelectFormRef.value?.resetValidation()
}

function startResubmitForm() {
  if (!resubmitDialog.app) return
  resubmitFormDialog.uid = resubmitDialog.uid
  resubmitFormDialog.app = resubmitDialog.app
  const data = initResubmitFormData()
  // 用旧数据预填
  for (const key of Object.keys(resubmitDialog.oldData)) {
    if (key !== '跑步APP' && key in data) {
      data[key] = resubmitDialog.oldData[key]
    }
  }
  resubmitFormDialog.data = data
  resubmitDialog.show = false
  resubmitFormDialog.show = true
  resubmitFormValid.value = false
  resubmitFormRef.value?.resetValidation()
}

async function doResubmit() {
  const { valid } = await resubmitFormRef.value.validate()
  if (!valid) return
  isSubmitting.value = true
  const token = cookie.get('token')
  const submissionData = {
    跑步APP: resubmitFormDialog.app,
    ...resubmitFormDialog.data
  }
  try {
    const res = await ajax(`${ApiUrl.RESUBMIT_REGISTRATION}/${resubmitFormDialog.uid}`, {
      method: 'PUT',
      headers: { 'Authorization': `Bearer ${token}` },
      body: submissionData
    })
    if (res.code === 200) {
      resubmitFormDialog.show = false
      showMsg('重新提交成功')
      loadHistory(true)
    } else {
      showMsg(res.msg, 'error')
    }
  } catch (err) {
    showMsg('提交失败', 'error')
  } finally {
    isSubmitting.value = false
  }
}

onMounted(() => {
  fetchConfig()
  loadHistory(true)
})
</script>

<style scoped lang="scss">
.sign-page {
  max-height: 100%;
  overflow-y: auto;
}

.sign-page::-webkit-scrollbar {
  display: none;
}

.form-section {
  background: #fff;
  border-radius: 12px;
}

.history-item {
  background: #fff;
  border-radius: 10px;
}

.gap-x-4 {
  column-gap: 5px;
}
</style>
