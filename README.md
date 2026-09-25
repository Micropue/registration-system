# 登记系统

一套面向多角色（普通用户 / 管理员 / 超级管理员）的**业务登记与订单管理系统**。用户通过动态表单提交登记订单并跟踪处理进度，管理员按 APP 分类处理订单、审核充值、处理工单，并可通过账户组、下属与余额委托构成层级化的运营体系。

前端为可安装的 PWA（Vue 3 + Vuetify），后端为 FastAPI + MySQL 8.0，支持 WebSocket 实时通知与聊天。

---

## 目录

- [功能特性](#功能特性)
- [技术栈](#技术栈)
- [项目结构](#项目结构)
- [快速开始（本地开发）](#快速开始本地开发)
- [环境变量与配置](#环境变量与配置)
- [生产部署](#生产部署)
  - [方式一：Docker Compose 部署后端 + Nginx 托管前端](#方式一docker-compose-部署后端--nginx-托管前端)
  - [方式二：使用仓库自带 CI/CD（GitHub Actions）](#方式二使用仓库自带-cicdgithub-actions)
  - [数据库备份与恢复](#数据库备份与恢复)
- [常用命令](#常用命令)
- [常见问题](#常见问题)
- [相关文档](#相关文档)

---

## 功能特性

| 模块 | 说明 |
| --- | --- |
| 账户与权限 | 账户组 + 权限树（模块 × 操作，含用户/订单/工单的「下属 · 其他」数据范围）；账户批量创建、强制下线 |
| APP 与模板配置 | 维护业务 APP（名称、图标、强调色、余额类型/扣除方式）；每个 APP 可配置多版本动态模板（字段类型、样式、复制按钮、强调弹窗） |
| 订单（登记） | 用户按模板提交订单，支持优先级、图片上传、余额自动扣减；管理员"全部分类/按 APP"分栏处理，支持通过、驳回、自定义退回数量、二次订单标记、字段级修改、转发到聊天室 |
| 余额体系 | 每用户 × 每 APP 独立余额（按公里数/次数）；管理员增减余额、查看流水；用户余额查看、余额流水；充值申请与审批 |
| 下属与委托 | 上级-下级层级树；余额扣除链接（消费从上级余额层层扣除） |
| 工单 | 用户提交反馈、与管理员多轮回复；管理员工单处理、状态流转 |
| 公告 | 公告编辑、发布/下架；最新公告进入应用后弹窗展示 |
| 通知中心 | 站内通知、待处理任务统计；WebSocket 实时推送 `notification_update` / `business_update` / `chat_unread` |
| 聊天 | 订单专属聊天（用户 ⇄ 管理员）+ 全局聊天室（在线状态、置顶、转发、撤回、图片） |
| 日报 | 自定义日报字段、用户填写、管理员统计与 Excel 导出 |
| 实时更新 | PWA 自动检测版本，检测到新版本强制更新后才可继续使用 |

## 技术栈

| 层 | 技术 |
| --- | --- |
| 前端 | Vue 3、Vite 8、Vuetify 4、Pinia、Vue Router 5、GSAP、xlsx、vite-plugin-pwa |
| 后端 | Python 3.10+、FastAPI、Uvicorn、mysql-connector-python（原生 SQL，无 ORM）、openpyxl |
| 数据库 | MySQL 8.0（utf8mb4） |
| 部署 | Docker Compose、Nginx、GitHub Actions（SCP 增量部署） |

## 项目结构

```
.
├── app/                    # 前端（Vue 3 + Vite，开发端口 3000）
│   ├── src/
│   │   ├── api/            # ajax 封装、token cookie、鉴权
│   │   ├── components/     # AppDataTable、RegistrationChat 等通用组件
│   │   ├── config/         # 接口地址(api-url.ts)、类型(api-type.ts)、侧边栏菜单、更新日志
│   │   ├── pages/          # 页面（用户端 + admin 管理端）
│   │   ├── plugins/        # Vuetify 主题（红色系）
│   │   ├── router/         # 路由与权限守卫
│   │   └── stores/         # Pinia store（用户信息、聊天未读）
│   ├── public/             # favicon、PWA 图标（48–512）
│   ├── scripts/            # 构建脚本（版本号、更新日志、代理端口切换）
│   └── vite.config.mts     # 代理与 PWA manifest
├── server/                 # 后端（FastAPI）
│   ├── src/
│   │   ├── main.py         # 路由、鉴权中间件、WebSocket
│   │   ├── account_service.py  # 业务逻辑与建表/迁移（单体服务类）
│   │   └── database.py     # 数据库连接（环境变量 + 兜底默认值）
│   └── Dockerfile
├── docker-compose.yml      # MySQL + FastAPI
├── .github/workflows/      # 前端 / 后端自动部署
├── README.md               # 本文档
├── API文档.md              # 接口文档
├── 启动方法.md             # 部署与运维细节
├── 登记系统项目要求.md     # 功能需求说明
└── AGENTS.md               # 二次开发约定（面向开发者/AI）
```

## 快速开始（本地开发）

### 1. 环境要求

- Docker 与 Docker Compose
- Node.js 20.19+ 或 22.12+（CI 使用 Node 22）
- Python 3.10+（仅在宿主机直接跑后端时需要）

### 2. 启动数据库与后端

```bash
docker compose up -d
```

首次启动会自动创建数据库、全部数据表与默认管理员账户。启动的两个容器：

| 容器 | 说明 | 端口 |
| --- | --- | --- |
| `huhurun-database` | MySQL 8.0 | `3308` → 容器 `3306` |
| `huhurun-api` | FastAPI（`--reload` 开发模式） | `8001` → 容器 `8000` |

> 后端源码目录 `./server/src` 已挂载进容器，修改代码后容器会自动重载；如未生效执行 `docker compose restart server`。

### 3. 启动前端

```bash
cd app
npm install      # 首次运行
npm run dev      # http://localhost:3000
```

Vite 会把 `/api`、`/media`、`/ws` 代理到后端 `http://localhost:8001`，并把 `/api` 前缀去掉（与生产 Nginx 的转发规则保持一致）。

### 4. 访问系统

| 地址 | 说明 |
| --- | --- |
| http://localhost:3000 | 前端（用户端 / 管理端） |
| http://localhost:8001/docs | FastAPI Swagger 接口文档 |
| http://localhost:8001/redoc | ReDoc 接口文档 |

默认超级管理员：**`admin` / `admin-123456`**（首次登录后请立即修改密码）。

## 环境变量与配置

后端读取环境变量（支持项目根目录 / 运行目录下的 `.env`，由 `python-dotenv` 加载）：

| 变量 | 说明 | Compose 默认值 | 代码兜底值（`database.py`） |
| --- | --- | --- | --- |
| `DB_URL` | `host:port` 形式的数据库地址 | `db:3306` | — |
| `DB_HOST` | 数据库主机（优先于 `DB_URL`） | — | `localhost` |
| `DB_PORT` | 数据库端口 | — | `3308` |
| `DB_NAME` | 数据库名 | `huhurun` | `huhurun` |
| `DB_USERNAME` | 数据库用户名 | `root` | `root` |
| `DB_PASSWORD` | 数据库密码 | `root` | `root` |
| `MEDIA_DIR` | 上传文件存储目录 | `/data/media` | `server/media` |
| `TZ` | 时区 | `Asia/Shanghai` | 系统时区 |

> `server/src/database.py` 顶部的兜底常量被标记为「禁止修改」，用于非 Docker 的本地直跑场景；容器中请以环境变量为准。

前端不需要环境变量，代理目标与端口都写在 `app/vite.config.mts`：

- 开发代理：`/api` → `http://localhost:8001`（去除 `/api` 前缀）、`/media` → `http://localhost:8001`、`/ws` → `ws://localhost:8001`
- `npm run build` 时会临时把代理端口改为 `8000`（生产后端端口）再构建，随后自动还原，不影响开发

其他限制：

- 图片上传仅支持 `PNG / JPEG / WebP / GIF / HEIC / HEIF`，单文件 **最大 1MB**
- 后端 CORS 白名单：`http://localhost:3000`、`http://localhost:3001`、`https://huhurun.micropue.com.cn`（新增域名需同步修改 `server/src/main.py` 的 `ALLOWED_ORIGINS`）

## 生产部署

整体架构：

```
浏览器 ──HTTPS──> Nginx ──┬── 静态文件：前端 dist（/www/huhurun-www/client）
                          ├── /api/**   → FastAPI 后端（重写去掉 /api 前缀）
                          ├── /media/** → FastAPI 静态资源
                          └── /ws/**    → FastAPI WebSocket（需 Upgrade 头）
FastAPI ──> MySQL 8.0（Docker 或独立实例）
```

### 方式一：Docker Compose 部署后端 + Nginx 托管前端

#### 1. 服务器准备

```bash
# 安装 Docker 与 Docker Compose（示例为 Debian/Ubuntu）
curl -fsSL https://get.docker.com | sh
```

把项目上传到服务器（`git clone` 或 `scp` 均可）：

```bash
git clone <你的仓库地址> registration-system
cd registration-system
```

#### 2. 启动数据库与后端

```bash
docker compose up -d --build
docker compose ps               # 确认 huhurun-api / huhurun-database 均为 Up
docker compose logs -f server   # 查看后端启动日志
```

如生产环境数据库密码、端口需要调整，修改 `docker-compose.yml` 中 `server` 服务的环境变量后重新 `docker compose up -d`。

> **生产运行模式**：`server/Dockerfile` 默认使用 `fastapi dev`（热重载，方便开发）。生产建议改为：

```dockerfile
CMD ["fastapi", "run", "--host", "0.0.0.0", "--port", "8000"]
```

> 也可以不改 Dockerfile，直接在 `docker-compose.yml` 的 `server` 服务中覆盖：
>
> ```yaml
> command: ["fastapi", "run", "--host", "0.0.0.0", "--port", "8000"]
> ```

#### 3. 构建前端

在本地或服务器上执行：

```bash
cd app
npm ci
npm run build      # 产物在 app/dist/
```

`npm run build` 会依次执行：生成构建版本号 → 生成更新日志 → 切换代理端口 8000 → `vue-tsc` 类型检查 → Vite 打包 → 还原代理端口与版本号。构建产物为纯静态文件，并包含 PWA Service Worker。

#### 4. 部署前端与 Nginx 配置

把 `app/dist/*` 上传到站点目录（仓库 CI 的目标目录为 `/www/huhurun-www/client`），Nginx 参考配置：

```nginx
server {
    listen 443 ssl;
    server_name huhurun.micropue.com.cn;

    ssl_certificate     /path/to/fullchain.pem;
    ssl_certificate_key /path/to/privkey.pem;

    root /www/huhurun-www/client;
    index index.html;

    # SPA 路由回退
    location / {
        try_files $uri $uri/ /index.html;
    }

    # 接口：去掉 /api 前缀后转发给后端
    location /api/ {
        rewrite ^/api/?(.*)$ /$1 break;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 300s;
        client_max_body_size 10m;
    }

    # 上传的图片等静态资源
    location /media/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }

    # WebSocket（通知 / 订单聊天 / 聊天室）
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 3600s;
    }
}
```

> PWA 的 Service Worker 与「安装到桌面」要求 **HTTPS**（`localhost` 除外），请务必配置证书。
>
> `client_max_body_size` 需大于 1MB（图片上限），示例为 10m。

#### 5. 上线检查

```bash
curl -I https://你的域名/                    # 前端 200
curl    https://你的域名/api/apps             # 返回 {"code":200,...}
docker compose logs --tail=50 server          # 无报错
```

### 方式二：使用仓库自带 CI/CD（GitHub Actions）

> **当前状态：自动部署已关闭。** push 到 `main` 不会触发任何部署，两个工作流只支持在 GitHub `Actions` 页面手动 **Run workflow**。
>
> 如需恢复「push 自动部署」，取消 `.github/workflows/build-client.yml`、`build-server.yml` 中 `push` 段的注释后提交即可。

两个工作流（手动触发时执行）的作用与目标：

| 工作流 | 文件 | 作用 | 部署目标 |
| --- | --- | --- | --- |
| Build Vue | `.github/workflows/build-client.yml` | Node 22 安装依赖、`npm run build`、SCP 上传 dist | `/www/huhurun-www/client` |
| Upload Server | `.github/workflows/build-server.yml` | SCP 上传后端源码 | `/sdb/huhurun@api/src` |

#### 1. 配置仓库 Secrets

在 GitHub 仓库 `Settings → Secrets and variables → Actions` 中添加：

| Secret | 说明 |
| --- | --- |
| `SERVER_HOST` | 服务器 IP / 域名 |
| `SERVER_USER` | SSH 用户名 |
| `SERVER_KEY` | SSH 私钥（对应服务器 `~/.ssh/authorized_keys`） |

#### 2. 服务器侧准备

- 目标目录存在且当前用户有写权限：`/www/huhurun-www/client`、`/sdb/huhurun@api/src`
- 后端进程（容器 / systemd / 面板进程管理器）已配置为从该目录启动，并在源码更新后重启
- `server/src/*` 会直接覆盖到服务器目标目录，`requirements.txt`、`Dockerfile` 等文件不在同步范围内；依赖变更需在服务器手动处理
- 数据库结构由后端启动时自动迁移（`init_db`），无需手工执行 SQL

#### 3. 部署

方式一：在 GitHub `Actions` 页面选择对应工作流，点击 **Run workflow**（`main` 分支）。
方式二：恢复 `push` 触发后直接推送：

```bash
git push origin main
```

随后在 GitHub `Actions` 页面确认两个工作流均为绿色；再重启后端进程并刷新页面验证。

> 自动部署发生后端接口路径或数据结构变更时（例如接口前缀 `/api/apps`），前后端必须**同时发布**；旧版 PWA 缓存会在检测到新版本时强制更新。
### 数据库备份与恢复

```bash
# 备份（通过数据库容器执行 mysqldump）
docker exec huhurun-database sh -c \
  'exec mysqldump -uroot -proot --default-character-set=utf8mb4 huhurun' > backup_$(date +%F).sql

# 恢复
docker exec -i huhurun-database mysql -uroot -proot huhurun < backup_2026-01-01.sql
```

数据持久化在 Docker 卷 `huhurun-server_db-data` 中；`docker compose down`（不带 `-v`）不会删除数据。

## 常用命令

```bash
# ---- 后端 ----
docker compose up -d              # 启动数据库 + 后端
docker compose restart server     # 代码更新后重启后端
docker compose logs -f server     # 查看后端日志
docker compose down               # 停止（保留数据）
docker compose down -v            # 停止并清空数据库（慎用！）
docker exec -it huhurun-api bash  # 进入后端容器

# ---- 前端（app/）----
npm install                       # 安装依赖
npm run dev                       # 开发服务器（默认 3000，端口被占用时自动 +1）
npm run type-check                # vue-tsc 类型检查
npm run build                     # 生产构建（含类型检查）
npm run preview                   # 本地预览构建产物
```

## 常见问题

| 现象 | 排查方向 |
| --- | --- |
| 前端打开后接口 502 / 404 | 后端容器未启动或 Nginx `/api/` 重写规则不正确；确认 `curl localhost:8001` 正常 |
| 数据库连接失败 | `docker compose ps` 检查 MySQL 是否健康；核对 `.env` / compose 中的 `DB_*`；注意容器内端口是 `3306`、宿主机是 `3308` |
| 图片上传 403 / 413 | 403：请求头 User-Agent 被判定为自动化工具，或来源不在 CORS 白名单；413：文件超过 1MB 或 Nginx `client_max_body_size` 过小 |
| WebSocket 连不上 | Nginx 的 `/ws/` 未透传 `Upgrade` / `Connection` 头；HTTPS 页面需使用 `wss://` |
| PWA 提示更新但一直不消失 | 点击「立即更新」后会自动刷新并注销旧 Service Worker；如仍异常，清除站点数据后重试 |
| 前端端口不是 3000 | 3000 被占用时 Vite 自动递增（如 3001），以终端输出为准 |
| 更新日志内容不符合预期 | 更新日志由 `app/scripts/gen-update-logs.mjs` 从 git 提交历史自动生成，每次构建都会重写 `src/config/update-logs.ts`，请勿手工编辑该文件 |
| 部署后样式/接口仍是旧版 | 浏览器/PWA 缓存；强制刷新或清除站点数据；确认 CI 两个工作流都成功且后端进程已重启 |

## 相关文档

| 文档 | 内容 |
| --- | --- |
| [API文档.md](API文档.md) | 全部接口、鉴权、权限、WebSocket 协议 |
| [启动方法.md](启动方法.md) | 部署与运维手册（服务管理、数据表、排障） |
| [登记系统项目要求.md](登记系统项目要求.md) | 功能需求说明 |
| [AGENTS.md](AGENTS.md) | 二次开发约定（代码结构、命名、接口规范） |

---

默认管理员：`admin` / `admin-123456`（**上线后请立即修改**）。
