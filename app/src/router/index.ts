/**
 * router/index.ts
 *
 * Manual routes for ./src/pages/*.vue
 */

// Composables
import { createRouter, createWebHistory, type NavigationGuard } from 'vue-router'
import Index from '@/pages/index.vue'
import { checkLoginStatus } from '@/api/auth'
import { useAppStore } from '@/stores/app'

const ADMIN_PERMISSION_KEYS = ['账户管理', '账户组管理', '订单处理', '工单处理', 'APP配置', '充值审批', '下属管理']

function hasAnyAdminPermission(permissions: Record<string, any> | undefined): boolean {
  if (!permissions) return false
  return ADMIN_PERMISSION_KEYS.some(key => {
    const val = permissions[key]
    if (typeof val === 'object' && val !== null) return Object.values(val).some(Boolean)
    return !!val
  })
}

/**
 * 路由守卫：要求必须登录（用户页面，含后台权限的用户也可访问）
 */
const requireDefault: NavigationGuard = async (_to, _from, next) => {
  const userInfo = await checkLoginStatus()
  if (!userInfo) {
    return next('/login')
  }
  next()
}

/**
 * 路由守卫：要求必须登录且拥有任一后台权限
 */
const requireAdmin: NavigationGuard = async (_to, _from, next) => {
  const userInfo = await checkLoginStatus()
  if (!userInfo) {
    return next('/login')
  }
  if (hasAnyAdminPermission(userInfo.permissions)) {
    next()
  } else {
    next('/')
  }
}

/**
 * 路由守卫：要求必须未登录 (访客状态)
 */
const requireGuest: NavigationGuard = async (_to, _from, next) => {
  const userInfo = await checkLoginStatus()
  if (userInfo) {
    if (hasAnyAdminPermission(userInfo.permissions)) {
      next('/admin')
    } else {
      next('/')
    }
  } else {
    next()
  }
}

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      component: Index,
      meta: { title: '首页' }
    },
    {
      path: '/login',
      component: () => import("@/pages/login/index.vue"),
      beforeEnter: requireGuest,
      meta: { title: '登录' }
    },
    {
      path: '/sign',
      component: () => import("@/pages/sign/index.vue"),
      beforeEnter: requireDefault,
      meta: { title: '数据登记' }
    },
    {
      path: '/feedback',
      component: () => import("@/pages/feedback/index.vue"),
      beforeEnter: requireDefault,
      meta: { title: '工单反馈' }
    },
    {
      path: '/recharge',
      component: () => import("@/pages/recharge/index.vue"),
      beforeEnter: requireDefault,
      meta: { title: '充值申请' }
    },
    {
      path: '/balance',
      component: () => import("@/pages/balance/index.vue"),
      beforeEnter: requireDefault,
      meta: { title: '余额查看' }
    },
    {
      path: '/balance-transactions',
      component: () => import("@/pages/balance-transactions/index.vue"),
      beforeEnter: requireDefault,
      meta: { title: '余额流水' }
    },
    {
      path: '/about',
      component: () => import("@/pages/about/index.vue"),
      meta: { title: '关于' }
    },
    {
      path: '/admin',
      component: () => import("@/pages/admin/index.vue"),
      beforeEnter: requireAdmin,
      meta: { title: '后台管理' },
      children: [
        { path: '', component: () => import("@/pages/admin/dashboard.vue"), meta: { title: '仪表盘' } },
        { path: 'users', component: () => import("@/pages/admin/users/index.vue"), meta: { title: '账户管理' } },
        { path: 'registers/:appName?', component: () => import("@/pages/admin/registers/index.vue"), meta: { title: '订单处理' } },
        { path: 'feedbacks', component: () => import("@/pages/admin/feedbacks/index.vue"), meta: { title: '工单处理' } },
        { path: 'running-apps', component: () => import("@/pages/admin/settings/running-apps/index.vue"), meta: { title: '跑步APP配置' } },
        { path: 'running-apps/:appUid/templates', component: () => import("@/pages/admin/settings/running-apps/templates/index.vue"), meta: { title: '模板管理' } },
        { path: 'settings/running-apps/:appUid/templates', redirect: (to: any) => `/admin/running-apps/${to.params.appUid}/templates` },
        { path: 'settings/running-apps', redirect: '/admin/running-apps' },
        { path: 'settings', redirect: '/admin' },
        { path: 'groups', component: () => import("@/pages/admin/groups/index.vue"), meta: { title: '账户组管理' } },
        { path: 'recharges', component: () => import("@/pages/admin/recharges/index.vue"), meta: { title: '充值审批' } },
        { path: 'subordinates/:uid?', component: () => import("@/pages/admin/subordinates/index.vue"), meta: { title: '下属管理' } },
        { path: 'running-apps/:appUid/balance', component: () => import("@/pages/admin/running-apps/balance/index.vue"), meta: { title: '用户余额管理' } },
        { path: 'update-logs', component: () => import("@/pages/admin/update-logs/index.vue"), meta: { title: '更新日志' } },
      ]
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'NotFound',
      component: () => import("@/pages/404/index.vue"),
      meta: { title: '404' }
    },
  ],
})

// 全局路由加载动画守卫
router.beforeEach((_to, _from, next) => {
  const appStore = useAppStore()
  appStore.setPageLoading(true)
  next()
})

router.afterEach((to) => {
  const appStore = useAppStore()
  setTimeout(() => {
    appStore.setPageLoading(false)
  }, 400)

  document.title = to.meta.title ? `${to.meta.title} - 哆啦A梦（校园跑版）` : '哆啦A梦（校园跑版）'
})

export default router
