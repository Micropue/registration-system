<template>
  <v-container fluid class="pa-4 pa-md-6">
    <div class="mb-4">
      <h1 class="text-h4 font-weight-bold">仪表盘</h1>
      <p class="text-body-2 text-medium-emphasis mt-1">系统运行数据概览</p>
    </div>

    <v-row v-if="loading" class="py-8">
      <v-col cols="12" class="d-flex justify-center">
        <v-progress-circular indeterminate color="primary" size="48"></v-progress-circular>
      </v-col>
    </v-row>

    <template v-else>
      <!-- 统计卡片 -->
      <v-row dense>
        <v-col cols="6" sm="4" md="3" lg="2">
          <v-card class="stat-card" border rounded="lg" @click="router.push('/admin/users')">
            <div class="pa-4 d-flex align-center">
              <v-avatar color="primary" variant="tonal" size="44" class="me-3">
                <v-icon size="24">mdi-account-group</v-icon>
              </v-avatar>
              <div>
                <div class="text-h5 font-weight-bold">{{ stats.total_users }}</div>
                <div class="text-caption text-medium-emphasis">用户总数</div>
              </div>
            </div>
          </v-card>
        </v-col>

        <v-col cols="6" sm="4" md="3" lg="2">
          <v-card class="stat-card" border rounded="lg" @click="router.push('/admin/registers')">
            <div class="pa-4 d-flex align-center">
              <v-avatar color="success" variant="tonal" size="44" class="me-3">
                <v-icon size="24">mdi-file-document-multiple</v-icon>
              </v-avatar>
              <div>
                <div class="text-h5 font-weight-bold">{{ stats.total_registrations }}</div>
                <div class="text-caption text-medium-emphasis">订单总数</div>
              </div>
            </div>
          </v-card>
        </v-col>

        <v-col cols="6" sm="4" md="3" lg="2">
          <v-card class="stat-card" border rounded="lg" @click="router.push('/admin/registers')">
            <div class="pa-4 d-flex align-center">
              <v-avatar color="warning" variant="tonal" size="44" class="me-3">
                <v-icon size="24">mdi-clock-outline</v-icon>
              </v-avatar>
              <div>
                <div class="text-h5 font-weight-bold">{{ stats.pending_registrations }}</div>
                <div class="text-caption text-medium-emphasis">待处理订单</div>
              </div>
            </div>
          </v-card>
        </v-col>

        <v-col cols="6" sm="4" md="3" lg="2">
          <v-card class="stat-card" border rounded="lg" @click="router.push('/admin/feedbacks')">
            <div class="pa-4 d-flex align-center">
              <v-avatar color="info" variant="tonal" size="44" class="me-3">
                <v-icon size="24">mdi-ticket-confirmation</v-icon>
              </v-avatar>
              <div>
                <div class="text-h5 font-weight-bold">{{ stats.total_feedbacks }}</div>
                <div class="text-caption text-medium-emphasis">工单总数</div>
              </div>
            </div>
          </v-card>
        </v-col>

        <v-col cols="6" sm="4" md="3" lg="2">
          <v-card class="stat-card" border rounded="lg" @click="router.push('/admin/feedbacks')">
            <div class="pa-4 d-flex align-center">
              <v-avatar color="error" variant="tonal" size="44" class="me-3">
                <v-icon size="24">mdi-alert-circle-outline</v-icon>
              </v-avatar>
              <div>
                <div class="text-h5 font-weight-bold">{{ stats.pending_feedbacks }}</div>
                <div class="text-caption text-medium-emphasis">待处理工单</div>
              </div>
            </div>
          </v-card>
        </v-col>

        <v-col cols="6" sm="4" md="3" lg="2">
          <v-card class="stat-card" border rounded="lg" @click="router.push('/admin/settings/running-apps')">
            <div class="pa-4 d-flex align-center">
              <v-avatar color="purple" variant="tonal" size="44" class="me-3">
                <v-icon size="24">mdi-run-fast</v-icon>
              </v-avatar>
              <div>
                <div class="text-h5 font-weight-bold">{{ stats.total_apps }}</div>
                <div class="text-caption text-medium-emphasis">跑步APP</div>
              </div>
            </div>
          </v-card>
        </v-col>
      </v-row>

      <!-- 今日数据 -->
      <v-row dense class="mt-2">
        <v-col cols="6" sm="4" md="3">
          <v-card border rounded="lg" class="h-100">
            <div class="pa-4">
              <div class="d-flex align-center mb-2">
                <v-icon color="success" size="20" class="me-1">mdi-trending-up</v-icon>
                <span class="text-caption text-medium-emphasis">今日新增订单</span>
              </div>
              <span class="text-h4 font-weight-bold text-success">{{ stats.today_registrations }}</span>
            </div>
          </v-card>
        </v-col>
        <v-col cols="6" sm="4" md="3">
          <v-card border rounded="lg" class="h-100">
            <div class="pa-4">
              <div class="d-flex align-center mb-2">
                <v-icon color="info" size="20" class="me-1">mdi-message-text</v-icon>
                <span class="text-caption text-medium-emphasis">今日新增工单</span>
              </div>
              <span class="text-h4 font-weight-bold text-info">{{ stats.today_feedbacks }}</span>
            </div>
          </v-card>
        </v-col>
        <v-col cols="6" sm="4" md="3">
          <v-card border rounded="lg" class="h-100">
            <div class="pa-4">
              <div class="d-flex align-center mb-2">
                <v-icon color="primary" size="20" class="me-1">mdi-chat-processing</v-icon>
                <span class="text-caption text-medium-emphasis">今日聊天消息</span>
              </div>
              <span class="text-h4 font-weight-bold text-primary">{{ stats.today_chats }}</span>
            </div>
          </v-card>
        </v-col>
        <v-col cols="6" sm="4" md="3">
          <v-card border rounded="lg" class="h-100">
            <div class="pa-4">
              <div class="d-flex align-center mb-2">
                <v-icon color="purple" size="20" class="me-1">mdi-account-plus</v-icon>
                <span class="text-caption text-medium-emphasis">总用户数</span>
              </div>
              <span class="text-h4 font-weight-bold text-purple">{{ stats.total_users }}</span>
            </div>
          </v-card>
        </v-col>
      </v-row>

      <!-- 快捷入口 -->
      <v-row class="mt-4">
        <v-col cols="12">
          <v-card border rounded="lg">
            <v-card-title class="text-subtitle-1 pa-4 pb-2">快捷操作</v-card-title>
            <v-card-text class="pa-4 pt-0">
              <div class="d-flex flex-wrap ga-2">
                <v-btn variant="tonal" rounded color="primary" prepend-icon="mdi-file-document-edit-outline" :to="'/admin/registers'">订单处理</v-btn>
                <v-btn variant="tonal" rounded color="info" prepend-icon="mdi-ticket-confirmation-outline" :to="'/admin/feedbacks'">工单处理</v-btn>
                <v-btn variant="tonal" rounded color="success" prepend-icon="mdi-account-group-outline" :to="'/admin/users'">账户管理</v-btn>
                <v-btn variant="tonal" rounded color="secondary" prepend-icon="mdi-run-fast" :to="'/admin/settings/running-apps'">APP管理</v-btn>
                <v-btn variant="tonal" rounded color="purple" prepend-icon="mdi-cog-outline" :to="'/admin/settings'">系统设置</v-btn>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </template>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ajax } from '@/api/ajax'
import { cookie } from '@/api/cookie'
import { ApiUrl } from '@/config/api-url'

const router = useRouter()
const loading = ref(true)
const stats = ref({
  total_users: 0,
  total_registrations: 0,
  pending_registrations: 0,
  total_feedbacks: 0,
  pending_feedbacks: 0,
  today_registrations: 0,
  today_feedbacks: 0,
  total_apps: 0,
  today_chats: 0
})

onMounted(async () => {
  try {
    const res = await ajax<any>(ApiUrl.DASHBOARD_STATS, {
      headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
    })
    if (res.code === 200) {
      stats.value = res.data
    }
  } catch { /* ignore */ }
  finally { loading.value = false }
})
</script>

<style scoped>
.stat-card {
  cursor: pointer;
  transition: transform 0.15s, box-shadow 0.15s;
}
.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0,0,0,0.08);
}
</style>
