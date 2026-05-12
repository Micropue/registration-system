import { ajax } from './ajax';
import { cookie } from './cookie';
import { ApiUrl } from '@/config/api-url';
import type { CheckLoginData } from '@/config/api-type';

/**
 * 登录状态验证服务
 */

/**
 * 检查当前用户的登录状态
 * @returns 返回用户信息或 null (未登录/登录失效)
 */
export async function checkLoginStatus(): Promise<CheckLoginData | null> {
  const token = cookie.get('token');
  
  // 1. 如果本地没有 token，直接判定为未登录
  if (!token) {
    return null;
  }

  try {
    // 2. 向后端发起验证请求
    // 使用 Authorization Header 传递 Token
    const res = await ajax<CheckLoginData>(ApiUrl.CHECK_LOGIN, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (res.code === 200 && res.data) {
      // 3. 验证通过，返回用户信息
      return res.data;
    } else {
      // 4. 验证失败 (如 token 过期)，清理本地无效的 cookie
      cookie.remove('token');
      return null;
    }
  } catch (error) {
    console.error('Login check failed:', error);
    // 网络错误等情况，暂时判定为未登录
    return null;
  }
}
