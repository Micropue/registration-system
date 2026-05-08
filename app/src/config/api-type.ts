/**
 * 接口响应体与请求体类型定义
 */

/** 登录请求体 */
export interface LoginParams {
  username?: string;
  password?: string;
}

/** 登录响应数据 */
export interface LoginData {
  token: string;
}

/** 登录检测响应数据 */
export interface CheckLoginData {
  username: string;
  type: 'admin' | 'default';
  token: string;
}
