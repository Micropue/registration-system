<template>
  <div class="app-data-table">
    <!-- 搜索与筛选区域 -->
    <v-card class="elevation-0 mb-4 pa-4" border v-if="showSearch || showFilter">
      <v-row align="center">
        <!-- 动态搜索框 -->
        <v-col v-if="showSearch" cols="12" md="4">
          <v-text-field v-model="search" :label="searchLabel" prepend-inner-icon="mdi-magnify" variant="outlined"
            density="compact" hide-details clearable></v-text-field>
        </v-col>

        <!-- 动态筛选器 -->
        <v-col v-if="showFilter" cols="12" md="3">
          <v-select v-model="filterField" :items="filterableHeaders" item-title="title" item-value="key" label="筛选字段"
            variant="outlined" density="compact" hide-details @update:model-value="filterValue = ''"></v-select>
        </v-col>
        <v-col v-if="showFilter" cols="12" md="3">
          <v-select v-model="filterValue" :items="filterValues" label="筛选值" variant="outlined" density="compact"
            hide-details :disabled="!filterField"></v-select>
        </v-col>

        <v-col cols="12" md="2">
          <v-btn variant="tonal" block @click="resetFilters">重置</v-btn>
        </v-col>
      </v-row>
    </v-card>

    <!-- 数据表格 -->
    <v-card class="elevation-0" border style="overflow: auto; ">
      <!-- 客户端模式：v-data-table 自己处理分页/排序/搜索 -->
      <v-data-table v-if="clientSide" :headers="headers" :items="filteredItems" :loading="loading"
        v-model:page="localPage" v-model:items-per-page="localItemsPerPage"
        items-per-page-text="每页行数" page-text="{0}-{1} 共 {2}" class="elevation-0"
        :row-props="props.rowProps">
        <template v-for="(_, name) in $slots" #[name]="slotProps">
          <slot :name="name" v-bind="slotProps"></slot>
        </template>
      </v-data-table>

      <!-- 服务端模式：v-data-table-server 由外部控制分页 -->
      <v-data-table-server v-else :headers="headers" :items="filteredItems" :loading="loading" v-model:page="localPage"
        v-model:items-per-page="localItemsPerPage" :items-length="totalItems" items-per-page-text="每页行数"
        page-text="{0}-{1} 共 {2}" @update:options="onOptionsUpdate" class="elevation-0"
        :row-props="props.rowProps">
        <template v-for="(_, name) in $slots" #[name]="slotProps">
          <slot :name="name" v-bind="slotProps"></slot>
        </template>
      </v-data-table-server>
    </v-card>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, watch } from 'vue'

interface Header {
  title: string
  key: string
  sortable?: boolean
  searchable?: boolean
  filterable?: boolean
  // 可选：自定义格式化函数（仅用于生成筛选候选值）
  filterFormatter?: (val: any) => string
}

const props = defineProps<{
  headers: Header[]
  items: any[]
  totalItems: number
  loading?: boolean
  itemsPerPage?: number
  page?: number
  showSearch?: boolean
  showFilter?: boolean
  searchLabel?: string
  clientSide?: boolean
  rowProps?: any
}>()

const emit = defineEmits(['update:options', 'update:page', 'update:itemsPerPage', 'reset'])

// 本地状态
const search = ref('')
const filterField = ref('')
const filterValue = ref('')
const localPage = ref(props.page || 1)
const localItemsPerPage = ref(props.itemsPerPage || 20)

// 暴露给外部的计算属性：处理前端过滤和搜索
const filteredItems = computed(() => {
  let result = [...props.items]

  // 1. 字段筛选
  if (filterField.value && filterValue.value) {
    const header = props.headers.find(h => h.key === filterField.value)
    result = result.filter(item => {
      const rawVal = item[filterField.value]
      const displayVal = header?.filterFormatter ? header.filterFormatter(rawVal) : String(rawVal)
      return displayVal === filterValue.value
    })
  }

  // 2. 纯前端搜索 (include)
  if (search.value) {
    const q = search.value.toLowerCase()
    const searchableKeys = props.headers.filter(h => h.searchable).map(h => h.key)
    
    result = result.filter(item => 
      searchableKeys.some(key => {
        const val = item[key]
        return val !== null && val !== undefined && String(val).toLowerCase().includes(q)
      })
    )
  }

  return result
})

// 筛选候选值计算
const filterableHeaders = computed(() => props.headers.filter(h => h.filterable))
const filterValues = computed(() => {
  if (!filterField.value) return []
  const header = props.headers.find(h => h.key === filterField.value)
  const values = props.items.map(item => {
    const val = item[filterField.value]
    if (val === null || val === undefined) return null
    return header?.filterFormatter ? header.filterFormatter(val) : String(val)
  }).filter(Boolean)
  return [...new Set(values)]
})

// 事件处理
function onOptionsUpdate(options: any) {
  emit('update:options', options)
}

function resetFilters() {
  search.value = ''
  filterField.value = ''
  filterValue.value = ''
  emit('reset')
}

// 同步外部 Props
watch(() => props.page, (val) => { if (val) localPage.value = val })
watch(() => props.itemsPerPage, (val) => { if (val) localItemsPerPage.value = val })
watch(localPage, (val) => emit('update:page', val))
watch(localItemsPerPage, (val) => emit('update:itemsPerPage', val))

</script>

<style scoped>
.app-data-table :deep(.v-data-table) {
  width: 100% !important;
  min-width: 800px;
}
.app-data-table :deep(th) {
  white-space: nowrap !important;
}
</style>
