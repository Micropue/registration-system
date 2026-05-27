<template>
  <div class="sign-page px-3 px-sm-6 py-4 py-sm-6 d-flex flex-column align-center">
    <div class="table-wrapper" style="width: 90%;">
    <!-- 顶部操作区 -->
    <div class="d-flex justify-space-between align-center mb-4">
      <h1 class="text-h5 text-sm-h4">数据登记</h1>
      <v-btn color="primary" size="default" prepend-icon="mdi-plus" @click="openNewDialog" class="text-none">
        新建登记
      </v-btn>
    </div>

    <!-- 新建登记表单 Dialog -->
    <v-dialog v-model="formDialog.show" max-width="700" persistent scrollable>
      <v-card class="pa-4">
        <v-card-title class="d-flex align-center">
          <span class="text-h5">新建登记</span>
          <v-spacer></v-spacer>
          <v-avatar v-if="selectedAppIcon" size="22" rounded class="me-1">
            <v-img :src="selectedAppIcon" cover></v-img>
          </v-avatar>
          <v-chip size="small" color="primary" label>{{ selectedApp }}</v-chip>
        </v-card-title>
        <v-divider class="mb-4"></v-divider>
        <v-card-text>
          <div class="mb-4">
            <div class="text-subtitle-2 mb-2 text-medium-emphasis">优先级</div>
            <v-btn-toggle v-model="priority" mandatory density="comfortable" variant="outlined" divided color="primary">
              <v-btn value="low" size="small">低</v-btn>
              <v-btn value="medium" size="small">中</v-btn>
              <v-btn value="high" size="small">高</v-btn>
            </v-btn-toggle>
          </div>

          <div v-if="isLoading" class="d-flex flex-column align-center py-6">
            <v-progress-circular indeterminate color="primary" size="40" width="4"></v-progress-circular>
          </div>

          <v-form v-else ref="formRef" v-model="isFormValid">
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
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="tonal" @click="cancelForm">取消</v-btn>
          <v-btn color="primary" size="large" rounded="pill" class="font-weight-bold"
            :loading="isSubmitting" :disabled="!isFormValid || isLoading" @click="openConfirm">
            提交登记
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 选择APP的Dialog -->
    <v-dialog v-model="newDialog.show" max-width="500" persistent>
      <v-card class="pa-4">
        <v-card-title class="text-h5">新建登记</v-card-title>
        <v-card-text>
          <v-form ref="selectFormRef" v-model="selectFormValid" @submit.prevent="goSelectTemplate">
            <v-autocomplete v-model="newDialog.app" :items="runningApps" item-title="name" item-value="name"
              label="搜索跑步APP" :rules="[v => !!v || '请选择跑步APP']"
              variant="outlined" density="comfortable" hide-no-data
              :item-props="(item: any) => item.icon ? { prependAvatar: item.icon } : { prependIcon: 'mdi-run-fast' }" />
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="tonal" @click="newDialog.show = false">取消</v-btn>
          <v-btn color="primary" variant="flat" :disabled="!selectFormValid" :loading="loadingTemplates" @click="goSelectTemplate">
            下一步
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 选择模板版本的Dialog -->
    <v-dialog v-model="templateDialog.show" max-width="500" persistent>
      <v-card class="pa-4">
        <v-card-title class="text-h5">选择模板版本</v-card-title>
        <v-card-subtitle>
          <div class="d-flex align-center ga-2">
            <v-avatar v-if="selectedAppIcon" size="24" rounded>
              <v-img :src="selectedAppIcon" cover></v-img>
            </v-avatar>
            <span>已选APP：{{ selectedApp }}</span>
          </div>
        </v-card-subtitle>
        <v-card-text>
          <v-form ref="templateFormRef" v-model="templateFormValid">
            <v-autocomplete v-model="templateDialog.uid" :items="appTemplates" item-title="version_name" item-value="uid"
              label="选择模板版本" :rules="[v => !!v || '请选择模板版本']"
              variant="outlined" density="comfortable" hide-no-data
              :item-props="(item: any) => ({ subtitle: `${item.fields?.length || 0} 个字段` })" />
            <div v-if="appTemplates.length === 0" class="text-center py-4 text-medium-emphasis">
              该APP暂无可用模板，请联系管理员配置
            </div>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="tonal" @click="templateDialog.show = false">取消</v-btn>
          <v-btn color="primary" variant="flat" :disabled="!templateFormValid || appTemplates.length === 0" @click="isResubmitMode ? startResubmitRegistration() : startNewRegistration()">
            开始填写
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 跑量输入 Dialog -->
    <v-dialog v-model="amountDialog.show" max-width="400" persistent>
      <v-card class="pa-4">
        <v-card-title class="text-h5">输入{{ amountDialog.modeLabel }}</v-card-title>
        <v-card-subtitle>APP: {{ selectedApp }}</v-card-subtitle>
        <v-card-text>
          <v-text-field v-model.number="amountDialog.value" :label="amountDialog.modeLabel" type="number"
            variant="outlined" density="comfortable"
            :rules="[v => !!v || '请输入', v => v > 0 || '必须大于0']"
            hide-details></v-text-field>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="tonal" @click="amountDialog.show = false; templateDialog.show = true">返回</v-btn>
          <v-btn color="primary" variant="flat" :disabled="!amountDialog.value || amountDialog.value <= 0" :loading="amountChecking" @click="confirmAmount">继续填写</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 确认提交对话框 -->
    <v-dialog v-model="confirmDialog" max-width="400">
      <v-card class="pa-4">
        <v-card-title class="text-h6">确认提交</v-card-title>
        <v-card-text>提交后订单信息将由管理员审核，确定提交吗？</v-card-text>
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
              variant="outlined" density="comfortable" hide-no-data
              :item-props="(item: any) => item.icon ? { prependAvatar: item.icon } : { prependIcon: 'mdi-run-fast' }" />
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
          <v-avatar v-if="resubmitFormAppIcon" size="22" rounded class="me-1">
            <v-img :src="resubmitFormAppIcon" cover></v-img>
          </v-avatar>
          <v-chip size="small" color="warning" label>{{ resubmitFormDialog.app }}</v-chip>
        </v-card-title>
        <v-divider class="mb-4"></v-divider>
        <v-card-text>
          <div class="mb-4">
            <div class="text-subtitle-2 mb-2 text-medium-emphasis">优先级</div>
            <v-btn-toggle v-model="resubmitPriority" mandatory density="comfortable" variant="outlined" divided color="primary">
              <v-btn value="low" size="small">低</v-btn>
              <v-btn value="medium" size="small">中</v-btn>
              <v-btn value="high" size="small">高</v-btn>
            </v-btn-toggle>
          </div>
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

    <!-- 查看信息对话框（仅查看表单数据） -->
    <v-dialog v-model="infoDialog.show" max-width="700">
      <v-card class="pa-4">
        <v-card-title class="d-flex align-center pa-4 pb-0">
          登记信息
          <v-spacer></v-spacer>
          <v-chip v-if="infoDialogItem" :color="getStatusColor(infoDialogItem.status)" size="small" variant="tonal" class="me-2">
            {{ getStatusText(infoDialogItem.status) }}
          </v-chip>
          <v-btn variant="text" size="small" @click="infoDialog.show = false">关闭</v-btn>
        </v-card-title>
        <v-card-text class="pa-4">
          <v-table v-if="infoDialogItem" density="compact" border>
            <thead>
              <tr><th class="text-left">字段</th><th class="text-left">内容</th></tr>
            </thead>
            <tbody>
              <tr v-if="infoDialogItem.amount != null">
                <td class="font-weight-bold text-primary">跑量</td>
                <td class="font-weight-bold text-primary">{{ infoDialogItem.amount }}{{ getAmountUnit(infoDialogItem.data['跑步APP']) }}</td>
              </tr>
              <tr v-for="key in infoSortedKeys" :key="key">
                <td class="font-weight-bold">{{ key }}</td>
                <td>{{ formatValue(infoDialogItem.data[key]) }}</td>
              </tr>
            </tbody>
          </v-table>
          <v-alert v-if="infoDialogItem?.reject_reason" type="error" variant="tonal" class="mt-3" density="compact">
            <strong>驳回原因：</strong>{{ infoDialogItem.reject_reason }}
          </v-alert>
          <div class="text-caption text-medium-emphasis mt-2" v-if="infoDialogItem">
            提交时间：{{ formatDate(infoDialogItem.created_at) }}
          </div>
        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- 登记历史 -->
    <h2 class="text-h6 font-weight-bold mb-3">登记历史</h2>

    <app-data-table
      :headers="historyHeaders"
      :items="registrations"
      :total-items="totalRegistrations"
      :loading="historyLoading"
      v-model:page="currentPage"
      v-model:items-per-page="itemsPerPage"
      show-search show-filter
      search-label="搜索跑步APP/模板/状态"
      @update:options="loadHistory"
      @reset="loadHistory"
    >
      <template v-slot:item.app="{ item }">
        <div class="d-flex align-center ga-1">
          <v-avatar v-if="getAppIcon(item.data['跑步APP'])" size="22" rounded>
            <v-img :src="getAppIcon(item.data['跑步APP'])" cover></v-img>
          </v-avatar>
          <span class="font-weight-bold text-body-2">{{ item.data['跑步APP'] || '-' }}</span>
        </div>
      </template>

      <template v-slot:item.template="{ item }">
        <span class="text-body-2">{{ item.template_name || '-' }}</span>
      </template>

      <template v-slot:item.amount="{ item }">
        <span v-if="item.amount != null" class="font-weight-bold text-primary">{{ item.amount }}{{ item.amount_unit }}</span>
        <span v-else class="text-grey">-</span>
      </template>

      <template v-slot:item.created_at="{ item }">
        {{ formatDate(item.created_at) }}
      </template>

      <template v-slot:item.status="{ item }">
        <v-chip :color="getStatusColor(item.status)" size="small" variant="tonal">
          {{ getStatusText(item.status) }}
        </v-chip>
      </template>

      <template v-slot:item.priority="{ item }">
        <v-chip :color="getPriorityColor(item.priority)" size="small" variant="tonal">
          {{ getPriorityText(item.priority) }}
        </v-chip>
      </template>

      <template v-slot:item.actions="{ item }">
        <div class="d-flex ga-1">
          <v-btn variant="tonal" rounded size="small" color="primary" @click="openInfoDialog(item)">查看信息</v-btn>
          <v-badge :model-value="chatStore.chatUnreadCounts[item.id] > 0" :content="chatStore.chatUnreadCounts[item.id]" color="error" offset-x="-4" offset-y="-4">
            <v-btn variant="tonal" rounded size="small" color="secondary" @click="openDetailDialog(item)">联系管理员</v-btn>
          </v-badge>
          <v-btn v-if="item.status === 'rejected'" variant="tonal" rounded size="small" color="warning" @click="openResubmitDialog(item)">重新提交</v-btn>
        </div>
      </template>
    </app-data-table>

    <!-- 详情查看对话框（集成聊天） -->
    <v-dialog v-model="detailDialog.show" max-width="1100">
      <v-card class="detail-card">
        <v-card-title class="d-flex align-center pa-4 pb-0">
          登记详情
          <v-spacer></v-spacer>
          <v-chip :color="getStatusColor(detailDialog.status)" size="small" variant="tonal" class="me-2">
            {{ getStatusText(detailDialog.status) }}
          </v-chip>
          <v-btn variant="text" size="small" @click="handleDetailClose">关闭</v-btn>
        </v-card-title>

        <div class="detail-body">
          <div class="detail-info-panel">
            <v-card-text class="pa-4 pt-2">
              <v-table density="compact" border>
                <thead>
                  <tr><th class="text-left">字段</th><th class="text-left">内容</th></tr>
                </thead>
                <tbody>
                  <tr v-if="detailDialog.amount != null">
                    <td class="font-weight-bold text-primary">跑量</td>
                    <td class="font-weight-bold text-primary">{{ detailDialog.amount }}{{ getAmountUnit(detailDialog.data['跑步APP']) }}</td>
                  </tr>
                  <tr v-for="key in sortedDetailKeys" :key="key">
                    <td class="font-weight-bold">{{ key }}</td>
                    <td>{{ formatValue(detailDialog.data[key]) }}</td>
                  </tr>
                </tbody>
              </v-table>
              <v-alert v-if="detailDialog.rejectReason" type="error" variant="tonal" class="mt-3" density="compact">
                <strong>驳回原因：</strong>{{ detailDialog.rejectReason }}
              </v-alert>
            </v-card-text>
          </div>

          <div class="detail-chat-panel">
            <RegistrationChat
              v-if="detailDialog.id"
              :registration-uid="detailDialog.id"
              :is-admin-view="false"
              :current-username="appStore.userInfo?.username || ''"
            />
          </div>
        </div>
      </v-card>
    </v-dialog>

    <v-snackbar v-model="snackbar.show" :color="snackbar.color" timeout="3000">
      {{ snackbar.text }}
    </v-snackbar>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive, computed, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ajax } from '@/api/ajax'
import { cookie } from '@/api/cookie'
import { ApiUrl } from '@/config/api-url'
import { useAppStore } from '@/stores/app'
import { useChatStore } from '@/stores/chat'
import AppDataTable from '@/components/AppDataTable.vue'
import RegistrationChat from '@/components/RegistrationChat.vue'


interface FormField {
  label: string
  type: string
  required: boolean
  default: any
  options: { label: string; value: any }[]
}

interface AppItem {
  id: number
  uid: string
  name: string
  note: string
  icon?: string
  balance_mode?: string
}

interface RegistrationItem {
  id: string
  data: Record<string, any>
  created_at: string
  status: string
  reject_reason?: string
  priority?: string
  template_uid?: string
  amount?: number | null
}

const isLoading = ref(true)
const historyLoading = ref(false)
const appStore = useAppStore()
const chatStore = useChatStore()
const route = useRoute()
const router = useRouter()
const itemsPerPage = ref(20)
const currentPage = ref(1)
const totalRegistrations = ref(0)
const isSubmitting = ref(false)
const isFormValid = ref(false)
const formDialog = reactive({ show: false })
const priority = ref('low')
const resubmitPriority = ref('low')
const resubmitTemplateUid = ref('')
const selectedTemplate = ref('')
const isResubmitMode = ref(false)
const appTemplates = ref<any[]>([])
const loadingTemplates = ref(false)
const templateDialog = reactive({ show: false, uid: '' })
const templateFormValid = ref(false)
const templateFormRef = ref<any>(null)
const confirmDialog = ref(false)
const registrationAmount = ref<number | null>(null)
const amountChecking = ref(false)

const amountDialog = reactive({
  show: false,
  value: 0,
  get modeLabel() {
    const app = runningApps.value.find(a => a.name === selectedApp.value)
    const mode = app?.balance_mode
    return mode === 'mileage' ? '公里数' : mode === 'count' ? '次数' : '数量'
  }
})

const formRef = ref<any>(null)
const selectFormRef = ref<any>(null)
const resubmitSelectFormRef = ref<any>(null)
const resubmitFormRef = ref<any>(null)

const formFields = ref<FormField[]>([])
const formData = reactive<Record<string, any>>({})
const runningApps = ref<AppItem[]>([])
const registrations = ref<RegistrationItem[]>([])
const selectedApp = ref('')
const selectedAppIcon = computed(() => {
  const app = runningApps.value.find(a => a.name === selectedApp.value)
  return app?.icon || ''
})

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

const resubmitFormAppIcon = computed(() => {
  const app = runningApps.value.find(a => a.name === resubmitFormDialog.app)
  return app?.icon || ''
})

const detailDialog = reactive({
  show: false,
  id: '',
  data: {} as Record<string, any>,
  status: '',
  createdAt: '',
  rejectReason: '',
  amount: null as number | null,
  templateUid: ''
})

const detailTemplateFieldOrder = ref<string[]>([])

const sortedDetailKeys = computed(() => {
  const data = detailDialog.data
  const keys = Object.keys(data)
  const fieldOrder = ['跑步APP', ...detailTemplateFieldOrder.value]
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

function getPriorityColor(p: string) {
  switch (p) {
    case 'high': return 'error'
    case 'medium': return 'warning'
    default: return 'grey'
  }
}

function getPriorityText(p: string) {
  switch (p) {
    case 'high': return '高'
    case 'medium': return '中'
    default: return '低'
  }
}

const historyHeaders = [
  { title: '跑步APP', key: 'app', sortable: false, searchable: true, filterable: true },
  { title: '模板', key: 'template', sortable: false, searchable: true },
  { title: '跑量', key: 'amount', sortable: false },
  { title: '状态', key: 'status', sortable: false, filterable: true },
  { title: '优先级', key: 'priority', sortable: false, filterable: true },
  { title: '操作', key: 'actions', sortable: false },
  { title: '创建时间', key: 'created_at', sortable: true },
]

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

function getAppIcon(appName: string): string {
  const app = runningApps.value.find(a => a.name === appName)
  return app?.icon || ''
}

function getAmountUnit(appName: string | undefined): string {
  if (!appName) return ''
  const app = runningApps.value.find(a => a.name === appName)
  if (app?.balance_mode === 'mileage') return ' 公里'
  if (app?.balance_mode === 'count') return ' 次'
  return ''
}

async function fetchConfig() {
  isLoading.value = true
  try {
    const appsRes = await ajax<AppItem[]>(ApiUrl.GET_PUBLIC_RUNNING_APPS)
    if (appsRes.code === 200) runningApps.value = appsRes.data
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

function openNewDialog() {
  newDialog.app = ''
  newDialog.show = true
  nextTick(() => {
    selectFormRef.value?.resetValidation()
  })
}

async function loadAppTemplates(appName: string) {
  loadingTemplates.value = true
  const app = runningApps.value.find(a => a.name === appName)
  if (!app) { loadingTemplates.value = false; return }
  try {
    const res = await ajax<any[]>(`${ApiUrl.GET_PUBLIC_APP_TEMPLATES}/${app.uid}/templates`)
    if (res.code === 200) appTemplates.value = res.data || []
    else appTemplates.value = []
  } catch { appTemplates.value = [] }
  finally { loadingTemplates.value = false }
}

async function goSelectTemplate() {
  if (!newDialog.app) return
  isResubmitMode.value = false
  selectedApp.value = newDialog.app
  await loadAppTemplates(newDialog.app)
  if (appTemplates.value.length === 0) {
    showMsg('该APP暂无可用模板', 'error')
    return
  }
  newDialog.show = false
  templateDialog.uid = ''
  templateDialog.show = true
  nextTick(() => {
    templateFormRef.value?.resetValidation()
  })
}

function startNewRegistration() {
  if (!templateDialog.uid) return
  const tpl = appTemplates.value.find(t => t.uid === templateDialog.uid)
  if (!tpl) return
  selectedTemplate.value = templateDialog.uid
  formFields.value = tpl.fields || []
  templateDialog.show = false
  const app = runningApps.value.find(a => a.name === selectedApp.value)
  if (app?.balance_mode) {
    amountDialog.value = 0
    amountDialog.show = true
  } else {
    registrationAmount.value = null
    initFormData()
    formDialog.show = true
  }
}

async function confirmAmount() {
  if (!amountDialog.value || amountDialog.value <= 0) return
  const app = runningApps.value.find(a => a.name === selectedApp.value)
  if (app) {
    amountChecking.value = true
    try {
      const res = await ajax<any[]>(ApiUrl.GET_USER_BALANCES, {
        headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
      })
      if (res.code === 200) {
        const bal = res.data.find((b: any) => b.app_uid === app.uid)
        const currentBalance = bal?.balance ?? 0
        const mode = app.balance_mode
        const unit = mode === 'mileage' ? '公里' : mode === 'count' ? '次' : ''
        if (currentBalance < amountDialog.value) {
          showMsg(`${selectedApp.value} 余额不足（当前余额：${currentBalance}${unit}，需要：${amountDialog.value}${unit}）`, 'error')
          amountChecking.value = false
          return
        }
      }
    } catch (e) { /* ignore */ }
    finally { amountChecking.value = false }
  }
  registrationAmount.value = amountDialog.value
  amountDialog.show = false
  if (isResubmitMode.value) {
    fillResubmitForm()
  } else {
    initFormData()
    formDialog.show = true
    nextTick(() => {
      formRef.value?.resetValidation()
    })
  }
}

function cancelForm() {
  formDialog.show = false
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
  const submissionData: Record<string, any> = {
    跑步APP: selectedApp.value,
    priority: priority.value,
    template_uid: selectedTemplate.value,
    ...formData
  }
  if (registrationAmount.value != null) {
    submissionData.amount = registrationAmount.value
  }
  try {
    const res = await ajax('/api/registrations', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
      body: submissionData
    })
    if (res.code === 200) {
      confirmDialog.value = false
      formDialog.show = false
      selectedApp.value = ''
      showMsg('登记提交成功')
      currentPage.value = 1
      loadHistory({ page: 1, itemsPerPage: itemsPerPage.value })
    } else {
      showMsg(res.msg, 'error')
    }
  } catch (error) {
    showMsg('提交失败，请稍后再试', 'error')
  } finally {
    isSubmitting.value = false
  }
}

async function loadHistory(options: any = { page: 1, itemsPerPage: 20 }) {
  const page = options.page || currentPage.value
  const pageSize = options.itemsPerPage || itemsPerPage.value
  historyLoading.value = true
  currentPage.value = page
  itemsPerPage.value = pageSize
  const token = cookie.get('token')
  try {
    const res = await ajax<any>(`${ApiUrl.GET_USER_REGISTRATIONS}?page=${page}&page_size=${pageSize}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (res.code === 200) {
      registrations.value = res.data.items.map((item: any) => ({
        ...item,
        amount_unit: getAmountUnit(item.data?.['跑步APP'])
      }))
      totalRegistrations.value = res.data.total
    }
  } catch (err) {
    console.error('Failed to load history', err)
  } finally {
    historyLoading.value = false
  }
}

function openDetailDialog(item: RegistrationItem) {
  infoDialogItem.value = item
  detailDialog.id = item.id
  detailDialog.data = item.data
  detailDialog.status = item.status
  detailDialog.createdAt = item.created_at
  detailDialog.rejectReason = item.reject_reason || ''
  detailDialog.amount = item.amount ?? null
  detailDialog.templateUid = item.template_uid || ''
  detailDialog.show = true
  chatStore.clearUnreadCount(item.id)
  loadDetailTemplateOrder(item.data['跑步APP'], item.template_uid || '')
}

const infoDialogItem = ref<RegistrationItem | null>(null)
const infoDialog = reactive({ show: false })

const infoSortedKeys = computed(() => {
  if (!infoDialogItem.value) return []
  const data = infoDialogItem.value.data
  const keys = Object.keys(data)
  const fieldOrder = ['跑步APP', ...detailTemplateFieldOrder.value]
  return keys.sort((a, b) => {
    const ai = fieldOrder.indexOf(a)
    const bi = fieldOrder.indexOf(b)
    if (ai === -1 && bi === -1) return a.localeCompare(b)
    if (ai === -1) return 1
    if (bi === -1) return -1
    return ai - bi
  })
})

function openInfoDialog(item: RegistrationItem) {
  infoDialogItem.value = item
  loadDetailTemplateOrder(item.data['跑步APP'], item.template_uid || '')
  infoDialog.show = true
}

async function loadDetailTemplateOrder(appName: string, templateUid: string) {
  detailTemplateFieldOrder.value = []
  if (!appName || !templateUid) return
  const app = runningApps.value.find(a => a.name === appName)
  if (!app) return
  try {
    const res = await ajax<any[]>(`/api/running-apps/${app.uid}/templates`)
    if (res.code === 200) {
      const tpl = (res.data || []).find((t: any) => t.uid === templateUid)
      if (tpl?.fields) {
        detailTemplateFieldOrder.value = tpl.fields.map((f: any) => f.label)
      }
    }
  } catch { /* ignore */ }
}

function handleDetailClose() {
  detailDialog.show = false
  if (route.query.chat) {
    router.replace({ query: { ...route.query, chat: undefined } })
  }
}

function openChatFromQuery() {
  const chatId = route.query.chat
  if (chatId && typeof chatId === 'string') {
    const item = registrations.value.find(r => String(r.id) === String(chatId))
    if (item) openDetailDialog(item)
  }
}

watch(() => route.query.chat, () => {
  openChatFromQuery()
})

function openResubmitDialog(item: RegistrationItem) {
  resubmitDialog.uid = item.id
  resubmitDialog.app = item.data['跑步APP'] || ''
  resubmitDialog.oldData = { ...item.data }
  resubmitPriority.value = item.priority || 'low'
  resubmitTemplateUid.value = item.template_uid || ''
  resubmitDialog.show = true
  nextTick(() => {
    resubmitSelectFormRef.value?.resetValidation()
  })
}

async function startResubmitForm() {
  if (!resubmitDialog.app) return
  selectedApp.value = resubmitDialog.app
  await loadAppTemplates(resubmitDialog.app)
  if (appTemplates.value.length === 0) {
    showMsg('该APP暂无可用模板', 'error')
    return
  }
  isResubmitMode.value = true
  resubmitDialog.show = false
  templateDialog.uid = ''
  templateDialog.show = true
  nextTick(() => {
    templateFormRef.value?.resetValidation()
  })
}

function startResubmitRegistration() {
  if (!templateDialog.uid) return
  const tpl = appTemplates.value.find(t => t.uid === templateDialog.uid)
  if (!tpl) return
  resubmitTemplateUid.value = templateDialog.uid
  formFields.value = tpl.fields || []
  templateDialog.show = false
  isResubmitMode.value = false
  const app = runningApps.value.find(a => a.name === selectedApp.value)
  if (app?.balance_mode) {
    amountDialog.value = 0
    amountDialog.show = true
  } else {
    registrationAmount.value = null
    fillResubmitForm()
  }
}

function fillResubmitForm() {
  const data: Record<string, any> = {}
  formFields.value.forEach(field => {
    if (field.type === 'checkbox') {
      data[field.label] = Array.isArray(field.default) ? [...field.default] : []
    } else {
      data[field.label] = field.default || ''
    }
  })
  for (const key of Object.keys(resubmitDialog.oldData)) {
    if (key !== '跑步APP' && key in data) {
      data[key] = resubmitDialog.oldData[key]
    }
  }
  resubmitFormDialog.uid = resubmitDialog.uid
  resubmitFormDialog.app = resubmitDialog.app
  resubmitFormDialog.data = data
  resubmitFormDialog.show = true
  nextTick(() => {
    resubmitFormRef.value?.resetValidation()
  })
}

async function doResubmit() {
  const { valid } = await resubmitFormRef.value.validate()
  if (!valid) return
  isSubmitting.value = true
  const token = cookie.get('token')
  const submissionData: Record<string, any> = {
    跑步APP: resubmitFormDialog.app,
    priority: resubmitPriority.value,
    template_uid: resubmitTemplateUid.value,
    ...resubmitFormDialog.data
  }
  if (registrationAmount.value != null) {
    submissionData.amount = registrationAmount.value
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
      currentPage.value = 1
      loadHistory({ page: 1, itemsPerPage: itemsPerPage.value })
    } else {
      showMsg(res.msg, 'error')
    }
  } catch (err) {
    showMsg('提交失败', 'error')
  } finally {
    isSubmitting.value = false
  }
}

onMounted(async () => {
  await fetchConfig()
  await loadHistory({ page: 1, itemsPerPage: 20 })
  openChatFromQuery()
})
</script>

<style scoped lang="scss">
.sign-page {
  max-height: 100%;
  overflow-y: auto;
}

.table-wrapper {
  overflow-x: auto;
}

.sign-page::-webkit-scrollbar {
  display: none;
}

.form-section {
  background: rgb(var(--v-theme-background));
  border-radius: 12px;
}

.detail-card {
  overflow: hidden;
  display: flex;
  flex-direction: column;
  max-height: 85vh;
}
.detail-body {
  display: flex;
  flex: 1;
  min-height: 0;
}
.detail-info-panel {
  flex: 0 0 45%;
  max-width: 45%;
  display: flex;
  flex-direction: column;
  border-right: 1px solid rgba(0,0,0,0.08);
  overflow-y: auto;
}
.detail-chat-panel {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

@media (max-width: 768px) {
  .detail-body {
    flex-direction: column;
  }
  .detail-info-panel {
    flex: 0 0 auto;
    max-width: 100%;
    border-right: none;
    border-bottom: 1px solid rgba(0,0,0,0.08);
    max-height: 250px;
  }
  .detail-chat-panel {
    flex: 1;
    min-height: 350px;
  }
}

.gap-x-4 {
  column-gap: 5px;
}
</style>
