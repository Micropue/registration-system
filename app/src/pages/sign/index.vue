<template>
  <v-container class="max-width-800 py-4 py-sm-8 main-container" style="max-height: 100%; overflow-y: auto;">
    <v-card class="pa-4 pa-sm-8 rounded-md shadow-lg" elevation="3">
      <v-card-title class="d-flex align-center pb-2">
        <v-icon color="primary" size="32" class="me-3">mdi-run-fast</v-icon>
        <span class="text-h5 font-weight-black">校园跑数据登记</span>
      </v-card-title>
      <v-card-subtitle class="pb-4">仔细核实填写内容，提交后管理员会审核后为你启动代跑工作。</v-card-subtitle>

      <v-divider class="mb-6"></v-divider>

      <!-- 已登记状态 (如果是初次提交成功显示绿勾，如果是之前已登记显示黄色提示) -->
      <div v-if="isRegistered" class="text-center py-12">
          <v-icon :color="isSuccess ? 'success' : 'warning'" size="80">
            {{ isSuccess ? 'mdi-check-circle-outline' : 'mdi-alert-circle-outline' }}
          </v-icon>
          <div class="text-h5 font-weight-bold mt-4">{{ isSuccess ? '登记成功！' : '您已登记过！' }}</div>
          <div class="text-body-1 text-grey mt-2">
            {{ isSuccess ? '您的登记信息已提交，感谢配合。' : '校园跑登记仅允许提交一次。' }}
          </div>
      </div>
      <!-- 加载中状态 -->
      <div v-else-if="isLoading" class="d-flex flex-column align-center py-12">
        <v-progress-circular indeterminate color="primary" size="64" width="6"></v-progress-circular>
        <div class="text-body-1 text-grey-darken-1 mt-4 font-weight-medium">获取表单配置中...</div>
      </div>

      <!-- 表单内容 -->
      <v-form v-else ref="formRef" v-model="isFormValid" @submit.prevent="submitForm">
        <v-row dense>
          <v-col v-for="field in formFields" :key="field.label" cols="12" class="mb-1">

            <!-- 文本/多行文本/数值/日期 -->
            <template v-if="['text', 'textarea', 'number', 'date'].includes(field.type)">
              <v-textarea v-if="field.type === 'textarea'" v-model="formData[field.label]" :label="field.label"
                :required="field.required" :rules="field.required ? [v => !!v || `${field.label}是必填项`] : []"
                variant="outlined" density="comfortable" color="primary" rows="2" auto-grow></v-textarea>
              <v-text-field v-else v-model="formData[field.label]" :label="field.label" :type="field.type"
                :required="field.required" :rules="field.required ? [v => !!v || `${field.label}是必填项`] : []"
                variant="outlined" density="comfortable" color="primary"></v-text-field>
            </template>

            <!-- 单选按钮 -->
            <template v-else-if="field.type === 'radio'">
              <div class="text-subtitle-2 mb-1 text-grey-darken-2">
                {{ field.label }} <span v-if="field.required" class="text-error">*</span>
              </div>
              <v-radio-group v-model="formData[field.label]" :rules="field.required ? [v => !!v || '请选择一个选项'] : []"
                inline color="primary" density="comfortable" class="mt-n2">
                <v-radio v-for="opt in field.options" :key="opt.value" :label="opt.label" :value="opt.value"></v-radio>
              </v-radio-group>
            </template>

            <!-- 下拉菜单 -->
            <template v-else-if="field.type === 'select'">
              <v-select v-model="formData[field.label]" :items="field.options" item-title="label" item-value="value"
                :label="field.label" :required="field.required" :rules="field.required ? [v => !!v || '请选择一个选项'] : []"
                variant="outlined" density="comfortable" color="primary"></v-select>
            </template>

            <!-- 复选框组 -->
            <template v-else-if="field.type === 'checkbox'">
              <div class="text-subtitle-2 mb-1 text-grey-darken-2">
                {{ field.label }} <span v-if="field.required" class="text-error">*</span>
              </div>
              <div class="d-flex flex-wrap gap-x-4 mt-n1">
                <v-checkbox v-for="opt in field.options" :key="opt.value" v-model="formData[field.label]"
                  :label="opt.label" :value="opt.value"
                  :rules="field.required ? [v => (formData[field.label] && formData[field.label].length > 0) || '至少选择一项'] : []"
                  color="primary" density="compact" hide-details class="me-2"></v-checkbox>
              </div>
            </template>

            <!-- 范围类 -->
            <template v-else-if="field.type.endsWith('-range')">
              <div class="text-subtitle-2 mb-1 text-grey-darken-2">
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
        <v-card-subtitle class="pb-4">注意⚠️：请仔细填写表单，您只可以填写一次。</v-card-subtitle>
        <v-btn color="primary" block size="x-large" rounded="pill" class="mt-4 font-weight-black elevation-4"
          :loading="isSubmitting" :disabled="!isFormValid || isLoading" @click="openConfirm">
          立即提交登记
        </v-btn>
      </v-form>
    </v-card>
    <!-- 确认提交对话框 -->
    <v-dialog v-model="confirmDialog" max-width="400">
      <v-card class="pa-4">
        <v-card-title class="text-h6">确认提交</v-card-title>
        <v-card-text>提交后登记信息将无法修改，确定提交吗？</v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="confirmDialog = false">取消</v-btn>
          <v-btn color="primary" variant="flat" :loading="isSubmitting" @click="submitForm">确认提交</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>


    <v-snackbar v-model="snackbar.show" :color="snackbar.color" timeout="3000" location="top">
      {{ snackbar.text }}
    </v-snackbar>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { ajax } from '@/api/ajax'
import { cookie } from '@/api/cookie'

interface FormField {
  label: string
  type: string
  required: boolean
  default: any
  options: { label: string; value: any }[]
}

const isLoading = ref(true)
const isSubmitting = ref(false)
const isFormValid = ref(false)
const isRegistered = ref(false)
const confirmDialog = ref(false)
const formRef = ref<any>(null)
const formFields = ref<FormField[]>([])
const formData = reactive<Record<string, any>>({})
const isSuccess = ref(false)
const snackbar = reactive({
  show: false,
  text: '',
  color: 'success'
})

async function fetchFields() {
  isLoading.value = true
  const token = cookie.get('token')
  try {
    // 1. 先检查是否已登记
    const regRes = await ajax<{ registered: boolean }>('/api/registrations/check', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    isRegistered.value = regRes.data?.registered || false
    if (isRegistered.value) {
      isLoading.value = false
      return
    }

    // 2. 拉取配置
    const res = await ajax<FormField[]>('/api/fields')
    if (res.code === 200) {
      formFields.value = res.data
      initFormData()
    } else {
      showMsg(res.msg, 'error')
    }
  } catch (error) {
    showMsg('获取表单配置失败', 'error')
  } finally {
    isLoading.value = false
  }
}

function initFormData() {
  formFields.value.forEach(field => {
    if (field.type === 'checkbox') {
      formData[field.label] = Array.isArray(field.default) ? [...field.default] : []
    } else if (field.type.endsWith('-range')) {
      // 确保范围字段初始化为数组
      formData[field.label] = (Array.isArray(field.default) && field.default.length === 2)
        ? [...field.default]
        : ['', '']
    } else {
      formData[field.label] = field.default || ''
    }
  })
}

function openConfirm() {
  formRef.value.validate().then((res: any) => {
    if (res.valid) {
      confirmDialog.value = true
    }
  })
}

async function submitForm() {
  isSubmitting.value = true
  const token = cookie.get('token')

  try {
    const res = await ajax('/api/registrations', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
      body: formData
    })

    console.log('Submission Response:', res);

    if (res.code === 200) {
      isRegistered.value = true
      isSuccess.value = true
      confirmDialog.value = false
    } else {
      showMsg(res.msg, 'error')
    }
  } catch (error) {
    console.error('Submission Error:', error);
    showMsg('提交失败，请稍后再试', 'error')
  } finally {
    isSubmitting.value = false
  }
}


function showMsg(text: string, color: string = 'success') {
  snackbar.text = text
  snackbar.color = color
  snackbar.show = true
}

onMounted(fetchFields)
</script>

<style scoped lang="scss">
.max-width-800 {
  max-width: 800px;
  margin: 0 auto;
}

.shadow-lg {
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1) !important;
}

.gap-x-4 {
  column-gap: 5px;
}

.main-container::-webkit-scrollbar {
  display: none;
}
</style>
