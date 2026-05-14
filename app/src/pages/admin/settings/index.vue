<template>
  <v-layout class="fill-height">
    <v-navigation-drawer v-model="drawer" :rail="rail" :permanent="$vuetify.display.mdAndUp"
      :temporary="!$vuetify.display.mdAndUp" @click="rail = false" width="250">
      <v-list density="compact" nav>
        <v-list-item prepend-icon="mdi-form-select" title="登记字段配置" value="fields"
          to="/admin/settings/fields"></v-list-item>
      </v-list>

      <template v-slot:append>
        <v-list-item v-if="!rail" prepend-icon="mdi-chevron-left" title="收起菜单" nav
          @click.stop="rail = true"></v-list-item>
      </template>
    </v-navigation-drawer>

    <v-main style="height: calc(100vh - 65px); overflow-y: auto;">
      <!-- 移动端侧边栏切换按钮 -->
      <div v-if="!$vuetify.display.mdAndUp" class="d-flex align-center pa-2 bg-white border-b"
        style="position: sticky; top: 0; z-index: 10;">
        <v-btn icon="mdi-menu" variant="text" @click="drawer = !drawer" color="primary"></v-btn>
        <span class="text-subtitle-1 font-weight-bold ms-2">设置菜单</span>
      </div>
      <router-view></router-view>
    </v-main>
  </v-layout>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const drawer = ref(true)
const rail = ref(false)
</script>
