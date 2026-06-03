/**
 * 接口地址配置
 */

export enum ApiUrl {
  /** 登录接口 */
  LOGIN = '/api/auth/login',
  /** 登录状态检测 */
  CHECK_LOGIN = '/api/auth/check-login',
  /** 获取所有用户 (管理员) */
  GET_USERS = '/api/admin/users',
  /** 创建用户 (管理员) */
  CREATE_USER = '/api/admin/users',
  /** 批量创建用户 (管理员) */
  BULK_CREATE_USER = '/api/admin/users/bulk',
  /** 修改用户 (管理员) */
  UPDATE_USER = '/api/admin/users',
  /** 删除用户 (管理员) */
  DELETE_USER = '/api/admin/users',
  /** 强制下线 (管理员) */
  FORCE_LOGOUT = '/api/admin/users',
  /** 获取筛选候选值 */
  GET_FILTER_VALUES = '/api/admin/filter-values',
  /** 获取表单字段 (管理员) */
  GET_FORM_FIELDS = '/api/admin/settings/fields',
  /** 创建表单字段 (管理员) */
  CREATE_FORM_FIELD = '/api/admin/settings/fields',
  /** 修改表单字段 (管理员) */
  UPDATE_FORM_FIELD = '/api/admin/settings/fields',
  /** 删除表单字段 (管理员) */
  DELETE_FORM_FIELD = '/api/admin/settings/fields',
  /** 获取登记列表 (管理员) */
  GET_REGISTRATIONS = '/api/admin/registrations',
  /** 更新登记状态 (管理员) */
  UPDATE_REGISTRATION_STATUS = '/api/admin/registrations',
  /** 删除登记记录 (管理员) */
  DELETE_REGISTRATION = '/api/admin/registrations',
  /** 获取各APP登记统计 */
  REGISTRATION_STATS = '/api/admin/registrations/stats',
  /** 获取登记聊天记录 */
  REGISTRATION_CHAT = '/api/chat',
  /** 获取跑步APP配置 */
  GET_RUNNING_APPS = '/api/admin/settings/running-apps',
  /** 创建跑步APP配置 */
  CREATE_RUNNING_APP = '/api/admin/settings/running-apps',
  /** 修改跑步APP配置 */
  UPDATE_RUNNING_APP = '/api/admin/settings/running-apps',
  /** 删除跑步APP配置 */
  DELETE_RUNNING_APP = '/api/admin/settings/running-apps',
  /** 批量导入跑步APP配置 */
  BULK_CREATE_RUNNING_APPS = '/api/admin/settings/running-apps/bulk',
  /** 获取APP模板列表 */
  GET_APP_TEMPLATES = '/api/admin/settings/running-apps',
  /** 获取公开APP模板 */
  GET_PUBLIC_APP_TEMPLATES = '/api/running-apps',
  /** 仪表盘统计数据 */
  DASHBOARD_STATS = '/api/admin/dashboard/stats',
  /** 获取用户订单历史 */
  GET_USER_REGISTRATIONS = '/api/registrations',
  /** 获取单条订单详情 */
  GET_REGISTRATION_DETAIL = '/api/registrations',
  /** 重新提交被驳回的登记 */
  RESUBMIT_REGISTRATION = '/api/registrations',
  /** 获取跑步APP列表（公开） */
  GET_PUBLIC_RUNNING_APPS = '/api/running-apps',
  /** 创建工单 */
  CREATE_FEEDBACK = '/api/feedbacks',
  /** 获取用户工单 */
  GET_USER_FEEDBACKS = '/api/feedbacks',
  /** 获取工单详情 */
  GET_FEEDBACK_DETAIL = '/api/feedbacks',
  /** 回复工单 */
  REPLY_FEEDBACK = '/api/feedbacks',
  /** 管理员工单列表 */
  ADMIN_GET_FEEDBACKS = '/api/admin/feedbacks',
  /** 管理员工单状态 */
  ADMIN_UPDATE_FEEDBACK_STATUS = '/api/admin/feedbacks',
  /** 获取通知 */
  GET_NOTIFICATIONS = '/api/notifications',
  /** 账户组管理 */
  GET_GROUPS = '/api/admin/groups',
  CREATE_GROUP = '/api/admin/groups',
  UPDATE_GROUP = '/api/admin/groups',
  DELETE_GROUP = '/api/admin/groups',
  /** 用户分配组 */
  ASSIGN_USER_GROUP = '/api/admin/users',
  REMOVE_USER_GROUP = '/api/admin/users',
  /** APP余额 */
  UPDATE_APP_BALANCE = '/api/admin/running-apps',
  /** 余额流水 */
  GET_BALANCE_TRANSACTIONS = '/api/admin/balance-transactions',
  /** 用户余额 */
  GET_USER_BALANCES = '/api/user/balances',
  GET_USER_BALANCE_TRANSACTIONS = '/api/user/balance-transactions',
  /** 管理员查询指定用户余额 */
  ADMIN_GET_USER_BALANCES = '/api/admin/users',
  /** APP用户余额管理 */
  GET_APP_USER_BALANCES = '/api/admin/running-apps',
  ADJUST_APP_USER_BALANCE = '/api/admin/running-apps',
  /** 充值申请 */
  CREATE_RECHARGE = '/api/balance-recharges',
  GET_MY_RECHARGES = '/api/balance-recharges',
  GET_ALL_RECHARGES = '/api/admin/balance-recharges',
  PROCESS_RECHARGE = '/api/admin/balance-recharges',
  /** 图片上传 */
  UPLOAD_IMAGE = '/api/upload/image',
  /** 下属管理 */
  GET_SUBORDINATES = '/api/admin/users',
  ADD_SUBORDINATE = '/api/admin/users',
  REMOVE_SUBORDINATE = '/api/admin/users',
  GET_SUBORDINATE_TREE = '/api/admin/users',
  CREATE_BALANCE_LINK = '/api/admin/subordinates',
  REMOVE_BALANCE_LINK = '/api/admin/subordinates',
  GET_USER_DELEGATIONS = '/api/admin/users',
}
