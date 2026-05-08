/**
 * 错误码与中文提示映射表
 */

export const ErrorCodeMap: Record<number, string> = {
  200: '操作成功',
  400: '请求参数错误',
  401: '用户名或密码错误',
  403: '拒绝访问',
  404: '请求资源不存在',
  405: '请求方法不允许',
  422: '表单验证失败',
  500: '服务器内部错误',
  502: '网关错误',
  503: '服务不可用',
  504: '网关超时',
};

/**
 * 根据状态码获取中文提示
 * @param code 状态码
 * @param defaultMsg 默认提示信息 (如果映射表中没有对应项)
 * @returns 中文提示
 */
export function getErrorMessage(code: number, defaultMsg?: string): string {
  return ErrorCodeMap[code] || defaultMsg || '未知系统错误';
}
