<template>
  <v-layout class="fill-height">
    <!-- 左侧导航栏 -->
    <v-navigation-drawer 
      v-model="drawer"
      :rail="rail"
      :permanent="$vuetify.display.mdAndUp"
      :temporary="!$vuetify.display.mdAndUp"
      @click="rail = false"
      width="250"
    >
      <v-list density="compact" nav>
        <v-list-item
          prepend-icon="mdi-form-select"
          title="登记字段配置"
          value="fields"
          to="/admin/settings/fields"
        ></v-list-item>
      </v-list>

      <template v-slot:append>
        <v-list-item
          v-if="!rail"
          prepend-icon="mdi-chevron-left"
          title="收起菜单"
          nav
          @click.stop="rail = true"
        ></v-list-item>
      </template>
    </v-navigation-drawer>

    <!-- 右侧内容区域 -->
    <v-main>
      <v-container v-if="!$vuetify.display.mdAndUp" class="pa-2">
        <v-btn icon="mdi-menu" variant="text" @click.stop="drawer = !drawer"></v-btn>
      </v-container>
      <router-view></router-view>
    </v-main>
  </v-layout>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const drawer = ref(true)
const rail = ref(false)
</script>
