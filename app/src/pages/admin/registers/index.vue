<template>
  <v-container fluid class="pa-0 d-flex flex-column align-center">
    <div class="table-wrapper mt-4">
      <div class="d-flex justify-space-between align-center mb-4">
        <h1 class="text-h4">登记处理</h1>
      </div>

      <!-- 使用封装后的通用表格组件 -->
      <app-data-table 
        :headers="headers" 
        :items="registers" 
        :total-items="totalRegisters" 
        :loading="loading"
        v-model:page="currentPage" 
        v-model:items-per-page="itemsPerPage" 
        show-search 
        show-filter
        search-label="搜索用户名" 
        @update:options="loadRegisters" 
        @reset="loadRegisters"
      >
        
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

        <!-- 自定义槽位：登记信息 -->
        <template v-slot:item.details="{ item }">
          <v-btn variant="text" size="small" color="primary" @click="openDetailsDialog(item)">查看信息</v-btn>
        </template>

        <!-- 自定义槽位：操作 -->
        <template v-slot:item.actions="{ item }">
          <v-menu location="bottom">
            <template v-slot:activator="{ props }">
              <v-btn icon="mdi-dots-vertical" variant="text" size="small" v-bind="props"></v-btn>
            </template>
            <v-list density="compact">
              <v-list-item @click="handleView(item)">查看详情</v-list-item>
              <v-menu location="right">
                <template v-slot:activator="{ props }">
                  <v-list-item v-bind="props" append-icon="mdi-chevron-right">更新状态</v-list-item>
                </template>
                <v-list density="compact">
                  <v-list-item @click="updateStatus(item, 'approved')" class="text-success">已处理</v-list-item>
                  <v-list-item @click="updateStatus(item, 'rejected')" class="text-error">驳回</v-list-item>
                  <v-list-item @click="updateStatus(item, 'pending')">未处理</v-list-item>
                </v-list>
              </v-menu>
            </v-list>
          </v-menu>
        </template>
      </app-data-table>
    </div>

    <!-- 登记信息详情 Dialog -->
    <v-dialog v-model="detailsDialog.show" max-width="600">
      <v-card class="pa-2">
        <v-card-title>登记信息 - {{ detailsDialog.item?.username }}</v-card-title>
        <v-card-text>
          <v-table density="compact" border>
            <thead>
              <tr>
                <th class="text-left">字段</th>
                <th class="text-left">内容</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(val, key) in formatDetails(detailsDialog.item?.registration_info)" :key="key">
                <td>{{ key }}</td>
                <td>{{ val }}</td>
              </tr>
            </tbody>
          </v-table>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="tonal" @click="detailsDialog.show = false">关闭</v-btn>
        </v-card-actions>
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
  max-width: 1000px;
  overflow-x: auto;
}
</style>

<script lang="ts" setup>
import { ref, reactive } from 'vue'
import AppDataTable from '@/components/AppDataTable.vue'

// 类型定义
interface RegisterItem {
  id: string
  username: string
  created_at: string
  status: 'pending' | 'approved' | 'rejected'
  registration_info?: any
}

// 状态管理
const registers = ref<RegisterItem[]>([])
const loading = ref(false)
const totalRegisters = ref(0)
const itemsPerPage = ref(20)
const currentPage = ref(1)
const detailsDialog = reactive({ show: false, item: null as RegisterItem | null })

const snackbar = reactive({ show: false, text: '', color: 'success' })
function showMsg(text: string, color: string = 'success') {
  snackbar.text = text
  snackbar.color = color
  snackbar.show = true
}

function openDetailsDialog(item: RegisterItem) {
  detailsDialog.item = item
  detailsDialog.show = true
}

// 配置化表头
const headers = [
  { title: '用户名', key: 'username', searchable: true, filterable: true },
  { title: '登记信息', key: 'details', sortable: false },
  { title: '创建时间', key: 'created_at', sortable: true },
  { title: '登记状态', key: 'status', sortable: true, filterable: true },
  { title: '操作', key: 'actions', sortable: false },
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

function formatDetails(info: any) {
  if (!info) return {}
  const res: any = {}
  for (const [key, val] of Object.entries(info)) {
    if (Array.isArray(val)) {
      res[key] = val.join(' - ')
    } else {
      res[key] = val
    }
  }
  return res
}

// 事件处理
function handleView(item: RegisterItem) {
  openDetailsDialog(item)
}

function updateStatus(item: RegisterItem, status: RegisterItem['status']) {
  item.status = status
  showMsg(`已更新 ${item.username} 的状态为: ${getStatusText(status)}`)
}

// 加载数据
async function loadRegisters(options: any = { page: 1, itemsPerPage: 20 }) {
  loading.value = true
  // 模拟更丰富的数据加载
  setTimeout(() => {
    registers.value = [
      { 
        id: '1', username: '张三', created_at: new Date().toISOString(), status: 'pending', 
        registration_info: { 
          "QQ号": "12345678", "密码": "pass123", "校区": "南校区", "学校名": "XX大学", 
          "跑步用的APP": "运动世界", "一天能跑几次": "2", "特殊要求备注": "无",
          "目前下单的总km数": "50", "跑步的准确时间段": ["06:00-07:00", "18:00-19:00"],
          "学校是第一次开展校园跑吗": "yes", "跑步的时候是否有人脸识别": "yes",
          "学校规定的单次上限-下限公里数": ["3", "5"]
        } 
      },
      { 
        id: '2', username: '李四', created_at: new Date().toISOString(), status: 'approved', 
        registration_info: { 
          "QQ号": "87654321", "密码": "mima987", "校区": "北校区", "学校名": "YY学院", 
          "跑步用的APP": "悦跑圈", "一天能跑几次": "1", "特殊要求备注": "希望能尽快处理",
          "目前下单的总km数": "20", "跑步的准确时间段": ["20:00-21:00"],
          "学校是第一次开展校园跑吗": "no", "跑步的时候是否有人脸识别": "no",
          "学校规定的单次上限-下限公里数": ["2", "4"]
        } 
      },
      { 
        id: '3', username: '王五', created_at: new Date().toISOString(), status: 'rejected', 
        registration_info: { 
          "QQ号": "55566677", "密码": "xyz789", "校区": "西校区", "学校名": "ZZ理工", 
          "跑步用的APP": "咕咚", "一天能跑几次": "3", "特殊要求备注": "备注测试",
          "目前下单的总km数": "100", "跑步的准确时间段": ["05:00-06:00"],
          "学校是第一次开展校园跑吗": "yes", "跑步的时候是否有人脸识别": "yes",
          "学校规定的单次上限-下限公里数": ["1", "10"]
        } 
      }
    ]
    totalRegisters.value = 3
    loading.value = false
  }, 500)
}
</script>
