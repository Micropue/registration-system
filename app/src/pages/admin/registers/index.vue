<template>
  <v-container fluid class="pa-0 d-flex flex-column align-center">
    <div class="table-wrapper mt-4">
      <div class="d-flex justify-space-between align-center mb-2">
        <h1 class="text-h4">订单处理</h1>
      </div>

      <div class="d-flex flex-wrap ga-2 mb-4">
        <v-badge
          :content="totalPending"
          color="error"
          offset-x="-6"
          offset-y="-6"
          :model-value="totalPending > 0"
        >
          <v-btn
            :to="{ path: '/admin/registers', query: route.query }"
            :variant="!selectedApp ? 'tonal' : 'text'"
            :color="!selectedApp ? 'primary' : ''"
            rounded
            size="small"
          >
            全部订单
          </v-btn>
        </v-badge>
        <v-badge
          v-for="app in runningApps"
          :key="app.id"
          :content="appStats[app.name]?.pending || 0"
          color="error"
          offset-x="-6"
          offset-y="-6"
          :model-value="(appStats[app.name]?.pending || 0) > 0"
        >
          <v-btn
            :to="{ path: `/admin/registers/${encodeURIComponent(app.name)}`, query: route.query }"
            :variant="selectedApp === app.name ? 'tonal' : 'text'"
            :color="selectedApp === app.name ? 'primary' : ''"
            rounded
            size="small"
          >
            <v-avatar v-if="app.icon" size="20" rounded class="me-1">
              <v-img :src="app.icon" cover></v-img>
            </v-avatar>
            <span class="color-dot" :style="{ backgroundColor: app.accent_color || '#1976D2' }"></span>
            {{ app.name }}
          </v-btn>
        </v-badge>
      </div>

      <app-data-table :headers="headers" :items="registers" :total-items="totalRegisters" :loading="loading"
        v-model:page="currentPage" v-model:items-per-page="itemsPerPage" show-search show-filter search-label="搜索"
        @update:options="loadRegisters" @reset="loadRegisters"
        :row-props="({ item }: any) => item.status !== 'pending' ? { class: 'row-processed' } : {}">

        <!-- 自定义槽位：跑步APP -->
        <template v-slot:item.app="{ item }">
          <div class="d-flex align-center ga-1 app-name-cell">
            <v-avatar v-if="getAppInfo(item.app)?.icon" size="22" rounded>
              <v-img :src="getAppInfo(item.app)?.icon" cover></v-img>
            </v-avatar>
            <span class="color-dot" :style="{ backgroundColor: getAppInfo(item.app)?.accent_color || '#1976D2' }"></span>
            <span class="font-weight-bold text-body-2 text-no-wrap">{{ item.app }}</span>
          </div>
        </template>

        <!-- 自定义槽位：模板 -->
        <template v-slot:item.template_name="{ item }">
          <span class="text-body-2">{{ item.template_name || '-' }}</span>
        </template>

        <!-- 自定义槽位：跑量 -->
  <template v-slot:item.amount="{ item }">
    <span v-if="item.amount != null" class="font-weight-black text-error">{{ item.amount }}{{ getAmountUnit(item.app) }}</span>
    <span v-else class="text-grey">-</span>
  </template>

        <!-- 自定义槽位：创建时间 -->
        <template v-slot:item.created_at="{ item }">
          {{ formatDate(item.created_at) }}
        </template>

        <!-- 自定义槽位：登记状态 -->
        <template v-slot:item.status="{ item }">
          <v-chip :color="getStatusColor(item.status)" size="small">
            {{ getStatusText(item.status) }}
          </v-chip>
        </template>

        <!-- 自定义槽位：优先级 -->
        <template v-slot:item.priority="{ item }">
          <v-chip :color="getPriorityColor(item.priority)" size="small" variant="tonal">
            {{ getPriorityText(item.priority) }}
          </v-chip>
        </template>

        <!-- 自定义槽位：客户信息 -->
        <template v-slot:item.details="{ item }">
          <v-btn variant="tonal" size="small" color="primary" class="font-weight-bold" @click="openDetailsDialog(item)">查看信息</v-btn>
        </template>

        <!-- 自定义槽位：操作 -->
        <template v-slot:item.actions="{ item }">
          <div class="d-flex ga-1">
            <v-badge :model-value="chatUnreadCount(item.id) > 0" :content="chatUnreadCount(item.id)" color="error" offset-x="-4" offset-y="-4">
              <v-btn variant="tonal" rounded color="primary" @click="openDetailsDialog(item)">聊天</v-btn>
            </v-badge>
            <v-btn variant="tonal" rounded color="success" @click="updateStatus(item, 'approved')">已处理</v-btn>
            <v-btn variant="tonal" rounded color="error" @click="openReject(item)">驳回</v-btn>
            <v-btn variant="tonal" rounded color="warning" @click="updateStatus(item, 'pending')">未处理</v-btn>
            <v-btn variant="tonal" rounded color="error" @click="confirmDelete(item)">删除记录</v-btn>
          </div>
        </template>
      </app-data-table>
    </div>

    <!-- 客户信息详情 Dialog（集成聊天） -->
    <v-dialog v-model="detailsDialog.show" max-width="1100">
      <v-card v-if="detailsDialog.item" class="detail-card">
        <v-card-title class="d-flex align-center pa-4 pb-0">
          客户信息 - {{ detailsDialog.item?.username }}
          <v-chip v-if="detailsDialog.item?.is_secondary" color="warning" size="small" variant="tonal" class="me-2">
            待二次处理
          </v-chip>
          <v-spacer></v-spacer>
          <v-chip :color="getPriorityColor(detailsDialog.item?.priority || 'low')" size="small" variant="tonal" class="me-2">
            {{ getPriorityText(detailsDialog.item?.priority || 'low') }}
          </v-chip>
          <v-btn variant="text" size="small" @click="handleDetailsClose">关闭</v-btn>
        </v-card-title>

        <div class="detail-body">
          <div class="detail-info-panel">
            <v-progress-linear v-if="detailTemplateLoading" indeterminate color="primary"></v-progress-linear>
            <template v-else>
            <v-card-text class="pa-4 pt-2">
              <v-table density="compact" border>
                <thead>
                  <tr><th class="text-left">字段</th><th class="text-left">内容</th></tr>
                </thead>
                <tbody>
                  <tr v-if="detailsDialog.item?.amount != null">
                    <td class="font-weight-bold text-primary">跑量</td>
                    <td class="font-weight-bold text-primary">{{ detailsDialog.item.amount }}{{ getAmountUnit(detailsDialog.item.app) }}</td>
                  </tr>
              <tr v-for="row in detailFields" :key="row.key">
                <td :style="fieldStyle(row.key)">{{ row.key }}</td>
                <td :style="fieldStyle(row.key)">
                  <template v-if="hasImageData(detailsDialog.item?.registration_info[row.key])">
                    <div class="d-flex align-center">
                      <div class="d-flex align-center cursor-pointer" @click="openImagePreview(getImageUrls(detailsDialog.item?.registration_info[row.key]), 0)">
                        <v-img :src="getFirstImageUrl(detailsDialog.item?.registration_info[row.key])" height="80" width="100"
                          class="rounded elevation-1 my-1" cover></v-img>
                        <span v-if="getImageCount(detailsDialog.item?.registration_info[row.key]) > 1" class="text-caption text-primary ms-1 font-weight-bold">+{{ getImageCount(detailsDialog.item?.registration_info[row.key]) - 1 }}</span>
                      </div>
                      <v-btn icon="mdi-download" size="x-small" variant="text" density="compact"
                        class="ms-2" @click="downloadAllImages(detailsDialog.item?.registration_info || {})"></v-btn>
                    </div>
                  </template>
                  <template v-else>
                    {{ row.value }}
                    <v-btn v-if="templateFieldCopyable[row.key]" icon="mdi-content-copy" variant="text" density="compact" size="x-small" color="primary" class="ms-1" @click="copyFieldValue(row.key, row.value)"></v-btn>
                  </template>
                </td>
              </tr>
                </tbody>
              </v-table>
              <v-alert v-if="detailsDialog.item?.reject_reason" type="error" variant="tonal" class="mt-3" density="compact">
                <strong>驳回原因：</strong>{{ detailsDialog.item.reject_reason }}
              </v-alert>
            </v-card-text>
            <v-card-actions class="pa-4 pt-0 flex-wrap" style="gap:6px">
              <v-btn variant="text" size="small" prepend-icon="mdi-content-copy" @click="copyDetailText">复制为文本</v-btn>
              <v-btn v-if="hasAnyImages(detailsDialog.item?.registration_info || {})" variant="text" size="small" prepend-icon="mdi-download-multiple" color="primary" @click="downloadAllImages(detailsDialog.item?.registration_info || {})">导出所有图片</v-btn>
              <v-btn v-if="detailsDialog.item?.status === 'pending'" variant="elevated" rounded size="small" color="warning" prepend-icon="mdi-pencil" class="px-4 font-weight-bold ms-2" @click="openModifyDialog(detailsDialog.item)">修改</v-btn>
              <v-spacer></v-spacer>
              <v-btn v-if="detailsDialog.item?.status !== 'approved'" variant="elevated" rounded size="small" color="success" prepend-icon="mdi-check" class="px-4 font-weight-bold" @click="doDetailsApprove">已处理</v-btn>
              <v-btn v-if="detailsDialog.item?.status !== 'rejected'" variant="elevated" rounded size="small" color="error" prepend-icon="mdi-close" class="px-4 font-weight-bold" @click="doDetailsReject">驳回</v-btn>
              <v-btn v-if="emphasisTemplateConfig" variant="tonal" rounded size="small" color="warning" prepend-icon="mdi-alert-octagon" class="ms-auto" @click="showEmphasisDialog">强调窗</v-btn>
            </v-card-actions>
            </template>
          </div>

          <div class="detail-chat-panel">
            <RegistrationChat
              v-if="detailsDialog.item?.id"
              :registration-uid="detailsDialog.item.id"
              :is-admin-view="true"
              :current-username="appStore.userInfo?.username || ''"
            />
          </div>
        </div>
      </v-card>
    </v-dialog>

    <!-- 强调弹窗 -->
    <v-dialog v-model="emphasisDialog.show" max-width="650" scrollable>
      <v-card v-if="emphasisDialog.items.length" class="pa-4">
        <v-card-title class="d-flex align-center">
          <v-icon color="warning" class="mr-2">mdi-alert-octagon</v-icon>
          <span class="text-h6">重要提醒</span>
          <v-spacer></v-spacer>
          <v-btn icon="mdi-close" variant="text" size="small" @click="emphasisDialog.show = false"></v-btn>
        </v-card-title>
        <v-divider class="mb-3"></v-divider>
        <v-card-text>
          <v-table density="compact" border>
            <thead>
              <tr><th class="text-left">项目</th><th class="text-left">内容</th></tr>
            </thead>
            <tbody>
              <tr v-for="(item, i) in emphasisDialog.items" :key="'em'+i">
                <td :style="{ fontWeight: item.bold ? 'bold' : 'normal', color: item.color || undefined, fontSize: item.size || undefined }">{{ item.label }}</td>
                <td :style="{ fontWeight: item.bold ? 'bold' : 'normal', color: item.color || undefined, fontSize: item.size || undefined }">
                  {{ item.value }}
                  <v-btn v-if="item.copyable" icon="mdi-content-copy" variant="text" density="compact" size="x-small" color="primary" class="ms-1" @click="copyEmphasisValue(item.value)"></v-btn>
                </td>
              </tr>
            </tbody>
          </v-table>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="tonal" @click="emphasisDialog.show = false">关闭</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 修改订单信息 Dialog -->
    <v-dialog v-model="modifyDialog.show" max-width="700" persistent scrollable>
      <v-card rounded="lg">
        <v-card-title class="d-flex align-center pa-4">
          <v-icon color="warning" class="mr-2">mdi-pencil-box</v-icon>
          <span class="text-h6">修改订单信息</span>
          <v-chip class="ml-3" color="primary" variant="tonal" size="small">{{ modifyDialog.app }}</v-chip>
          <v-spacer></v-spacer>
          <v-btn icon="mdi-close" variant="text" @click="modifyDialog.show = false"></v-btn>
        </v-card-title>
        <v-divider></v-divider>
        <v-alert v-if="modifyDialog.templateMismatch" type="warning" variant="tonal" density="compact" class="ma-4 mb-0" icon="mdi-alert">
          无法恢复原状态，模板与原模板不一致
        </v-alert>
        <v-card-text class="pa-4" style="max-height: 55vh; overflow-y: auto;">
          <div class="mb-4">
            <div class="text-subtitle-2 mb-2">优先级</div>
            <v-btn-toggle v-model="modifyPriority" mandatory density="comfortable" variant="outlined" divided color="primary">
              <v-btn value="low" size="small">低</v-btn>
              <v-btn value="medium" size="small">中</v-btn>
              <v-btn value="high" size="small">高</v-btn>
            </v-btn-toggle>
          </div>
          <v-row dense>
            <v-col v-for="field in modifyFields" :key="field.label" cols="12">
              <template v-if="['text', 'textarea', 'number', 'date'].includes(field.type)">
                <v-textarea v-if="field.type === 'textarea'" v-model="modifyFormData[field.label]" :label="field.label"
                  :required="field.required" :rules="field.required ? [v => !!v || `${field.label}是必填项`] : []"
                  variant="outlined" density="comfortable" color="primary" rows="2" auto-grow></v-textarea>
                <v-text-field v-else v-model="modifyFormData[field.label]" :label="field.label" :type="field.type"
                  :required="field.required" :rules="field.required ? [v => !!v || `${field.label}是必填项`] : []"
                  variant="outlined" density="comfortable" color="primary"></v-text-field>
              </template>
              <template v-else-if="field.type === 'radio'">
                <div class="text-subtitle-2 mb-1">{{ field.label }} <span v-if="field.required" class="text-error">*</span></div>
                <v-radio-group v-model="modifyFormData[field.label]" :rules="field.required ? [v => !!v || '请选择一个选项'] : []"
                  inline color="primary" density="comfortable">
                  <v-radio v-for="opt in field.options" :key="opt.value" :label="opt.label" :value="opt.value"></v-radio>
                </v-radio-group>
              </template>
              <template v-else-if="field.type === 'select'">
                <v-select v-model="modifyFormData[field.label]" :items="field.options" item-title="label" item-value="value"
                  :label="field.label" :required="field.required" :rules="field.required ? [v => !!v || '请选择一个选项'] : []"
                  variant="outlined" density="comfortable" color="primary"></v-select>
              </template>
              <template v-else-if="field.type === 'checkbox'">
                <div class="text-subtitle-2 mb-1">{{ field.label }} <span v-if="field.required" class="text-error">*</span></div>
                <v-checkbox v-for="opt in field.options" :key="opt.value" v-model="modifyFormData[field.label]"
                  :label="opt.label" :value="opt.value" density="compact" color="primary" hide-details></v-checkbox>
              </template>
              <template v-else-if="field.type.endsWith('-range')">
                <div class="text-subtitle-2 mb-1">{{ field.label }} <span v-if="field.required" class="text-error">*</span></div>
                <v-row dense>
                  <v-col cols="6">
                    <v-text-field v-model="modifyFormData[field.label][0]"
                      :label="field.type === 'number-range' ? '最小值' : '开始'"
                      :type="field.type === 'number-range' ? 'number' : field.type === 'date-range' ? 'date' : 'time'"
                      variant="outlined" density="comfortable"></v-text-field>
                  </v-col>
                  <v-col cols="6">
                    <v-text-field v-model="modifyFormData[field.label][1]"
                      :label="field.type === 'number-range' ? '最大值' : '结束'"
                      :type="field.type === 'number-range' ? 'number' : field.type === 'date-range' ? 'date' : 'time'"
                      variant="outlined" density="comfortable"></v-text-field>
                  </v-col>
                </v-row>
              </template>
              <template v-else-if="field.type === 'image'">
                <div class="text-subtitle-2 mb-2">{{ field.label }} <span v-if="field.required" class="text-error">*</span></div>
                <v-file-input
                  :key="field.label"
                  @update:model-value="onModifyImageChange(field.label, $event)"
                  :label="field.label"
                  :multiple="!!field.multiple"
                  accept="image/png,image/jpeg,image/webp,image/gif,image/heic,image/heif"
                  prepend-icon="mdi-camera-image"
                  variant="outlined"
                  density="comfortable"
                  :rules="field.required ? [(v: any) => (field.multiple ? (v && v.length > 0) : !!v) || '请上传' + field.label] : []"
                  show-size
                ></v-file-input>
                <div v-if="hasAdminImageValue(field.label)" class="d-flex flex-wrap ga-2 py-2">
                  <div v-for="(url, idx) in getAdminDisplayImages(field.label)" :key="idx" class="position-relative">
                    <v-img :src="url" height="80" width="100"
                      class="rounded elevation-1 cursor-pointer"
                      cover @click="openAdminImagePreview(getAdminPreviewUrls(field.label), idx)"></v-img>
                    <v-btn v-if="field.multiple" icon="mdi-close-circle" size="x-small"
                      variant="plain" color="error"
                      class="position-absolute" style="top:-6px;right:-6px"
                      @click="removeAdminImage(field.label, idx)"></v-btn>
                  </div>
                </div>
              </template>
            </v-col>
          </v-row>
          <v-row v-if="modifyDialog.showAmount">
            <v-col cols="12">
              <v-text-field v-model.number="modifyDialog.amount" label="跑量" type="number"
                variant="outlined" density="comfortable"></v-text-field>
            </v-col>
          </v-row>
        </v-card-text>
        <v-divider></v-divider>
        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="modifyDialog.show = false">取消</v-btn>
          <v-btn color="warning" variant="flat" :loading="modifySaving" @click="doModify">保存修改</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 删除确认 Dialog -->
    <v-dialog v-model="deleteDialog.show" max-width="400">
      <v-card>
        <v-card-title class="text-h5">确认删除</v-card-title>
        <v-card-text>
          确定要删除用户 <b>{{ deleteDialog.item?.username }}</b> 的登记记录吗？此操作不可撤销。
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="deleteDialog.show = false">取消</v-btn>
          <v-btn color="error" variant="elevated" @click="handleDelete" :loading="loading">确认删除</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 驳回原因 Dialog -->
    <v-dialog v-model="rejectDialog.show" max-width="450">
      <v-card>
        <v-card-title class="text-h5 pa-4">驳回登记</v-card-title>
        <v-card-text class="pa-4 pt-0">
          <v-textarea v-model="rejectDialog.reason" label="驳回原因" variant="outlined"
            placeholder="请填写驳回原因，用户将看到此内容"
            rows="3" hide-details auto-grow></v-textarea>
        </v-card-text>
        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="rejectDialog.show = false">取消</v-btn>
          <v-btn color="error" variant="flat" :loading="loading" @click="confirmReject">确认驳回</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 图片预览弹窗 -->
    <v-dialog v-model="imagePreviewDialog.show" max-width="900">
      <v-card>
        <v-card-actions class="pa-2">
          <v-spacer></v-spacer>
          <v-btn icon="mdi-close" variant="text" @click="imagePreviewDialog.show = false"></v-btn>
        </v-card-actions>
        <div class="d-flex" style="min-height:300px">
          <div v-if="imagePreviewDialog.urls.length > 1" class="d-flex flex-column pa-2 overflow-y-auto flex-shrink-0" style="width:80px;max-height:70vh;gap:6px">
            <div v-for="(url, idx) in imagePreviewDialog.urls" :key="idx"
              style="width:60px;height:60px;overflow:hidden;flex-shrink:0;border-radius:4px"
              class="cursor-pointer"
              :class="idx === imagePreviewDialog.currentIndex ? 'elevation-3' : 'elevation-1'"
              :style="{ border: idx === imagePreviewDialog.currentIndex ? '2px solid rgb(var(--v-theme-primary))' : '2px solid transparent' }"
              @click="imagePreviewDialog.currentIndex = idx">
              <v-img :src="url" height="60" width="60" cover></v-img>
            </div>
          </div>
          <div class="flex-grow-1 pa-2">
            <v-img :src="imagePreviewDialog.urls[imagePreviewDialog.currentIndex] || ''" max-height="75vh" contain></v-img>
          </div>
        </div>
      </v-card>
    </v-dialog>

    <v-snackbar v-model="snackbar.show" :color="snackbar.color" timeout="3000">
      {{ snackbar.text }}
    </v-snackbar>
  </v-container>
</template>

<style scoped>
.table-wrapper {
  width: 90%;
  overflow-x: auto;
}
:deep(.row-processed) { opacity: 0.5; }
.color-dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 5px; vertical-align: middle; flex-shrink: 0; }
.app-name-cell { min-width: 120px; white-space: nowrap; }

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
</style>

<script lang="ts" setup>
import { ref, shallowRef, reactive, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppDataTable from '@/components/AppDataTable.vue'
import RegistrationChat from '@/components/RegistrationChat.vue'
import { ApiUrl } from '@/config/api-url'
import { ajax } from '@/api/ajax'
import { cookie } from '@/api/cookie'
import type { RunningApp } from '@/config/api-type'
import { useAppStore } from '@/stores/app'
import { useChatStore } from '@/stores/chat'
// 类型定义
interface RegistrationItem {
  id: string
  username: string
  created_at: string
  status: 'pending' | 'approved' | 'rejected'
  registration_info?: any
  reject_reason?: string
  app?: string
  priority?: string
  template_uid?: string
  amount?: number | null
  process_count?: number
  is_secondary?: boolean
}

// 状态管理
const route = useRoute()
const router = useRouter()
const appStore = useAppStore()
const chatStore = useChatStore()

const runningApps = ref<RunningApp[]>([])
const appStats = ref<Record<string, { pending: number }>>({})
const selectedApp = computed(() => decodeURIComponent(route.params.appName as string || ''))
const totalPending = computed(() => Object.values(appStats.value).reduce((sum, s) => sum + s.pending, 0))

const registers = ref<RegistrationItem[]>([])
const loading = ref(false)
const showSecondary = computed(() => route.query.tab === 'secondary')
const totalRegisters = ref(0)
const itemsPerPage = ref(20)
const currentPage = ref(1)
const detailsDialog = reactive({ show: false, item: null as RegistrationItem | null })
const deleteDialog = reactive({ show: false, item: null as RegistrationItem | null })
const rejectDialog = reactive({ show: false, item: null as RegistrationItem | null, reason: '' })
const modifyDialog = reactive({ show: false, item: null as RegistrationItem | null, app: '', amount: null as number | null | undefined, templateMismatch: false, showAmount: false })
const modifyFields = ref<any[]>([])
const modifyFormData = ref<Record<string, any>>({})
const modifyPriority = ref('low')
const modifySaving = ref(false)
const modifyImageFiles = shallowRef<Record<string, File[]>>({})
const imagePreviewDialog = reactive({ show: false, urls: [] as string[], currentIndex: 0 })

function onModifyImageChange(label: string, files: File | File[]) {
  const arr = Array.isArray(files) ? files : files ? [files] : []
  const valid = arr.filter(f => isAllowedImageType(f))
  if (valid.length < arr.length) showMsg('仅支持 PNG/JPEG/WebP/GIF/HEIC/HEIF 格式', 'warning')
  modifyImageFiles.value = { ...modifyImageFiles.value, [label]: valid }
}

function isImageUrl(val: any): boolean {
  if (typeof val !== 'string') return false
  return val.startsWith('/media/') || val.startsWith('http')
}

function hasImageData(val: any): boolean {
  if (typeof val === 'string') return isImageUrl(val)
  if (Array.isArray(val)) return val.some(isImageUrl)
  return false
}

function getFirstImageUrl(val: any): string {
  if (typeof val === 'string') return val
  if (Array.isArray(val)) return val.find((v: any) => isImageUrl(v)) || ''
  return ''
}

function getImageCount(val: any): number {
  if (typeof val === 'string') return isImageUrl(val) ? 1 : 0
  if (Array.isArray(val)) return val.filter((v: any) => isImageUrl(v)).length
  return 0
}

function getImageUrls(val: any): string[] {
  if (typeof val === 'string') return isImageUrl(val) ? [val] : []
  if (Array.isArray(val)) return val.filter((v: any) => isImageUrl(v))
  return []
}

function getModifyImageLocalUrl(file: File): string {
  return URL.createObjectURL(file)
}

function openImagePreview(urls: string | string[], index: number = 0) {
  const arr = typeof urls === 'string' ? [urls] : urls
  imagePreviewDialog.urls = arr
  imagePreviewDialog.currentIndex = index
  imagePreviewDialog.show = true
}

function downloadImage(url: string) {
  const a = document.createElement('a')
  a.href = url
  a.download = url.split('/').pop() || 'image'
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
}

async function downloadAllImages(data: Record<string, any>) {
  const urls: string[] = []
  for (const key of Object.keys(data)) {
    const val = data[key]
    if (typeof val === 'string' && isImageUrl(val)) urls.push(val)
    else if (Array.isArray(val)) val.filter((v: any) => isImageUrl(v)).forEach((u: string) => urls.push(u))
  }
  for (let i = 0; i < urls.length; i++) {
    setTimeout(() => { const a = document.createElement('a'); a.href = urls[i]; a.download = urls[i].split('/').pop() || 'image'; document.body.appendChild(a); a.click(); document.body.removeChild(a) }, i * 300)
  }
}

function hasAnyImages(data: Record<string, any>): boolean {
  for (const key of Object.keys(data)) {
    if (hasImageData(data[key])) return true
  }
  return false
}

async function uploadModifyImage(file: File): Promise<string | null> {
  if (!isAllowedImageType(file)) return null
  const token = cookie.get('token')
  try {
    const res = await ajax<{ url: string }>(ApiUrl.UPLOAD_IMAGE, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
      body: { file },
      isFormData: true
    })
    if (res.code === 200) {
      return res.data?.url || null
    }
  } catch { /* ignore */ }
  return null
}

function isAllowedImageType(file: File): boolean {
  const allowed = ['image/png','image/jpeg','image/webp','image/gif','image/heic','image/heif']
  if (allowed.includes(file.type)) return true
  const ext = file.name.split('.').pop()?.toLowerCase() || ''
  return ['png','jpg','jpeg','webp','gif','heic','heif'].includes(ext)
}

function getAdminImageModel(label: string): File | File[] | null {
  const val = modifyImageFiles.value[label]
  if (!val || val.length === 0) return null
  const field = modifyFields.value.find((f: any) => f.label === label)
  if (field?.multiple) return val
  return val[0]
}

function hasAdminImageValue(label: string): boolean {
  const files = modifyImageFiles.value[label]
  if (files && files.length > 0) return true
  const data = modifyFormData.value[label]
  return hasImageData(data)
}

function getAdminDisplayImages(label: string): string[] {
  const files = modifyImageFiles.value[label]
  if (files && files.length > 0) return files.map((f: File) => URL.createObjectURL(f))
  const data = modifyFormData.value[label]
  if (Array.isArray(data)) return data.filter((d: any) => isImageUrl(d))
  if (typeof data === 'string' && isImageUrl(data)) return [data]
  return []
}

function getAdminPreviewUrls(label: string): string[] {
  const files = modifyImageFiles.value[label]
  if (files && files.length > 0) return files.map((f: File) => URL.createObjectURL(f))
  const data = modifyFormData.value[label]
  if (Array.isArray(data)) return data.filter((d: any) => isImageUrl(d)).map((u: any) => u)
  if (typeof data === 'string' && isImageUrl(data)) return [data]
  return []
}

function removeAdminImage(label: string, idx: number) {
  const files = modifyImageFiles.value[label]
  if (files) {
    const next = files.filter((_: File, i: number) => i !== idx)
    modifyImageFiles.value = { ...modifyImageFiles.value, [label]: next }
  }
  const data = modifyFormData.value[label]
  if (Array.isArray(data)) {
    modifyFormData.value[label] = data.filter((_: any, i: number) => i !== idx)
  }
}

function openAdminImagePreview(urls: string[], index: number) {
  imagePreviewDialog.urls = urls
  imagePreviewDialog.currentIndex = index
  imagePreviewDialog.show = true
}

const snackbar = reactive({ show: false, text: '', color: 'success' })
const templateFieldOrder = ref<string[]>([])
const templateFieldCopyable = ref<Record<string, boolean>>({})
const templateFieldStyles = ref<Record<string, { bold: boolean; color: string; size: string }>>({})
const emphasisTemplateConfig = ref<any>(null)
const emphasisDialog = reactive({ show: false, items: [] as { label: string; value: string; bold: boolean; color: string; size: string; copyable: boolean }[] })
const detailTemplateLoading = ref(false)

const detailFields = computed(() => {
  const info = detailsDialog.item?.registration_info
  if (!info) return []
  const keys = Object.keys(info)
  const order = ['跑步APP', ...templateFieldOrder.value]
  return keys
    .map(k => ({ key: k, value: _formatVal(info[k]) }))
    .sort((a, b) => {
      const ai = order.indexOf(a.key)
      const bi = order.indexOf(b.key)
      if (ai === -1 && bi === -1) return a.key.localeCompare(b.key)
      if (ai === -1) return 1
      if (bi === -1) return -1
      return ai - bi
    })
})

function _formatVal(val: any): string {
  if (val === null || val === undefined) return '-'
  if (Array.isArray(val)) return val.join(' - ')
  return String(val)
}

function fieldStyle(key: string): Record<string, string> {
  const style: Record<string, string> = {}
  const s = templateFieldStyles.value[key]
  if (s) {
    if (s.bold) style['font-weight'] = '900'
    if (s.color) style['color'] = s.color
    if (s.size) style['font-size'] = s.size
  }
  return style
}

function showMsg(text: string, color: string = 'success') {
  snackbar.text = text
  snackbar.color = color
  snackbar.show = true
}

async function loadRunningApps() {
  try {
    const res = await ajax<RunningApp[]>(ApiUrl.GET_RUNNING_APPS, {
      headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
    })
    if (res.code === 200) runningApps.value = res.data
  } catch (err) { /* ignore */ }
}

async function loadStats() {
  try {
    const res = await ajax<{ app: string; pending: number }[]>(ApiUrl.REGISTRATION_STATS, {
      headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
    })
    if (res.code === 200) {
      const map: Record<string, { pending: number }> = {}
      for (const s of res.data) {
        map[s.app] = { pending: s.pending }
      }
      appStats.value = map
    }
  } catch (err) { /* ignore */ }
}

async function loadTemplateFieldOrder(appName: string, templateUid: string) {
  const app = runningApps.value.find(a => a.name === appName)
  if (!app || !templateUid) { templateFieldOrder.value = []; templateFieldCopyable.value = {}; templateFieldStyles.value = {}; detailTemplateLoading.value = false; return }
  try {
    const res = await ajax<any[]>(`/api/admin/settings/running-apps/${app.uid}/templates`, {
      headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
    })
    if (res.code === 200) {
      const tpl = (res.data || []).find((t: any) => t.uid === templateUid)
      if (tpl?.fields) {
        templateFieldOrder.value = tpl.fields.map((f: any) => f.label)
        const copyableMap: Record<string, boolean> = {}
        const stylesMap: Record<string, { bold: boolean; color: string; size: string }> = {}
        tpl.fields.forEach((f: any) => {
          if (f.copyable) copyableMap[f.label] = true
          if (f.bold || f.color || f.size) {
            stylesMap[f.label] = { bold: f.bold || false, color: f.color || '', size: f.size || '' }
          }
        })
        templateFieldCopyable.value = copyableMap
        templateFieldStyles.value = stylesMap
        emphasisTemplateConfig.value = tpl.emphasis_config || null
        detailTemplateLoading.value = false
        checkEmphasisConditions()
        return
      }
    }
  } catch (err) { /* ignore */ }
  templateFieldOrder.value = []
  templateFieldCopyable.value = {}
  templateFieldStyles.value = {}
  emphasisTemplateConfig.value = null
  detailTemplateLoading.value = false
}

function checkEmphasisConditions() {
  const config = emphasisTemplateConfig.value
  if (!config || !config.conditions || config.conditions.length === 0) return
  const info = detailsDialog.item?.registration_info
  if (!info) return
  const allMet = config.conditions.every((c: any) => {
    const fieldVal = info[c.field]
    if (fieldVal == null || fieldVal === '') return false
    const matchLines = (c.values || '').split('\n').map((s: string) => s.trim()).filter(Boolean)
    if (matchLines.length === 0) return false
    const strVal = Array.isArray(fieldVal) ? fieldVal.join(', ') : String(fieldVal)
    return matchLines.some((line: string) => strVal.includes(line))
  })
  if (allMet) {
    showEmphasisDialog()
  }
}

function showEmphasisDialog() {
  const config = emphasisTemplateConfig.value
  if (!config || !config.content) return
  const info = detailsDialog.item?.registration_info || {}
  emphasisDialog.items = config.content.map((c: any) => ({
    label: c.label,
    value: info[c.label] != null ? String(info[c.label]) : '',
    bold: c.bold || false,
    color: c.color || '#000000',
    size: c.size || '',
    copyable: c.copyable || false
  }))
  emphasisDialog.show = true
}

async function copyEmphasisValue(val: string) {
  try {
    await navigator.clipboard.writeText(val)
  } catch { /* ignore */ }
}

onMounted(async () => {
  await loadRunningApps()
  await loadStats()
  if (runningApps.value.length > 0) {
    if (selectedApp.value && !runningApps.value.find(a => a.name === selectedApp.value) && !route.query.chat) {
      router.replace({ path: `/admin/registers/${encodeURIComponent(runningApps.value[0].name)}`, query: route.query })
      return
    }
  }
  await loadRegisters()
  openChatFromQuery()
})

watch(() => route.query.tab, () => {
  loadRegisters()
})

watch(selectedApp, () => {
  currentPage.value = 1
  loadRegisters()
})

function openDetailsDialog(item: RegistrationItem) {
  detailsDialog.item = item
  detailsDialog.show = true
  chatStore.clearUnreadCount(item.id)
  if (item.app && item.template_uid) {
    detailTemplateLoading.value = true
    loadTemplateFieldOrder(item.app, item.template_uid)
  }
}

function handleDetailsClose() {
  detailsDialog.show = false
  detailTemplateLoading.value = false
  emphasisTemplateConfig.value = null
  if (route.query.chat) {
    router.replace({ query: { ...route.query, chat: undefined } })
  }
}

function doDetailsApprove() {
  if (!detailsDialog.item) return
  updateStatus(detailsDialog.item, 'approved')
  detailsDialog.show = false
}

function doDetailsReject() {
  if (!detailsDialog.item) return
  openReject(detailsDialog.item)
  detailsDialog.show = false
}

function openChatFromQuery() {
  const chatId = route.query.chat
  if (chatId && typeof chatId === 'string') {
    const item = registers.value.find(r => String(r.id) === String(chatId))
    if (item) openDetailsDialog(item)
  }
}

watch(() => route.query.chat, () => {
  openChatFromQuery()
})

function chatUnreadCount(id: string) {
  return chatStore.chatUnreadCounts[id] || 0
}

function getAppInfo(appName: string) {
  return runningApps.value.find(a => a.name === appName)
}

function getAmountUnit(appName: string | undefined): string {
  if (!appName) return ''
  const app = runningApps.value.find(a => a.name === appName)
  if (app?.balance_mode === 'mileage') return ' 公里'
  if (app?.balance_mode === 'count') return ' 次'
  return ''
}

function confirmDelete(item: RegistrationItem) {
  deleteDialog.item = item
  deleteDialog.show = true
}

// 配置化表头
const headers = [
  { title: '用户名', key: 'username', searchable: true, filterable: true },
  { title: '跑步APP', key: 'app', sortable: true, filterable: true },
  { title: '模板', key: 'template_name', sortable: true },
  { title: '跑量', key: 'amount', sortable: true },
  { title: '客户信息', key: 'details', sortable: false },
  { title: '登记状态', key: 'status', sortable: true, filterable: true },
  { title: '优先级', key: 'priority', sortable: true, filterable: true },
  { title: '操作', key: 'actions', sortable: false },
  { title: '创建时间', key: 'created_at', sortable: true },
]

// 工具函数
function formatDate(isoString: string) {
  if (!isoString) return '-'
  const date = new Date(isoString)
  return date.toLocaleString()
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
    case 'approved': return '已通过'
    case 'rejected': return '已拒绝'
    default: return '待处理'
  }
}

function getPriorityColor(priority: string) {
  switch (priority) {
    case 'high': return 'error'
    case 'medium': return 'warning'
    default: return 'grey'
  }
}

function getPriorityText(priority: string) {
  switch (priority) {
    case 'high': return '高'
    case 'medium': return '中'
    default: return '低'
  }
}

// 事件处理
async function copyDetailText() {
  const item = detailsDialog.item
  if (!item?.registration_info) return
  const info = item.registration_info
  const keys = Object.keys(info)
  const order = ['跑步APP', ...templateFieldOrder.value]
  const sorted = [...keys].sort((a, b) => {
    const ai = order.indexOf(a)
    const bi = order.indexOf(b)
    if (ai === -1 && bi === -1) return a.localeCompare(b)
    if (ai === -1) return 1
    if (bi === -1) return -1
    return ai - bi
  })
  const text = sorted.map(k => `${k}：${info[k] ?? ''}`).join('\n')
  try {
    await navigator.clipboard.writeText(text)
    showMsg('已复制到剪贴板')
  } catch {
    showMsg('复制失败', 'error')
  }
}

async function copyFieldValue(key: string, value: string) {
  try {
    await navigator.clipboard.writeText(value)
    showMsg(`已复制：${key}`)
  } catch {
    showMsg('复制失败', 'error')
  }
}

function openReject(item: RegistrationItem) {
  rejectDialog.item = item
  rejectDialog.reason = ''
  rejectDialog.show = true
}

async function confirmReject() {
  if (!rejectDialog.item) return
  loading.value = true
  try {
    const res = await ajax(`${ApiUrl.UPDATE_REGISTRATION_STATUS}/${rejectDialog.item.id}/status`, {
      method: 'POST',
      body: { status: 'rejected', reject_reason: rejectDialog.reason },
      isFormData: true,
      headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
    })
    if (res.code === 200) {
      rejectDialog.item.status = 'rejected'
      showMsg(`已驳回 ${rejectDialog.item.username} 的登记`)
      rejectDialog.show = false
      loadRegisters()
    } else {
      showMsg(res.msg || '驳回失败', 'error')
    }
  } catch (err) {
    showMsg('请求失败', 'error')
  } finally {
    loading.value = false
  }
}

async function updateStatus(item: RegistrationItem, status: RegistrationItem['status']) {
  loading.value = true
  try {
    const res = await ajax(`${ApiUrl.UPDATE_REGISTRATION_STATUS}/${item.id}/status`, {
      method: 'POST',
      body: { status },
      isFormData: true,
      headers: { 
        'Authorization': `Bearer ${cookie.get('token') || ''}`
      }
    })
    if (res.code === 200) {
      item.status = status
      showMsg(`已更新 ${item.username} 的状态为: ${getStatusText(status)}`)
      loadRegisters()
    } else {
      showMsg(res.msg || '状态更新失败', 'error')
    }
  } catch (err) {
    showMsg('请求失败', 'error')
  } finally {
    loading.value = false
  }
}

async function handleDelete() {
  if (!deleteDialog.item) return
  
  loading.value = true
  try {
    const res = await ajax(`${ApiUrl.DELETE_REGISTRATION}/${deleteDialog.item.id}`, {
      method: 'DELETE',
      headers: { 
        'Authorization': `Bearer ${cookie.get('token') || ''}`
      }
    })
    if (res.code === 200) {
      showMsg(`已成功删除 ${deleteDialog.item.username} 的登记记录`)
      deleteDialog.show = false
      loadRegisters()
    } else {
      showMsg(res.msg || '删除失败', 'error')
    }
  } catch (err) {
    showMsg('请求失败', 'error')
  } finally {
    loading.value = false
  }
}

async function openModifyDialog(item: RegistrationItem) {
  const info = item.registration_info || {}
  const appName = info['跑步APP'] || ''
  const templateUid = item.template_uid || ''
  if (!appName || !templateUid) { showMsg('无法修改：缺少APP或模板信息', 'error'); return }
  const app = runningApps.value.find(a => a.name === appName)
  if (!app) { showMsg('无法修改：APP不存在', 'error'); return }
  try {
    const res = await ajax<any[]>(`/api/admin/settings/running-apps/${app.uid}/templates`, {
      headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
    })
    if (res.code === 200) {
      const tpl = (res.data || []).find((t: any) => t.uid === templateUid)
      if (!tpl) { showMsg('无法修改：模板不存在', 'error'); return }
      modifyFields.value = tpl.fields || []
      const templateLabels = (tpl.fields || []).map((f: any) => f.label)
      const oldKeys = Object.keys(info).filter(k => k !== '跑步APP')
      const mismatch = oldKeys.length !== templateLabels.length ||
        !oldKeys.every(k => templateLabels.includes(k)) ||
        !templateLabels.every((l: string) => oldKeys.includes(l))
      const formData: Record<string, any> = {}
      modifyFields.value.forEach((field: any) => {
        if (field.type === 'checkbox') {
          formData[field.label] = Array.isArray(field.default) ? [...field.default] : []
        } else if (field.type.endsWith('-range')) {
          formData[field.label] = ['', '']
        } else if (field.type === 'image') {
          formData[field.label] = field.multiple ? [] : (field.default || '')
          modifyImageFiles.value = { ...modifyImageFiles.value, [field.label]: [] }
        } else {
          formData[field.label] = field.default || ''
        }
      })
      if (!mismatch) {
        for (const key of Object.keys(info)) {
          if (key !== '跑步APP' && key in formData) {
            formData[key] = info[key]
          }
        }
      }
      modifyDialog.item = item
      modifyDialog.app = appName
      modifyDialog.amount = item.amount
      modifyDialog.templateMismatch = mismatch
      modifyDialog.showAmount = !!app.balance_mode
      modifyPriority.value = item.priority || 'low'
      modifyFormData.value = formData
      modifyDialog.show = true
    }
  } catch { showMsg('加载模板失败', 'error') }
}

async function doModify() {
  if (!modifyDialog.item) return
  modifySaving.value = true
  try {
    for (const field of modifyFields.value) {
      if (field.type === 'image') {
        const files = modifyImageFiles.value[field.label]
        if (files && files.length > 0) {
          const urls: string[] = []
          for (const file of files) {
            const url = await uploadModifyImage(file)
            if (url) {
              urls.push(url)
            } else {
              showMsg(`${field.label} 上传失败`, 'error')
              modifySaving.value = false
              return
            }
          }
          modifyFormData.value[field.label] = (field as any).multiple ? urls : urls[0]
        }
      }
    }

    const data: Record<string, any> = { '跑步APP': modifyDialog.app }
    for (const [key, value] of Object.entries(modifyFormData.value)) {
      data[key] = value
    }
    const token = cookie.get('token') || ''
    const res = await ajax(`/api/admin/registrations/${modifyDialog.item.id}/data`, {
      method: 'PUT',
      body: { data, amount: modifyDialog.amount, priority: modifyPriority.value },
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (res.code === 200) {
      showMsg('订单信息已修改')
      modifyDialog.show = false
      detailsDialog.show = false
      loadRegisters()
    } else {
      showMsg(res.msg || '修改失败', 'error')
    }
  } catch {
    showMsg('请求失败', 'error')
  } finally {
    modifySaving.value = false
  }
}

// 加载数据
async function loadRegisters(options: any = { page: 1, itemsPerPage: 20 }) {
  const page = options.page || currentPage.value
  const pageSize = options.itemsPerPage || itemsPerPage.value

  loading.value = true
  currentPage.value = page
  itemsPerPage.value = pageSize

  let url = `${ApiUrl.GET_REGISTRATIONS}?page=${page}&page_size=${pageSize}`
  if (selectedApp.value) {
    url += `&running_app=${encodeURIComponent(selectedApp.value)}`
  }
  const username = route.query.username as string || ''
  if (username) {
    url += `&username=${encodeURIComponent(username)}`
  }
  if (options.sortBy && options.sortBy.length > 0) {
    url += `&sort_by=${encodeURIComponent(options.sortBy[0].key)}&order=${options.sortBy[0].order}`
  }
  if (showSecondary.value) {
    url += '&secondary=1'
  }

  try {
    const res = await ajax(url, {
      method: 'GET',
      headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
    })
    if (res.code === 200) {
      registers.value = res.data.items.map((item: any) => ({
        ...item,
        app: item.registration_info?.['跑步APP'] || '',
        amount: item.amount ?? null,
        process_count: item.process_count || 0,
        is_secondary: item.is_secondary || false,
        _searchable: item.registration_info
          ? Object.values(item.registration_info)
              .filter((v: any) => v != null)
              .map((v: any) => Array.isArray(v) ? v.join(', ') : String(v))
              .join(' ')
          : ''
      }))
      totalRegisters.value = res.data.total
      loadStats()
    }
  } catch (err) {
    showMsg('加载登记数据失败', 'error')
  } finally {
    loading.value = false
  }
}

</script>
