import { defineStore } from 'pinia'

export const useAppStore = defineStore('app', {
  state: () => ({
    /** 页面切换加载状态 */
    isPageLoading: false,
  }),
  actions: {
    setPageLoading(status: boolean) {
      this.isPageLoading = status
    }
  }
})
