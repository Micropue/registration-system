<template>
  <v-container fluid class="pa-0 d-flex flex-column align-center">
    <div class="table-wrapper mt-4">
      <div class="d-flex justify-space-between align-center mb-4">
        <h1 class="text-h4">账户组管理</h1>
        <v-btn color="primary" prepend-icon="mdi-plus" @click="openCreateDialog">新建账户组</v-btn>
      </div>

      <app-data-table
        :headers="headers"
        :items="groups"
        :total-items="groups.length"
        :loading="loading"
        client-side
        show-search
        search-label="搜索组名"
      >
        <template v-slot:item.name="{ item }">
          <v-chip size="small" :color="item.name === '超级管理员' ? 'error' : 'primary'">
            {{ item.name }}
          </v-chip>
        </template>
        <template v-slot:item.created_at="{ item }">
          {{ formatDate(item.created_at) }}
        </template>
        <template v-slot:item.actions="{ item }">
          <v-btn variant="tonal" rounded size="small" color="primary" @click="openEditDialog(item)">编辑</v-btn>
          <v-btn v-if="item.name !== '超级管理员'" class="ml-2" variant="tonal" rounded size="small" color="error" @click="confirmDelete(item)">删除</v-btn>
        </template>
      </app-data-table>
    </div>

    <v-dialog v-model="dialog.show" max-width="800" persistent>
      <v-card class="pa-4">
        <v-card-title>{{ dialog.isNew ? '新建账户组' : '编辑账户组' }}</v-card-title>
        <v-card-text>
          <v-text-field v-model="dialog.name" label="组名" variant="outlined" density="comfortable" :disabled="dialog.uid ? groups.find(g => g.uid === dialog.uid)?.name === '超级管理员' : false"></v-text-field>
          <div class="text-subtitle-2 mt-4 mb-2">权限配置<template v-if="dialog.uid && groups.find(g => g.uid === dialog.uid)?.name === '超级管理员'"><span class="text-caption text-grey">（超级管理员组权限不可修改）</span></template></div>
           <div v-for="(perms, category) in dialog.permissions" :key="category" class="mb-3">
            <div class="font-weight-bold text-body-2 mb-1">{{ category }}</div>
            <div v-if="typeof perms === 'object'" class="ml-4">
              <template v-for="(enabled, permKey) in perms" :key="permKey">
                <template v-if="typeof enabled === 'object' && !Array.isArray(enabled)">
                  <v-checkbox
                    :label="String(permKey)"
                    :model-value="areAllTrue(enabled)"
                    :indeterminate="isPartialTrue(enabled)"
                    @update:model-value="setAllSub((dialog.permissions[category] as Record<string,any>)[permKey] as Record<string,any>, $event)"
                    density="compact" hide-details color="primary"
                    :disabled="!!dialog.uid && groups.find(g => g.uid === dialog.uid)?.name === '超级管理员'" />
                  <div class="ml-6">
                    <v-checkbox
                      v-for="(v, subKey) in enabled"
                      :key="subKey"
                      :model-value="v"
                      @update:model-value="((dialog.permissions[category] as Record<string,any>)[permKey] as Record<string,any>)[subKey] = $event"
                      :label="String(subKey)"
                      density="compact" hide-details color="primary"
                      :disabled="!!dialog.uid && groups.find(g => g.uid === dialog.uid)?.name === '超级管理员'" />
                  </div>
                </template>
                <v-checkbox v-else
                  :model-value="enabled"
                  @update:model-value="(dialog.permissions[category] as Record<string,any>)[permKey] = $event"
                  :label="String(permKey)" density="compact" hide-details color="primary"
                  :disabled="!!dialog.uid && groups.find(g => g.uid === dialog.uid)?.name === '超级管理员'" />
              </template>
            </div>
            <v-checkbox v-else v-model="dialog.permissions[category]"
              :label="category" density="compact" hide-details color="primary" class="ml-4"
              :disabled="!!dialog.uid && groups.find(g => g.uid === dialog.uid)?.name === '超级管理员'" />
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="tonal" @click="dialog.show = false">取消</v-btn>
          <v-btn color="primary" variant="flat" :loading="saving" @click="saveGroup">保存</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="deleteDialog.show" max-width="400">
      <v-card class="pa-4">
        <v-card-title>确认删除</v-card-title>
        <v-card-text>确定要删除账户组「{{ deleteDialog.name }}」吗？该组成员将失去权限。</v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="tonal" @click="deleteDialog.show = false">取消</v-btn>
          <v-btn color="error" variant="flat" @click="doDelete">确认删除</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-snackbar v-model="snackbar.show" :color="snackbar.color" timeout="3000">
      {{ snackbar.text }}
    </v-snackbar>
  </v-container>
</template>

<style scoped>
.table-wrapper { width: 90%; }
</style>

<script lang="ts" setup>
import { ref, reactive, onMounted } from 'vue'
import { ajax } from '@/api/ajax'
import { cookie } from '@/api/cookie'
import { ApiUrl } from '@/config/api-url'
import type { UserGroup } from '@/config/api-type'
import AppDataTable from '@/components/AppDataTable.vue'

const groups = ref<UserGroup[]>([])
const loading = ref(false)
const saving = ref(false)
const dialog = reactive({ show: false, isNew: false, uid: '', name: '', permissions: {} as Record<string, any> })
const deleteDialog = reactive({ show: false, uid: '', name: '' })
const snackbar = reactive({ show: false, text: '', color: 'success' })

const headers = [
  { title: '组名', key: 'name', searchable: true },
  { title: '创建时间', key: 'created_at', sortable: true },
  { title: '操作', key: 'actions', sortable: false },
]

function showMsg(text: string, color = 'success') {
  snackbar.text = text; snackbar.color = color; snackbar.show = true
}

function formatDate(iso: string) {
  return iso ? new Date(iso).toLocaleString('zh-CN') : '-'
}

function defaultPermissions(): Record<string, any> {
  return {
    "账户管理": { "查看": { "下属用户": false, "其他用户": false }, "创建": false, "修改": false, "删除": false, "强制下线": false },
    "账户组管理": { "查看": false, "创建": false, "修改": false, "删除": false },
    "订单处理": { "查看": false, "处理": false, "驳回": false, "删除": false, "修改": false },
    "工单处理": { "查看": false, "回复": false, "解决": false, "删除": false },
    "APP配置": { "查看": false, "修改": false, "余额管理": false },
    "充值审批": { "查看": false, "处理": false },
    "下属管理": { "查看": false, "配置": false },
    "公告管理": { "查看": false, "编辑": false, "发布": false, "删除": false },
    "新建登记": false,
    "新建工单": false,
    "充值申请": false,
    "余额查看": false,
  }
}

function areAllTrue(obj: Record<string, any>): boolean {
  return Object.values(obj).every(v => v === true)
}

function isPartialTrue(obj: Record<string, any>): boolean {
  const values = Object.values(obj)
  return values.some(v => v === true) && !values.every(v => v === true)
}

function setAllSub(obj: Record<string, any>, value: boolean | null) {
  Object.keys(obj).forEach(k => { obj[k] = !!value })
}

async function loadGroups() {
  loading.value = true
  try {
    const res = await ajax<UserGroup[]>(ApiUrl.GET_GROUPS, {
      headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
    })
    if (res.code === 200) groups.value = res.data
  } catch (e) { /* ignore */ }
  finally { loading.value = false }
}

function openCreateDialog() {
  dialog.isNew = true
  dialog.uid = ''
  dialog.name = ''
  dialog.permissions = defaultPermissions()
  dialog.show = true
}

function openEditDialog(group: UserGroup) {
  dialog.isNew = false
  dialog.uid = group.uid
  dialog.name = group.name
  const raw = JSON.parse(JSON.stringify(group.permissions))
  dialog.permissions = normalizePermissions({ ...defaultPermissions(), ...raw }, defaultPermissions())
  dialog.show = true
}

function normalizePermissions(perms: Record<string, any>, defaults: Record<string, any>): Record<string, any> {
  const result: Record<string, any> = {}
  for (const [key, defaultValue] of Object.entries(defaults)) {
    const current = perms[key]
    if (typeof defaultValue === 'object' && !Array.isArray(defaultValue) && typeof current !== 'object') {
      const oldVal = !!current
      const newDict: Record<string, boolean> = {}
      for (const subKey of Object.keys(defaultValue as Record<string, any>)) {
        newDict[subKey] = oldVal
      }
      result[key] = newDict
    } else if (typeof defaultValue === 'object' && !Array.isArray(defaultValue) && typeof current === 'object' && !Array.isArray(current)) {
      result[key] = normalizePermissions(current, defaultValue)
    } else {
      result[key] = current !== undefined ? current : defaultValue
    }
  }
  return result
}

async function saveGroup() {
  saving.value = true
  try {
    const token = cookie.get('token') || ''
    if (dialog.isNew) {
      const res = await ajax(ApiUrl.CREATE_GROUP, {
        method: 'POST',
        body: { name: dialog.name, permissions: dialog.permissions },

        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (res.code === 200) { showMsg('创建成功'); dialog.show = false; loadGroups() }
      else showMsg(res.msg, 'error')
    } else {
      const res = await ajax(`${ApiUrl.UPDATE_GROUP}/${dialog.uid}`, {
        method: 'PATCH',
        body: { name: dialog.name, permissions: dialog.permissions },

        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (res.code === 200) { showMsg('更新成功'); dialog.show = false; loadGroups() }
      else showMsg(res.msg, 'error')
    }
  } catch (e) { showMsg('操作失败', 'error') }
  finally { saving.value = false }
}

function confirmDelete(group: UserGroup) {
  deleteDialog.uid = group.uid
  deleteDialog.name = group.name
  deleteDialog.show = true
}

function doDelete() {
  deleteDialog.show = false
  deleteGroup(deleteDialog.uid)
}

async function deleteGroup(uid: string) {
  try {
    const res = await ajax(`${ApiUrl.DELETE_GROUP}/${uid}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
    })
    if (res.code === 200) { showMsg('已删除'); loadGroups() }
    else showMsg(res.msg, 'error')
  } catch (e) { showMsg('删除失败', 'error') }
}

onMounted(loadGroups)
</script>
