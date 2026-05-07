<template>
  <v-app>
    <v-navigation-drawer v-model="drawer" temporary class="d-md-none border-0" elevation="16" width="300">
      <v-img height="160" src="https://cdn.vuetifyjs.com/images/backgrounds/vbanner.jpg" cover class="align-end">
        <div class="pa-4 bg-gradient-overlay text-white">
          <v-avatar size="64" class="mb-3 border-white border-md shadow-lg">
            <v-img src="@/assets/logo.jpg" alt="Logo"></v-img>
          </v-avatar>
          <div class="text-h6 font-weight-bold mb-0">虎虎校园跑</div>
        </div>
      </v-img>

      <v-list nav density="comfortable" class="pa-3">
        <v-list-subheader class="text-uppercase font-weight-bold">业务菜单</v-list-subheader>

        <v-list-item prepend-icon="mdi-plus-circle-outline" title="数据登记" to="/register" rounded="xl"
          active-color="primary" class="mb-1"></v-list-item>

        <v-list-item prepend-icon="mdi-message-text-outline" title="工单反馈" to="/feedback" rounded="xl"
          active-color="primary" class="mb-1"></v-list-item>
      </v-list>

      <template v-slot:append>
        <div class="pa-4">
          <v-btn block color="error" variant="tonal" prepend-icon="mdi-logout" class="rounded-pill">
            退出登录
          </v-btn>
        </div>
      </template>
    </v-navigation-drawer>

    <v-app-bar app color="rgba(255, 255, 255, 0.8)" flat class="px-3 px-md-10 border-b"
      style="backdrop-filter: blur(12px);">
      <v-container class="d-flex align-center pa-0" fluid>
        <div class="d-flex align-center cursor-pointer" @click="$router.push('/')">
          <v-avatar size="40" class="me-3">
            <v-img src="@/assets/logo.jpg"></v-img>
          </v-avatar>
          <span class="text-h6 font-weight-black color-primary d-none d-sm-flex">
            虎虎校园跑
          </span>
        </div>

        <v-divider vertical inset class="mx-6 d-none d-md-flex"></v-divider>

        <div class="d-none d-md-flex gap-2">
          <v-btn variant="text" to="/register" class="rounded-pill px-6" active-color="primary">登记</v-btn>
          <v-btn variant="text" to="/feedback" class="rounded-pill px-6" active-color="primary">工单反馈</v-btn>
        </div>

        <v-spacer></v-spacer>

        <div class="d-flex align-center">
          <v-btn color="primary" variant="flat" to="/login" class="rounded-pill px-6 font-weight-bold" elevation="0">
            登录
          </v-btn>

          <v-app-bar-nav-icon class="d-md-none ms-2" @click="drawer = !drawer"></v-app-bar-nav-icon>
        </div>
      </v-container>
    </v-app-bar>

    <v-main class="bg-grey-lighten-4">
      <div class="main-gradient-bg"></div>

      <v-container class="py-8 position-relative fill-height">
        <RouterView />
      </v-container>
    </v-main>
  </v-app>
</template>

<script setup lang="ts">
import { ref } from 'vue'
const drawer = ref(false)
</script>

<style scoped>
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

/* 页面切换动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

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