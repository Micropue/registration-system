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
  role: 'super_admin' | 'admin' | 'default';
  group_name?: string;
  token: string;
  permissions?: Record<string, any>;
}

/** 用户列表项 */
export interface UserItem {
  uid: string;
  username: string;
  session_count: number;
  type: 'admin' | 'default' | 'super_admin';
  register_time: string;
  last_login_time: string | null;
  login_ip: string | null;
  login_device: string;
  group_uid?: string;
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
  priority?: 'low' | 'medium' | 'high';
}

/** 跑步APP配置 */
export interface RunningApp {
  id: number;
  uid: string;
  name: string;
  note: string;
  accent_color: string;
  icon?: string;
  template_count?: number;
  balance_mode?: string;
}

/** APP模板 */
export interface AppTemplate {
  uid: string;
  app_id: number;
  version_name: string;
  fields: any[];
  create_time: string;
}

/** 账户组 */
export interface UserGroup {
  uid: string;
  name: string;
  permissions: Record<string, any>;
  created_at: string;
}

/** 用户余额 */
export interface UserBalance {
  id: string;
  app_uid: string;
  app_name: string;
  balance: number;
  balance_mode: string;
  icon?: string;
  is_delegated?: boolean;
  delegated_to?: string | null;
  delegated_to_name?: string | null;
}

/** APP用户余额（管理员查看） */
export interface AppUserBalance {
  id: string;
  user_uid: string;
  app_uid: string;
  username: string;
  balance: number;
  updated_at: string;
  is_delegated?: boolean;
  delegated_to?: string | null;
  delegated_to_name?: string | null;
  group_name?: string;
}

/** 余额流水项 */
export interface BalanceTransaction {
  id: string;
  app_uid: string;
  app_name: string;
  app_icon?: string;
  type: string;
  amount: number;
  balance_after: number;
  related_uid: string;
  related_type: string;
  note: string;
  user_uid?: string;
  username?: string;
  created_at: string;
}

/** 充值申请 */
export interface BalanceRecharge {
  id: string;
  username?: string;
  app_name: string;
  app_balance_mode: string;
  amount: number;
  reason: string;
  status: 'pending' | 'approved' | 'rejected';
  reject_reason?: string;
  created_at: string;
  processed_at?: string | null;
}

/** 下属用户 */
export interface SubordinateUser {
  relation_id: string;
  uid: string;
  username: string;
  group_name: string;
  created_at: string;
  is_delegated: boolean;
  delegated_to: string | null;
  delegated_to_name: string | null;
  delegated_app_uid?: string | null;
  children?: SubordinateUser[];
}

/** 余额链接信息 */
export interface BalanceDelegation {
  uid: string;
  user_uid: string;
  parent_uid: string;
  app_uid: string;
  parent_name: string;
  created_at: string;
}

/** 余额链接（用户视角） */
export interface UserBalanceDelegation {
  uid: string;
  parent_uid: string;
  parent_name: string;
  app_uid: string;
  app_name: string;
  created_at: string;
}
