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
        enableDragSort
        @reorder="onReorder"
      >
        <template v-slot:item.name="{ item }">
          <div class="d-flex align-center ga-2">
            <v-avatar v-if="item.icon" size="28" rounded>
              <v-img :src="item.icon" cover></v-img>
            </v-avatar>
            <v-icon v-else size="20" color="grey">mdi-run-fast</v-icon>
            {{ item.name }}
          </div>
        </template>
        <template v-slot:item.note="{ item }">
          {{ item.note || '-' }}
        </template>
        <template v-slot:item.accent_color="{ item }">
          <span class="color-dot" :style="{ backgroundColor: item.accent_color || '#1976D2' }"></span>
          {{ item.accent_color || '#1976D2' }}
        </template>
        <template v-slot:item.template_count="{ item }">
          {{ item.template_count ?? '-' }}
        </template>
        <template v-slot:item.balance_mode="{ item }">
          <v-chip size="x-small" :color="item.balance_mode === 'mileage' ? 'blue' : item.balance_mode === 'count' ? 'green' : 'grey'">
            {{ item.balance_mode === 'mileage' ? '公里数' : item.balance_mode === 'count' ? '次数' : '未设置' }}
          </v-chip>
        </template>
        <template v-slot:item.actions="{ item }">
          <div class="d-flex ga-1">
            <v-btn variant="tonal" rounded size="small" color="secondary" :to="`/admin/running-apps/${item.uid}/templates`">模板管理</v-btn>
            <v-btn variant="tonal" rounded size="small" color="info" :to="`/admin/running-apps/${item.uid}/balance`">余额管理</v-btn>
            <v-btn variant="tonal" rounded size="small" color="primary" @click="openEditDialog(item)">修改</v-btn>
            <v-btn variant="tonal" rounded size="small" color="error" @click="confirmDeleteDialog(item)">删除</v-btn>
          </div>
        </template>
      </app-data-table>
    </div>

    <!-- 新增/编辑 Dialog -->
    <v-dialog v-model="dialog.show" max-width="520">
      <v-card class="pa-4">
        <v-card-title>{{ dialog.isEdit ? '修改APP' : '新增APP' }}</v-card-title>
        <v-card-text>
          <v-form ref="formRef" @submit.prevent="submitApp">
            <div class="d-flex align-start ga-4 mb-4">
              <div class="d-flex flex-column align-center ga-2">
                <v-avatar size="72" rounded class="bg-grey-lighten-3">
                  <v-img v-if="dialog.iconPreview" :src="dialog.iconPreview" cover></v-img>
                  <v-icon v-else size="36" color="grey-lighten-1">mdi-image-outline</v-icon>
                </v-avatar>
                <v-btn size="x-small" variant="tonal" color="secondary" @click="uploadRef?.click()">
                  {{ dialog.iconPreview ? '更换图标' : '上传图标' }}
                </v-btn>
                <v-btn v-if="dialog.iconPreview" size="x-small" variant="text" color="error" @click="dialog.iconPreview = ''; dialog.icon = ''">移除</v-btn>
                <input ref="uploadRef" type="file" accept="image/webp,image/jpeg,image/png,image/gif,image/heic,image/heif" style="display:none" @change="handleIconUpload">
              </div>
              <div class="flex-fill">
                <v-text-field v-model="dialog.name" label="APP名称" variant="outlined"
                  :rules="[v => !!v || 'APP名称必填']" hide-details="auto" class="mb-4" required></v-text-field>
            <v-textarea v-model="dialog.note" label="备注" variant="outlined" rows="3" hide-details="auto"></v-textarea>
            <v-select v-model="dialog.balance_mode" :items="balanceModeOptions" label="余额类型" variant="outlined" density="comfortable" class="mt-3" hide-details></v-select>
            <div class="d-flex align-center ga-3 mt-4">
              <label class="color-picker-label">
                <div class="color-preview" :style="{ backgroundColor: dialog.accent_color || '#1976D2' }"></div>
                <input type="color" v-model="dialog.accent_color" class="hidden-input">
              </label>
              <span class="text-body-2">{{ dialog.accent_color || '#1976D2' }}</span>
            </div>
              </div>
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
              <v-list-item prepend-icon="mdi-check-circle" title="第一行为表头：APP名称、备注、强调色"></v-list-item>
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
                      <th style="width: 20%">备注</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(item, index) in bulkDialog.parsedItems" :key="index">
                      <td class="pa-1">{{ item.name }}</td>
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
.table-wrapper { width: 90%; }
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
const iconUploading = ref(false)
const formRef = ref<any>(null)
const uploadRef = ref<HTMLInputElement | null>(null)

const dialog = reactive({
  show: false,
  isEdit: false,
  editId: 0,
  name: '',
  note: '',
  accent_color: '#1976D2',
  icon: '',
  iconPreview: '',
  balance_mode: ''
})

const deleteDialog = reactive({ show: false, id: 0, name: '' })

const balanceModeOptions = [{ title: '未设置', value: '' }, { title: '公里数', value: 'mileage' }, { title: '次数', value: 'count' }]

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
  { title: '备注', key: 'note', searchable: true },
  { title: '强调色', key: 'accent_color', sortable: false },
  { title: '模板数', key: 'template_count', sortable: true },
  { title: '余额类型', key: 'balance_mode', sortable: false },
  { title: '操作', key: 'actions', sortable: false }
]

async function onReorder(orderedIds: number[]) {
  const idToApp = new Map(apps.value.map(a => [a.id, a]))
  const reordered = orderedIds.map(id => idToApp.get(id)).filter(Boolean) as RunningApp[]
  if (reordered.length === apps.value.length) {
    apps.value.splice(0, apps.value.length, ...reordered)
  }
  try {
    await ajax(`${ApiUrl.GET_RUNNING_APPS}/sort`, {
      method: 'POST',
      body: { ordered_ids: orderedIds },
      headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
    })
  } catch (err) {
    showMsg('排序保存失败', 'error')
    loadApps()
  }
}

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
          note: String(row[1] || ''),
          accent_color: String(row[2] || '#1976D2')
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
    ['APP名称', '备注', '强调色'],
    ['校园跑', '基础跑步APP', '#1976D2'],
    ['乐跑', '', '#E53935']
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
  dialog.note = ''
  dialog.accent_color = '#1976D2'
  dialog.icon = ''
  dialog.iconPreview = ''
  dialog.balance_mode = ''
}

function openEditDialog(item: RunningApp) {
  dialog.show = true
  dialog.isEdit = true
  dialog.editId = item.id
  dialog.name = item.name
  dialog.note = item.note
  dialog.accent_color = item.accent_color || '#1976D2'
  dialog.icon = item.icon || ''
  dialog.iconPreview = item.icon || ''
  dialog.balance_mode = item.balance_mode || ''
}

async function submitApp() {
  const { valid } = await formRef.value.validate()
  if (!valid) return
  loading.value = true
  try {
    if (dialog.isEdit) {
      const res = await ajax(`${ApiUrl.UPDATE_RUNNING_APP}/${dialog.editId}`, {
        method: 'PUT',
        body: { name: dialog.name, note: dialog.note, accent_color: dialog.accent_color, icon: dialog.icon, balance_mode: dialog.balance_mode },
        headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
      })
      if (res.code === 200) { showMsg('修改成功'); dialog.show = false; loadApps() }
      else showMsg(res.msg || '修改失败', 'error')
    } else {
      const res = await ajax(ApiUrl.CREATE_RUNNING_APP, {
        method: 'POST',
        body: { name: dialog.name, note: dialog.note, accent_color: dialog.accent_color, icon: dialog.icon, balance_mode: dialog.balance_mode },
        headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
      })
      if (res.code === 200) { showMsg('创建成功'); dialog.show = false; loadApps() }
      else showMsg(res.msg || '创建失败', 'error')
    }
  } catch (err) {
    showMsg('请求失败，请稍后再试', 'error')
  } finally { loading.value = false }
}

async function handleIconUpload(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  const allowedTypes = ['image/webp', 'image/jpeg', 'image/png', 'image/gif', 'image/heic', 'image/heif']
  if (!allowedTypes.includes(file.type)) {
    showMsg('不支持的图片格式，仅支持 WebP/JPEG/PNG/GIF/HEIC', 'error')
    return
  }
  if (file.size > 5 * 1024 * 1024) {
    showMsg('图片大小不能超过 5MB', 'error')
    return
  }
  iconUploading.value = true
  try {
    const res = await ajax(ApiUrl.UPLOAD_IMAGE, {
      method: 'POST',
      isFormData: true,
      body: { file },
      headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
    })
    if (res.code === 200) {
      dialog.icon = res.data.url
      dialog.iconPreview = res.data.url
    } else {
      showMsg(res.msg || '上传失败', 'error')
    }
  } catch {
    showMsg('上传失败，请稍后再试', 'error')
  } finally {
    iconUploading.value = false
    input.value = ''
  }
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
