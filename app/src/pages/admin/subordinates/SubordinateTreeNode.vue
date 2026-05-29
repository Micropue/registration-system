<template>
  <div>
    <v-list-item
      :value="node.uid"
      :active="selectedUid === node.uid"
      active-color="#1677ff"
      @click="$emit('select', node)"
      class="tree-node py-1"
      density="compact"
      :style="{ paddingLeft: (level <= 1 ? 8 : 4) + level * 16 + 'px' }"
      min-height="38"
    >
      <template v-slot:prepend>
        <div class="d-flex align-center" style="width: 28px; flex-shrink: 0">
          <v-icon v-if="node.children && node.children.length" size="18"
            :class="expanded ? 'rotate-open' : ''"
            @click.stop="expanded = !expanded"
            class="expand-icon"
            color="grey-darken-1">
            mdi-chevron-right
          </v-icon>
          <v-icon v-else size="6" color="grey-lighten-1" class="ml-2">mdi-circle-small</v-icon>
        </div>
        <v-icon v-if="node.is_delegated" size="14" color="#D97706"
          class="mr-1" title="已链接余额">mdi-link-variant</v-icon>
        <v-icon v-else size="18" :color="selectedUid === node.uid ? '#1677ff' : '#9CA3AF'">
          mdi-account-outline
        </v-icon>
      </template>
      <template v-slot:title>
        <div class="d-flex align-center">
          <span class="text-body-2 font-weight-medium">{{ node.username }}</span>
          <v-chip v-if="node.group_name" size="x-small" class="ml-2" variant="flat"
            :color="node.group_name === '超级管理员' ? '#DC2626' : node.group_name === '未分配' ? '#6B7280' : '#1677ff'"
            style="font-size: 10px; height: 18px">
            {{ node.group_name }}
          </v-chip>
        </div>
      </template>
      <template v-slot:append>
        <v-btn
          icon="mdi-close-circle-outline"
          size="x-small"
          variant="text"
          color="grey"
          class="remove-btn"
          @click.stop="$emit('remove', node)"
          title="移除此下属"
        />
      </template>
    </v-list-item>
    <div v-if="expanded && node.children && node.children.length">
      <subordinate-tree-node
        v-for="child in node.children"
        :key="child.uid"
        :node="child"
        :selected-uid="selectedUid"
        :level="level + 1"
        @select="$emit('select', $event)"
        @remove="$emit('remove', $event)"
      />
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref } from 'vue'
import type { SubordinateUser } from '@/config/api-type'

defineProps<{
  node: SubordinateUser
  selectedUid: string
  level: number
}>()

defineEmits<{
  select: [node: SubordinateUser]
  remove: [node: SubordinateUser]
}>()

const expanded = ref(true)
</script>

<style scoped>
.tree-node {
  transition: background-color 0.15s ease;
  border-radius: 0 8px 8px 0;
  margin-right: 4px;
}

.tree-node:hover {
  background-color: rgba(22, 119, 255, 0.04);
}

.tree-node:hover .remove-btn {
  opacity: 1;
}

.remove-btn {
  opacity: 0;
  transition: opacity 0.15s ease;
}

.expand-icon {
  transition: transform 0.2s ease;
  transform: rotate(0deg);
}

.expand-icon.rotate-open {
  transform: rotate(90deg);
}

:deep(.v-list-item--active) {
  background-color: rgba(22, 119, 255, 0.08) !important;
  border-radius: 0 8px 8px 0;
  margin-right: 4px;
}
</style>
