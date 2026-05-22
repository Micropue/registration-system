<template>
    <v-container fluid class="pa-0 login-container">
        <v-row no-gutters class="fill-height min-h-800 align-center justify-center">
            <v-card width="100%" max-width="1000px" height="auto" min-height="500px"
                class="d-flex flex-row rounded-md elevation-12 overflow-hidden mx-4">

                <!-- 左侧：logo 区域 -->
                <v-col md="6" class="d-none d-md-flex align-center justify-center left-section">
                    <div class="text-center pa-8">
                        <v-avatar size="80" class="mb-4 bg-background shadow-lg">
                            <v-img src="@/assets/logo.jpg"></v-img>
                        </v-avatar>
                        <h2 class="text-h5 font-weight-black mb-2 color-primary">哆啦A梦（校园跑版）</h2>
                        <p class="text-body-2 text-grey-darken-1">8年专业校园跑</p>
                    </div>
                </v-col>

                <!-- 右侧：表单区域 -->
                <v-col cols="12" md="6" class="d-flex align-center justify-center bg-background">
                    <div class="login-form-wrapper pa-8 pa-md-12">
                        <!-- 修复了原本强行负边距导致的拥挤感 -->
                        <div class="mb-6">
                            <h2 class="text-h4 font-weight-bold color-primary mb-2">登录</h2>
                            <p class="text-body-2 text-grey-darken-1" style="font-size: 0.9em">
                                使用管理员为您开放的账户进行登录。
                            </p>
                        </div>

                        <v-form @submit.prevent="handleLogin">
                            <v-alert v-if="errorMessage" type="error" variant="tonal" density="compact" class="mb-4 text-caption">
                                {{ errorMessage }}
                            </v-alert>
                            <!-- 优化1：采用 outlined 风格，拆分 label 和 placeholder -->
                            <div class="mb-4">
                                <v-text-field v-model="username" label="账号" placeholder="请输入账号" variant="outlined"
                                    color="primary" density="comfortable" prepend-inner-icon="mdi-account-outline"
                                    hide-details="auto" class="login-input"></v-text-field>
                            </div>

                            <div class="mb-8">
                                <v-text-field v-model="password" :type="showPassword ? 'text' : 'password'" label="密码"
                                    placeholder="请输入密码" variant="outlined" color="primary" density="comfortable"
                                    prepend-inner-icon="mdi-lock-outline"
                                    :append-inner-icon="showPassword ? 'mdi-eye-outline' : 'mdi-eye-off-outline'"
                                    @click:append-inner="showPassword = !showPassword" hide-details="auto"
                                    class="login-input"></v-text-field>
                            </div>

                            <v-btn type="submit" block color="primary" size="large" height="48" elevation="2"
                                :loading="loading" class="font-weight-bold login-btn" :disabled="username.length === 0 || password.length === 0">
                                登 录
                            </v-btn>
                        </v-form>
                    </div>
                </v-col>
            </v-card>
        </v-row>
    </v-container>
</template>

<script lang="ts" setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ajax } from '@/api/ajax'
import { cookie } from '@/api/cookie'
import { ApiUrl } from '@/config/api-url'
import { checkLoginStatus } from '@/api/auth'
import type { LoginData } from '@/config/api-type'

const router = useRouter()
const username = ref('')
const password = ref('')
const showPassword = ref(false)
const loading = ref(false)
const errorMessage = ref('')

// 页面加载时检查是否有旧登录状态，禁用按钮
onMounted(async () => {
    loading.value = true
    const user = await checkLoginStatus()
    if (user) {
        router.push('/')
    }
    loading.value = false
})

async function handleLogin() {
    if (!username.value || !password.value) return
    
    loading.value = true
    errorMessage.value = ''
    
    try {
        const res = await ajax<LoginData>(ApiUrl.LOGIN, {
            method: 'POST',
            isFormData: true,
            body: {
                username: username.value,
                password: password.value
            }
        })

        if (res.code === 200) {
            cookie.set('token', res.data.token, 7)
            router.push('/')
        } else {
            errorMessage.value = res.msg
        }
    } catch (error) {
        errorMessage.value = '网络服务异常，请稍后再试'
    } finally {
        loading.value = false
    }
}
</script>

<style scoped>
.label {
    font-size: 0.8em;
    margin: 10px 0;
}

/* --- 完全保留你的垂直居中代码 --- */
/* 垂直居中 */
.login-container {
    min-height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
}
/* 左侧无背景色，直接继承卡片背景 */
.left-section {
    background: transparent;
    background-color: rgb(var(--v-theme-surface));
}

/* 表单宽度控制 */
.login-form-wrapper {
    width: 100%;
    max-width: 400px;
}

.color-primary {
    color: rgb(var(--v-theme-primary));
}

.login-input :deep(.v-field__input) {
    font-size: 0.9rem;
}

/* 按钮悬停轻微缩放 */
.login-btn {
    text-transform: none;
    letter-spacing: 2px;
    transition: all 0.2s;
}

.login-btn:hover {
    filter: brightness(1.1);
    transform: translateY(-1px);
}
</style>