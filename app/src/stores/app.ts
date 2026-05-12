import { defineStore } from 'pinia'

export const useAppStore = defineStore('app', {
  state: () => ({
    /** 页面切换加载状态 */
    isPageLoading: false,
    /** 当前登录用户信息 */
    userInfo: null as { username: string, type: string, token: string } | null,
  }),
  actions: {
    setPageLoading(status: boolean) {
      this.isPageLoading = status
    },
    setUserInfo(info: any) {
      this.userInfo = info
    }
  }
})
