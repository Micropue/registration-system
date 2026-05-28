# 虎虎校园跑登记系统 — Agent 指南

## Repo structure

```
app/          # Vue 3 + Vite 8 frontend (port 3000)
server/       # Python FastAPI backend (port 8001)
docker-compose.yml  # MySQL 8.0 + FastAPI
```

## Essential commands

```bash
# Start everything
docker compose up -d           # DB + backend
cd app && npm run dev          # Frontend dev server

# Frontend (app/)
npm run dev          # Port 3000
npm run type-check   # vue-tsc --build --force
npm run build        # type-check → build (swaps proxy port 8001↔8000)

# Backend (server/)
docker compose restart server   # After code changes
docker compose logs -f server   # Tail backend logs

# Full rebuild
docker compose down -v && docker compose up -d
```

## Architecture notes

- **Build quirk**: `npm run build` runs `scripts/update-proxy-port.mjs` which rewrites `vite.config.mts` port 8001→8000, builds, then restores it. The dev port is always 8001.
- **API proxy**: Vite rewrites `/api` → no prefix. So in code, use `/api/auth/login` which becomes `localhost:8001/auth/login`.
- **Auth**: Token stored in cookie (`token`), no HttpOnly flag. Every protected request uses `Authorization: Bearer ${cookie.get('token')}`.
- **Database**: MySQL 8.0 on port 3308 (host) / 3306 (container). Tables auto-created on backend startup. Default admin: `admin` / `admin-123456`.
- **Backend code hot-reloads** inside Docker because `./server/src` is mounted as a volume. Just `docker compose restart server` to pick up changes.
- **No tests exist**. No unit, integration, or e2e.

## Frontend conventions

- **API calls**: Always use `ajax()` from `@/api/ajax`. `isFormData: true` for file uploads or form-style POST. JSON body by default.
- **Auth header**: Manually attach `{ 'Authorization': \`Bearer ${cookie.get('token') || ''}\` }` where needed.
- **Snackbar**: Each page has its own `snackbar` reactive with `showMsg(text, color)` — do not centralize.
- **AppDataTable**: Shared table component supporting client/server pagination, search, filter, and optional drag sort (`enableDragSort`). Pass headers with `searchable`/`filterable` booleans.
- **No `alert()`** — use snackbar only.
- **Admin pages**: `.table-wrapper { width: 90%; }` is the standard container pattern.
- **Router guards**: `requireDefault` (any login), `requireAdmin` (has admin permission), `requireGuest` (no login).
- **Page title**: Set via route `meta.title`, formatted as `"{title} - 哆啦A梦（校园跑版）"` in `router.afterEach`.

## Backend conventions

- **AccountService** is a monolithic ~1526-line class with ~55 methods — do not duplicate its logic.
- **API response format**: `{"code": 200, "msg": "Success", "data": ...}`.
- **Auth middleware**: `require_perm(authorization, "模块", "操作")` returns `(session, error)`. Check `if err: return err`.
- **DB migrations**: Done via `try/except ALTER TABLE ADD COLUMN` in `_init_settings_tables()`. Never manual SQL.
- **WS chat**: URL is `/ws/chat/{registration_uid}?token=xxx`. Token sent as query param.

## Key API endpoints

| Method | Path | Auth |
|--------|------|------|
| POST | `/auth/login` | No |
| GET | `/auth/check-login` | Bearer |
| GET | `/admin/dashboard/stats` | Bearer + admin perm |
| GET | `/admin/registrations` | Bearer + 订单处理.查看 |
| POST | `/admin/registrations/{uid}/status` | Bearer + 订单处理.处理 |
| POST | `/admin/settings/running-apps/sort` | Bearer + APP配置.修改 |
| WS | `/ws/chat/{registration_uid}` | Token query param |

## Permission group names (for require_perm)

`账户管理`, `账户组管理`, `订单处理`, `工单处理`, `APP配置`, `充值审批`, `新建登记`, `新建工单`, `充值申请`, `余额查看`
