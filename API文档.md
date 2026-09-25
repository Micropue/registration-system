# 登记系统 API 文档

本文档覆盖后端全部接口。所有路径均为**后端路径**（不带 `/api` 前缀）；前端通过 Vite（开发）或 Nginx（生产）把 `/api` 转发到后端并去掉前缀，因此前端代码中的实际调用路径为 `/api` + 本文路径。

- 开发环境 Base URL：`http://localhost:8001`
- 生产环境 Base URL：`https://<你的域名>/api`
- 在线文档（Swagger / ReDoc）：`/docs`、`/redoc`

---

## 目录

- [1. 全局规范](#1-全局规范)
- [2. 权限模型](#2-权限模型)
- [3. 认证](#3-认证)
- [4. 账户管理](#4-账户管理)
- [5. 账户组与权限](#5-账户组与权限)
- [6. APP 与模板配置](#6-app-与模板配置)
- [7. 登记订单（用户端）](#7-登记订单用户端)
- [8. 订单处理（管理端）](#8-订单处理管理端)
- [9. 余额、流水与充值](#9-余额流水与充值)
- [10. 下属与余额委托](#10-下属与余额委托)
- [11. 工单](#11-工单)
- [12. 公告](#12-公告)
- [13. 通知与待处理任务](#13-通知与待处理任务)
- [14. 日报](#14-日报)
- [15. 聊天](#15-聊天)
- [16. 文件上传](#16-文件上传)
- [17. 兼容接口（旧版表单字段）](#17-兼容接口旧版表单字段)
- [附录 A. 枚举与状态](#附录-a-枚举与状态)
- [附录 B. WebSocket 消息协议](#附录-b-websocket-消息协议)

---

## 1. 全局规范

### 1.1 响应格式

所有 HTTP 接口返回统一 JSON：

```json
{
  "code": 200,
  "msg": "Success",
  "data": {}
}
```

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `code` | Int | 状态码，与 HTTP 响应码一致（200 / 400 / 401 / 403 / 404 / 500） |
| `msg` | String | 提示信息，英文为主，部分业务错误为中文 |
| `data` | Object \| Array \| null | 业务数据；无数据时为 `[]` 或 `null` |

> 注意：`api_response()` 会把 `None` 的 `data` 转为 `[]`；需要返回 `null` 的接口使用 `JSONResponse` 直接输出。

### 1.2 鉴权

除标注「公开」的接口外，均需在请求头携带登录 token：

```http
Authorization: Bearer <token>
```

token 在登录接口获取；前端保存在 cookie 中（7 天）。服务端会话不设过期时间，强制下线或移除会话即失效。失效返回：

```json
{ "code": 401, "msg": "登录状态已失效，请重新登录", "data": [] }
```

### 1.3 分页

分页接口统一使用查询参数：

| 参数 | 类型 | 默认 | 说明 |
| --- | --- | --- | --- |
| `page` | Int | 1 | 页码 |
| `page_size` | Int | 20 | 每页条数 |

分页响应结构：

```json
{
  "code": 200,
  "msg": "Success",
  "data": { "total": 100, "page": 1, "page_size": 20, "items": [] }
}
```

部分列表接口（如账户组、充值记录）直接返回数组，不分页。

### 1.4 请求体格式

| 场景 | 格式 |
| --- | --- |
| 登录 | `multipart/form-data`（FormData） |
| 普通 JSON 接口 | `application/json` |
| 驳回 / 回复 / 状态变更 | `multipart/form-data`（Form 字段） |
| 图片上传 | `multipart/form-data`，字段名 `file` |

---

## 2. 权限模型

权限为「模块 → 操作」两级树，挂在账户组上，用户通过 `group_uid` 归属账户组。超级管理员组始终拥有全部权限。

| 模块 | 操作（子权限） |
| --- | --- |
| `账户管理` | 查看（下属用户 / 其他用户）、创建、修改、删除、强制下线 |
| `账户组管理` | 查看、创建、修改、删除 |
| `订单处理` | 查看（下属订单 / 其他订单）、处理、驳回、删除、修改 |
| `工单处理` | 查看（下属工单 / 其他工单）、回复、解决、删除 |
| `APP配置` | 查看、修改、余额管理 |
| `充值审批` | 查看、处理 |
| `下属管理` | 查看、配置 |
| `公告管理` | 查看、编辑、发布、删除 |
| `日报管理` | 查看、字段配置、填写报告、无需填写 |
| 独立开关 | `新建登记`、`新建工单`、`充值申请`、`余额查看`、`聊天`、`聊天室`、`调整侧边栏位置` |

后端通过 `require_perm(authorization, "模块", "操作")` 校验并返回 `(session, error)`；数据范围（下属 / 其他）在查询时按权限动态过滤。

---

## 3. 认证

### 3.1 登录

- **URL**：`/auth/login`
- **方法**：`POST`
- **鉴权**：公开
- **请求体**：`multipart/form-data`

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `username` | String | 是 | 用户名 |
| `password` | String | 是 | 密码（SHA-256 存储） |

**响应**：

```json
{ "code": 200, "msg": "Login successful", "data": { "token": "3f2a9c..." } }
```

失败：`code=401`，`msg` 为「用户名或密码错误」。

### 3.2 登录状态检测

- **URL**：`/auth/check-login`
- **方法**：`GET`
- **鉴权**：`Authorization: Bearer <token>`

**响应 data**：

| 字段 | 说明 |
| --- | --- |
| `username` | 用户名 |
| `role` | `super_admin` / `admin` / `default` |
| `group_name` | 账户组名称 |
| `token` | 当前 token |
| `permissions` | 权限树对象 |

---

## 4. 账户管理

> 模块权限：`账户管理`

| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| GET | `/admin/users` | 查看 | 用户分页列表 |
| POST | `/admin/users` | 创建 | 创建账户 |
| PATCH | `/admin/users/{uid}` | 修改 | 修改用户名 / 密码 |
| DELETE | `/admin/users/{uid}` | 删除 | 删除账户 |
| POST | `/admin/users/{uid}/force-logout` | 强制下线 | 清空该用户所有登录会话 |
| POST | `/admin/users/{uid}/group` | 修改 | 分配账户组 |
| DELETE | `/admin/users/{uid}/group` | 修改 | 移出账户组 |
| GET | `/admin/users/{user_uid}/balances` | `APP配置.余额管理` | 查看指定用户的各 APP 余额 |

### 4.1 用户列表

- **URL**：`/admin/users`
- **方法**：`GET`
- **查询参数**：`page`、`page_size`、`sort_by`（`register_time` / `last_login_time` / `session_count`）、`order`（`asc` / `desc`）

**items 字段**：`uid`、`username`、`session_count`、`type`（`admin` / `default` / `super_admin`）、`group_name`、`register_time`、`last_login_time`、`login_ip`、`login_device`。

### 4.2 创建账户

- **URL**：`/admin/users`
- **方法**：`POST`
- **请求体**（JSON）：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `username` | String | 是 | 1–20 位，可重复 |
| `password` | String | 是 | 6–16 位，仅字母/数字/短横线 |
| `group_uid` | String | 否 | 账户组 UID，缺省为超级管理员组 |
| `type` | String | 否 | 兼容字段 |

### 4.3 修改账户

- **URL**：`/admin/users/{uid}`
- **方法**：`PATCH`
- **请求体**（JSON）：`username`、`password`（均可选，传哪个改哪个）

---

## 5. 账户组与权限

> 模块权限：`账户组管理`

| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| GET | `/admin/groups` | 查看 | 账户组列表（含权限树） |
| GET | `/admin/groups/{group_uid}` | 查看 | 账户组详情 |
| POST | `/admin/groups` | 创建 | 新建账户组 |
| PATCH | `/admin/groups/{group_uid}` | 修改 | 修改名称 / 权限 |
| DELETE | `/admin/groups/{group_uid}` | 删除 | 删除账户组 |
| GET | `/admin/available-groups` | `账户管理.创建` 或 `修改` | 可供当前用户选择分配的账户组 |

**请求体**（创建 / 修改，JSON）：

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `name` | String | 账户组名称 |
| `permissions` | Object | 权限树对象，结构见[第 2 节](#2-权限模型) |

---

## 6. APP 与模板配置

> 模块权限：`APP配置`

| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| GET | `/apps` | 公开 | 公开 APP 列表（用户端选择用） |
| GET | `/admin/settings/apps` | 查看 | APP 列表（含模板数、余额类型） |
| POST | `/admin/settings/apps` | 修改 | 新增 APP |
| PUT | `/admin/settings/apps/{app_id}` | 修改 | 修改 APP |
| DELETE | `/admin/settings/apps/{app_id}` | 修改 | 删除 APP |
| POST | `/admin/settings/apps/bulk` | 修改 | Excel 批量导入 |
| POST | `/admin/settings/apps/sort` | 修改 | 拖拽排序 |
| GET | `/admin/settings/apps/{app_uid}/templates` | 查看 | 模板列表 |
| POST | `/admin/settings/apps/{app_uid}/templates` | 管理员账户 | 新建模板 |
| PUT | `/admin/settings/apps/{app_uid}/templates/{uid}` | 管理员账户 | 修改模板 |
| DELETE | `/admin/settings/apps/{app_uid}/templates/{uid}` | 管理员账户 | 删除模板 |
| POST | `/admin/settings/apps/{app_uid}/templates/clone` | 管理员账户 | 复刻模板 |
| GET | `/apps/{app_uid}/templates` | 公开 | 公开模板列表（用户端填写用） |
| PATCH | `/admin/apps/{app_uid}/balance` | 余额管理 | 设置 APP 余额类型 |
| GET | `/admin/apps/{app_uid}/users-balance` | 余额管理 | 指定 APP 的用户余额分页 |
| PATCH | `/admin/apps/{app_uid}/users/{user_uid}/balance` | 余额管理 | 增减用户余额 |

### 6.1 APP 字段

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `name` | String | APP 名称（业务唯一标识，登记数据中按名称关联） |
| `note` | String | 备注 |
| `accent_color` | String | 强调色 `#RRGGBB`，默认 `#D32F2F` |
| `icon` | String | 图标 URL（`/media/...`） |
| `balance_mode` | String | 余额类型：`mileage`（公里数）/ `count`（次数）/ 空 |
| `balance_round` | String | 扣除方式：`四舍五入` / `五舍六入` / 空 |
| `template_count` | Int | 模板数量（响应字段） |

**批量导入**请求体为数组，元素：`{ "name": "示例应用", "note": "", "accent_color": "#D32F2F" }`。

**排序**请求体：`{ "ordered_ids": [3, 1, 2] }`。

### 6.2 模板字段

模板对象：`{ uid, app_id, version_name, fields: [], emphasis_config, create_time }`。

`fields[]` 元素：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `label` | String | 字段名（登记数据 JSON 的 key） |
| `type` | String | `text` / `textarea` / `number` / `date` / `select` / `radio` / `checkbox` / `image` / `number-range` / `date-range` / `time-range` |
| `required` | Boolean | 是否必填 |
| `default` | Any | 默认值 |
| `options` | Array | 选项（select / radio / checkbox） |
| `multiple` | Boolean | 图片字段是否多图 |
| `copyable` | Boolean | 详情中是否显示复制按钮 |
| `bold` / `color` / `size` | — | 详情展示样式 |
| `validation` | String | 校验规则（可选） |

`emphasis_config`：强调弹窗配置 `{ conditions: [{ field, values }], content: [{ label, bold, color, size, copyable }] }`。

**复刻模板**请求体：`{ "source_uid": "<模板UID>", "version_name": "v2" }`。

### 6.3 余额管理

- 设置 APP 余额类型：`PATCH /admin/apps/{app_uid}/balance`，请求体 `{ "balance_mode": "mileage" | "count" | "" }`
- 增减用户余额：`PATCH /admin/apps/{app_uid}/users/{user_uid}/balance`，请求体 `{ "amount": 10.5, "note": "手动充值" }`（负数为扣减；若该用户已建立余额委托，实际作用于上级余额）

---

## 7. 登记订单（用户端）

> 权限：`新建登记`（未登录返回 401）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/registrations` | 我的订单分页 |
| POST | `/registrations` | 提交订单 |
| GET | `/registrations/{uid}` | 订单详情 |
| PUT | `/registrations/{uid}` | 重新提交 / 修改被驳回或被处理的订单 |
| GET | `/registrations/check` | 是否已提交过订单 |
| GET | `/registrations/latest` | 最近一条订单 |

### 7.1 提交订单

- **URL**：`/registrations`
- **方法**：`POST`
- **请求体**（JSON）：模板字段平铺 + 以下保留字段

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `应用` | String | 是 | APP 名称（与 APP 配置的 `name` 一致） |
| `priority` | String | 否 | `low` / `medium` / `high`，默认 `low` |
| `template_uid` | String | 否 | 使用的模板 UID |
| `amount` | Number | 否 | 数量（启用余额的 APP 必填），提交时自动校验并扣减余额 |
| 其他字段 | Any | — | 模板 `fields[].label` 对应的值；图片字段传上传后的 URL 或 URL 数组 |

**响应**：`{ "code": 200, "msg": "Registration submitted successfully" }`；余额不足返回 `400`：`'<应用>' 余额不足，无法创建登记`。

### 7.2 重新提交订单

- **URL**：`/registrations/{uid}`
- **方法**：`PUT`
- **请求体**：同提交订单。重新提交会将订单重置为 `pending` 并标记为二次订单，余额执行「先退回原扣除、再按新数量扣除」。

### 7.3 列表与详情响应

`GET /registrations` 的 `items[]`：

| 字段 | 说明 |
| --- | --- |
| `id` | 订单 UID |
| `data` | 订单 JSON 数据（含 `应用` 及模板字段） |
| `status` | `pending` / `approved` / `rejected` |
| `reject_reason` | 驳回原因 |
| `priority` | 优先级 |
| `template_uid` / `template_name` | 模板 UID / 版本名 |
| `amount` | 数量 |
| `created_at` | 创建时间（ISO 8601） |

---

## 8. 订单处理（管理端）

> 模块权限：`订单处理`

| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| GET | `/admin/registrations` | 查看 | 订单分页（按权限过滤数据范围） |
| GET | `/admin/registrations/stats` | 查看 | 按 APP 统计各状态数量（侧边栏角标） |
| POST | `/admin/registrations/{uid}/status` | 处理 / 驳回 | 更新订单状态 |
| PUT | `/admin/registrations/{uid}/data` | 修改 | 修改订单数据 / 数量 / 优先级 |
| DELETE | `/admin/registrations/{uid}` | 删除 | 删除订单（已通过的订单会退回余额） |
| GET | `/admin/dashboard/stats` | 查看 | 仪表盘统计 |

### 8.1 订单分页

- **URL**：`/admin/registrations`
- **方法**：`GET`
- **查询参数**：`page`、`page_size`、`sort_by`（`priority` 等）、`order`、`app_name`（按 APP 名称过滤）、`username`（按用户名过滤）、`secondary`（`1` 只看二次订单，`0` 只看一次订单）
- **items 字段**：`id`、`username`、`registration_info`、`status`、`reject_reason`、`priority`、`template_uid`、`template_name`、`amount`、`process_count`、`is_secondary`、`created_at`

### 8.2 更新状态

- **URL**：`/admin/registrations/{uid}/status`
- **方法**：`POST`
- **请求体**（Form）：

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `status` | String | `pending`（未处理）/ `approved`（已处理）/ `rejected`（驳回） |
| `reject_reason` | String | 驳回原因 |
| `refund_amount` | Number | 自定义退回数量（驳回时，缺省退回全部） |

> 状态从「未处理」变为「已处理 / 驳回」时 `process_count` 自增，订单进入二次订单池；驳回且订单有数量时按 APP 余额类型退回。

### 8.3 修改订单数据

- **URL**：`/admin/registrations/{uid}/data`
- **方法**：`PUT`
- **请求体**（JSON）：`{ "data": { "应用": "...", "...": "..." }, "amount": 5, "priority": "low" }`
- 修改后订单重置为 `pending`，并对余额执行「先退旧、再扣新」。

### 8.4 仪表盘统计

`GET /admin/dashboard/stats` 返回：`total_users`、`total_registrations`、`pending_registrations`、`total_feedbacks`、`pending_feedbacks`、`today_registrations`、`today_feedbacks`、`today_chats`、`total_apps`。

---

## 9. 余额、流水与充值

| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| GET | `/user/balances` | `余额查看` | 我的各 APP 余额 |
| GET | `/user/balance-transactions` | `余额查看` | 我的余额流水分页 |
| GET | `/admin/balance-transactions` | `APP配置.查看` | 全部余额流水分页 |
| POST | `/balance-recharges` | `充值申请` | 提交充值申请 |
| GET | `/balance-recharges` | `充值申请` | 我的充值申请 |
| GET | `/admin/balance-recharges` | `充值审批.查看` | 全部充值申请 |
| POST | `/admin/balance-recharges/{uid}/process` | `充值审批.处理` | 审批充值申请 |

### 9.1 我的余额

`GET /user/balances` 返回数组，元素：

| 字段 | 说明 |
| --- | --- |
| `app_uid` / `app_name` | APP UID / 名称 |
| `balance` | 余额 |
| `balance_mode` | `mileage` / `count` |
| `is_delegated` | 是否已委托给上级扣除 |
| `delegated_to` / `delegated_to_name` | 上级 UID / 用户名 |

### 9.2 流水

`GET /user/balance-transactions` 查询参数：`app_uid`、`page`、`page_size`。
`GET /admin/balance-transactions` 查询参数：`app_uid`、`user_uid`、`page`、`page_size`。

items 字段：`id`、`app_uid`、`app_name`、`app_icon`、`type`、`amount`、`balance_after`、`related_uid`、`related_type`、`note`、`username`、`created_at`。

### 9.3 充值申请与审批

**提交**（JSON）：`{ "app_uid": "...", "amount": 100, "reason": "当月额度" }`（若已委托上级，返回 400）。

**审批**（JSON）：`{ "status": "approved" | "rejected", "reject_reason": "" }`；通过后余额入账并向申请人发送通知。

---

## 10. 下属与余额委托

> 模块权限：`下属管理`

| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| GET | `/admin/users/{uid}/subordinates` | 查看 | 直属下属列表 |
| POST | `/admin/users/{uid}/subordinates` | 配置 | 添加下属 |
| DELETE | `/admin/users/{uid}/subordinates/{sub_uid}` | 配置 | 移除下属 |
| GET | `/admin/users/{uid}/subordinate-tree` | 查看 | 下属树（含余额链接状态） |
| POST | `/admin/subordinates/{uid}/balance-link` | 配置 | 建立余额扣除链接 |
| DELETE | `/admin/subordinates/{uid}/balance-link/{app_uid}` | 配置 | 解除余额扣除链接 |
| GET | `/admin/users/{uid}/balance-delegations` | 查看 | 用户的余额链接列表 |

- 添加下属请求体：`{ "subordinate_uid": "<用户UID>" }`
- 建立链接请求体：`{ "parent_uid": "<上级UID>", "app_uid": "<APP UID>" }`；建立后该用户的消费从上级余额扣除，且其充值/余额查看功能被禁用。

---

## 11. 工单

| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| POST | `/feedbacks` | `新建工单` | 提交工单 |
| GET | `/feedbacks` | `新建工单` | 我的工单分页 |
| GET | `/feedbacks/{uid}` | `新建工单` | 工单详情（含回复） |
| POST | `/feedbacks/{uid}/reply` | `新建工单` | 回复工单 |
| GET | `/admin/feedbacks` | `工单处理.查看` | 工单分页（`username` 可选过滤） |
| POST | `/admin/feedbacks/{uid}/status` | `工单处理.解决` | 更新状态 |
| DELETE | `/admin/feedbacks/{uid}` | `工单处理.删除` | 删除工单 |

- 提交（Form）：`title`、`content`（0–100 字）
- 回复（Form）：`content`
- 状态（Form）：`status` = `pending` / `resolved` / `rejected`

---

## 12. 公告

| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| GET | `/announcements/latest` | 公开 | 最新已发布公告（进入应用弹窗） |
| GET | `/announcements` | 登录即可 | 公告列表（仅已发布；有「公告管理.查看」权限时包含未发布） |
| GET | `/admin/announcements` | `公告管理.查看` | 全部公告（含未发布） |
| POST | `/admin/announcements` | `公告管理.编辑` | 新建公告 |
| PUT | `/admin/announcements/{uid}` | `公告管理.编辑` | 修改公告 |
| POST | `/admin/announcements/{uid}/publish` | `公告管理.发布` | 发布 |
| POST | `/admin/announcements/{uid}/unpublish` | `公告管理.发布` | 下架 |
| DELETE | `/admin/announcements/{uid}` | `公告管理.删除` | 删除 |

创建 / 修改请求体：`{ "title": "...", "content": "..." }`。

---

## 13. 通知与待处理任务

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/pending-items` | 管理员待处理任务分页（含 `counts`） |
| GET | `/pending-items/count` | 待处理任务总数 |
| GET | `/notifications` | 我的通知分页 |
| GET | `/notifications/unread-count` | 未读数 |
| POST | `/notifications/{uid}/read` | 单条已读 |
| POST | `/notifications/read-all` | 全部已读 |
| POST | `/notifications/read-by-reference/{reference_id}` | 按关联 ID 已读（如订单 UID） |
| POST | `/notifications/read-by-types` | 按类型批量已读，请求体 `{ "types": ["chat_message"] }` |

通知类型（`type`）常见值：`chat_message`、`global_chat_message`、`recharge_approved`、`recharge_rejected`、`registration_*`、`feedback_*` 等。

---

## 14. 日报

| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| GET | `/daily-report/fields` | `日报管理.填写报告` | 日报字段配置 |
| GET | `/daily-report/status` | 登录即可 | 今日是否已填写 / 是否需要填写（无填写权限时返回 `need_fill=false`） |
| POST | `/daily-report/submit` | `日报管理.填写报告` | 提交今日日报 |
| GET | `/admin/daily-report-fields` | `日报管理.字段配置` | 读取字段配置 |
| POST | `/admin/daily-report-fields` | `日报管理.字段配置` | 保存字段配置（数组） |
| GET | `/admin/daily-reports` | `日报管理.查看` | 日报分页（`date_from` / `date_to`） |
| GET | `/admin/daily-reports/statistics` | `日报管理.查看` | 统计（`report_date` 可选） |
| GET | `/admin/daily-reports/export` | `日报管理.查看` | 导出 Excel（`date_from` / `date_to`） |

日报字段配置元素与模板字段类似：`label`、`type`、`required`、`default`、`options` 等。
提交日报请求体：`{ "<字段名>": "<值>", ... }`。

---

## 15. 聊天

### 15.1 订单聊天

| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| GET | `/chat/{registration_uid}` | `聊天` | 历史消息（管理员或订单所属用户） |
| POST | `/chat/{registration_uid}/recall/{message_uid}` | `聊天` | 撤回消息（仅本人） |
| WS | `/ws/chat/{registration_uid}?token=<token>` | `聊天` | 实时聊天 |

### 15.2 全局聊天室

| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| WS | `/ws/global-chat?token=<token>` | `聊天室` | 实时聊天室（在线状态、置顶、撤回、图片） |
| GET | `/global-chats` | `聊天室` | 历史消息（`limit` ≤ 200，`before_id` 翻页） |
| GET | `/global-chats/online` | `聊天室` | 在线用户 |
| GET | `/global-chats/pinned` | `聊天室` | 当前置顶消息 |
| POST | `/global-chats/recall/{message_uid}` | `聊天室` | 撤回消息 |
| POST | `/global-chats/pin/{message_uid}` | `聊天室` | 置顶消息 |
| POST | `/global-chats/unpin` | `聊天室` | 取消置顶 |
| POST | `/global-chats/forward` | `订单处理.查看` + `聊天室` | 把订单转发到聊天室 |

转发请求体（JSON）：

```json
{
  "registration_uid": "<订单UID>",
  "title": "订单 #A1B2C3D4",
  "username": "客户名",
  "created_at": "2026-01-01T12:00:00",
  "status": "pending",
  "amount": 5,
  "summary": "应用名称 · 字段值1 · 字段值2",
  "is_secondary": false
}
```

消息协议见[附录 B](#附录-b-websocket-消息协议)。

---

## 16. 文件上传

- **URL**：`/upload/image`
- **方法**：`POST`
- **鉴权**：无需登录 token；校验 `Origin` / `Referer`（必须来自允许的站点）与 `User-Agent`
- **请求体**：`multipart/form-data`，字段名 `file`
- **限制**：
  - 允许类型：`PNG / JPEG / WebP / GIF / HEIC / HEIF`（同时校验 MIME、扩展名与文件头）
  - 大小：≤ 1MB
  - 拒绝 curl / wget / python-requests 等自动化 User-Agent
- **响应**：`{ "code": 200, "msg": "Upload success", "data": { "url": "/media/xxxx.png" } }`

上传后的文件由后端 `/media/**` 静态目录提供访问。

---

## 17. 兼容接口（旧版表单字段）

早期版本的全局登记表单字段配置，当前前端 UI 已改用「APP 模板」，以下接口仅为兼容保留：

| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| GET | `/fields` | 公开 | 旧版全局字段配置 |
| GET | `/admin/settings/fields` | `APP配置.查看` | 读取全局字段 |
| POST | `/admin/settings/fields` | `APP配置.修改` | 覆盖保存全局字段（数组） |

---

## 附录 A. 枚举与状态

| 枚举 | 取值 |
| --- | --- |
| 订单状态 | `pending` 未处理 / `approved` 已处理 / `rejected` 已驳回 |
| 工单状态 | `pending` 待处理 / `resolved` 已解决 / `rejected` 已驳回 |
| 充值状态 | `pending` 待审核 / `approved` 已通过 / `rejected` 已驳回 |
| 优先级 | `low` 低 / `medium` 中 / `high` 高 |
| 余额类型 | `mileage` 公里数 / `count` 次数 |
| 余额扣除方式 | `四舍五入` / `五舍六入` / 空 |
| 用户类型 | `super_admin` / `admin` / `default` |

## 附录 B. WebSocket 消息协议

### B.1 `/ws/notifications?token=<token>`

服务端推送（客户端无需发送业务消息）：

| `type` | 说明 | 附加字段 |
| --- | --- | --- |
| `notification_update` | 有新通知 | — |
| `business_update` | 业务数据变化（用于刷新侧边栏角标/待处理） | `key`（如 `订单处理`）、`delta` |
| `chat_unread` | 某订单有未读聊天消息 | `uid`（订单 UID） |

### B.2 `/ws/chat/{registration_uid}?token=<token>`

客户端发送：

```json
{ "type": "text", "message": "你好" }
{ "type": "image", "message": "/media/xxx.png" }
{ "type": "recall_message", "message_uid": "<消息UID>" }
```

服务端广播（在客户端消息基础上补充 `username` / `is_admin` / `id` / `created_at`）：

```json
{ "type": "text", "message": "你好", "username": "admin", "is_admin": true, "id": "...", "created_at": "..." }
{ "type": "recall_message", "message_uid": "...", "username": "admin" }
{ "type": "error", "message": "撤回失败原因" }
```

> 无权限时服务端以关闭码断开：`4001` 未登录，`4003` 无权限（`聊天` 或订单归属不符）。

### B.3 `/ws/global-chat?token=<token>`

客户端发送：

```json
{ "msg_type": "text", "message": "大家好" }
{ "msg_type": "image", "message": "/media/xxx.png" }
{ "msg_type": "recall_message", "message_uid": "<消息UID>" }
{ "msg_type": "pin_message", "message_uid": "<消息UID>" }
```

服务端广播：

| `type` | 说明 |
| --- | --- |
| `text` / `image` | 新消息（含发送者、时间、`is_admin`） |
| `recall_message` | 消息被撤回 |
| `pin_update` | 置顶变化（`pinned`、`by`） |
| `presence` | 在线用户列表更新 |
| `error` | 操作失败原因 |

> 关闭码同上：`4001` 未登录、`4003` 无 `聊天室` 权限。
