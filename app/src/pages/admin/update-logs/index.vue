<template>
  <v-container fluid class="pa-0 d-flex flex-column align-center">
    <div class="table-wrapper mt-4">
      <h1 class="text-h5 text-sm-h4 mb-4">更新日志</h1>

      <v-timeline side="end" density="compact" align="start" line-inset="8" class="hidden-xs">
        <v-timeline-item
          v-for="log in logs"
          :key="log.version"
          dot-color="primary"
          size="x-small"
        >
          <template v-slot:opposite>
            <div class="text-caption text-medium-emphasis pt-1">{{ log.date }}</div>
          </template>
          <v-card elevation="0" border rounded="md" class="mb-2">
            <v-card-title class="py-3 px-3" style="word-break: break-word; white-space: normal">
              <v-chip size="x-small" color="primary" variant="flat" class="mr-2 mb-1">{{ log.version }}</v-chip>
              {{ log.title }}
            </v-card-title>
            <v-divider />
            <v-card-text class="pa-3">
              <ul class="text-body-2 pl-4 mb-0" style="list-style-type: disc">
                <li v-for="(d, i) in log.details" :key="i" class="mb-1">{{ d }}</li>
              </ul>
            </v-card-text>
          </v-card>
        </v-timeline-item>
      </v-timeline>

      <div class="hidden-sm-and-up">
        <v-card v-for="log in logs" :key="log.version" elevation="0" border rounded="md" class="mb-3">
          <v-card-title class="py-3 px-3" style="word-break: break-word; white-space: normal">
            <v-chip size="x-small" color="primary" variant="flat" class="mr-2 mb-1">{{ log.version }}</v-chip>
            {{ log.title }}
          </v-card-title>
          <v-divider />
          <v-card-subtitle class="text-caption text-medium-emphasis pa-3 pb-0">{{ log.date }}</v-card-subtitle>
          <v-card-text class="pa-3 pt-1">
            <ul class="text-body-2 pl-4 mb-0" style="list-style-type: disc">
              <li v-for="(d, i) in log.details" :key="i" class="mb-1">{{ d }}</li>
            </ul>
          </v-card-text>
        </v-card>
      </div>
    </div>
  </v-container>
</template>

<style scoped>
.table-wrapper { width: 90%; padding: 0 16px; }
@media (max-width: 600px) {
  .table-wrapper { width: 100%; padding: 0 12px; }
}
</style>

<script lang="ts" setup>
import { updateLogs } from '@/config/update-logs'

const logs = updateLogs
</script>
