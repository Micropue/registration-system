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

/**
 * 路由守卫：要求必须登录且为普通用户
 */
const requireDefault: NavigationGuard = async (to, from, next) => {
  const userInfo = await checkLoginStatus()
  if (!userInfo) {
    return next('/login')
  }
  if (userInfo.type === 'default') {
    next()
  } else {
    // 管理员尝试访问普通用户页面，重定向到管理员首页
    next('/admin')
  }
}

/**
 * 路由守卫：要求必须登录且为管理员
 */
const requireAdmin: NavigationGuard = async (to, from, next) => {
  const userInfo = await checkLoginStatus()
  if (!userInfo) {
    return next('/login')
  }
  if (userInfo.type === 'admin') {
    next()
  } else {
    // 普通用户尝试访问管理页面，重定向到普通用户首页
    next('/')
  }
}

/**
 * 路由守卫：要求必须未登录 (访客状态)
 */
const requireGuest: NavigationGuard = async (to, from, next) => {
  const userInfo = await checkLoginStatus()
  if (userInfo) {
    if (userInfo.type === 'admin') {
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
      path: '/admin',
      component: () => import("@/pages/admin/index.vue"),
      beforeEnter: requireAdmin,
      meta: { title: '后台管理' },
      children: [
        { path: 'users', component: () => import("@/pages/admin/users/index.vue"), meta: { title: '账户管理' } },
        { path: 'registers', component: () => import("@/pages/admin/registers/index.vue"), meta: { title: '登记处理' } },
        { path: 'feedbacks', component: () => import("@/pages/admin/feedbacks/index.vue"), meta: { title: '工单处理' } },
        {
          path: 'settings',
          component: () => import("@/pages/admin/settings/index.vue"),
          meta: { title: '系统设置' },
          children: [
            { path: '', component: () => import("@/pages/admin/settings/welcome.vue") },
            { path: 'fields', component: () => import("@/pages/admin/settings/fields/index.vue"), meta: { title: '登记字段配置' } },
            { path: 'running-apps', component: () => import("@/pages/admin/settings/running-apps/index.vue"), meta: { title: '跑步APP配置' } }
          ]
        }
      ]
    }
  ],
})

// 全局路由加载动画守卫
router.beforeEach((to, from, next) => {
  const appStore = useAppStore()
  appStore.setPageLoading(true)
  next()
})

router.afterEach((to) => {
  const appStore = useAppStore()
  // 延迟关闭以增加视觉反馈
  setTimeout(() => {
    appStore.setPageLoading(false)
  }, 400)

  // 动态修改标题
  document.title = to.meta.title ? `${to.meta.title} - 哆啦A梦（校园跑版）` : '哆啦A梦（校园跑版）'
})

export default router
