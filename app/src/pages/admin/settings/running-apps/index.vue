<template>
  <v-container fluid class="pa-0 d-flex flex-column align-center">
    <div class="table-wrapper mt-4">
      <v-row align="center" class="mb-4">
        <v-col cols="12" sm="auto">
          <h1 class="text-h4">跑步APP配置</h1>
        </v-col>
        <v-col cols="12" sm class="d-flex flex-wrap ga-2 justify-sm-end">
          <v-btn color="secondary" variant="tonal" @click="bulkDialog.show = true" prepend-icon="mdi-file-upload">Excel批量导入</v-btn>
          <v-btn color="primary" @click="openCreateDialog" prepend-icon="mdi-plus">新增APP</v-btn>
        </v-col>
      </v-row>

      <app-data-table
        :headers="headers"
        :items="apps"
        :total-items="apps.length"
        :loading="loading"
        clientSide
        show-search show-filter
        search-label="搜索APP名称/备注"
      >
        <template v-slot:item.normal_price="{ item }">
          {{ item.normal_price.toFixed(2) }}
        </template>
        <template v-slot:item.morning_price="{ item }">
          {{ item.morning_price.toFixed(2) }}
        </template>
        <template v-slot:item.accent_color="{ item }">
          <span class="color-dot" :style="{ backgroundColor: item.accent_color || '#1976D2' }"></span>
          {{ item.accent_color || '#1976D2' }}
        </template>
        <template v-slot:item.actions="{ item }">
          <div class="d-flex ga-1">
            <v-btn variant="tonal" rounded color="primary" @click="openEditDialog(item)">修改</v-btn>
            <v-btn variant="tonal" rounded color="error" @click="confirmDeleteDialog(item)">删除</v-btn>
          </div>
        </template>
      </app-data-table>
    </div>

    <!-- 新增/编辑 Dialog -->
    <v-dialog v-model="dialog.show" max-width="500">
      <v-card class="pa-4">
        <v-card-title>{{ dialog.isEdit ? '修改APP' : '新增APP' }}</v-card-title>
        <v-card-text>
          <v-form ref="formRef" @submit.prevent="submitApp">
            <v-text-field v-model="dialog.name" label="APP名称" variant="outlined"
              :rules="[v => !!v || 'APP名称必填']" hide-details="auto" class="mb-4" required></v-text-field>
            <v-text-field v-model.number="dialog.normal_price" label="普通跑步价格" type="number" variant="outlined"
              :rules="[v => v !== '' || '价格必填', v => v >= 0 || '价格不能为负']" hide-details="auto" class="mb-4" required></v-text-field>
            <v-text-field v-model.number="dialog.morning_price" label="晨跑价格" type="number" variant="outlined"
              :rules="[v => v !== '' || '价格必填', v => v >= 0 || '价格不能为负']" hide-details="auto" class="mb-4" required></v-text-field>
            <v-textarea v-model="dialog.note" label="备注" variant="outlined" rows="3" hide-details="auto"></v-textarea>
            <div class="d-flex align-center ga-3 mt-4">
              <label class="color-picker-label">
                <div class="color-preview" :style="{ backgroundColor: dialog.accent_color || '#1976D2' }"></div>
                <input type="color" v-model="dialog.accent_color" class="hidden-input">
              </label>
              <span class="text-body-2">{{ dialog.accent_color || '#1976D2' }}</span>
            </div>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="tonal" @click="dialog.show = false">取消</v-btn>
          <v-btn color="primary" variant="flat" :loading="loading" @click="submitApp">提交</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 删除确认 Dialog -->
    <v-dialog v-model="deleteDialog.show" max-width="400">
      <v-card>
        <v-card-title class="text-h5 pa-4">确认删除</v-card-title>
        <v-card-text class="pa-4 pt-0">
          您确定要删除APP <strong>{{ deleteDialog.name }}</strong> 吗？
        </v-card-text>
        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="deleteDialog.show = false">取消</v-btn>
          <v-btn color="error" variant="flat" :loading="loading" @click="doDelete">确认删除</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 批量导入 Dialog -->
    <v-dialog v-model="bulkDialog.show" max-width="600">
      <v-card class="pa-4">
        <v-card-title>Excel批量导入</v-card-title>
        <v-card-text>
          <div class="mb-4">
            <div class="text-subtitle-2 mb-2">1. 下载样板文件</div>
            <v-btn variant="outlined" size="small" prepend-icon="mdi-download" @click="downloadTemplate">下载 Excel 样板</v-btn>
          </div>
          <div class="mb-4">
            <div class="text-subtitle-2 mb-2">2. 格式要求</div>
            <v-list density="compact">
              <v-list-item prepend-icon="mdi-check-circle" title="第一行为表头：APP名称、普通跑步价格、晨跑价格、备注、强调色"></v-list-item>
              <v-list-item prepend-icon="mdi-check-circle" title="价格字段为数字，备注和强调色可选，强调色格式#RRGGBB"></v-list-item>
            </v-list>
          </div>
          <div class="mb-4">
            <div class="text-subtitle-2 mb-2">3. 上传文件</div>
            <v-file-input v-model="bulkDialog.file" label="选择 Excel 文件" variant="outlined" density="compact"
              accept=".xlsx, .xls" prepend-icon="mdi-microsoft-excel" hide-details :loading="bulkDialog.isParsing"></v-file-input>
          </div>

          <v-expand-transition>
            <div v-if="bulkDialog.parsedItems.length" class="mb-4">
              <div class="d-flex justify-space-between align-center mb-2">
                <div class="text-subtitle-2">4. 预览与编辑 (共 {{ bulkDialog.parsedItems.length }} 条)</div>
                <v-btn variant="text" size="small" color="error" @click="bulkDialog.parsedItems = []">清空列表</v-btn>
              </div>
              <v-card border flat class="preview-list">
                <v-table density="compact">
                  <thead>
                    <tr>
                      <th class="text-left" style="width: 30%">APP名称</th>
                      <th class="text-left" style="width: 25%">普通价格</th>
                      <th class="text-left" style="width: 25%">晨跑价格</th>
                      <th style="width: 20%">备注</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(item, index) in bulkDialog.parsedItems" :key="index">
                      <td class="pa-1">{{ item.name }}</td>
                      <td class="pa-1">{{ item.normal_price }}</td>
                      <td class="pa-1">{{ item.morning_price }}</td>
                      <td class="pa-1">{{ item.note }}</td>
                    </tr>
                  </tbody>
                </v-table>
              </v-card>
            </div>
          </v-expand-transition>

          <v-expand-transition>
            <div v-if="bulkDialog.result" class="mt-4 pa-4 bg-grey-lighten-4 rounded">
              <div class="text-subtitle-1 font-weight-bold mb-2">导入结果</div>
              <div class="d-flex gap-4 mb-2">
                <span class="text-success">成功: {{ bulkDialog.result.success_count }}</span>
                <span class="text-error">失败: {{ bulkDialog.result.errors.length }}</span>
                <span>总计: {{ bulkDialog.result.total_count }}</span>
              </div>
              <v-divider v-if="bulkDialog.result.errors.length" class="my-2"></v-divider>
              <div v-if="bulkDialog.result.errors.length" style="max-height: 150px; overflow-y: auto;">
                <div v-for="(err, i) in bulkDialog.result.errors" :key="i" class="text-caption text-error">
                  {{ err }}
                </div>
              </div>
            </div>
          </v-expand-transition>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="tonal" @click="bulkDialog.show = false; bulkDialog.result = null">取消</v-btn>
          <v-btn color="primary" variant="flat" :loading="loading" :disabled="!bulkDialog.file" @click="handleBulkImport">
            开始导入
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-snackbar v-model="snackbar.show" :color="snackbar.color" timeout="3000">
      {{ snackbar.text }}
    </v-snackbar>
  </v-container>
</template>

<style scoped>
.table-wrapper { width: 90%; max-width: 1000px; }
.preview-list { max-height: 300px; overflow-y: auto; overflow-x: auto; }
.color-picker-label { position: relative; cursor: pointer; }
.color-picker-label .hidden-input { position: absolute; top: 0; left: 0; width: 100%; height: 100%; opacity: 0; cursor: pointer; }
.color-preview { width: 36px; height: 36px; border-radius: 8px; border: 2px solid rgba(0,0,0,.2); cursor: pointer; transition: transform .15s; }
.color-preview:hover { transform: scale(1.1); }
.color-dot { display: inline-block; width: 14px; height: 14px; border-radius: 50%; margin-right: 6px; vertical-align: middle; }
</style>

<script lang="ts" setup>
import { ref, reactive, watch, onMounted } from 'vue'
import * as XLSX from 'xlsx'
import { ajax } from '@/api/ajax'
import { cookie } from '@/api/cookie'
import { ApiUrl } from '@/config/api-url'
import type { RunningApp } from '@/config/api-type'
import AppDataTable from '@/components/AppDataTable.vue'

const apps = ref<RunningApp[]>([])
const loading = ref(false)
const formRef = ref<any>(null)

const dialog = reactive({
  show: false,
  isEdit: false,
  editId: 0,
  name: '',
  normal_price: 0,
  morning_price: 0,
  note: '',
  accent_color: '#1976D2'
})

const deleteDialog = reactive({ show: false, id: 0, name: '' })

const bulkDialog = reactive({
  show: false,
  file: null as File | null,
  parsedItems: [] as any[],
  isParsing: false,
  result: null as any
})

const snackbar = reactive({ show: false, text: '', color: 'success' })
function showMsg(text: string, color: string = 'success') {
  snackbar.text = text
  snackbar.color = color
  snackbar.show = true
}

const headers = [
  { title: 'APP名称', key: 'name', searchable: true, filterable: true },
  { title: '普通跑步价格', key: 'normal_price', sortable: true },
  { title: '晨跑价格', key: 'morning_price', sortable: true },
  { title: '备注', key: 'note', searchable: true },
  { title: '强调色', key: 'accent_color', sortable: false },
  { title: '操作', key: 'actions', sortable: false }
]

watch(() => bulkDialog.file, (newFile) => {
  if (newFile) {
    parseFile(newFile)
  } else {
    bulkDialog.parsedItems = []
    bulkDialog.result = null
  }
})

function parseFile(file: File) {
  bulkDialog.isParsing = true
  bulkDialog.result = null
  const reader = new FileReader()
  reader.onload = (e: any) => {
    try {
      const data = e.target.result
      const workbook = XLSX.read(data, { type: 'binary' })
      const sheetName = workbook.SheetNames[0]
      const sheet = workbook.Sheets[sheetName]
      const rows = XLSX.utils.sheet_to_json(sheet, { header: 1 }) as any[][]
      bulkDialog.parsedItems = rows.slice(1)
        .filter(row => row.length > 0 && row[0])
        .map(row => ({
          name: String(row[0] || ''),
          normal_price: parseFloat(row[1]) || 0,
          morning_price: parseFloat(row[2]) || 0,
          note: String(row[3] || ''),
          accent_color: String(row[4] || '#1976D2')
        }))
    } catch (err) {
      showMsg('文件解析失败', 'error')
    } finally {
      bulkDialog.isParsing = false
    }
  }
  reader.readAsBinaryString(file)
}

function downloadTemplate() {
  const data = [
    ['APP名称', '普通跑步价格', '晨跑价格', '备注', '强调色'],
    ['校园跑', '3.00', '2.50', '基础跑步APP', '#1976D2'],
    ['乐跑', '5.00', '4.00', '', '#E53935']
  ]
  const ws = XLSX.utils.aoa_to_sheet(data)
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, "跑步APP导入模板")
  XLSX.writeFile(wb, "跑步APP导入样板.xlsx")
}

async function handleBulkImport() {
  if (!bulkDialog.parsedItems.length) return
  loading.value = true
  try {
    const res = await ajax(ApiUrl.BULK_CREATE_RUNNING_APPS, {
      method: 'POST',
      body: bulkDialog.parsedItems,
      headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
    })
    if (res.code === 200) {
      bulkDialog.result = {
        success_count: bulkDialog.parsedItems.length,
        total_count: bulkDialog.parsedItems.length,
        errors: []
      }
      showMsg(`导入成功，共 ${bulkDialog.parsedItems.length} 条`)
      loadApps()
    } else {
      showMsg(res.msg || '导入失败', 'error')
    }
  } catch (err) {
    showMsg('请求失败，请稍后再试', 'error')
  } finally {
    loading.value = false
  }
}

function openCreateDialog() {
  dialog.show = true
  dialog.isEdit = false
  dialog.editId = 0
  dialog.name = ''
  dialog.normal_price = 0
  dialog.morning_price = 0
  dialog.note = ''
  dialog.accent_color = '#1976D2'
}

function openEditDialog(item: RunningApp) {
  dialog.show = true
  dialog.isEdit = true
  dialog.editId = item.id
  dialog.name = item.name
  dialog.normal_price = item.normal_price
  dialog.morning_price = item.morning_price
  dialog.note = item.note
  dialog.accent_color = item.accent_color || '#1976D2'
}

async function submitApp() {
  const { valid } = await formRef.value.validate()
  if (!valid) return
  loading.value = true
  try {
    if (dialog.isEdit) {
      const res = await ajax(`${ApiUrl.UPDATE_RUNNING_APP}/${dialog.editId}`, {
        method: 'PUT',
        body: { name: dialog.name, normal_price: dialog.normal_price, morning_price: dialog.morning_price, note: dialog.note, accent_color: dialog.accent_color },
        headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
      })
      if (res.code === 200) { showMsg('修改成功'); dialog.show = false; loadApps() }
      else showMsg(res.msg || '修改失败', 'error')
    } else {
      const res = await ajax(ApiUrl.CREATE_RUNNING_APP, {
        method: 'POST',
        body: { name: dialog.name, normal_price: dialog.normal_price, morning_price: dialog.morning_price, note: dialog.note, accent_color: dialog.accent_color },
        headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
      })
      if (res.code === 200) { showMsg('创建成功'); dialog.show = false; loadApps() }
      else showMsg(res.msg || '创建失败', 'error')
    }
  } catch (err) {
    showMsg('请求失败，请稍后再试', 'error')
  } finally { loading.value = false }
}

function confirmDeleteDialog(item: RunningApp) {
  deleteDialog.id = item.id
  deleteDialog.name = item.name
  deleteDialog.show = true
}

async function doDelete() {
  loading.value = true
  try {
    const res = await ajax(`${ApiUrl.DELETE_RUNNING_APP}/${deleteDialog.id}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
    })
    if (res.code === 200) { showMsg('删除成功'); deleteDialog.show = false; loadApps() }
    else showMsg(res.msg || '删除失败', 'error')
  } catch (err) {
    showMsg('请求失败，请稍后再试', 'error')
  } finally { loading.value = false }
}

async function loadApps() {
  loading.value = true
  try {
    const res = await ajax<RunningApp[]>(ApiUrl.GET_RUNNING_APPS, {
      method: 'GET',
      headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
    })
    if (res.code === 200) apps.value = res.data
  } catch (err) {
    console.error('Failed to load apps', err)
  } finally { loading.value = false }
}

onMounted(() => { loadApps() })
</script>
