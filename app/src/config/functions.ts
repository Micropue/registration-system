/**
 * 功能菜单配置
 */

export interface NavFunction {
  /** 显示名称 */
  title: string;
  /** 路由跳转地址 */
  to: string;
  /** 图标名称 (MDI) */
  icon?: string;
  /** 允许访问的角色 (可选，不填则默认 default 可见) */
  role?: 'admin' | 'default';
}

export const functions: NavFunction[] = [
  {
    title: '数据登记',
    to: '/sign',
    icon: 'mdi-plus-circle-outline',
    role: 'default'
  },
  {
    title: '工单反馈',
    to: '/feedback',
    icon: 'mdi-message-text-outline',
    role: 'default'
  },
  {
    title: '仪表盘',
    to: '/admin',
    icon: 'mdi-view-dashboard-outline',
    role: 'admin'
  },
  {
    title: '账户管理',
    to: '/admin/users',
    icon: 'mdi-account-group-outline',
    role: 'admin'
  },
  {
    title: '订单处理',
    to: '/admin/registers',
    icon: 'mdi-file-document-edit-outline',
    role: 'admin'
  },
  {
    title: '工单处理',
    to: '/admin/feedbacks',
    icon: 'mdi-folder-multiple-outline',
    role: 'admin'
  },
  {
    title: '系统设置',
    to: '/admin/settings',
    icon: 'mdi-cog-outline',
    role: 'admin'
  }
];
