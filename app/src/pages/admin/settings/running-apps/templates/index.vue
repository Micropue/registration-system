<template>
  <v-container fluid class="pa-4">
    <div class="mb-4">
      <div class="d-flex align-center" style="align-items: center;">
        <v-icon color="primary" size="28" class="mr-2">mdi-file-document-multiple-outline</v-icon>
        <h1 class="text-h4 mt-0 mb-0">模板管理</h1>
      </div>
      <div class="d-flex align-center mt-1">
        <v-icon size="14" color="grey" class="mr-1">mdi-run-fast</v-icon>
        <span class="text-body-2 text-medium-emphasis">
          正在为 <b class="text-primary">「{{ appName || '加载中...' }}」</b> 配置模板版本
        </span>
      </div>
    </div>

    <div class="d-flex justify-end mb-3">
      <v-btn color="secondary" elevation="2" prepend-icon="mdi-content-copy" @click="openCloneDrawer">模板复刻</v-btn>
      <v-btn color="primary" elevation="2" prepend-icon="mdi-plus" class="ml-2" @click="openCreateDialog">新建模板</v-btn>
    </div>

    <app-data-table
      :headers="templateHeaders"
      :items="templates"
      :total-items="templates.length"
      :loading="loading"
      client-side
    >
      <template v-slot:item.version_name="{ item }">
        <span class="font-weight-medium">{{ item.version_name }}</span>
      </template>
      <template v-slot:item.field_count="{ item }">
        <v-chip size="small" variant="tonal" color="primary">{{ item.fields?.length || 0 }}</v-chip>
      </template>
      <template v-slot:item.create_time="{ item }">
        {{ formatDate(item.create_time) }}
      </template>
      <template v-slot:item.actions="{ item }">
        <div class="d-flex ga-1">
          <v-btn variant="tonal" rounded size="small" color="primary" @click="openEditDialog(item)">编辑</v-btn>
          <v-btn variant="tonal" rounded size="small" color="error" @click="confirmDeleteDialog(item)">删除</v-btn>
        </div>
      </template>
    </app-data-table>

    <!-- 新建模板 Dialog -->
    <v-dialog v-model="createDialog.show" max-width="400">
      <v-card rounded="lg">
        <v-card-title class="d-flex align-center">
          <v-icon color="primary" class="mr-2">mdi-plus-box</v-icon>
          新建模板
        </v-card-title>
        <v-card-text>
          <v-text-field
            v-model="createDialog.versionName"
            label="版本名称"
            placeholder="例如：v1.0、标准版"
            variant="outlined"
            density="comfortable"
            hide-details
            @keyup.enter="doCreate"
          ></v-text-field>
        </v-card-text>
        <v-card-actions class="pa-4 pt-0">
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="createDialog.show = false">取消</v-btn>
          <v-btn color="primary" variant="flat" :loading="saving" @click="doCreate">确认创建</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 编辑模板字段 Dialog -->
    <v-dialog v-model="editorDialog.show" max-width="800" persistent scrollable>
      <v-card rounded="lg">
        <v-card-title class="d-flex align-center border-bottom pa-4">
          <v-icon color="primary" class="mr-2">mdi-pencil-box</v-icon>
          <span class="text-h6">编辑模板字段</span>
          <v-chip class="ml-3" color="primary" variant="tonal" size="small">
            {{ editorDialog.versionName || currentTemplate?.version_name }}
          </v-chip>
          <v-spacer></v-spacer>
          <v-btn icon="mdi-close" variant="text" density="comfortable" @click="editorDialog.show = false"></v-btn>
        </v-card-title>

        <v-card-text class="pa-4 pa-sm-5" style="max-height: 60vh;">
          <v-text-field v-model="editorDialog.editVersionName" label="模板版本名称" variant="outlined" density="comfortable"
            :rules="[v => !!v || '版本名称必填']" class="mb-4" hide-details="auto"></v-text-field>

          <div v-if="fields.length === 0" class="d-flex flex-column align-center py-8">
            <v-icon size="48" color="grey-lighten-1">mdi-playlist-remove</v-icon>
            <div class="text-body-2 text-grey mt-3">暂无字段，点击下方按钮添加</div>
          </div>

          <draggable v-else v-model="fields" item-key="_key" handle=".drag-handle" ghost-class="ghost-card" animation="220">
            <template #item="{ element, index }">
              <v-card class="mb-3 field-card" variant="outlined" rounded="lg">
                <div class="d-flex align-center pa-3">
                  <v-icon class="mr-2 drag-handle" color="grey-lighten-1" size="24">mdi-drag</v-icon>
                  <div class="d-flex flex-column flex-grow-1 overflow-hidden mr-2">
                    <span class="text-subtitle-1 font-weight-bold text-truncate">
                      {{ element.label || '未命名字段' }}
                    </span>
                    <div class="d-flex align-center gap-1 mt-1">
                      <v-chip size="x-small" color="primary" variant="tonal">
                        <v-icon start size="x-small" class="mr-1">{{ getFieldIcon(element.type) }}</v-icon>
                        {{ fieldTypeLabel(element.type) }}
                      </v-chip>
                      <v-chip v-if="element.required" size="x-small" color="error" variant="flat">必填</v-chip>
                    </div>
                  </div>
                  <div class="d-flex align-center gap-1 flex-shrink-0">
                    <v-btn icon="mdi-pencil-outline" size="x-small" variant="text" color="primary" @click="editField(index)"></v-btn>
                    <v-btn icon="mdi-trash-can-outline" size="x-small" variant="text" color="error" @click="openDeleteFieldConfirm(index)"></v-btn>
                  </div>
                </div>
              </v-card>
            </template>
          </draggable>

          <v-btn
            block
            color="secondary"
            variant="tonal"
            prepend-icon="mdi-plus"
            class="mt-3"
            @click="addField"
          >
            添加字段
          </v-btn>
        </v-card-text>

        <v-divider></v-divider>

        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="editorDialog.show = false">取消</v-btn>
          <v-btn color="primary" variant="flat" :loading="saving" @click="saveFields">保存配置</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 字段添加/编辑 子 Dialog -->
    <v-dialog v-model="fieldDialog.show" max-width="600" persistent scrollable>
      <v-card rounded="lg">
        <v-card-title class="d-flex align-center border-bottom pa-4">
          <v-icon color="primary" class="mr-2">
            {{ fieldDialog.isEdit ? 'mdi-pencil-box' : 'mdi-plus-box' }}
          </v-icon>
          <span class="text-h6">{{ fieldDialog.isEdit ? '编辑字段' : '添加字段' }}</span>
          <v-spacer></v-spacer>
          <v-btn icon="mdi-close" variant="text" density="comfortable" @click="fieldDialog.show = false"></v-btn>
        </v-card-title>

        <v-card-text class="pa-4" style="max-height: 60vh;">
          <v-row>
            <v-col cols="12" sm="8">
              <v-text-field
                v-model="editFieldData.label"
                label="字段名称 *"
                placeholder="例如：姓名"
                variant="outlined"
                density="comfortable"
                hide-details="auto"
              ></v-text-field>
            </v-col>
            <v-col cols="12" sm="4">
              <v-select
                v-model="editFieldData.type"
                :items="fieldTypes"
                label="字段类型"
                item-title="label"
                item-value="value"
                variant="outlined"
                density="comfortable"
                hide-details
              >
                <template #selection>
                  <div class="d-flex align-center">
                    <v-icon :icon="getFieldIcon(editFieldData.type)" size="small" class="mr-2" color="primary"></v-icon>
                    <span>{{ fieldTypeLabel(editFieldData.type) }}</span>
                  </div>
                </template>
              </v-select>
            </v-col>

            <v-col cols="12" class="pt-2 pb-2">
              <v-sheet class="pa-3 bg-surface rounded-lg d-flex align-center">
                <span class="text-subtitle-2 mr-4">必填项</span>
                <v-switch v-model="editFieldData.required" color="error" hide-details density="compact"></v-switch>
                <v-divider vertical class="mx-4" length="24"></v-divider>
                <span class="text-subtitle-2 mr-4">自定义复制按钮</span>
                <v-switch v-model="editFieldData.copyable" color="primary" hide-details density="compact"></v-switch>
              </v-sheet>
            </v-col>

            <v-col cols="12" v-if="!isOptionType(editFieldData.type) && !isRangeType(editFieldData.type)">
              <v-text-field
                v-model="editFieldData.default"
                label="默认填充内容"
                placeholder="选填"
                variant="outlined"
                density="comfortable"
                hide-details
                :type="editFieldData.type"
              ></v-text-field>
            </v-col>

            <v-col cols="12" v-if="isRangeType(editFieldData.type)">
              <div class="text-subtitle-2 mb-2">默认范围设置</div>
              <v-row dense>
                <v-col cols="6">
                  <v-text-field
                    v-model="editFieldData.default[0]"
                    :label="editFieldData.type === 'number-range' ? '最小值' : '开始'"
                    :type="editFieldData.type === 'number-range' ? 'number' : editFieldData.type === 'date-range' ? 'date' : 'time'"
                    variant="outlined"
                    density="comfortable"
                    hide-details="auto"
                  ></v-text-field>
                </v-col>
                <v-col cols="6">
                  <v-text-field
                    v-model="editFieldData.default[1]"
                    :label="editFieldData.type === 'number-range' ? '最大值' : '结束'"
                    :type="editFieldData.type === 'number-range' ? 'number' : editFieldData.type === 'date-range' ? 'date' : 'time'"
                    variant="outlined"
                    density="comfortable"
                    hide-details="auto"
                  ></v-text-field>
                </v-col>
              </v-row>
            </v-col>

            <v-col cols="12" v-if="isOptionType(editFieldData.type)">
              <v-card variant="outlined" rounded="lg">
                <v-card-title class="bg-surface text-subtitle-2 py-2 px-3 d-flex align-center">
                  <v-icon size="small" class="mr-2">mdi-format-list-bulleted</v-icon>
                  选项列表
                  <v-spacer></v-spacer>
                  <v-btn size="small" color="primary" variant="elevated" prepend-icon="mdi-plus" @click="addOption">
                    新增选项
                  </v-btn>
                </v-card-title>
                <v-divider></v-divider>
                <v-card-text class="pa-3">
                  <div v-if="!editFieldData.options || editFieldData.options.length === 0" class="text-center py-4 text-body-2 text-grey">
                    暂无选项，请点击右上角新增
                  </div>
                  <div
                    v-for="(opt, i) in editFieldData.options"
                    :key="i"
                    class="d-flex align-center mb-3 gap-2"
                  >
                    <div class="d-flex flex-grow-1 gap-2">
                      <v-text-field
                        v-model="opt.label"
                        label="显示文本"
                        placeholder="如：男"
                        density="comfortable"
                        variant="outlined"
                        hide-details
                      ></v-text-field>
                      <v-text-field
                        v-model="opt.value"
                        label="数据值"
                        placeholder="如：male"
                        density="comfortable"
                        variant="outlined"
                        hide-details
                      ></v-text-field>
                    </div>
                    <v-btn
                      icon="mdi-delete-outline"
                      size="small"
                      variant="text"
                      color="error"
                      @click="removeOption(i)"
                    ></v-btn>
                  </div>

                  <div class="mt-4" v-if="editFieldData.options && editFieldData.options.length > 0">
                    <v-select
                      v-model="editFieldData.default"
                      :items="editFieldData.options"
                      item-title="label"
                      item-value="value"
                      label="默认选中项"
                      variant="outlined"
                      density="comfortable"
                      clearable
                      hint="可选，不选则默认无选中项"
                      persistent-hint
                    ></v-select>
                  </div>
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>
        </v-card-text>

        <v-divider></v-divider>

        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="fieldDialog.show = false">取消</v-btn>
          <v-btn
            color="primary"
            variant="flat"
            :disabled="!editFieldData.label"
            @click="saveField"
          >
            确认保存
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 删除字段确认 Dialog -->
    <v-dialog v-model="deleteFieldDialog" max-width="400">
      <v-card rounded="lg">
        <v-card-title class="d-flex align-center text-error pa-4 pb-2">
          <v-icon color="error" class="mr-2">mdi-alert-circle</v-icon>
          确认删除字段
        </v-card-title>
        <v-card-text class="pa-4 pt-0">
          确定要删除该字段吗？此操作不可撤销。
        </v-card-text>
        <v-card-actions class="pa-4 pt-0">
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="deleteFieldDialog = false">取消</v-btn>
          <v-btn color="error" variant="flat" @click="confirmDeleteField">确认删除</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 删除模板确认 Dialog -->
    <v-dialog v-model="deleteDialog.show" max-width="400">
      <v-card rounded="lg">
        <v-card-title class="d-flex align-center text-error pa-4 pb-2">
          <v-icon color="error" class="mr-2">mdi-alert-circle</v-icon>
          确认删除模板
        </v-card-title>
        <v-card-text class="pa-4 pt-0">
          确定要删除模板 <strong>{{ deleteDialog.name }}</strong> 吗？此操作不可撤销。
        </v-card-text>
        <v-card-actions class="pa-4 pt-0">
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="deleteDialog.show = false">取消</v-btn>
          <v-btn color="error" variant="flat" :loading="saving" @click="doDelete">确认删除</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 模板复刻确认 Dialog -->
    <v-dialog v-model="cloneDialog.show" max-width="400">
      <v-card rounded="lg">
        <v-card-title class="d-flex align-center">
          <v-icon color="primary" class="mr-2">mdi-content-copy</v-icon>
          模板复刻
        </v-card-title>
        <v-card-text>
          <div class="text-body-2 text-medium-emphasis mb-3">
            将从 <b>{{ cloneDialog.sourceApp }}</b> 复刻模板 <br><b>{{ cloneDialog.sourceName }}</b> 到当前 APP
          </div>
          <v-text-field
            v-model="cloneDialog.versionName"
            label="新版本名称"
            variant="outlined"
            density="comfortable"
            hide-details
            @keyup.enter="doClone"
          ></v-text-field>
        </v-card-text>
        <v-card-actions class="pa-4 pt-0">
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="cloneDialog.show = false">取消</v-btn>
          <v-btn color="primary" variant="flat" :loading="saving" @click="doClone">确认复刻</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-snackbar v-model="snackbar.show" :color="snackbar.color" timeout="3000">
      {{ snackbar.text }}
    </v-snackbar>

    <!-- 模板复刻 选择源模板 Dialog -->
    <v-dialog v-model="pickerDialog" max-width="500" scrollable>
      <v-card rounded="lg" max-height="75vh">
        <v-card-title class="d-flex align-center pa-4">
          <v-icon color="primary" class="mr-2">mdi-content-copy</v-icon>
          <span class="text-h6">模板复刻</span>
          <v-spacer></v-spacer>
          <v-btn icon="mdi-close" variant="text" size="small" @click="pickerDialog = false"></v-btn>
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text class="pa-0">
          <v-expansion-panels v-model="expandedApp" variant="accordion" v-if="cloneApps.length > 0">
            <v-expansion-panel
              v-for="app in cloneApps"
              :key="app.uid"
              :value="app.uid"
            >
              <v-expansion-panel-title>
                <div class="d-flex align-center w-100">
                  <v-icon size="20" class="me-2" :color="app.accent_color || 'primary'">
                    {{ app.icon || 'mdi-run' }}
                  </v-icon>
                  <span class="font-weight-medium">{{ app.name }}</span>
                  <v-chip size="x-small" variant="tonal" class="ml-2" color="grey">
                    {{ app.template_count || 0 }}
                  </v-chip>
                </div>
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <div v-if="loadingApps[app.uid]" class="d-flex justify-center py-6">
                  <v-progress-circular indeterminate size="24" color="primary"></v-progress-circular>
                </div>
                <div v-else-if="!loadedTemplates[app.uid] || loadedTemplates[app.uid].length === 0"
                  class="text-center py-6 text-body-2 text-grey">
                  暂无模板
                </div>
                <v-list v-else density="compact" nav>
                  <v-list-item
                    v-for="tpl in loadedTemplates[app.uid]"
                    :key="tpl.uid"
                    @click="selectTemplate(tpl, app)"
                    rounded="lg"
                    class="mb-1"
                  >
                    <template v-slot:prepend>
                      <v-icon size="18" color="grey">mdi-file-document-outline</v-icon>
                    </template>
                    <v-list-item-title class="text-body-2">{{ tpl.version_name }}</v-list-item-title>
                    <v-list-item-subtitle class="text-caption">
                      {{ tpl.fields?.length || 0 }} 个字段
                    </v-list-item-subtitle>
                    <template v-slot:append>
                      <v-icon size="16" color="primary">mdi-content-copy</v-icon>
                    </template>
                  </v-list-item>
                </v-list>
              </v-expansion-panel-text>
            </v-expansion-panel>
          </v-expansion-panels>
          <div v-else class="pa-6 text-center text-grey text-body-2">
            <v-progress-circular indeterminate size="24" color="primary" class="mb-2"></v-progress-circular>
            <div>加载 APP 列表中...</div>
          </div>
        </v-card-text>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<style scoped>
.gap-1 { gap: 4px; }
.gap-2 { gap: 8px; }
.border-bottom { border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08); }
.ghost-card { opacity: 0.4; background: rgb(var(--v-theme-surface)); }
.field-card { transition: box-shadow 0.2s; }
.field-card:hover { box-shadow: 0 2px 8px rgba(var(--v-theme-on-surface), 0.08); }
</style>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import draggable from 'vuedraggable'
import AppDataTable from '@/components/AppDataTable.vue'
import { ajax } from '@/api/ajax'
import { cookie } from '@/api/cookie'

interface FieldOption {
  label: string
  value: string
}

interface Field {
  _key?: string
  id?: string
  label: string
  type: string
  required: boolean
  copyable: boolean
  default: string | string[]
  options: FieldOption[]
}

interface Template {
  uid: string
  version_name: string
  fields: Field[]
  create_time: string
}

const route = useRoute()
const appUid = route.params.appUid as string
const appName = ref('')
const authHeaders = () => ({ 'Authorization': `Bearer ${cookie.get('token') || ''}` })

const templates = ref<Template[]>([])
const currentTemplate = ref<Template | null>(null)
const fields = ref<Field[]>([])
const loading = ref(false)
const saving = ref(false)

const snackbar = reactive({ show: false, text: '', color: 'success' })

const createDialog = reactive({ show: false, versionName: '' })

const editorDialog = reactive({ show: false, versionName: '', editVersionName: '' })

const fieldDialog = reactive({ show: false, isEdit: false, editIndex: -1 })

const deleteFieldDialog = ref(false)
const deleteFieldIndex = ref(-1)

const deleteDialog = reactive({ show: false, uid: '', name: '' })

const editFieldData = reactive<Field>({
  label: '',
  type: 'text',
  required: false,
  copyable: false,
  default: '',
  options: []
})

function showMsg(text: string, color: string = 'success') {
  snackbar.text = text
  snackbar.color = color
  snackbar.show = true
}

function formatDate(iso: string) {
  if (!iso) return ''
  return new Date(iso).toLocaleString('zh-CN')
}

const templateHeaders = [
  { title: '版本名称', key: 'version_name', sortable: true },
  { title: '字段数量', key: 'field_count', sortable: false },
  { title: '创建时间', key: 'create_time', sortable: true },
  { title: '操作', key: 'actions', sortable: false }
]

const fieldTypes = [
  { label: '单行文本', value: 'text', icon: 'mdi-format-text' },
  { label: '多行文本', value: 'textarea', icon: 'mdi-text-box-outline' },
  { label: '日期选择', value: 'date', icon: 'mdi-calendar-blank-outline' },
  { label: '日期范围', value: 'date-range', icon: 'mdi-calendar-range-outline' },
  { label: '数值', value: 'number', icon: 'mdi-sort-numeric-variant' },
  { label: '数字范围', value: 'number-range', icon: 'mdi-numeric' },
  { label: '时间范围', value: 'time-range', icon: 'mdi-clock-time-eight-outline' },
  { label: '单选按钮', value: 'radio', icon: 'mdi-radiobox-marked' },
  { label: '复选框组', value: 'checkbox', icon: 'mdi-checkbox-marked-outline' },
  { label: '下拉菜单', value: 'select', icon: 'mdi-form-dropdown' }
]

function getFieldIcon(type: string) {
  const t = fieldTypes.find(f => f.value === type)
  return t ? t.icon : 'mdi-form-textbox'
}

function fieldTypeLabel(type: string) {
  const t = fieldTypes.find(f => f.value === type)
  return t ? t.label : type
}

function isOptionType(type: string) {
  return ['radio', 'checkbox', 'select'].includes(type)
}

function isRangeType(type: string) {
  return ['date-range', 'number-range', 'time-range'].includes(type)
}

watch(() => editFieldData.type, (newType) => {
  if (isRangeType(newType)) {
    if (!Array.isArray(editFieldData.default)) {
      editFieldData.default = ['', '']
    }
  } else if (isOptionType(newType)) {
    if (Array.isArray(editFieldData.default)) {
      editFieldData.default = ''
    }
    if (!editFieldData.options) {
      editFieldData.options = []
    }
  } else {
    if (Array.isArray(editFieldData.default)) {
      editFieldData.default = ''
    }
  }
})

function genKey() {
  return Math.random().toString(36).substring(2, 9) + Date.now().toString(36)
}

// ===== Template CRUD =====

async function loadTemplates() {
  loading.value = true
  try {
    const res = await ajax<Template[]>(`/api/admin/settings/running-apps/${appUid}/templates`, {
      method: 'GET',
      headers: authHeaders()
    })
    if (res.code === 200) {
      templates.value = res.data || []
    } else {
      showMsg(res.msg || '加载失败', 'error')
    }
  } catch {
    showMsg('请求失败，请稍后再试', 'error')
  } finally {
    loading.value = false
  }
}

function openCreateDialog() {
  createDialog.versionName = ''
  createDialog.show = true
}

async function doCreate() {
  if (!createDialog.versionName.trim()) {
    showMsg('请输入版本名称', 'error')
    return
  }
  saving.value = true
  try {
    const res = await ajax<Template>(`/api/admin/settings/running-apps/${appUid}/templates`, {
      method: 'POST',
      body: { version_name: createDialog.versionName.trim(), fields: [] },
      headers: authHeaders()
    })
    if (res.code === 200) {
      createDialog.show = false
      showMsg('模板创建成功')
      await loadTemplates()
      const created = templates.value.find(t => t.uid === res.data?.uid)
      if (created) {
        openEditDialog(created)
      }
    } else {
      showMsg(res.msg || '创建失败', 'error')
    }
  } catch {
    showMsg('请求失败，请稍后再试', 'error')
  } finally {
    saving.value = false
  }
}

function openEditDialog(tpl: Template) {
  currentTemplate.value = tpl
  fields.value = JSON.parse(JSON.stringify(tpl.fields || []))
  fields.value.forEach(f => { f._key = genKey() })
  editorDialog.versionName = tpl.version_name
  editorDialog.editVersionName = tpl.version_name
  editorDialog.show = true
}

async function saveFields() {
  if (!currentTemplate.value) return
  saving.value = true
  try {
    const cleanFields = JSON.parse(JSON.stringify(fields.value))
    cleanFields.forEach((f: any) => delete f._key)
    const res = await ajax(
      `/api/admin/settings/running-apps/${appUid}/templates/${currentTemplate.value.uid}`,
      {
        method: 'PUT',
        body: { version_name: editorDialog.editVersionName || currentTemplate.value.version_name, fields: cleanFields },
        headers: authHeaders()
      }
    )
    if (res.code === 200) {
      showMsg('配置已保存')
      editorDialog.show = false
      await loadTemplates()
    } else {
      showMsg(res.msg || '保存失败', 'error')
    }
  } catch {
    showMsg('请求失败，请稍后再试', 'error')
  } finally {
    saving.value = false
  }
}

function confirmDeleteDialog(tpl: Template) {
  deleteDialog.uid = tpl.uid
  deleteDialog.name = tpl.version_name
  deleteDialog.show = true
}

async function doDelete() {
  saving.value = true
  try {
    const res = await ajax(`/api/admin/settings/running-apps/${appUid}/templates/${deleteDialog.uid}`, {
      method: 'DELETE',
      headers: authHeaders()
    })
    if (res.code === 200) {
      showMsg('删除成功')
      deleteDialog.show = false
      await loadTemplates()
    } else {
      showMsg(res.msg || '删除失败', 'error')
    }
  } catch {
    showMsg('请求失败，请稍后再试', 'error')
  } finally {
    saving.value = false
  }
}

// ===== Field Editor =====

function addField() {
  fieldDialog.isEdit = false
  fieldDialog.editIndex = -1
  Object.assign(editFieldData, {
    label: '',
    type: 'text',
    required: false,
    copyable: false,
    default: '',
    options: []
  })
  fieldDialog.show = true
}

function editField(index: number) {
  fieldDialog.isEdit = true
  fieldDialog.editIndex = index
  Object.assign(editFieldData, JSON.parse(JSON.stringify(fields.value[index])))
  fieldDialog.show = true
}

function saveField() {
  if (!editFieldData.label) {
    showMsg('请输入字段名称', 'error')
    return
  }
  if (isOptionType(editFieldData.type)) {
    editFieldData.options = editFieldData.options?.filter(
      (o: FieldOption) => o.label.trim() !== '' && o.value.trim() !== ''
    ) || []
    if (editFieldData.options.length === 0) {
      showMsg('选项类字段至少需要一个有效选项', 'error')
      return
    }
  } else {
    editFieldData.options = []
  }

  const saved = JSON.parse(JSON.stringify(editFieldData))
  saved._key = genKey()

  if (fieldDialog.editIndex === -1) {
    fields.value.push(saved)
  } else {
    fields.value[fieldDialog.editIndex] = saved
  }

  fieldDialog.show = false
}

function openDeleteFieldConfirm(index: number) {
  deleteFieldIndex.value = index
  deleteFieldDialog.value = true
}

function confirmDeleteField() {
  if (deleteFieldIndex.value >= 0) {
    fields.value.splice(deleteFieldIndex.value, 1)
    deleteFieldIndex.value = -1
    deleteFieldDialog.value = false
    showMsg('字段已删除', 'info')
  }
}

function addOption() {
  if (!editFieldData.options) editFieldData.options = []
  editFieldData.options.push({ label: '', value: '' })
}

function removeOption(i: number) {
  editFieldData.options.splice(i, 1)
}

onMounted(async () => {
  await loadAppName()
  loadTemplates()
})

async function loadAppName() {
  try {
    const res = await ajax<any[]>('/api/admin/settings/running-apps', { headers: authHeaders() })
    if (res.code === 200) {
      const app = res.data.find((a: any) => String(a.uid) === String(appUid))
      if (app) appName.value = app.name
    }
  } catch { /* ignore */ }
}

// ===== 模板复刻 =====

interface RunningApp {
  uid: string
  name: string
  icon: string
  accent_color: string
  template_count: number
}

const pickerDialog = ref(false)
const expandedApp = ref('')
watch(expandedApp, (uid) => {
  if (uid) loadTemplatesForApp(uid)
})
const cloneApps = ref<RunningApp[]>([])
const loadedTemplates = ref<Record<string, Template[]>>({})
const loadingApps = ref<Record<string, boolean>>({})
const cloneDialog = reactive({
  show: false,
  versionName: '',
  sourceUid: '',
  sourceName: '',
  sourceApp: '',
})

async function openCloneDrawer() {
  pickerDialog.value = true
  expandedApp.value = ''
  if (cloneApps.value.length > 0) return
  try {
    const res = await ajax<RunningApp[]>('/api/admin/settings/running-apps', { headers: authHeaders() })
    if (res.code === 200) {
      cloneApps.value = res.data || []
    }
  } catch { /* ignore */ }
}

async function loadTemplatesForApp(uid: string) {
  if (loadedTemplates.value[uid] || loadingApps.value[uid]) return
  loadingApps.value[uid] = true
  try {
    const res = await ajax<Template[]>(`/api/admin/settings/running-apps/${uid}/templates`, {
      headers: authHeaders()
    })
    if (res.code === 200) {
      loadedTemplates.value[uid] = res.data || []
    }
  } catch { /* ignore */ }
  finally {
    loadingApps.value[uid] = false
  }
}

function selectTemplate(tpl: Template, app: RunningApp) {
  cloneDialog.sourceUid = tpl.uid
  cloneDialog.sourceName = tpl.version_name
  cloneDialog.sourceApp = app.name
  cloneDialog.versionName = `复刻 - ${tpl.version_name}`
  cloneDialog.show = true
}

async function doClone() {
  if (!cloneDialog.versionName.trim()) {
    showMsg('请输入版本名称', 'error')
    return
  }
  saving.value = true
  try {
    const res = await ajax(`/api/admin/settings/running-apps/${appUid}/templates/clone`, {
      method: 'POST',
      body: { source_uid: cloneDialog.sourceUid, version_name: cloneDialog.versionName.trim() },
      headers: authHeaders()
    })
    if (res.code === 200) {
      cloneDialog.show = false
      pickerDialog.value = false
      showMsg('模板复刻成功')
      await loadTemplates()
    } else {
      showMsg(res.msg || '复刻失败', 'error')
    }
  } catch {
    showMsg('请求失败，请稍后再试', 'error')
  } finally {
    saving.value = false
  }
}
</script>
