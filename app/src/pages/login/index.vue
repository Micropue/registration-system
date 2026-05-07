<template>
    <v-container fluid class="pa-0 login-container">
        <v-row no-gutters class="fill-height align-center justify-center">
            <v-card width="100%" max-width="1000px" height="auto" min-height="400px"
                class="d-flex flex-row rounded-md elevation-24 overflow-hidden mx-4">
                <!-- 左侧：logo 区域，去除深色背景 -->
                <v-col md="6" class="d-none d-md-flex align-center justify-center left-section">
                    <div class="text-center pa-8">
                        <v-avatar size="80" class="mb-4 bg-white shadow-lg">
                            <v-img src="@/assets/logo.jpg"></v-img>
                        </v-avatar>
                        <h2 class="text-h5 font-weight-black mb-2 color-primary">虎虎校园跑</h2>
                        <p class="text-body-2 text-grey-darken-1">8年专业校园跑</p>
                    </div>
                </v-col>
                <v-col cols="12" md="6" class="d-flex align-center justify-center bg-white">
                    <div class="login-form-wrapper pa-8 pa-md-12 flex align-center justify-center">
                        <div>
                            <h2 class="text-h4 font-weight-bold color-primary mb-1">登录</h2>
                            <p class="text-body-2 text-grey-darken-1">
                                使用管理员为您开放的账户进行登录。
                            </p>
                        </div>
                        <v-form @submit.prevent="handleLogin">
                            <div class="mb-4">
                                <span class="text-subtitle-2 font-weight-bold d-block mb-1">用户名</span>
                                <v-text-field v-model="username" placeholder="请输入账号" variant="outlined"
                                    density="comfortable" color="primary" rounded="lg" hide-details="auto"
                                    prepend-inner-icon="mdi-account-outline"></v-text-field>
                            </div>
                            <div class="mb-8">
                                <span class="text-subtitle-2 font-weight-bold d-block mb-1">密码</span>
                                <v-text-field v-model="password" :type="showPassword ? 'text' : 'password'"
                                    placeholder="请输入密码" variant="outlined" density="comfortable" color="primary"
                                    rounded="lg" hide-details="auto" prepend-inner-icon="mdi-lock-outline"
                                    :append-inner-icon="showPassword ? 'mdi-eye' : 'mdi-eye-off'"
                                    @click:append-inner="showPassword = !showPassword"></v-text-field>
                            </div>
                            <v-btn type="submit" block color="primary" size="large" height="48" rounded="lg"
                                elevation="0" :loading="loading" class="font-weight-bold">
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
import { ref } from 'vue'

const username = ref('')
const password = ref('')
const showPassword = ref(false)
const loading = ref(false)

async function handleLogin() {
    if (!username.value || !password.value) return
    loading.value = true
    setTimeout(() => {
        loading.value = false
        console.log('Login logic here')
    }, 1000)
}
</script>

<style scoped>
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
}

/* 表单宽度控制 */
.login-form-wrapper {
    width: 100%;
    max-width: 400px;
}

.color-primary {
    color: #1867c0;
}

/* 按钮悬停轻微缩放 */
.v-btn {
    text-transform: none;
    letter-spacing: 1px;
    transition: all 0.2s;
}

.v-btn:hover {
    filter: brightness(1.1);
}

/* 边框微调 */
:deep(.v-field__outline) {
    --v-field-border-opacity: 0.15;
}
</style>