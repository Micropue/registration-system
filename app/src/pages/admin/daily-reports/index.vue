<template>
  <div class="px-3 px-sm-6 py-4 py-sm-6 d-flex flex-column align-center">
    <div class="table-wrapper" style="width: 90%;">
      <div class="d-flex justify-space-between align-center mb-4 flex-wrap ga-2">
        <h1 class="text-h5 text-sm-h4">日报管理</h1>
        <div class="d-flex ga-2">
          <v-btn variant="outlined" size="small" prepend-icon="mdi-cog" @click="openFieldEditor" class="text-none">
            字段配置
          </v-btn>
          <v-btn color="success" variant="flat" size="small" prepend-icon="mdi-file-excel-outline" @click="handleExport" :loading="isExporting" class="text-none">
            导出Excel
          </v-btn>
        </div>
      </div>

      <v-row dense class="mb-4">
        <v-col cols="12" sm="4">
          <v-card rounded="lg" elevation="1" class="pa-4 text-center">
            <div class="text-h5 font-weight-bold text-primary">{{ stats.should_fill }}</div>
            <div class="text-caption text-medium-emphasis">应填人数</div>
          </v-card>
        </v-col>
        <v-col cols="12" sm="4">
          <v-card rounded="lg" elevation="1" class="pa-4 text-center">
            <div class="text-h5 font-weight-bold text-success">{{ stats.filled }}</div>
            <div class="text-caption text-medium-emphasis">已填人数</div>
          </v-card>
        </v-col>
        <v-col cols="12" sm="4">
          <v-card rounded="lg" elevation="1" class="pa-4 text-center">
            <div class="text-h5 font-weight-bold text-warning">{{ stats.unfilled }}</div>
            <div class="text-caption text-medium-emphasis">未填人数</div>
          </v-card>
        </v-col>
      </v-row>

      <div class="d-flex align-center ga-2 mb-4 flex-wrap">
        <v-text-field v-model="dateFrom" label="开始日期" type="date" variant="outlined" density="compact"
          hide-details style="max-width: 180px;"></v-text-field>
        <v-text-field v-model="dateTo" label="结束日期" type="date" variant="outlined" density="compact"
          hide-details style="max-width: 180px;"></v-text-field>
        <v-btn color="primary" variant="flat" size="small" @click="loadReports" class="text-none">查询</v-btn>
      </div>

      <AppDataTable
        :headers="tableHeaders"
        :items="tableItems"
        :total-items="total"
        :loading="isLoading"
        :items-per-page="pageSize"
        :page="page"
        :show-search="true"
        search-label="搜索用户名"
        @update:options="onTableOptions"
      />
    </div>

    <!-- 字段配置 Dialog -->
    <v-dialog v-model="fieldEditorDialog" max-width="800" persistent scrollable>
      <v-card rounded="lg">
        <v-card-title class="d-flex align-center border-bottom pa-4">
          <v-icon color="primary" class="mr-2">mdi-notebook-edit-outline</v-icon>
          <span class="text-h6">日报字段配置</span>
          <v-spacer></v-spacer>
          <v-btn icon="mdi-close" variant="text" density="comfortable" @click="fieldEditorDialog = false"></v-btn>
        </v-card-title>

        <v-card-text class="pa-4 pa-sm-5" style="max-height: 60vh;">
          <div v-if="editFields.length === 0" class="d-flex flex-column align-center py-8">
            <v-icon size="48" color="grey-lighten-1">mdi-playlist-remove</v-icon>
            <div class="text-body-2 text-grey mt-3">暂无字段，点击下方按钮添加</div>
          </div>

          <draggable v-else v-model="editFields" item-key="_key" handle=".drag-handle" ghost-class="ghost-card" animation="220">
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
                    <v-btn icon="mdi-pencil-outline" size="x-small" variant="text" color="primary" @click="openFieldEdit(index)"></v-btn>
                    <v-btn icon="mdi-trash-can-outline" size="x-small" variant="text" color="error" @click="editFields.splice(index, 1)"></v-btn>
                  </div>
                </div>
              </v-card>
            </template>
          </draggable>

          <v-btn block color="secondary" variant="tonal" prepend-icon="mdi-plus" class="mt-3" @click="openFieldEdit(-1)">
            添加字段
          </v-btn>
        </v-card-text>

        <v-divider></v-divider>
        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="fieldEditorDialog = false">取消</v-btn>
          <v-btn color="primary" variant="flat" :loading="isSavingFields" @click="saveFieldConfig">保存配置</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 单个字段编辑 Dialog -->
    <v-dialog v-model="fieldDialog.show" max-width="600" persistent scrollable>
      <v-card rounded="lg">
        <v-card-title class="d-flex align-center border-bottom pa-4">
          <v-icon color="primary" class="mr-2">
            {{ fieldDialog.editIndex >= 0 ? 'mdi-pencil-box' : 'mdi-plus-box' }}
          </v-icon>
          <span class="text-h6">{{ fieldDialog.editIndex >= 0 ? '编辑字段' : '添加字段' }}</span>
          <v-spacer></v-spacer>
          <v-btn icon="mdi-close" variant="text" density="comfortable" @click="fieldDialog.show = false"></v-btn>
        </v-card-title>

        <v-card-text class="pa-4" style="max-height: 60vh;">
          <v-row>
            <v-col cols="12" sm="8">
              <v-text-field v-model="fieldDialog.label" label="字段名称 *" placeholder="例如：今日工作内容"
                variant="outlined" density="comfortable" hide-details="auto"></v-text-field>
            </v-col>
            <v-col cols="12" sm="4">
              <v-select v-model="fieldDialog.type" :items="typeOptions" item-title="text" item-value="value"
                label="字段类型" variant="outlined" density="comfortable" hide-details>
                <template #selection>
                  <div class="d-flex align-center">
                    <v-icon :icon="getFieldIcon(fieldDialog.type)" size="small" class="mr-2" color="primary"></v-icon>
                    <span>{{ typeLabels[fieldDialog.type] || fieldDialog.type }}</span>
                  </div>
                </template>
              </v-select>
            </v-col>
            <v-col cols="12" class="pt-2 pb-2">
              <v-sheet class="pa-3 bg-surface rounded-lg">
                <div class="d-flex align-center">
                  <span class="text-subtitle-2 mr-4">必填项</span>
                  <v-switch v-model="fieldDialog.required" color="error" hide-details density="compact"></v-switch>
                </div>
              </v-sheet>
            </v-col>
            <v-col cols="12" v-if="['radio', 'checkbox', 'select'].includes(fieldDialog.type)">
              <div class="text-subtitle-2 mb-2">选项配置（每行一个，格式：显示文本:值 或直接填写）</div>
              <v-textarea v-model="fieldDialog.optionsText" variant="outlined" density="comfortable" rows="4"
                placeholder="选项1&#10;选项2&#10;选项3" hide-details></v-textarea>
            </v-col>
          </v-row>
        </v-card-text>

        <v-divider></v-divider>
        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="fieldDialog.show = false">取消</v-btn>
          <v-btn color="primary" variant="flat" @click="confirmFieldEdit">确定</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-snackbar v-model="snackbar.show" :color="snackbar.color" location="bottom">
      {{ snackbar.text }}
    </v-snackbar>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ajax } from '@/api/ajax'
import { cookie } from '@/api/cookie'
import AppDataTable from '@/components/AppDataTable.vue'
import draggable from 'vuedraggable'

const isLoading = ref(true)
const isExporting = ref(false)
const isSavingFields = ref(false)
const fields = ref<any[]>([])
const reports = ref<any[]>([])
const stats = reactive({ should_fill: 0, filled: 0, unfilled: 0 })
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const today = new Date().toISOString().slice(0, 10)
const dateFrom = ref(today)
const dateTo = ref(today)
const snackbar = reactive({ show: false, text: '', color: 'success' })

const fieldEditorDialog = ref(false)
const editFields = ref<any[]>([])

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

const fieldDialog = reactive({
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

function formatCellValue(val: any): string {
  if (val === null || val === undefined) return ''
  if (Array.isArray(val)) return val.join(', ')
  return String(val)
}

const tableHeaders = computed(() => {
  const base: { title: string; key: string; searchable?: boolean; filterable?: boolean }[] = [
    { title: '用户名', key: 'username', searchable: true },
    { title: '日期', key: 'report_date', filterable: true },
  ]
  for (const f of fields.value) {
    base.push({ title: f.label, key: `field__${f.label}` })
  }
  return base
})

const tableItems = computed(() => {
  return reports.value.map(r => {
    const row: Record<string, any> = {
      uid: r.uid,
      username: r.username,
      report_date: r.report_date,
    }
    for (const f of fields.value) {
      row[`field__${f.label}`] = formatCellValue(r.data?.[f.label])
    }
    return row
  })
})

const authHeaders = { 'Authorization': `Bearer ${cookie.get('token') || ''}` }

async function loadFields() {
  try {
    const res = await ajax<any>('/api/admin/daily-report-fields', { headers: authHeaders })
    if (res.code === 200) fields.value = res.data || []
  } catch { /* ignore */ }
}

async function loadStats() {
  try {
    const res = await ajax<any>(`/api/admin/daily-reports/statistics?report_date=${today}`, { headers: authHeaders })
    if (res.code === 200 && res.data) {
      stats.should_fill = res.data.should_fill || 0
      stats.filled = res.data.filled || 0
      stats.unfilled = res.data.unfilled || 0
    }
  } catch { /* ignore */ }
}

async function loadReports() {
  isLoading.value = true
  try {
    const params = new URLSearchParams({
      page: String(page.value),
      page_size: String(pageSize.value),
    })
    if (dateFrom.value) params.set('date_from', dateFrom.value)
    if (dateTo.value) params.set('date_to', dateTo.value)
    const res = await ajax<any>(`/api/admin/daily-reports?${params}`, { headers: authHeaders })
    if (res.code === 200 && res.data) {
      reports.value = res.data.items || []
      total.value = res.data.total || 0
    }
  } catch { /* ignore */ }
  isLoading.value = false
}

function onTableOptions(options: any) {
  page.value = options.page || 1
  pageSize.value = options.itemsPerPage || 20
  loadReports()
}

function openFieldEditor() {
  editFields.value = fields.value.map((f: any, i: number) => ({ ...f, _key: `field_${i}_${Date.now()}` }))
  fieldEditorDialog.value = true
}

function openFieldEdit(index: number) {
  if (index >= 0) {
    const f = editFields.value[index]
    fieldDialog.editIndex = index
    fieldDialog.label = f.label
    fieldDialog.type = f.type
    fieldDialog.required = f.required
    fieldDialog.optionsText = (f.options || []).map((o: any) => o.label === o.value ? o.label : `${o.label}:${o.value}`).join('\n')
  } else {
    fieldDialog.editIndex = -1
    fieldDialog.label = ''
    fieldDialog.type = 'text'
    fieldDialog.required = false
    fieldDialog.optionsText = ''
  }
  fieldDialog.show = true
}

function confirmFieldEdit() {
  if (!fieldDialog.label.trim()) {
    showMsg('字段名称不能为空', 'warning')
    return
  }
  const options = ['radio', 'checkbox', 'select'].includes(fieldDialog.type)
    ? fieldDialog.optionsText.split('\n').filter(Boolean).map(line => {
        const parts = line.split(':')
        return parts.length >= 2
          ? { label: parts[0].trim(), value: parts.slice(1).join(':').trim() }
          : { label: line.trim(), value: line.trim() }
      })
    : []
  const fieldData = {
    label: fieldDialog.label.trim(),
    type: fieldDialog.type,
    required: fieldDialog.required,
    options,
    _key: `field_${fieldDialog.editIndex >= 0 ? fieldDialog.editIndex : editFields.value.length}_${Date.now()}`,
  }
  if (fieldDialog.editIndex >= 0) {
    editFields.value[fieldDialog.editIndex] = fieldData
  } else {
    editFields.value.push(fieldData)
  }
  fieldDialog.show = false
}

async function saveFieldConfig() {
  isSavingFields.value = true
  try {
    const payload = editFields.value.map(f => ({
      label: f.label,
      type: f.type,
      required: f.required,
      options: f.options || [],
    }))
    const res = await ajax<any>('/api/admin/daily-report-fields', {
      method: 'POST',
      headers: authHeaders,
      body: payload,
    })
    if (res.code === 200) {
      showMsg('字段配置已保存')
      fieldEditorDialog.value = false
      await loadFields()
      await loadReports()
    } else {
      showMsg(res.msg || '保存失败', 'error')
    }
  } catch {
    showMsg('网络错误', 'error')
  }
  isSavingFields.value = false
}

async function handleExport() {
  if (!dateFrom.value || !dateTo.value) {
    showMsg('请先选择日期范围', 'warning')
    return
  }
  isExporting.value = true
  try {
    const url = `/api/admin/daily-reports/export?date_from=${dateFrom.value}&date_to=${dateTo.value}`
    const response = await fetch(url, { headers: authHeaders })
    if (!response.ok) {
      showMsg('导出失败', 'error')
      isExporting.value = false
      return
    }
    const blob = await response.blob()
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = `日报_${dateFrom.value}_${dateTo.value}.xlsx`
    a.click()
    URL.revokeObjectURL(a.href)
    showMsg('导出成功')
  } catch {
    showMsg('导出失败', 'error')
  }
  isExporting.value = false
}

onMounted(async () => {
  await loadFields()
  await Promise.all([loadStats(), loadReports()])
})
</script>

<style scoped>
.ghost-card {
  opacity: 0.4;
  background: #f0f0f0;
}
</style>
