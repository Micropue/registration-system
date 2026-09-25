<template>
  <div>
    <!-- 横向设置菜单 -->
    <div class="bg-white border-b d-flex align-center px-4 overflow-x-auto"
      style="position: sticky; top: 0; z-index: 10; min-height: 48px; white-space: nowrap; flex-wrap: nowrap;">
      <v-btn
        v-for="item in settingsMenu"
        :key="item.to"
        variant="text"
        :to="item.to"
        class="rounded-pill"
        active-color="primary"
        :prepend-icon="item.icon"
      >{{ item.title }}</v-btn>
    </div>
    <router-view></router-view>
  </div>
</template>

<script setup lang="ts">
const settingsMenu = [
  { title: 'APP配置', to: '/admin/settings/apps', icon: 'mdi-apps' }
]
</script>
