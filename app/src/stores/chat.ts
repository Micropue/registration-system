import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useChatStore = defineStore('chat', () => {
  const isOpen = ref(false)
  const registrationUid = ref('')
  const title = ref('')
  const isAdminView = ref(false)
  const currentUsername = ref('')

  function open(uid: string, t: string, admin: boolean, username: string) {
    registrationUid.value = uid
    title.value = t
    isAdminView.value = admin
    currentUsername.value = username
    isOpen.value = true
  }

  function close() {
    isOpen.value = false
  }

  function toggle(uid: string, t: string, admin: boolean, username: string) {
    if (isOpen.value && registrationUid.value === uid) {
      close()
    } else {
      open(uid, t, admin, username)
    }
  }

  return { isOpen, registrationUid, title, isAdminView, currentUsername, open, close, toggle }
})
