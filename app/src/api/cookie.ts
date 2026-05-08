/**
 * Cookie 操作封装工具类
 */

export const cookie = {
  /**
   * 设置 Cookie
   * @param name Cookie 名称
   * @param value Cookie 值
   * @param days 有效天数 (可选)
   */
  set(name: string, value: string, days?: number): void {
    let expires = "";
    if (days) {
      const date = new Date();
      date.setTime(date.getTime() + days * 24 * 60 * 60 * 1000);
      expires = "; expires=" + date.toUTCString();
    }
    document.cookie = name + "=" + (value || "") + expires + "; path=/; SameSite=Lax";
  },

  /**
   * 获取 Cookie
   * @param name Cookie 名称
   * @returns Cookie 值，如果不存在则返回 null
   */
  get(name: string): string | null {
    const nameEQ = name + "=";
    const ca = document.cookie.split(";");
    for (let i = 0; i < ca.length; i++) {
      let c = ca[i];
      while (c.charAt(0) === " ") c = c.substring(1, c.length);
      if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
    }
    return null;
  },

  /**
   * 删除 Cookie
   * @param name Cookie 名称
   */
  remove(name: string): void {
    document.cookie = name + "=; Path=/; Expires=Thu, 01 Jan 1970 00:00:01 GMT;";
  },

  /**
   * 清除所有 Cookie
   */
  clear(): void {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i];
      const eqPos = cookie.indexOf("=");
      const name = eqPos > -1 ? cookie.substr(0, eqPos) : cookie;
      this.remove(name.trim());
    }
  }
};
