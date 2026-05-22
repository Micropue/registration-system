<template>
    <v-container class="max-width-800 pa-3 pa-sm-6">
        <!-- 头部区域：响应式排版 -->
        <v-row class="mb-2 mb-sm-4">
            <v-col cols="12">
                <div class="d-flex flex-column flex-md-row align-start align-md-center gap-3">
                    <div class="d-flex align-center">
                        <v-icon color="primary" size="32" class="mr-2 mt-n1">mdi-form-dropdown</v-icon>
                        <h2 class="text-h5 font-weight-bold text-grey-darken-3 mb-0"
                            style="line-height: 1.2; margin-block-start: 0;">登记字段配置</h2>
                    </div>
                    <v-spacer class="d-none d-md-block"></v-spacer>
                    <div class="d-flex flex-wrap align-center w-100 w-md-auto gap-2">
                        <v-btn color="success" elevation="2" prepend-icon="mdi-check-circle" class="flex-grow-1 flex-md-grow-0"
                            @click="saveFields" :loading="isSaving" :disabled="isLoading">
                            保存配置
                        </v-btn>
                        <v-btn color="error" variant="tonal" prepend-icon="mdi-refresh" class="flex-grow-1 flex-md-grow-0"
                            @click="resetDialog = true" :disabled="isLoading || fields.length === 0">
                            一键重置
                        </v-btn>
                        <v-btn color="primary" elevation="2" prepend-icon="mdi-plus" class="flex-grow-1 flex-md-grow-0"
                            @click="addField">
                            添加字段
                        </v-btn>
                        <v-btn color="secondary" elevation="2" prepend-icon="mdi-file-import" class="flex-grow-1 flex-md-grow-0"
                            @click="importDialog = true">
                            批量导入
                        </v-btn>
                    </div>
                </div>
            </v-col>
        </v-row>

        <!-- 批量导入对话框 -->
        <v-dialog v-model="importDialog" max-width="500" rounded="lg">
            <v-card class="pa-2 pa-sm-4">
                <v-card-title class="d-flex align-center px-3 px-sm-4 text-subtitle-1 text-sm-h6">
                    <v-icon color="primary" class="mr-2">mdi-file-import</v-icon>
                    批量导入字段
                    <v-spacer></v-spacer>
                    <v-btn icon="mdi-close" variant="text" @click="importDialog = false"></v-btn>
                </v-card-title>
                <v-card-text class="px-3 px-sm-4">
                    <div class="dashed-border pa-6 pa-sm-8 text-center cursor-pointer rounded-lg" @click="fileInput?.click()">
                        <v-icon size="48" color="primary">mdi-cloud-upload</v-icon>
                        <div class="text-body-1 font-weight-medium mt-2">点击此处选择 TXT 文件</div>
                        <div class="text-caption text-grey mt-1">支持格式：名称|类型|必填(1/0)</div>
                    </div>
                    <input type="file" ref="fileInput" accept=".txt" class="d-none" @change="handleFileImport" />
                    <v-btn variant="text" color="primary" class="mt-4" @click="downloadTemplate" block>
                        下载标准导入模板
                    </v-btn>
                </v-card-text>
            </v-card>
        </v-dialog>

        <v-row>
            <v-col cols="12">
                <!-- 加载中状态 -->
                <div v-if="isLoading" class="d-flex flex-column align-center py-12">
                    <v-progress-circular indeterminate color="primary" size="64"></v-progress-circular>
                    <div class="text-body-1 text-grey-darken-1 mt-4">正在获取配置...</div>
                </div>

                <!-- 拖拽列表区域 -->
                <draggable v-else v-model="fields" item-key="id" handle=".drag-handle" ghost-class="ghost-card"
                    chosen-class="sortable-chosen" drag-class="sortable-drag" animation="220">
                    <template #item="{ element, index }">
                        <v-card class="mb-3 mb-sm-4 field-card" elevation="0">
                            <!-- 卡片主行：响应式布局，移动端上下折行，桌面端左右排列 -->
                            <div class="d-flex align-start align-sm-center px-3 px-sm-5 py-3 py-sm-4">
                                <v-icon class="mr-2 mr-sm-4 drag-handle mt-1 mt-sm-0" color="grey-lighten-1" size="24">mdi-drag</v-icon>

                                <div class="d-flex flex-column flex-sm-row align-start align-sm-center flex-grow-1 overflow-hidden mr-2 gap-1 gap-sm-3">
                                    <span class="text-subtitle-1 font-weight-bold text-grey-darken-3 text-truncate w-100 w-sm-auto" style="max-width: 100%;">
                                        {{ element.label || '未命名字段' }}
                                    </span>

                                    <div class="d-flex flex-wrap align-center gap-1 mt-1 mt-sm-0">
                                        <v-chip size="small" color="primary" variant="tonal" class="font-weight-medium">
                                            <v-icon start size="small" class="mr-1">{{ getFieldIcon(element.type) }}</v-icon>
                                            {{ fieldTypeLabel(element.type) }}
                                        </v-chip>

                                        <v-chip v-if="element.required" size="small" color="error" variant="flat"
                                            class="font-weight-medium">
                                            必填
                                        </v-chip>
                                    </div>
                                </div>

                                <div class="d-flex align-center flex-shrink-0">
                                    <v-btn icon="mdi-pencil-outline" size="small" variant="text" color="primary"
                                        class="hover-action" @click="editField(index)"></v-btn>
                                    <v-btn icon="mdi-trash-can-outline" size="small" variant="text" color="error"
                                        class="hover-action ml-1" @click="openDeleteConfirm(index)"></v-btn>
                                </div>
                            </div>

                            <!-- 卡片详情行 -->
                            <v-expand-transition>
                                <div v-if="element.default || (element.options && isOptionType(element.type)) || isRangeType(element.type)">
                                    <v-divider class="mx-2 mx-sm-4 border-opacity-50"></v-divider>
                                    <div class="px-4 px-sm-12 py-3 bg-surface rounded-b-lg">
                                        <v-row dense>
                                            <v-col cols="12" sm="6" v-if="element.default">
                                                <div class="text-caption text-grey-darken-1 mb-1">默认值</div>
                                                <div class="text-body-2 text-grey-darken-3 font-weight-medium">
                                                    <template v-if="isRangeType(element.type) && Array.isArray(element.default)">
                                                        {{ element.default[0] || '未设' }} 至 {{ element.default[1] || '未设' }}
                                                    </template>
                                                    <template v-else>
                                                        {{ element.default }}
                                                    </template>
                                                </div>
                                            </v-col>
                                            <v-col cols="12" :sm="element.default ? 6 : 12"
                                                v-if="element.options && isOptionType(element.type)">
                                                <div class="text-caption text-grey-darken-1 mb-1 mt-2 mt-sm-0">可选项目</div>
                                                <div class="d-flex flex-wrap gap-1">
                                                    <v-chip v-for="opt in element.options" :key="opt.value" size="small"
                                                        variant="outlined" color="grey-darken-1" class="bg-white">
                                                        {{ opt.label }}
                                                    </v-chip>
                                                </div>
                                            </v-col>
                                        </v-row>
                                    </div>
                                </div>
                            </v-expand-transition>
                        </v-card>
                    </template>
                </draggable>

                <!-- 空状态：响应式内边距 -->
                <v-card v-if="fields.length === 0" elevation="0" rounded="lg"
                    class="text-center py-10 py-sm-16 px-4 dashed-border bg-surface">
                    <v-avatar color="grey-lighten-3" size="70" class="mb-4">
                        <v-icon size="36" color="grey-darken-1">mdi-file-document-outline</v-icon>
                    </v-avatar>
                    <div class="text-h6 text-grey-darken-1 mb-2">暂无任何表单字段</div>
                    <div class="text-body-2 text-grey">点击右上角的“添加字段”按钮开始构建您的表单</div>
                    <v-btn color="primary" variant="tonal" class="mt-6" prepend-icon="mdi-plus" @click="addField">
                        立即添加
                    </v-btn>
                </v-card>
            </v-col>
        </v-row>

        <!-- 一键重置确认对话框 -->
        <v-dialog v-model="resetDialog" max-width="400">
            <v-card rounded="lg">
                <v-card-title class="text-subtitle-1 text-sm-h6 pa-4 pa-sm-5 pb-2 d-flex align-center text-error">
                    <v-icon color="error" class="mr-2">mdi-alert</v-icon>
                    确认重置
                </v-card-title>
                <v-card-text class="px-4 px-sm-5 py-3 text-body-2 text-sm-body-1 text-grey-darken-2">
                    确定要删除所有已配置的字段吗？此操作将清空当前列表，需点击“保存配置”后才会同步到服务器。
                </v-card-text>
                <v-card-actions class="pa-3 pa-sm-4 pt-0">
                    <v-spacer></v-spacer>
                    <v-btn variant="text" class="font-weight-medium" @click="resetDialog = false">取消</v-btn>
                    <v-btn color="error" variant="flat" class="px-4 font-weight-medium"
                        @click="confirmReset">确认重置</v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>

        <!-- 消息提示 -->

        <v-dialog v-model="dialog" max-width="650" persistent scrollable>
            <v-card rounded="lg">
                <v-card-title class="pa-4 pa-sm-5 d-flex align-center border-bottom">
                    <v-icon color="primary" class="mr-2">{{ editIndex === null ? 'mdi-plus-box' : 'mdi-pencil-box' }}</v-icon>
                    <span class="text-subtitle-1 text-sm-h6 font-weight-bold">{{ editIndex === null ? '添加新字段' : '编辑字段' }}</span>
                    <v-spacer></v-spacer>
                    <v-btn icon="mdi-close" variant="text" density="comfortable" @click="dialog = false"></v-btn>
                </v-card-title>

                <v-divider></v-divider>

                <!-- 增加 max-height 控制滚动 -->
                <v-card-text class="pa-4 pa-sm-5" style="max-height: 65vh;">
                    <v-row>
                        <v-col cols="12" sm="8">
                            <v-text-field v-model="editFieldData.label" label="字段名称 *" placeholder="例如：姓名、联系方式"
                                variant="outlined" density="comfortable" color="primary"
                                hide-details="auto"></v-text-field>
                        </v-col>
                        <v-col cols="12" sm="4">
                            <v-select v-model="editFieldData.type" :items="fieldTypes" label="字段类型" item-title="label"
                                item-value="value" :item-props="itemTypeProps" variant="outlined" density="comfortable"
                                color="primary" hide-details>
                                <template #selection>
                                    <div class="d-flex align-center">
                                        <v-icon :icon="getFieldIcon(editFieldData.type)" size="small" class="mr-2"
                                            color="primary"></v-icon>
                                        <span>{{ fieldTypeLabel(editFieldData.type) }}</span>
                                    </div>
                                </template>
                            </v-select>
                        </v-col>

                        <v-col cols="12" class="pt-2 pb-2">
                            <v-sheet class="pa-3 pa-sm-4 bg-surface rounded-lg d-flex align-center border gap-2">
                                <span class="text-subtitle-2 text-grey-darken-3 mr-auto mr-sm-4">通用设置：</span>
                                <v-switch v-model="editFieldData.required" label="必填项" color="error" hide-details
                                    density="compact" class="ml-auto ml-sm-0 mr-sm-6"></v-switch>
                            </v-sheet>
                        </v-col>

                        <!-- 默认值（非选项类，非范围类） -->
                        <v-col cols="12" v-if="!isOptionType(editFieldData.type) && !isRangeType(editFieldData.type)">
                            <v-text-field v-model="editFieldData.default" label="默认填充内容" placeholder="用户打开表单时默认显示的文本"
                                variant="outlined" density="comfortable" color="primary" hint="选填，可留空"
                                :type="editFieldData.type" persistent-hint></v-text-field>
                        </v-col>

                        <!-- 范围类配置 -->
                        <v-col cols="12" v-if="isRangeType(editFieldData.type)">
                            <div class="text-subtitle-2 text-grey-darken-3 mb-2">默认范围设置</div>
                            <v-row dense>
                                <v-col cols="12" sm="6">
                                    <v-text-field v-model="editFieldData.default[0]"
                                        :label="editFieldData.type === 'number-range' ? '最小默认值' : '开始时间'"
                                        :type="editFieldData.type === 'number-range' ? 'number' : (editFieldData.type === 'date-range' ? 'date' : 'time')"
                                        variant="outlined" density="comfortable" hide-details="auto"></v-text-field>
                                </v-col>
                                <v-col cols="12" sm="6">
                                    <v-text-field v-model="editFieldData.default[1]"
                                        :label="editFieldData.type === 'number-range' ? '最大默认值' : '结束时间'"
                                        :type="editFieldData.type === 'number-range' ? 'number' : (editFieldData.type === 'date-range' ? 'date' : 'time')"
                                        variant="outlined" density="comfortable" hide-details="auto"></v-text-field>
                                </v-col>
                            </v-row>
                        </v-col>

                        <!-- 选项配置区域：极致的响应式 Flex 布局 -->
                        <v-col cols="12" v-if="isOptionType(editFieldData.type)">
                            <v-card variant="outlined" class="border-opacity-50" rounded="lg">
                                <v-card-title class="bg-surface text-subtitle-2 py-2 px-3 px-sm-4 d-flex align-center flex-wrap gap-2"
                                    style="font-size: 0.9em">
                                    <div class="d-flex align-center">
                                        <v-icon size="small" class="mr-2">mdi-format-list-bulleted</v-icon>
                                        配置选项列表
                                    </div>
                                    <v-spacer></v-spacer>
                                    <v-btn size="small" color="primary" variant="elevated" elevation="1"
                                        prepend-icon="mdi-plus" @click="addOption">
                                        新增选项
                                    </v-btn>
                                </v-card-title>
                                <v-divider></v-divider>

                                <v-card-text class="pa-3 pa-sm-4">
                                    <div v-if="!editFieldData.options || editFieldData.options.length === 0"
                                        class="text-center text-body-2 text-grey py-4">
                                        暂无选项，请点击右上角新增
                                    </div>

                                    <!-- 响应式选项列表：移动端堆叠，PC端并排，删除按钮始终居右 -->
                                    <div v-for="(opt, i) in editFieldData.options" :key="i" class="d-flex align-stretch mb-3 gap-2 pa-2 pa-sm-0 border-sm-none rounded-lg">
                                        <div class="d-flex flex-column flex-sm-row flex-grow-1 gap-2">
                                            <v-text-field v-model="opt.label" label="显示文本" placeholder="如：男"
                                                hide-details density="comfortable" variant="outlined" bg-color="surface"
                                                class="custom-font-input"></v-text-field>
                                            <v-text-field v-model="opt.value" label="数据值" placeholder="如：male"
                                                hide-details density="comfortable" variant="outlined" bg-color="surface"
                                                class="custom-font-input"></v-text-field>
                                        </div>
                                        <div class="d-flex align-center justify-center px-1">
                                            <v-btn icon="mdi-delete-outline" size="small" variant="text" color="error"
                                                @click="removeOption(Number(i))"></v-btn>
                                        </div>
                                    </div>

                                    <div class="mt-4 mt-sm-6" v-if="editFieldData.options && editFieldData.options.length > 0">
                                        <v-select v-model="editFieldData.default" :items="editFieldData.options"
                                            item-title="label" item-value="value" label="设置默认选中的项" variant="outlined"
                                            density="comfortable" color="primary" clearable hint="如果不设置则默认不选中任何项"
                                            persistent-hint></v-select>
                                    </div>
                                </v-card-text>
                            </v-card>
                        </v-col>
                    </v-row>
                </v-card-text>

                <v-divider></v-divider>

                <v-card-actions class="pa-3 pa-sm-4 bg-surface">
                    <v-spacer></v-spacer>
                    <v-btn variant="text" class="px-4 px-sm-5 font-weight-medium" @click="dialog = false">取消</v-btn>
                    <v-btn color="primary" variant="flat" class="px-4 px-sm-5 font-weight-medium" elevation="1"
                        :disabled="!editFieldData.label" @click="saveField">
                        确认保存
                    </v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>

        <!-- 删除确认对话框 -->
        <v-dialog v-model="confirmDialog" max-width="400">
            <v-card rounded="lg">
                <v-card-title class="text-subtitle-1 text-sm-h6 pa-4 pa-sm-5 pb-2 d-flex align-center text-error">
                    <v-icon color="error" class="mr-2">mdi-alert-circle</v-icon>
                    确认删除
                </v-card-title>
                <v-card-text class="px-4 px-sm-5 py-3 text-body-2 text-sm-body-1 text-grey-darken-2">
                    确定要删除该字段吗？此操作不可撤销。
                </v-card-text>
                <v-card-actions class="pa-3 pa-sm-4 pt-0">
                    <v-spacer></v-spacer>
                    <v-btn variant="text" class="font-weight-medium" @click="confirmDialog = false">取消</v-btn>
                    <v-btn color="error" variant="flat" class="px-4 font-weight-medium"
                        @click="confirmDelete">确认删除</v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>

        <!-- 消息提示 -->
        <v-snackbar v-model="snackbar" :timeout="2500" :color="snackbarColor">
            <div class="d-flex align-center text-body-2 text-sm-subtitle-1">
                <v-icon start size="small" class="mr-2">{{ snackbarIcon }}</v-icon>
                {{ snackbarText }}
            </div>
        </v-snackbar>
    </v-container>
</template>

<script setup lang="ts">
import { ref, reactive, watch, useTemplateRef, onMounted } from 'vue';
import draggable from 'vuedraggable';
import { ajax } from '@/api/ajax';
import { cookie } from '@/api/cookie';

const fields = ref<any[]>([]);
const isLoading = ref(false);
const isSaving = ref(false);
const dialog = ref(false);
const resetDialog = ref(false);
const importDialog = ref(false);
const editIndex = ref<number | null>(null);
const editFieldData = reactive<any>({});

const confirmDialog = ref(false);
const deleteIndex = ref<number | null>(null);
const snackbar = ref(false);
const snackbarText = ref('');
const snackbarColor = ref('success');
const snackbarIcon = ref('mdi-check-circle');
const fileInput = useTemplateRef("fileInput")

onMounted(async () => {
    const token = cookie.get('token');
    // 防止未登录报错，生产环境按需开启
    if(!token) return; 
    isLoading.value = true;
    try {
        const res = await ajax<any[]>('/api/admin/settings/fields', {
            method: 'GET',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.code === 200) {
            fields.value = res.data || [];
        } else {
            showMsg(res.msg, 'error', 'mdi-alert-circle');
        }
    } finally {
        isLoading.value = false;
    }
});

const fieldTypes = [
    { label: '单行文本', value: 'text', icon: 'mdi-format-text' },
    { label: '多行文本', value: 'textarea', icon: 'mdi-text-box-outline' },
    { label: '日期选择', value: 'date', icon: 'mdi-calendar-blank-outline' },
    { label: '日期范围', value: 'date-range', icon: 'mdi-calendar-range-outline' },
    { label: '数值', value: 'number', icon: 'mdi-sort-numeric-variant' },
    { label: '数字范围', value: 'number-range', icon: 'mdi-numeric' },
    { label: '时间范围', value: 'time-range', icon: 'mdi-clock-time-eight-outline' },
    { label: '单选按钮', value: 'radio', icon: 'mdi-radiobox-marked' },
    { label: '复选框组', value: 'checkbox', icon: 'mdi-checkbox-marked-outline' },
    { label: '下拉菜单', value: 'select', icon: 'mdi-form-dropdown' },
];

const generateId = () => Math.random().toString(36).substring(2, 9) + Date.now().toString(36);

function fieldTypeLabel(type: string) {
    const t = fieldTypes.find(f => f.value === type);
    return t ? t.label : type;
}

function getFieldIcon(type: string) {
    const t = fieldTypes.find(f => f.value === type);
    return t ? t.icon : 'mdi-form-textbox';
}

function itemTypeProps(item: any) {
    return {
        prependIcon: item.icon,
        title: item.label
    };
}

function isOptionType(type: string) {
    return ['radio', 'checkbox', 'select'].includes(type);
}

function isRangeType(type: string) {
    return ['date-range', 'number-range', 'time-range'].includes(type);
}

watch(() => editFieldData.type, (newType) => {
    if (isRangeType(newType)) {
        if (!Array.isArray(editFieldData.default)) {
            editFieldData.default = ['', ''];
        }
    } else if (isOptionType(newType)) {
        if (Array.isArray(editFieldData.default)) {
            editFieldData.default = '';
        }
    } else {
        if (Array.isArray(editFieldData.default)) {
            editFieldData.default = '';
        }
    }
});

function addField() {
    editIndex.value = null;
    Object.assign(editFieldData, {
        id: generateId(),
        label: '',
        type: 'text',
        required: false,
        default: '',
        options: [],
    });
    dialog.value = true;
}

function editField(index: number) {
    editIndex.value = index;
    Object.assign(editFieldData, JSON.parse(JSON.stringify(fields.value[index])));
    dialog.value = true;
}

function saveField() {
    if (!editFieldData.label) {
        showMsg('请输入字段名称', 'error', 'mdi-alert-circle');
        return;
    }

    if (isOptionType(editFieldData.type)) {
        editFieldData.options = editFieldData.options?.filter((o: any) => o.label.trim() !== '' && o.value.trim() !== '') || [];
        if (editFieldData.options.length === 0) {
            showMsg('选项类字段至少需要填写一个有效选项', 'warning', 'mdi-alert');
            return;
        }
    } else {
        editFieldData.options = [];
    }

    const savedData = JSON.parse(JSON.stringify(editFieldData));

    if (editIndex.value === null) {
        fields.value.push(savedData);
        showMsg('字段添加成功');
    } else {
        fields.value[editIndex.value] = savedData;
        showMsg('字段修改已保存');
    }
    dialog.value = false;
}

function openDeleteConfirm(index: number) {
    deleteIndex.value = index;
    confirmDialog.value = true;
}

function confirmDelete() {
    if (deleteIndex.value !== null) {
        fields.value.splice(deleteIndex.value, 1);
        deleteIndex.value = null;
        confirmDialog.value = false;
        showMsg('字段已删除', 'info', 'mdi-information');
    }
}

function confirmReset() {
    fields.value = [];
    resetDialog.value = false;
    showMsg('已清空所有字段', 'info', 'mdi-delete-sweep');
}

function addOption() {
    if (!editFieldData.options) editFieldData.options = [];
    editFieldData.options.push({ label: '', value: '' });
}

function removeOption(i: number) {
    editFieldData.options.splice(i, 1);
}

function showMsg(msg: string, color: string = 'success', icon: string = 'mdi-check-circle') {
    snackbarText.value = msg;
    snackbarColor.value = color;
    snackbarIcon.value = icon;
    snackbar.value = true;
}

function saveFields() {
    const token = cookie.get('token');
    isSaving.value = true;
    ajax('/api/admin/settings/fields', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: fields.value
    }).then(res => {
        if (res.code === 200) {
            showMsg('配置已成功同步至服务器');
        } else {
            showMsg(res.msg, 'error', 'mdi-alert-circle');
        }
    }).finally(() => {
        isSaving.value = false;
    });
}

function downloadTemplate() {
    const template = `# 登记字段配置导入模板

每一行代表一个字段，格式为：字段名称|字段类型|是否必填(1/0)|选项(label:value,label:value,...)
字段类型选项：text, textarea, date, date-range, number-range, time-range, radio, checkbox, select

示例：
姓名|text|1
自我介绍|textarea|0
选择性别|select|1|男:male,女:female
兴趣爱好|checkbox|0|篮球:basketball,足球:football
`;

    const blob = new Blob([template], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = '登记字段导入模板.txt';
    a.click();
    URL.revokeObjectURL(url);
}

function handleFileImport(event: any) {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
        const text = e.target?.result as string;
        const lines = text.split('\n');
        const newFields = lines.map(line => {
            const [label, type, required, optionsStr] = line.split('|');
            if (!label || !type) return null;

            let options: any[] = [];
            if (optionsStr && isOptionType(type.trim())) {
                options = optionsStr.split(',').map(pair => {
                    const [label, value] = pair.split(':');
                    return { label: label.trim(), value: value.trim() };
                });
            }

            return {
                id: generateId(),
                label: label.trim(),
                type: type.trim(),
                required: required?.trim() === '1',
                default: isRangeType(type.trim()) ? ['', ''] : '',
                options: options
            };
        }).filter(f => f !== null);

        fields.value.push(...newFields as any[]);
        showMsg(`成功导入 ${newFields.length} 个字段`, 'success', 'mdi-file-check');
        event.target.value = ''; // Reset input
        importDialog.value = false;
    };
    reader.readAsText(file);
}
</script>

<style scoped>
.max-width-800 {
    max-width: 800px;
    margin: 0 auto;
}

/* 响应式间距辅助类 */
.gap-1 { gap: 4px; }
.gap-2 { gap: 8px; }
.gap-3 { gap: 12px; }

/* 拖拽把手 */
.drag-handle {
    cursor: grab;
    opacity: 0.45;
    transition: opacity .2s ease, transform .2s ease, color .2s ease;
}

.field-card:hover .drag-handle {
    opacity: 1;
    transform: scale(1.08);
    color: rgb(var(--v-theme-primary)) !important;
}

.drag-handle:active {
    cursor: grabbing;
    transform: scale(0.95);
}

/* 卡片整体质感 */
.field-card {
    position: relative;
    overflow: hidden;
    border: 1px solid rgba(var(--v-theme-on-surface), 0.08) !important;
    background: rgb(var(--v-theme-background));
    transition: transform .22s ease, box-shadow .22s ease, border-color .22s ease;
    box-shadow: 0 1px 3px rgba(var(--v-theme-on-surface), 0.03), 0 4px 12px rgba(var(--v-theme-on-surface), 0.03);
}

.field-card:hover {
    border-color: rgba(var(--v-theme-primary), 0.4) !important;
    box-shadow: 0 4px 16px rgba(var(--v-theme-on-surface), 0.08) !important;
    transform: translateY(-1px);
}

/* 顶部渐变线 */
.field-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 3px;
    background: linear-gradient(90deg, rgba(var(--v-theme-primary), 0.9), rgba(var(--v-theme-primary), 0.3));
    opacity: 0;
    transition: opacity .2s ease;
}
.field-card:hover::before {
    opacity: 1;
}

/* =========================
   触摸屏与悬浮适配 (重要)
========================= */
/* 仅在支持鼠标悬浮的设备上隐藏操作按钮 */
@media (hover: hover) {
    .hover-action {
        opacity: 0;
        transform: translateY(4px);
        transition: opacity .2s ease, transform .2s ease;
    }
    .field-card:hover .hover-action {
        opacity: 1;
        transform: translateY(0);
    }
}
/* 触摸屏设备上始终显示，防止无法点击 */
@media (hover: none) {
    .hover-action {
        opacity: 1;
        transform: none;
    }
}

/* 拖拽相关类 */
.ghost-card {
    opacity: 0.7;
    background: rgb(var(--v-theme-surface)) !important;
    border: 2px dashed rgba(var(--v-theme-primary), 0.45) !important;
    box-shadow: none !important;
    transform: scale(1.02);
}
.sortable-chosen {
    transform: scale(1.01);
}
.sortable-drag {
    opacity: 1 !important;
    transform: rotate(1deg);
    box-shadow: 0 18px 40px rgba(var(--v-theme-on-surface), 0.2) !important;
}

/* 拖拽相关类 */
.ghost-card {
    border: 2px dashed rgba(var(--v-theme-on-surface), 0.15) !important;
    background: rgb(var(--v-theme-surface)) !important;
    transition: border-color .2s ease, transform .2s ease, background .2s ease;
}
.dashed-border:hover {
    border-color: rgba(var(--v-theme-primary), 0.4) !important;
    transform: translateY(-2px);
    background: rgb(var(--v-theme-surface)) !important;
}

.border-bottom {
    border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.custom-font-input :deep(.v-field__input) {
    font-size: 0.95rem;
}
.custom-font-input :deep(.v-label) {
    font-size: 0.85rem;
}
</style>
