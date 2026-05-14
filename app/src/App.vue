<template>
  <v-app class="d-flex flex-column h-screen overflow-hidden">
    <!-- 侧边抽屉 (移动端) -->
    <v-navigation-drawer v-model="drawer" temporary class="d-md-none border-0" elevation="16" width="300">
      <v-img height="160" src="https://cdn.vuetifyjs.com/images/backgrounds/vbanner.jpg" cover class="align-end">
        <div class="pa-4 bg-gradient-overlay text-white">
          <v-avatar size="64" class="mb-3 border-white border-md shadow-lg">
            <v-img src="@/assets/logo.jpg" alt="Logo"></v-img>
          </v-avatar>
          <div class="text-h6 font-weight-bold mb-0 d-flex align-center">
            {{ user ? user.username : '哆啦A梦（校园跑版）' }}
            <v-progress-circular v-if="isPageLoading" indeterminate color="white" size="16" width="2"
              class="ms-2"></v-progress-circular>
          </div>
          <div v-if="user" class="text-caption opacity-80">
            {{ user.type === 'admin' ? '系统管理员' : '普通账户' }}
          </div>
        </div>
      </v-img>

      <v-list nav density="comfortable" class="pa-3">
        <v-list-subheader class="text-uppercase font-weight-bold">业务菜单</v-list-subheader>

        <v-list-item v-for="item in displayFunctions" :key="item.to" :prepend-icon="item.icon" :title="item.title" :to="item.to"
          rounded="xl" active-color="primary" class="mb-1 px-6"></v-list-item>
      </v-list>

      <template v-slot:append v-if="user">
        <div class="pa-4">
          <v-btn block color="error" variant="tonal" prepend-icon="mdi-logout" class="rounded-pill" @click="handleLogout">
            退出登录
          </v-btn>
        </div>
      </template>
    </v-navigation-drawer>

    <!-- 顶部导航栏 -->
    <v-app-bar app color="rgba(255, 255, 255, 0.8)" flat class="px-3 px-md-10 border-b flex-grow-0"
      style="backdrop-filter: blur(12px);">
      <v-container class="d-flex align-center pa-0" fluid>
        <div class="d-flex align-center cursor-pointer" @click="$router.push('/')">
          <v-avatar size="40" class="me-3">
            <v-img src="@/assets/logo.jpg"></v-img>
          </v-avatar>
          <span class="logo-text font-weight-black color-primary d-none d-sm-flex">
            哆啦A梦（校园跑版）
          </span>
        </div>

        <v-divider vertical inset class="mx-6 d-none d-md-flex"></v-divider>

        <div class="d-none d-md-flex gap-2">
          <v-btn v-for="item in displayFunctions" :key="item.to" variant="text" :to="item.to" class="rounded-pill px-6"
            active-color="primary" :prepend-icon="item.icon">{{ item.title }}</v-btn>
        </div>

        <v-spacer></v-spacer>

        <div class="d-flex align-center">
          <!-- 页面加载动画 -->
          <v-fade-transition>
            <v-progress-circular v-if="isPageLoading" indeterminate color="primary" size="20" width="2"
              class="me-4"></v-progress-circular>
          </v-fade-transition>

          <template v-if="user">
            <span class="text-body-2 font-weight-bold me-4 color-primary d-none d-sm-inline">
              已登录：{{ user.username }}
            </span>
            <v-btn color="error" variant="tonal" class="rounded-pill px-4 font-weight-bold" @click="handleLogout">
              退出登录
            </v-btn>
          </template>
          <v-btn v-else-if="!isAuthChecking" color="primary" variant="flat" to="/login"
            class="rounded-pill px-6 font-weight-bold" elevation="0">
            登录
          </v-btn>
          <v-btn v-else color="primary" variant="flat" class="rounded-pill px-6 font-weight-bold" elevation="0"
            disabled loading>
            检测中
          </v-btn>

          <v-app-bar-nav-icon class="d-md-none ms-2" @click="drawer = !drawer"></v-app-bar-nav-icon>
        </div>
      </v-container>
    </v-app-bar>

    <v-main class="bg-grey-lighten-4 flex-grow-1 overflow-y-auto">
      <div class="main-gradient-bg"></div>
      <RouterView />
    </v-main>
  </v-app>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { checkLoginStatus } from '@/api/auth'
import { cookie } from '@/api/cookie'
import { functions } from '@/config/functions'
import { useAppStore } from '@/stores/app'
import type { CheckLoginData } from '@/config/api-type'

const router = useRouter()
const route = useRoute()
const appStore = useAppStore()
const drawer = ref(false)
const user = ref<CheckLoginData | null>(null)
const isAuthChecking = ref(true)

// 页面加载状态
const isPageLoading = computed(() => appStore.isPageLoading)

// 根据用户角色过滤功能菜单
const displayFunctions = computed(() => {
  if (!user.value) return []
  return functions.filter(item => {
    const targetRole = item.role || 'default'
    return user.value?.type === targetRole
  })
})

async function fetchUser() {
  isAuthChecking.value = true
  user.value = await checkLoginStatus()
  appStore.setUserInfo(user.value)
  isAuthChecking.value = false
}

function handleLogout() {
  cookie.remove('token')
  user.value = null
  appStore.setUserInfo(null)
  router.push('/login')
}

// 初始加载及路由变化时检查登录状态
onMounted(fetchUser)
watch(() => route.path, fetchUser)
</script>

<style>
/* 全局字体大小调整 */
.logo-text {
  font-size: 16px !important;
  /* line-height: 1.2 !important; */
}

/* 品牌颜色 */
.color-primary {
  color: #1867C0;
}


/* 抽屉顶部渐变：确保在背景图上文字清晰 */
.bg-gradient-overlay {
  background: linear-gradient(to top, rgba(0, 0, 0, 0.8) 0%, transparent 100%);
  width: 100%;
}

/* 桌面背景装饰 */
.main-gradient-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 400px;
  background: linear-gradient(180deg, rgba(24, 103, 192, 0.08) 0%, rgba(255, 255, 255, 0) 100%);
  pointer-events: none;
}

/* 深度选择器修改 Vuetify 内部样式 */
:deep(.v-navigation-drawer__content) {
  overflow-y: auto;
}

/* 激活项样式强化 */
:deep(.v-list-item--active) {
  background: rgba(24, 103, 192, 0.1) !important;
  color: #1867C0 !important;
}

/* 间距辅助 */
.gap-2 {
  gap: 8px;
}

.cursor-pointer {
  cursor: pointer;
}

.border-md {
  border-width: 2px !important;
  border-style: solid;
}
</style>
