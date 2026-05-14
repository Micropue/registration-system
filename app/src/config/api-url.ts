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
  /** 重新排序表单字段 (管理员) */
  REORDER_FORM_FIELDS = '/api/admin/settings/fields/reorder',
}
