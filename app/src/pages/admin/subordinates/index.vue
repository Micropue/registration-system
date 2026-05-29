<template>
  <v-container fluid class="pa-0 d-flex flex-column align-center">
    <div class="table-wrapper mt-4">
      <v-row align="center" class="mb-4">
        <v-col cols="12" sm="auto">
          <h1 class="text-h4">下属管理</h1>
        </v-col>
        <v-col cols="12" sm class="d-flex flex-wrap ga-2 justify-sm-end">
          <v-btn color="primary" variant="flat" @click="openAddDialog" prepend-icon="mdi-plus">添加下属</v-btn>
        </v-col>
      </v-row>

      <v-row v-if="!loading">
        <v-col cols="12" md="5" lg="4">
          <v-card elevation="0" border rounded="md">
            <v-card-title class="d-flex align-center justify-space-between py-3 px-4">
              <div class="d-flex align-center">
                <span class="text-subtitle-1 font-weight-bold">账户树</span>
                <v-chip v-if="tree.length" size="x-small" class="ml-2" color="primary" variant="flat">{{ tree.length }} 个</v-chip>
              </div>
              <v-btn v-if="tree.length" icon="mdi-collapse-all" size="x-small" variant="text" color="grey" @click="collapseAll" />
            </v-card-title>
            <v-divider />
            <v-card-text class="pa-0">
              <div v-if="!tree.length" class="d-flex flex-column align-center justify-center pa-8">
                <v-icon size="48" color="grey-lighten-1" class="mb-3">mdi-account-group-outline</v-icon>
                <div class="text-body-2 text-medium-emphasis mb-1">暂无下属账户</div>
                <div class="text-caption text-grey">点击"添加下属"按钮添加账户</div>
              </div>
              <v-list v-else density="compact" class="pa-0" nav bg-color="transparent">
                <subordinate-tree-node
                  v-for="node in tree"
                  :key="node.uid"
                  :node="node"
                  :selected-uid="selectedUid"
                  :level="0"
                  @select="selectNode"
                  @remove="confirmRemoveSubordinate"
                />
              </v-list>
            </v-card-text>
          </v-card>
        </v-col>

        <v-col cols="12" md="7" lg="8">
          <template v-if="selectedUid && selectedNode">
            <v-card elevation="0" border rounded="md" class="mb-4">
              <v-card-title class="d-flex align-center py-3 px-4">
                <v-icon size="20" color="primary" class="mr-2">mdi-account-circle</v-icon>
                <span class="font-weight-bold">{{ selectedNode.username }}</span>
                <v-chip v-if="selectedNode.group_name" size="x-small" class="ml-2"
                  :color="selectedNode.group_name === '超级管理员' ? '#DC2626' : selectedNode.group_name === '未分配' ? '#6B7280' : '#1677ff'"
                  variant="flat">
                  {{ selectedNode.group_name }}
                </v-chip>
                <v-chip v-if="selectedNode.is_delegated" size="x-small" class="ml-1" color="warning" variant="flat">
                  <v-icon start size="12">mdi-link-variant</v-icon>
                  已委托
                </v-chip>
                <v-spacer />
                <v-btn variant="outlined" size="small" color="error"
                  @click="confirmRemoveSubordinate(selectedNode)" prepend-icon="mdi-account-remove">
                  移除下属
                </v-btn>
              </v-card-title>
            </v-card>

            <v-card elevation="0" border rounded="md">
              <v-card-title class="d-flex align-center justify-space-between py-3 px-4">
                <span class="text-subtitle-1 font-weight-bold">余额扣除链配置</span>
                <v-chip size="x-small" :color="linkedCount > 0 ? 'warning' : 'success'" variant="flat">
                  {{ linkedCount > 0 ? `${linkedCount} 个已链接` : '全部可链接' }}
                </v-chip>
              </v-card-title>
              <v-divider />
              <v-card-text class="pa-0">
                <v-alert v-if="!runningApps.length" type="info" variant="tonal" class="ma-4 mb-0" density="compact">
                  暂无跑步APP配置，请先在APP管理中创建
                </v-alert>
                <v-table v-else density="compact" hover>
                  <thead>
                    <tr class="text-caption text-medium-emphasis">
                      <th class="pl-4">APP名称</th>
                      <th class="text-center" width="100">状态</th>
                      <th width="120">链接到</th>
                      <th class="pr-4 text-right" width="140">操作</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="app in runningApps" :key="app.uid"
                      :class="getDelegationStatus(app.uid) ? 'bg-warning-subtle' : ''">
                      <td class="pl-4">
                        <div class="d-flex align-center ga-3">
                          <v-avatar v-if="app.icon" size="28" rounded="sm">
                            <v-img :src="app.icon" cover />
                          </v-avatar>
                          <v-avatar v-else size="28" rounded="sm" color="#1677ff">
                            <v-icon size="14" color="white">mdi-run-fast</v-icon>
                          </v-avatar>
                          <span class="text-body-2 font-weight-medium">{{ app.name }}</span>
                        </div>
                      </td>
                      <td class="text-center">
                        <v-chip size="x-small"
                          :color="getDelegationStatus(app.uid) ? '#D97706' : '#16A34A'"
                          variant="flat">
                          {{ getDelegationStatus(app.uid) ? '已链接' : '可链接' }}
                        </v-chip>
                      </td>
                      <td>
                        <span v-if="getDelegationStatus(app.uid)" class="text-body-2 font-weight-medium">
                          {{ getDelegationStatus(app.uid).parent_name }}
                        </span>
                        <span v-else class="text-body-2 text-medium-emphasis">-</span>
                      </td>
                      <td class="pr-4 text-right">
                        <v-btn v-if="getDelegationStatus(app.uid)"
                          variant="tonal" size="x-small" rounded="md"
                          color="error"
                          @click="removeBalanceLink(app.uid)" :loading="linkingApps[app.uid]">
                          解除
                        </v-btn>
                        <v-btn v-else
                          variant="tonal" size="x-small" rounded="md"
                          color="primary"
                          @click="createBalanceLink(app.uid)" :loading="linkingApps[app.uid]">
                          建立链接
                        </v-btn>
                      </td>
                    </tr>
                  </tbody>
                </v-table>
                <v-divider v-if="selectedNode.is_delegated" />
                <v-alert v-if="selectedNode.is_delegated" type="warning" variant="tonal" density="compact"
                  class="ma-0" rounded="0">
                  <div class="text-caption">
                    该用户已建立余额扣除链接，其自身的余额查看、充值申请功能将被禁用，消费将从上级余额中层层扣除
                  </div>
                </v-alert>
              </v-card-text>
            </v-card>
          </template>

          <v-card v-else elevation="0" border rounded="md" class="d-flex align-center justify-center" style="min-height: 360px">
            <div class="d-flex flex-column align-center text-medium-emphasis">
              <v-icon size="56" color="grey-lighten-1" class="mb-3">mdi-arrow-left-circle-outline</v-icon>
              <div class="text-body-1">请在左侧选择下属账户查看详情</div>
              <div class="text-caption mt-1 text-grey">可查看账户信息、配置余额扣除链</div>
            </div>
          </v-card>
        </v-col>
      </v-row>

      <v-row v-else class="justify-center">
        <v-progress-circular indeterminate color="primary" />
      </v-row>
    </div>

    <v-snackbar v-model="snackbar.show" :color="snackbar.color" :timeout="3000" location="top" rounded="md">
      {{ snackbar.text }}
    </v-snackbar>

    <v-dialog v-model="addDialog.show" max-width="440" persistent>
      <v-card rounded="md">
        <v-card-title class="text-h6 pa-4 pb-2">添加下属</v-card-title>
        <v-divider />
        <v-card-text class="pa-4 pt-4">
          <v-select
            v-model="addDialog.selectedUid"
            :items="addDialog.candidates"
            item-title="username"
            item-value="uid"
            label="选择用户账户"
            variant="outlined"
            density="comfortable"
            :loading="addDialog.loading"
            :rules="[v => !!v || '请选择用户']"
            hide-details
          />
        </v-card-text>
        <v-card-actions class="pa-4 pt-0">
          <v-spacer />
          <v-btn variant="outlined" rounded="md" @click="addDialog.show = false">取消</v-btn>
          <v-btn color="primary" variant="flat" rounded="md" @click="addSubordinate"
            :loading="addDialog.submitting" :disabled="!addDialog.selectedUid">
            确认添加
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="removeDialog.show" max-width="420" persistent>
      <v-card rounded="md">
        <v-card-title class="text-h6 pa-4 pb-2 text-error">确认移除下属</v-card-title>
        <v-divider />
        <v-card-text class="pa-4">
          <p class="text-body-2 mb-0">
            确定要将 <strong>{{ removeDialog.username }}</strong> 从下属中移除吗？该用户的所有余额链接将同时被解除。
          </p>
        </v-card-text>
        <v-card-actions class="pa-4 pt-0">
          <v-spacer />
          <v-btn variant="outlined" rounded="md" @click="removeDialog.show = false">取消</v-btn>
          <v-btn color="error" variant="flat" rounded="md" @click="removeSubordinate" :loading="removeDialog.loading">
            确认移除
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<style scoped>
.table-wrapper { width: 90%; }

.bg-warning-subtle { background-color: rgba(217, 119, 6, 0.04); }
</style>

<script lang="ts" setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { ajax } from '@/api/ajax'
import { cookie } from '@/api/cookie'
import { ApiUrl } from '@/config/api-url'
import type { SubordinateUser, RunningApp, UserItem } from '@/config/api-type'
import SubordinateTreeNode from './SubordinateTreeNode.vue'

const route = useRoute()

const snackbar = reactive({ show: false, text: '', color: 'success' })
const loading = ref(false)
const tree = ref<SubordinateUser[]>([])
const selectedUid = ref('')
const selectedNode = ref<SubordinateUser | null>(null)
const runningApps = ref<RunningApp[]>([])

const uidParam = computed(() => {
  const p = route.params.uid as string | undefined
  return p && p !== ':uid' ? p : ''
})

const linkedCount = computed(() => {
  if (!selectedNode.value) return 0
  const delegations = (selectedNode.value as any)._delegations as Record<string, any> | undefined
  return delegations ? Object.keys(delegations).length : 0
})

function showMsg(text: string, color = 'success') {
  snackbar.text = text
  snackbar.color = color
  snackbar.show = true
}

const linkingApps = reactive<Record<string, boolean>>({})

async function loadData() {
  loading.value = true
  try {
    const headers = { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
    let parentUid = uidParam.value
    if (!parentUid) {
      const res = await ajax<any>('/api/auth/check-login', { headers })
      if (res.code === 200 && res.data) {
        const loginRes = await ajax<any>(`${ApiUrl.GET_USERS}?page=1&page_size=500`, { headers })
        if (loginRes.code === 200 && loginRes.data?.items) {
          const me = loginRes.data.items.find((u: any) => u.username === res.data.username)
          if (me) parentUid = me.uid
        }
      }
    }
    const [treeRes, appsRes] = await Promise.all([
      ajax<SubordinateUser[]>(`${ApiUrl.GET_SUBORDINATE_TREE}/${parentUid || ''}/subordinate-tree`, { headers }),
      ajax<RunningApp[]>(ApiUrl.GET_RUNNING_APPS, { headers })
    ])
    if (treeRes.code === 200) tree.value = treeRes.data
    if (appsRes.code === 200) runningApps.value = appsRes.data
  } catch (e) { /* ignore */ }
  finally { loading.value = false }
}

function collapseAll() {
  selectedUid.value = ''
  selectedNode.value = null
}

function selectNode(node: SubordinateUser) {
  selectedUid.value = node.uid
  selectedNode.value = node
  refreshDelegations(node.uid)
}

function getDelegationStatus(appUid: string) {
  if (!selectedNode.value) return null
  const delegations = (selectedNode.value as any)._delegations as Record<string, any> | undefined
  return delegations ? delegations[appUid] || null : null
}

const addDialog = reactive({
  show: false,
  candidates: [] as UserItem[],
  selectedUid: '',
  loading: false,
  submitting: false
})

async function openAddDialog() {
  addDialog.selectedUid = ''
  addDialog.loading = true
  addDialog.show = true
  try {
    const res = await ajax<{ items: UserItem[] }>(
      `${ApiUrl.GET_USERS}?page=1&page_size=500`,
      { headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` } }
    )
    if (res.code === 200) {
      const existingUids = new Set(collectAllUids(tree.value))
      addDialog.candidates = (res.data.items || []).filter(
        (u: UserItem) => !existingUids.has(u.uid) && u.username !== 'admin'
      )
    }
  } catch (e) { /* ignore */ }
  finally { addDialog.loading = false }
}

function collectAllUids(nodes: SubordinateUser[]): string[] {
  const uids: string[] = []
  for (const n of nodes) {
    uids.push(n.uid)
    if (n.children) uids.push(...collectAllUids(n.children))
  }
  return uids
}

async function addSubordinate() {
  if (!addDialog.selectedUid) return
  let parentUid = uidParam.value
  if (!parentUid) {
    const headers = { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
    const res = await ajax<any>('/api/auth/check-login', { headers })
    if (res.code === 200 && res.data) {
      const loginRes = await ajax<any>(`${ApiUrl.GET_USERS}?page=1&page_size=500&username=${res.data.username}`, { headers })
      if (loginRes.code === 200 && loginRes.data?.items?.[0]) {
        parentUid = loginRes.data.items[0].uid
      }
    }
    if (!parentUid) { showMsg('无法获取当前账户信息', 'error'); return }
  }
  addDialog.submitting = true
  try {
    const res = await ajax(`${ApiUrl.ADD_SUBORDINATE}/${parentUid}/subordinates`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` },
      body: { subordinate_uid: addDialog.selectedUid }
    })
    if (res.code === 200) {
      showMsg('下属添加成功')
      addDialog.show = false
      await loadData()
    } else { showMsg(res.msg || '添加失败', 'error') }
  } catch (e) { showMsg('添加失败', 'error') }
  finally { addDialog.submitting = false }
}

const removeDialog = reactive({ show: false, username: '', uid: '', loading: false })

function confirmRemoveSubordinate(node: SubordinateUser) {
  removeDialog.username = node.username
  removeDialog.uid = node.uid
  removeDialog.show = true
}

async function removeSubordinate() {
  let parentUid = uidParam.value
  if (!parentUid) {
    const headers = { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
    const res = await ajax<any>('/api/auth/check-login', { headers })
    if (res.code === 200 && res.data) {
      const loginRes = await ajax<any>(`${ApiUrl.GET_USERS}?page=1&page_size=500&username=${res.data.username}`, { headers })
      if (loginRes.code === 200 && loginRes.data?.items?.[0]) { parentUid = loginRes.data.items[0].uid }
    }
    if (!parentUid) { showMsg('无法获取当前账户信息', 'error'); return }
  }
  removeDialog.loading = true
  try {
    const res = await ajax(`${ApiUrl.REMOVE_SUBORDINATE}/${parentUid}/subordinates/${removeDialog.uid}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
    })
    if (res.code === 200) {
      showMsg('下属已移除')
      removeDialog.show = false
      if (selectedUid.value === removeDialog.uid) { selectedUid.value = ''; selectedNode.value = null }
      await loadData()
    } else { showMsg(res.msg || '移除失败', 'error') }
  } catch (e) { showMsg('移除失败', 'error') }
  finally { removeDialog.loading = false }
}

async function createBalanceLink(appUid: string) {
  if (!selectedNode.value) return
  let parentUid = uidParam.value
  if (!parentUid) {
    const headers = { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
    const res = await ajax<any>('/api/auth/check-login', { headers })
    if (res.code === 200 && res.data) {
      const loginRes = await ajax<any>(`${ApiUrl.GET_USERS}?page=1&page_size=500&username=${res.data.username}`, { headers })
      if (loginRes.code === 200 && loginRes.data?.items?.[0]) { parentUid = loginRes.data.items[0].uid }
    }
    if (!parentUid) { showMsg('无法获取当前账户信息', 'error'); return }
  }
  linkingApps[appUid] = true
  try {
    const res = await ajax(`${ApiUrl.CREATE_BALANCE_LINK}/${selectedNode.value.uid}/balance-link`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` },
      body: { parent_uid: parentUid, app_uid: appUid }
    })
    if (res.code === 200) { showMsg('余额链接已建立'); await refreshDelegations(selectedNode.value.uid) }
    else { showMsg(res.msg || '操作失败', 'error') }
  } catch (e) { showMsg('操作失败', 'error') }
  finally { linkingApps[appUid] = false }
}

async function removeBalanceLink(appUid: string) {
  if (!selectedNode.value) return
  linkingApps[appUid] = true
  try {
    const res = await ajax(`${ApiUrl.REMOVE_BALANCE_LINK}/${selectedNode.value.uid}/balance-link/${appUid}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` }
    })
    if (res.code === 200) { showMsg('余额链接已解除'); await refreshDelegations(selectedNode.value.uid) }
    else { showMsg(res.msg || '操作失败', 'error') }
  } catch (e) { showMsg('操作失败', 'error') }
  finally { linkingApps[appUid] = false }
}

async function refreshDelegations(userUid: string) {
  try {
    const res = await ajax<any[]>(
      `${ApiUrl.GET_USER_DELEGATIONS}/${userUid}/balance-delegations`,
      { headers: { 'Authorization': `Bearer ${cookie.get('token') || ''}` } }
    )
    if (res.code === 200 && selectedNode.value) {
      const delegations: Record<string, any> = {}
      for (const d of (res.data || [])) { delegations[d.app_uid] = d }
      (selectedNode.value as any)._delegations = delegations
    }
  } catch (e) { /* ignore */ }
}

onMounted(() => { loadData() })
</script>
