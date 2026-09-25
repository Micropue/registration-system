/**
 * 功能菜单配置
 */

export interface NavFunction {
  title: string;
  to: string;
  icon?: string;
  role?: 'admin' | 'default';
  exact?: boolean;
  group?: 'bottom';
  children?: { title: string; to: string; icon?: string }[];
}

export const functions: NavFunction[] = [
  {
    title: '订单处理',
    to: '/admin/registers',
    icon: 'mdi-file-document-edit-outline',
    role: 'admin',
    children: [
      { title: '一次订单', to: '/admin/registers', icon: 'mdi-file-document-outline' },
      { title: '二次订单', to: '/admin/registers?tab=secondary', icon: 'mdi-file-refresh-outline' },
    ]
  },
  {
    title: '充值审批',
    to: '/admin/recharges',
    icon: 'mdi-cash-check',
    role: 'admin'
  },
  {
    title: '订单',
    to: '/sign',
    icon: 'mdi-plus-circle-outline',
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
    title: '通知中心',
    to: '/notifications',
    icon: 'mdi-bell-outline',
    role: 'default'
  },
  {
    title: '账户管理',
    to: '/admin/users',
    icon: 'mdi-account-group-outline',
    role: 'admin'
  },
  {
    title: 'APP配置',
    to: '/admin/apps',
    icon: 'mdi-apps',
    role: 'admin'
  },
  {
    title: '公告',
    to: '/admin/announcements',
    icon: 'mdi-bullhorn-outline',
    role: 'admin'
  },
  {
    title: '下属管理',
    to: '/admin/subordinates',
    icon: 'mdi-file-tree-outline',
    role: 'admin'
  },
  {
    title: '账户组管理',
    to: '/admin/groups',
    icon: 'mdi-shield-account-outline',
    role: 'admin'
  },
  {
    title: '日报管理',
    to: '/admin/daily-reports',
    icon: 'mdi-notebook-edit-outline',
    role: 'admin'
  },
  {
    title: '每日报告',
    to: '/daily-report',
    icon: 'mdi-notebook-edit-outline',
    role: 'default'
  },
  {
    title: '余额查看',
    to: '/balance',
    icon: 'mdi-wallet-outline',
    role: 'default'
  },
  {
    title: '聊天室',
    to: '/chat-room',
    icon: 'mdi-comment-outline',
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
    role: 'admin',
    group: 'bottom'
  },
  {
    title: '关于',
    to: '/about',
    icon: 'mdi-information-outline',
    role: 'default',
    group: 'bottom'
  },
];
