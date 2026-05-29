<template>
  <v-container fluid class="d-flex align-center justify-center" style="min-height: calc(100vh - 64px);">
    <div class="text-center">
      <h1 class="text-h1 font-weight-bold text-primary mb-2">404</h1>
      <h2 class="text-h5 text-medium-emphasis mb-1">页面未找到</h2>
      <p class="text-body-2 text-disabled mb-6">你访问的页面不存在或已被移除</p>
      <v-btn color="primary" variant="flat" rounded="pill" size="large" to="/">
        <v-icon start>mdi-home-outline</v-icon>
        返回首页
      </v-btn>
    </div>
  </v-container>
</template>
