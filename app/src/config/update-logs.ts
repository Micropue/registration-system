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
    "date": "2026-05-30",
    "title": "添加下属管理和更新日志页面",
    "details": [
      "添加下属管理和更新日志页面",
      "修复默认管理员密码错误",
      "本次项目变更总结 一、下属管理体系（核心新功能） 数据库新增 2 张表： 表\t用途 user_subordinates\t上级-下级层级关系（UNIQUE 约束防重复/循环） balance_delegations\t余额扣除链接（每用户每APP最多链接一个上级） 后端新增（account_service.py）： 方法\t功能 get_subordinates / add_subordinate /…"
    ]
  },
  {
    "version": "2.1.0",
    "date": "2026-05-29",
    "title": "为编程加入了丰富的skill，加入了关于界面和更新日志界面",
    "details": [
      "为编程加入了丰富的skill，加入了关于界面和更新日志界面"
    ]
  },
  {
    "version": "2.2.0",
    "date": "2026-05-28",
    "title": "更新模板字段复制按钮的逻辑",
    "details": [
      "更新模板字段复制按钮的逻辑",
      "用户界面加入余额管理",
      "订单处理搜索支持搜索客户信息"
    ]
  },
  {
    "version": "2.3.0",
    "date": "2026-05-27",
    "title": "添加注册详情的处理和驳回按钮",
    "details": [
      "添加注册详情的处理和驳回按钮",
      "Add drag-and-drop sorting for running apps and enhance notification handling"
    ]
  },
  {
    "version": "2.4.0",
    "date": "2026-05-23",
    "title": "Implement user balance management and notifications",
    "details": [
      "Implement user balance management and notifications",
      "添加订单处理、工单处理、充值审批的待处理计数功能"
    ]
  },
  {
    "version": "2.5.0",
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
    "version": "2.6.0",
    "date": "2026-05-21",
    "title": "添加通知菜单打开状态控制与关联ID已读标记功能",
    "details": [
      "添加通知菜单打开状态控制与关联ID已读标记功能"
    ]
  },
  {
    "version": "2.7.0",
    "date": "2026-05-19",
    "title": "修正导航功能项及模板管理中的字段名称",
    "details": [
      "修正导航功能项及模板管理中的字段名称",
      "remove deleteOriginalAssets option from viteCompression configuration",
      "add icon support for running apps and image upload functionality",
      "移除 ChatDrawer 及相关逻辑",
      "Enhance admin dashboard and registration features"
    ]
  },
  {
    "version": "2.8.0",
    "date": "2026-05-18",
    "title": "add WebSocket chat functionality and enhance admin registra…",
    "details": [
      "add WebSocket chat functionality and enhance admin registration features"
    ]
  },
  {
    "version": "2.9.0",
    "date": "2026-05-16",
    "title": "add running apps management and feedback system",
    "details": [
      "add running apps management and feedback system",
      "添加构建前后的代理端口更新脚本及样式优化"
    ]
  },
  {
    "version": "2.10.0",
    "date": "2026-05-15",
    "title": "添加删除登记记录的功能",
    "details": [
      "添加删除登记记录的功能",
      "更新登记列表和状态处理逻辑",
      "添加开发启动指南"
    ]
  },
  {
    "version": "2.11.0",
    "date": "2026-05-14",
    "title": "添加校园跑数据登记功能",
    "details": [
      "添加校园跑数据登记功能",
      "添加表单字段配置功能"
    ]
  },
  {
    "version": "2.12.0",
    "date": "2026-05-13",
    "title": "添加登记字段配置页面和欢迎页面",
    "details": [
      "添加登记字段配置页面和欢迎页面"
    ]
  },
  {
    "version": "2.13.0",
    "date": "2026-05-12",
    "title": "添加用户批量创建和管理功能",
    "details": [
      "添加用户批量创建和管理功能",
      "更新登录检测和用户管理功能"
    ]
  },
  {
    "version": "2.14.0",
    "date": "2026-05-08",
    "title": "新增API文档及登录相关接口说明",
    "details": [
      "新增API文档及登录相关接口说明",
      "添加登录页面和导航栏"
    ]
  },
  {
    "version": "2.15.0",
    "date": "2026-05-07",
    "title": "init app",
    "details": [
      "init app",
      "添加账户系统和Docker配置"
    ]
  }
];
