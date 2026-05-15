<template>
  <div>
    <!-- 横向设置菜单 -->
    <div class="bg-white border-b d-flex align-center px-4"
      style="position: sticky; top: 0; z-index: 10; min-height: 48px;">
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
  { title: '登记字段配置', to: '/admin/settings/fields', icon: 'mdi-form-select' }
]
</script>
