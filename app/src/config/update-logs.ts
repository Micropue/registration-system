/**
 * 更新日志 — 由 scripts/gen-update-logs.mjs 在 build 时从 git 历史自动生成
 * 不要手动编辑此文件
 */
export interface UpdateLogItem {
  version: string
  date: string
  title: string
  details: string[]
}

export const updateLogs: UpdateLogItem[] = [
  {
    "version": "2.0.0",
    "date": "2026-09-15",
    "title": "新增余额扣除方式功能，支持四舍五入与五舍六入选项",
    "details": [
      "新增余额扣除方式功能，支持四舍五入与五舍六入选项"
    ]
  },
  {
    "version": "2.1.0",
    "date": "2026-09-14",
    "title": "新增转发聊天室功能，支持将订单信息转发至聊天室",
    "details": [
      "新增转发聊天室功能，支持将订单信息转发至聊天室"
    ]
  },
  {
    "version": "2.2.0",
    "date": "2026-09-12",
    "title": "聊天室消息置顶、侧边栏自定义排序与权限",
    "details": [
      "聊天室消息置顶、侧边栏自定义排序与权限"
    ]
  },
  {
    "version": "2.3.0",
    "date": "2026-09-10",
    "title": "修正上传目标路径，确保代码正确部署到指定目录",
    "details": [
      "修正上传目标路径，确保代码正确部署到指定目录",
      "add global chat feature with websocket support"
    ]
  },
  {
    "version": "2.4.0",
    "date": "2026-07-27",
    "title": "更新二次订单标记逻辑，确保仅在员工处理后标记为二次订单",
    "details": [
      "更新二次订单标记逻辑，确保仅在员工处理后标记为二次订单"
    ]
  },
  {
    "version": "2.5.0",
    "date": "2026-06-15",
    "title": "新增每日报告、账户组限制、常用回复语等功能",
    "details": [
      "新增每日报告、账户组限制、常用回复语等功能"
    ]
  },
  {
    "version": "2.6.0",
    "date": "2026-06-12",
    "title": "一次/二次订单红点与列表筛选条件统一为is_secondary",
    "details": [
      "一次/二次订单红点与列表筛选条件统一为is_secondary",
      "看板统计权限过滤与订单列表保持一致",
      "App分类红点按当前标签(一次/二次)筛选",
      "二次订单功能 — 侧边栏多级菜单 + 聊天/驳回触发上浮",
      "工单功能隐藏、版本号、消息撤回"
    ]
  },
  {
    "version": "2.7.0",
    "date": "2026-06-10",
    "title": "添加强调弹窗功能，支持条件配置和内容显示",
    "details": [
      "添加强调弹窗功能，支持条件配置和内容显示",
      "修复了一些问题： App模版编辑器支持上传多张图片， 支持多张一键导出 仪表盘默认显示所有下属创建的订单或工单数据或用户 订单填写表单上传图片组件存在问题，单独给一个上传会导致给当前表单下所有的图片上传器共用文件，模板中出现多个图片上传器在上传时会出现该问题。",
      "修复图片预览显示红叉问题：移除v-file-input的:model-value绑定",
      "图片上传组件支持多图上传+缩略图预览+一键导出"
    ]
  },
  {
    "version": "2.8.0",
    "date": "2026-06-09",
    "title": "修复了一些问题",
    "details": [
      "修复了一些问题",
      "修复权限配置关闭查看后仍能访问对应管理页面的问题",
      "修复余额流水 balance_after 重复计算bug",
      "用户端重新提交/修改订单也执行先退旧扣费再重新扣费",
      "用户端修改订单支持编辑数量"
    ]
  },
  {
    "version": "2.9.0",
    "date": "2026-06-08",
    "title": "修复订单修改后余额异常扣数量问题",
    "details": [
      "修复订单修改后余额异常扣数量问题",
      "订单新建历史支持与订单处理相同的复杂搜索字段功能"
    ]
  },
  {
    "version": "2.10.0",
    "date": "2026-06-07",
    "title": "模板添加图片上传器。",
    "details": [
      "模板添加图片上传器。"
    ]
  },
  {
    "version": "2.11.0",
    "date": "2026-06-05",
    "title": "更新更新日志，添加聊天功能和相关权限配置",
    "details": [
      "更新更新日志，添加聊天功能和相关权限配置",
      "添加通知中心功能，支持用户通知的创建、读取和管理",
      "Add announcement management functionality"
    ]
  },
  {
    "version": "2.12.0",
    "date": "2026-06-04",
    "title": "添加 dotenv 加载以支持环境变量配置",
    "details": [
      "添加 dotenv 加载以支持环境变量配置",
      "修复服务器上传步骤的源路径和目标路径配置",
      "Merge branch 'main' of https://github.com/Micropue/registration-system",
      "添加构建客户端和服务器的工作流",
      "Create build-server.yml",
      "Update build-client.yml",
      "Add upload step for built client files",
      "Update build-client.yml",
      "Create build-client.yml",
      "Delete .github/workflows/main.yml"
    ]
  },
  {
    "version": "2.13.0",
    "date": "2026-06-03",
    "title": "添加模板复刻功能",
    "details": [
      "添加模板复刻功能",
      "Create main.yml",
      "修改通知系统，仅显示未处理的任务"
    ]
  },
  {
    "version": "2.14.0",
    "date": "2026-06-02",
    "title": "修复通知菜单和用户状态处理逻辑",
    "details": [
      "修复通知菜单和用户状态处理逻辑"
    ]
  },
  {
    "version": "2.15.0",
    "date": "2026-06-01",
    "title": "将“数据登记”相关术语更改为“订单”，并更新相关权限配置",
    "details": [
      "将“数据登记”相关术语更改为“订单”，并更新相关权限配置"
    ]
  },
  {
    "version": "2.16.0",
    "date": "2026-05-31",
    "title": "server/src/account_service.py 里把委托余额的“实际持有人”统一纳入查询，修正了两处核心偏…",
    "details": [
      "server/src/account_service.py 里把委托余额的“实际持有人”统一纳入查询，修正了两处核心偏差：get_app_user_balances() 现在在同页出现上级/下属时也会显示真正的归属余额和更新时间；get_user_balance_transactions() 现在会按委托后的有效 owner 去查流水，不会再出现“余额变了但流水查不到”。 app/src/pag…",
      "更新 .gitignore 文件以忽略构建和测试相关文件",
      "更新更新日志以移除同步功能"
    ]
  },
  {
    "version": "2.17.0",
    "date": "2026-05-30",
    "title": "移除更新日志同步功能",
    "details": [
      "移除更新日志同步功能",
      "添加下属管理和更新日志页面",
      "修复默认管理员密码错误",
      "本次项目变更总结 一、下属管理体系（核心新功能） 数据库新增 2 张表： 表\t用途 user_subordinates\t上级-下级层级关系（UNIQUE 约束防重复/循环） balance_delegations\t余额扣除链接（每用户每APP最多链接一个上级） 后端新增（account_service.py）： 方法\t功能 get_subordinates / add_subordinate /…"
    ]
  },
  {
    "version": "2.18.0",
    "date": "2026-05-29",
    "title": "为编程加入了丰富的skill，加入了关于界面和更新日志界面",
    "details": [
      "为编程加入了丰富的skill，加入了关于界面和更新日志界面"
    ]
  },
  {
    "version": "2.19.0",
    "date": "2026-05-28",
    "title": "更新模板字段复制按钮的逻辑",
    "details": [
      "更新模板字段复制按钮的逻辑",
      "用户界面加入余额管理",
      "订单处理搜索支持搜索客户信息"
    ]
  },
  {
    "version": "2.20.0",
    "date": "2026-05-27",
    "title": "添加注册详情的处理和驳回按钮",
    "details": [
      "添加注册详情的处理和驳回按钮",
      "Add drag-and-drop sorting for apps and enhance notification handling"
    ]
  },
  {
    "version": "2.21.0",
    "date": "2026-05-23",
    "title": "Implement user balance management and notifications",
    "details": [
      "Implement user balance management and notifications",
      "添加订单处理、工单处理、充值审批的待处理计数功能"
    ]
  },
  {
    "version": "2.22.0",
    "date": "2026-05-22",
    "title": "优化主题颜色变量使用",
    "details": [
      "优化主题颜色变量使用",
      "修复首页文本对齐问题",
      "add PWA support with service worker and icons",
      "新增数据登记表单对话框",
      "添加Prism组件并优化首页样式",
      "更新注册聊天界面样式和功能",
      "加了很多功能，聊天框的背景没改上"
    ]
  },
  {
    "version": "2.23.0",
    "date": "2026-05-21",
    "title": "添加通知菜单打开状态控制与关联ID已读标记功能",
    "details": [
      "添加通知菜单打开状态控制与关联ID已读标记功能"
    ]
  },
  {
    "version": "2.24.0",
    "date": "2026-05-19",
    "title": "修正导航功能项及模板管理中的字段名称",
    "details": [
      "修正导航功能项及模板管理中的字段名称",
      "remove deleteOriginalAssets option from viteCompression configuration",
      "add icon support for apps and image upload functionality",
      "移除 ChatDrawer 及相关逻辑",
      "Enhance admin dashboard and registration features"
    ]
  },
  {
    "version": "2.25.0",
    "date": "2026-05-18",
    "title": "add WebSocket chat functionality and enhance admin registra…",
    "details": [
      "add WebSocket chat functionality and enhance admin registration features"
    ]
  },
  {
    "version": "2.26.0",
    "date": "2026-05-16",
    "title": "add apps management and feedback system",
    "details": [
      "add apps management and feedback system",
      "添加构建前后的代理端口更新脚本及样式优化"
    ]
  },
  {
    "version": "2.27.0",
    "date": "2026-05-15",
    "title": "添加删除登记记录的功能",
    "details": [
      "添加删除登记记录的功能",
      "更新登记列表和状态处理逻辑",
      "添加开发启动指南"
    ]
  },
  {
    "version": "2.28.0",
    "date": "2026-05-14",
    "title": "添加数据登记功能",
    "details": [
      "添加数据登记功能",
      "添加表单字段配置功能"
    ]
  },
  {
    "version": "2.29.0",
    "date": "2026-05-13",
    "title": "添加登记字段配置页面和欢迎页面",
    "details": [
      "添加登记字段配置页面和欢迎页面"
    ]
  },
  {
    "version": "2.30.0",
    "date": "2026-05-12",
    "title": "添加用户批量创建和管理功能",
    "details": [
      "添加用户批量创建和管理功能",
      "更新登录检测和用户管理功能"
    ]
  },
  {
    "version": "2.31.0",
    "date": "2026-05-08",
    "title": "新增API文档及登录相关接口说明",
    "details": [
      "新增API文档及登录相关接口说明",
      "添加登录页面和导航栏"
    ]
  },
  {
    "version": "2.32.0",
    "date": "2026-05-07",
    "title": "init app",
    "details": [
      "init app",
      "添加账户系统和Docker配置"
    ]
  }
];
