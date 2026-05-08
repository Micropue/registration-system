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

#### 响应数据 (`data`)
| 参数名 | 类型 | 说明 |
| :--- | :--- | :--- |
| `token` | String | 登录会话标识（Session UID），后续请求需携带此 token |

#### 响应示例
**成功 (200)**:
```json
{
  "code": 200,
  "msg": "Login successful",
  "data": {
    "token": "a1b2c3d4e5f6..."
  }
}
```

**失败 (401/400)**:
```json
{
  "code": 401,
  "msg": "invalid username or password",
  "data": []
}
```

### 2. 登录检测
通过 token 检查当前登录状态并获取用户信息。

- **URL**: `/auth/check-login`
- **方法**: `GET`

#### 请求参数
| 参数名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| `token` | String | 是 | 登录时返回的会话标识 |

#### 响应数据 (`data`)
| 参数名 | 类型 | 说明 |
| :--- | :--- | :--- |
| `username` | String | 用户名 |
| `type` | String | 用户类型 (`admin` 或 `default`) |
| `token` | String | 当前有效的会话标识 |

#### 响应示例
**成功 (200)**:
```json
{
  "code": 200,
  "msg": "Authorized",
  "data": {
    "username": "admin",
    "type": "admin",
    "token": "a1b2c3d4e5f6..."
  }
}
```

**失败 (401)**:
```json
{
  "code": 401,
  "msg": "Unauthorized",
  "data": []
}
```

---

## 默认账户
系统初始化后会自动创建一个默认管理员账户：
- **用户名**: `admin`
- **密码**: `admin-123456`
