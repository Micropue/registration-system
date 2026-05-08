import { getErrorMessage } from '@/config/error-msg';

/**
 * Fetch 请求封装工具类
 */

// 统一的响应体结构定义 (根据 @虎虎校园跑登记系统项目要求.md)
export interface ApiResponse<T = any> {
  code: number;
  msg: string;
  data: T;
}

export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';

export interface RequestOptions {
  method?: HttpMethod;
  headers?: Record<string, string>;
  body?: any;
  /**
   * 是否作为 FormData 发送
   */
  isFormData?: boolean;
}

/**
 * 封装的 Ajax 请求函数
 * @param url 请求地址
 * @param options 请求配置
 * @returns 自动解析后的 JSON 数据
 */
export async function ajax<T = any>(
  url: string,
  options: RequestOptions = {}
): Promise<ApiResponse<T>> {
  const { 
    method = 'GET', 
    headers = {}, 
    body, 
    isFormData = false 
  } = options;

  const fetchOptions: RequestInit = {
    method,
    headers: { ...headers },
  };

  // 处理请求体
  if (body) {
    if (isFormData) {
      // 如果是 FormData，不要手动设置 Content-Type，浏览器会自动处理边界
      const formData = new FormData();
      for (const key in body) {
        formData.append(key, body[key]);
      }
      fetchOptions.body = formData;
    } else {
      // 默认作为 JSON 处理
      if (!(fetchOptions.headers as Record<string, string>)['Content-Type']) {
        (fetchOptions.headers as Record<string, string>)['Content-Type'] = 'application/json';
      }
      fetchOptions.body = JSON.stringify(body);
    }
  }

  try {
    const response = await fetch(url, fetchOptions);
    
    // 即使状态码不是 2xx，也尝试解析 JSON，因为后端规范中 code 是写在 body 里的
    const data: ApiResponse<T> = await response.json();
    
    // 自动匹配中文提示
    data.msg = getErrorMessage(data.code, data.msg);
    
    return data;
  } catch (error) {
    console.error('Fetch error:', error);
    return {
      code: 500,
      msg: getErrorMessage(500),
      data: [] as any
    };
  }
}
