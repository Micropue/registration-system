# 虎虎校园跑登记系统 API 文档

## 全局规范

### 响应格式
所有接口均返回以下 JSON 格式：

| 名称 | 作用 | 类型 | 是否必含 |
| :--- | :--- | :--- | :--- |
| `code` | 状态码（与 HTTP 响应码一致） | Int | 是 |
| `msg` | 状态信息（英文） | String | 是 |
| `data` | 业务数据 | Object / Array | 是 |

示例：
```json
{
  "code": 200,
  "msg": "success",
  "data": { ... }
}
```

---

## 账户接口

### 1. 登录
用户通过用户名和密码登录系统。

- **URL**: `/auth/login`
- **方法**: `POST`
- **请求体类型**: `multipart/form-data` (FormData)

#### 请求参数
| 参数名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| `username` | String | 是 | 用户名 |
| `password` | String | 是 | 密码 |

### 2. 登录检测
通过 Authorization Header 检查当前登录状态并获取用户信息。

- **URL**: `/auth/check-login`
- **方法**: `GET`
- **Header**: `Authorization: Bearer <token>`

### 3. 获取所有用户信息 (管理员)
管理员获取系统中所有用户的分页列表，支持排序。

- **URL**: `/admin/users`
- **方法**: `GET`
- **Header**: `Authorization: Bearer <token>`
- **查询参数**:
  - `page` (可选, int, 默认为 1)
  - `page_size` (可选, int, 默认为 20)
  - `sort_by` (可选, string, 可选值: `register_time`, `last_login_time`, `session_count`)
  - `order` (可选, string, 可选值: `asc`, `desc`, 默认为 `desc`)

#### 响应数据 (`data`)
| 参数名 | 类型 | 说明 |
| :--- | :--- | :--- |
| `total` | Int | 用户总数 |
| `page` | Int | 当前页码 |
| `page_size` | Int | 每页条数 |
| `items` | Array | 用户详细信息列表 |

其中 `items` 数组包含对象：
| 参数名 | 类型 | 说明 |
| :--- | :--- | :--- |
| `username` | String | 用户名 |
| `session_count` | Int | 当前活跃会话数量 |
| `type` | String | 账户类型 (`admin` | `default`) |
| `register_time` | String | 注册时间 (ISO 8601) |
| `last_login_time`| String | 最后登录时间 |
| `login_ip` | String | 最后登录IP |
| `login_device` | String | 自动识别的登录设备 |

### 4. 创建账户 (管理员)
管理员在系统中创建一个新的账户。

- **URL**: `/admin/users`
- **方法**: `POST`
- **Header**: `Authorization: Bearer <token>`
- **请求体类型**: `application/json`

#### 请求参数
| 参数名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| `username` | String | 是 | 用户名 |
| `password` | String | 是 | 密码 |
| `type` | String | 是 | 账户类型 (`admin` | `default`) |

#### 响应示例
**成功 (200)**:
```json
{
  "code": 200,
  "msg": "User created successfully",
  "data": []
}
```

---

## 默认账户
系统初始化后会自动创建一个默认管理员账户：
- **用户名**: `admin`
- **密码**: `admin-123456`
