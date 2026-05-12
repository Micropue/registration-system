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

/** 用户列表项 */
export interface UserItem {
  username: string;
  session_count: number;
  type: 'admin' | 'default';
  register_time: string;
  last_login_time: string | null;
  login_ip: string | null;
  login_device: string;
}
