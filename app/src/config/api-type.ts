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
  uid: string;
  username: string;
  session_count: number;
  type: 'admin' | 'default';
  register_time: string;
  last_login_time: string | null;
  login_ip: string | null;
  login_device: string;
}

/** 表单字段选项 */
export interface FieldOption {
  label: string;
  value: string;
}

/** 表单字段配置 */
export interface FormFieldConfig {
  validation?: string;
  maxLength?: number;
  minLength?: number;
  rows?: number;
  options?: FieldOption[];
  minDate?: string;
  maxDate?: string;
  format?: string;
  accept?: string;
  maxSize?: number;
  [key: string]: any;
}

/** 表单字段类型 */
export type FieldType = 'text' | 'textarea' | 'select' | 'radio' | 'checkbox' | 'date' | 'time' | 'datetime' | 'file';

/** 登记列表项 */
export interface RegistrationItem {
  id: string;
  username: string;
  created_at: string;
  status: 'pending' | 'approved' | 'rejected';
  registration_info: Record<string, any>;
}

/** 跑步APP配置 */
export interface RunningApp {
  id: number;
  name: string;
  normal_price: number;
  morning_price: number;
  note: string;
  accent_color: string;
}
