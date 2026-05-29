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
  /** 精确匹配（默认 false，即前缀匹配） */
  exact?: boolean;
}

export const functions: NavFunction[] = [
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
    title: '充值审批',
    to: '/admin/recharges',
    icon: 'mdi-cash-check',
    role: 'admin'
  },
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
    title: '充值申请',
    to: '/recharge',
    icon: 'mdi-cash-plus',
    role: 'default'
  },
  {
    title: '仪表盘',
    to: '/admin',
    icon: 'mdi-view-dashboard-outline',
    role: 'admin',
    exact: true
  },
  {
    title: '账户管理',
    to: '/admin/users',
    icon: 'mdi-account-group-outline',
    role: 'admin'
  },
  {
    title: '跑步APP配置',
    to: '/admin/running-apps',
    icon: 'mdi-run',
    role: 'admin'
  },
  {
    title: '账户组管理',
    to: '/admin/groups',
    icon: 'mdi-shield-account-outline',
    role: 'admin'
  },
  {
    title: '余额查看',
    to: '/balance',
    icon: 'mdi-wallet-outline',
    role: 'default'
  },
  {
    title: '余额流水',
    to: '/balance-transactions',
    icon: 'mdi-history',
    role: 'default'
  },
  {
    title: '更新日志',
    to: '/admin/update-logs',
    icon: 'mdi-update',
    role: 'admin'
  },
  {
    title: '关于',
    to: '/about',
    icon: 'mdi-information-outline',
    role: 'default'
  },
];
