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
}
