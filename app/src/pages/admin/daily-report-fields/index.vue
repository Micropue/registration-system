<template>
  <div class="px-3 px-sm-6 py-4 py-sm-6 d-flex flex-column align-center">
    <div class="table-wrapper" style="width: 90%;">
      <div class="mb-4">
        <div class="d-flex align-center">
          <v-icon color="primary" size="28" class="mr-2">mdi-notebook-edit-outline</v-icon>
          <h1 class="text-h4 mt-0 mb-0">日报字段配置</h1>
        </div>
        <div class="d-flex align-center mt-1">
          <v-icon size="14" color="grey" class="mr-1">mdi-information-outline</v-icon>
          <span class="text-body-2 text-medium-emphasis">配置用户每日报告需要填写的字段，拖拽调整顺序</span>
        </div>
      </div>

      <div class="d-flex justify-end mb-3 ga-2">
        <v-btn variant="outlined" prepend-icon="mdi-arrow-left" @click="$router.push('/admin/daily-reports')" class="text-none">
          返回日报
        </v-btn>
        <v-btn color="primary" elevation="2" prepend-icon="mdi-content-save" :loading="isSaving" @click="saveFields" class="text-none">
          保存配置
        </v-btn>
      </div>

      <div v-if="isLoading" class="d-flex justify-center py-8">
        <v-progress-circular indeterminate color="primary" size="40" width="4"></v-progress-circular>
      </div>

      <template v-else>
        <div v-if="fields.length === 0" class="d-flex flex-column align-center py-8">
          <v-icon size="48" color="grey-lighten-1">mdi-playlist-remove</v-icon>
          <div class="text-body-2 text-grey mt-3">暂无字段，点击下方按钮添加</div>
        </div>

        <draggable v-else v-model="fields" item-key="_key" handle=".drag-handle" ghost-class="ghost-card" animation="220">
          <template #item="{ element, index }">
            <v-card class="mb-3" variant="outlined" rounded="lg">
              <div class="d-flex align-center pa-3">
                <v-icon class="mr-2 drag-handle" color="grey-lighten-1" size="24" style="cursor: grab;">mdi-drag</v-icon>
                <div class="d-flex flex-column flex-grow-1 overflow-hidden mr-2">
                  <span class="text-subtitle-1 font-weight-bold text-truncate">
                    {{ element.label || '未命名字段' }}
                  </span>
                  <div class="d-flex align-center gap-1 mt-1">
                    <v-chip size="x-small" color="primary" variant="tonal">
                      <v-icon start size="x-small" class="mr-1">{{ getFieldIcon(element.type) }}</v-icon>
                      {{ typeLabels[element.type] || element.type }}
                    </v-chip>
                    <v-chip v-if="element.required" size="x-small" color="error" variant="flat">必填</v-chip>
                  </div>
                </div>
                <div class="d-flex align-center gap-1 flex-shrink-0">
                  <v-btn icon="mdi-pencil-outline" size="x-small" variant="text" color="primary" @click="editField(index)"></v-btn>
                  <v-btn icon="mdi-trash-can-outline" size="x-small" variant="text" color="error" @click="removeField(index)"></v-btn>
                </div>
              </div>
            </v-card>
          </template>
        </draggable>

        <v-btn block color="secondary" variant="tonal" prepend-icon="mdi-plus" class="mt-3" @click="addField">
          添加字段
        </v-btn>
      </template>
    </div>

    <v-dialog v-model="dialog.show" max-width="600" persistent scrollable>
      <v-card rounded="lg">
        <v-card-title class="d-flex align-center border-bottom pa-4">
          <v-icon color="primary" class="mr-2">
            {{ dialog.editIndex >= 0 ? 'mdi-pencil-box' : 'mdi-plus-box' }}
          </v-icon>
          <span class="text-h6">{{ dialog.editIndex >= 0 ? '编辑字段' : '添加字段' }}</span>
          <v-spacer></v-spacer>
          <v-btn icon="mdi-close" variant="text" density="comfortable" @click="dialog.show = false"></v-btn>
        </v-card-title>

        <v-card-text class="pa-4" style="max-height: 60vh;">
          <v-row>
            <v-col cols="12" sm="8">
              <v-text-field v-model="dialog.label" label="字段名称 *" placeholder="例如：今日工作内容"
                variant="outlined" density="comfortable" hide-details="auto"></v-text-field>
            </v-col>
            <v-col cols="12" sm="4">
              <v-select v-model="dialog.type" :items="typeOptions" item-title="text" item-value="value"
                label="字段类型" variant="outlined" density="comfortable" hide-details>
                <template #selection>
                  <div class="d-flex align-center">
                    <v-icon :icon="getFieldIcon(dialog.type)" size="small" class="mr-2" color="primary"></v-icon>
                    <span>{{ typeLabels[dialog.type] || dialog.type }}</span>
                  </div>
                </template>
              </v-select>
            </v-col>
            <v-col cols="12" class="pt-2 pb-2">
              <v-sheet class="pa-3 bg-surface rounded-lg">
                <div class="d-flex align-center">
                  <span class="text-subtitle-2 mr-4">必填项</span>
                  <v-switch v-model="dialog.required" color="error" hide-details density="compact"></v-switch>
                </div>
              </v-sheet>
            </v-col>
            <v-col cols="12" v-if="['radio', 'checkbox', 'select'].includes(dialog.type)">
              <div class="text-subtitle-2 mb-2">选项配置（每行一个，格式：显示文本:值 或直接填写）</div>
              <v-textarea v-model="dialog.optionsText" variant="outlined" density="comfortable" rows="4"
                placeholder="选项1&#10;选项2&#10;选项3" hide-details></v-textarea>
            </v-col>
          </v-row>
        </v-card-text>

        <v-divider></v-divider>
        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="dialog.show = false">取消</v-btn>
          <v-btn color="primary" variant="flat" @click="confirmField">确定</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-snackbar v-model="snackbar.show" :color="snackbar.color" location="bottom">
      {{ snackbar.text }}
    </v-snackbar>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ajax } from '@/api/ajax'
import { cookie } from '@/api/cookie'
import draggable from 'vuedraggable'

const isLoading = ref(true)
const isSaving = ref(false)
const fields = ref<any[]>([])
const snackbar = reactive({ show: false, text: '', color: 'success' })

const typeLabels: Record<string, string> = {
  text: '单行文本',
  textarea: '多行文本',
  number: '数字',
  date: '日期',
  radio: '单选',
  checkbox: '多选',
  select: '下拉选择',
}

const typeOptions = [
  { text: '单行文本', value: 'text' },
  { text: '多行文本', value: 'textarea' },
  { text: '数字', value: 'number' },
  { text: '日期', value: 'date' },
  { text: '单选', value: 'radio' },
  { text: '多选', value: 'checkbox' },
  { text: '下拉选择', value: 'select' },
]

function getFieldIcon(type: string): string {
  const map: Record<string, string> = {
    text: 'mdi-form-textbox',
    textarea: 'mdi-text-box-outline',
    number: 'mdi-numeric',
    date: 'mdi-calendar',
    radio: 'mdi-radiobox-marked',
    checkbox: 'mdi-checkbox-marked-outline',
    select: 'mdi-form-dropdown',
  }
  return map[type] || 'mdi-form-textbox'
}

const dialog = reactive({
  show: false,
  editIndex: -1,
  label: '',
  type: 'text',
  required: false,
  optionsText: '',
})

function showMsg(text: string, color = 'success') {
  snackbar.text = text
  snackbar.color = color
  snackbar.show = true
}

const headers = { 'Authorization': `Bearer ${cookie.get('token') || ''}` }

async function loadFields() {
  isLoading.value = true
  try {
    const res = await ajax<any>('/api/admin/daily-report-fields', { headers })
    if (res.code === 200) {
      fields.value = (res.data || []).map((f: any, i: number) => ({ ...f, _key: `field_${i}_${Date.now()}` }))
    }
  } catch { /* ignore */ }
  isLoading.value = false
}

function addField() {
  dialog.editIndex = -1
  dialog.label = ''
  dialog.type = 'text'
  dialog.required = false
  dialog.optionsText = ''
  dialog.show = true
}

function editField(index: number) {
  const f = fields.value[index]
  dialog.editIndex = index
  dialog.label = f.label
  dialog.type = f.type
  dialog.required = f.required
  dialog.optionsText = (f.options || []).map((o: any) => o.label === o.value ? o.label : `${o.label}:${o.value}`).join('\n')
  dialog.show = true
}

function confirmField() {
  if (!dialog.label.trim()) {
    showMsg('字段名称不能为空', 'warning')
    return
  }
  const options = ['radio', 'checkbox', 'select'].includes(dialog.type)
    ? dialog.optionsText.split('\n').filter(Boolean).map(line => {
        const parts = line.split(':')
        return parts.length >= 2
          ? { label: parts[0].trim(), value: parts.slice(1).join(':').trim() }
          : { label: line.trim(), value: line.trim() }
      })
    : []
  const fieldData = {
    label: dialog.label.trim(),
    type: dialog.type,
    required: dialog.required,
    options,
    _key: `field_${dialog.editIndex >= 0 ? dialog.editIndex : fields.value.length}_${Date.now()}`,
  }
  if (dialog.editIndex >= 0) {
    fields.value[dialog.editIndex] = fieldData
  } else {
    fields.value.push(fieldData)
  }
  dialog.show = false
}

function removeField(index: number) {
  fields.value.splice(index, 1)
}

async function saveFields() {
  isSaving.value = true
  try {
    const payload = fields.value.map(f => ({
      label: f.label,
      type: f.type,
      required: f.required,
      options: f.options || [],
    }))
    const res = await ajax<any>('/api/admin/daily-report-fields', {
      method: 'POST',
      headers,
      body: payload,
    })
    if (res.code === 200) {
      showMsg('保存成功')
    } else {
      showMsg(res.msg || '保存失败', 'error')
    }
  } catch {
    showMsg('网络错误', 'error')
  }
  isSaving.value = false
}

onMounted(loadFields)
</script>

<style scoped>
.ghost-card {
  opacity: 0.4;
  background: #f0f0f0;
}
</style>
