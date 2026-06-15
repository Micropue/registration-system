<template>
  <div class="daily-report-page d-flex flex-column align-center justify-center" style="min-height: calc(100vh - 64px);">
    <div class="px-3 px-sm-6" style="width: 90%; max-width: 700px;">

      <div v-if="isLoading" class="d-flex justify-center py-8">
        <v-progress-circular indeterminate color="primary" size="40" width="4"></v-progress-circular>
      </div>

      <div v-else-if="fields.length === 0" class="text-center py-8 text-medium-emphasis">
        <v-icon size="48" class="mb-2">mdi-file-document-outline</v-icon>
        <div>暂未配置报告字段，请联系管理员。</div>
      </div>

      <div v-else-if="report && !isEditing" class="d-flex flex-column align-center py-12">
        <v-icon size="96" color="success" class="mb-4">mdi-check-circle</v-icon>
        <div class="text-h5 font-weight-bold mb-2">今日报告已提交</div>
        <div class="text-body-2 text-medium-emphasis mb-6">提交时间：{{ formatTime(report.update_time || report.create_time) }}</div>
        <v-btn color="primary" variant="flat" size="large" rounded="lg" prepend-icon="mdi-pencil" @click="isEditing = true" class="text-none px-8">
          修改报告
        </v-btn>
      </div>

      <template v-else>
        <div class="d-flex justify-space-between align-center mb-6">
          <h1 class="text-h5 text-sm-h4">每日报告</h1>
          <v-chip :color="report ? 'success' : 'warning'" label>
            <v-icon start>{{ report ? 'mdi-check-circle' : 'mdi-clock-outline' }}</v-icon>
            {{ report ? '修改中' : '今日未提交' }}
          </v-chip>
        </div>

        <v-form ref="formRef" v-model="isFormValid">
          <v-row dense>
            <v-col v-for="field in fields" :key="field.label" cols="12" class="mb-1">
              <template v-if="['text', 'number', 'date'].includes(field.type)">
                <v-text-field v-model="formData[field.label]" :label="field.label" :type="field.type"
                  :required="field.required" :rules="field.required ? [v => !!v || `${field.label}是必填项`] : []"
                  variant="outlined" density="comfortable" color="primary"></v-text-field>
              </template>
              <template v-else-if="field.type === 'textarea'">
                <v-textarea v-model="formData[field.label]" :label="field.label"
                  :required="field.required" :rules="field.required ? [v => !!v || `${field.label}是必填项`] : []"
                  variant="outlined" density="comfortable" color="primary" rows="3" auto-grow></v-textarea>
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
                    color="primary" density="compact" hide-details class="me-2"></v-checkbox>
                </div>
              </template>
            </v-col>
          </v-row>

          <div class="d-flex justify-end mt-4 ga-2">
            <v-btn v-if="report" variant="tonal" size="large" rounded="lg" @click="isEditing = false" class="text-none px-6">
              取消
            </v-btn>
            <v-btn color="primary" variant="flat" size="large" rounded="lg" :loading="isSubmitting"
              @click="handleSubmit" class="text-none px-8">
              {{ report ? '更新报告' : '提交报告' }}
            </v-btn>
          </div>
        </v-form>
      </template>
    </div>

    <v-snackbar v-model="snackbar.show" :color="snackbar.color" location="bottom">
      {{ snackbar.text }}
    </v-snackbar>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ajax } from '@/api/ajax'
import { cookie } from '@/api/cookie'

const isLoading = ref(true)
const isSubmitting = ref(false)
const isEditing = ref(false)
const isFormValid = ref(false)
const formRef = ref<any>(null)
const fields = ref<any[]>([])
const formData = reactive<Record<string, any>>({})
const report = ref<any>(null)
const snackbar = reactive({ show: false, text: '', color: 'success' })

function formatTime(iso: string) {
  if (!iso) return ''
  return new Date(iso).toLocaleString('zh-CN', { hour12: false })
}

function showMsg(text: string, color = 'success') {
  snackbar.text = text
  snackbar.color = color
  snackbar.show = true
}

async function loadData() {
  isLoading.value = true
  try {
    const headers = { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
    const [fieldsRes, statusRes] = await Promise.all([
      ajax<any>('/api/daily-report/fields', { headers }),
      ajax<any>('/api/daily-report/status', { headers }),
    ])
    if (fieldsRes.code === 200) {
      fields.value = fieldsRes.data || []
      for (const f of fields.value) {
        if (f.type === 'checkbox') {
          formData[f.label] = []
        } else {
          formData[f.label] = ''
        }
      }
    }
    if (statusRes.code === 200 && statusRes.data) {
      if (statusRes.data.report) {
        report.value = statusRes.data.report
        const savedData = statusRes.data.report.data || {}
        for (const key of Object.keys(savedData)) {
          formData[key] = savedData[key]
        }
      }
    }
  } catch { /* ignore */ }
  isLoading.value = false
}

async function handleSubmit() {
  const { valid } = await formRef.value?.validate()
  if (!valid) return
  isSubmitting.value = true
  try {
    const res = await ajax<any>('/api/daily-report/submit', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` },
      body: formData,
    })
    if (res.code === 200) {
      showMsg(report.value ? '报告已更新' : '报告提交成功')
      report.value = { uid: res.data?.uid, update_time: new Date().toISOString() }
      isEditing.value = false
    } else {
      showMsg(res.msg || '提交失败', 'error')
    }
  } catch {
    showMsg('网络错误', 'error')
  }
  isSubmitting.value = false
}

onMounted(loadData)
</script>
