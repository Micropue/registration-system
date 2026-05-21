import uvicorn
import uuid
import os
import mimetypes
from pathlib import Path
from fastapi import FastAPI, Form, Request, Header, HTTPException, WebSocket, WebSocketDisconnect, Query, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import Any, Optional
from contextlib import asynccontextmanager

# 尝试导入业务逻辑类
try:
    from .account_service import AccountService, AccountError, AccountAuthError
except (ImportError, ModuleNotFoundError):
    from account_service import AccountService, AccountError, AccountAuthError


# 1. 使用 lifespan 管理数据库初始化（替代过时的 on_event）
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        account_service.init_db()
        print("Database initialized.")
    except Exception as e:
        print(f"Error initializing database: {e}")
    yield
    # 这里可以放关闭数据库连接的逻辑


from pydantic import BaseModel
from typing import Any, Optional, cast

app = FastAPI(lifespan=lifespan)
account_service = AccountService()

MEDIA_DIR = Path(os.environ.get("MEDIA_DIR", str(Path(__file__).resolve().parent.parent / "media")))
os.makedirs(MEDIA_DIR, exist_ok=True)

ALLOWED_ORIGINS = {"http://localhost:3000", "https://huhurun.micropue.com.cn"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(ALLOWED_ORIGINS),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/media", StaticFiles(directory=str(MEDIA_DIR)), name="media")
ALLOWED_MIME_TYPES = {
    "image/webp", "image/jpeg", "image/png", "image/gif",
    "image/heic", "image/heif"
}
MAX_IMAGE_SIZE = 5 * 1024 * 1024

MIME_TO_EXT = {
    "image/webp": ".webp",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/heic": ".heic",
    "image/heif": ".heif",
}

class CreateUserRequest(BaseModel):
    username: str
    password: str
    group_uid: Optional[str] = None

class UpdateUserRequest(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None

class RunningAppRequest(BaseModel):
    name: str
    note: str = ''
    accent_color: str = '#1976D2'
    icon: str = ''

@app.post("/upload/image")
async def upload_image(
    file: UploadFile = File(...),
    request: Request = None,
    user_agent: Optional[str] = Header(None),
    origin: Optional[str] = Header(None)
):
    if origin and origin not in ALLOWED_ORIGINS:
        return api_response(403, "Origin not allowed")
    referer = request.headers.get("referer", "") if request else ""
    if origin is None and not referer:
        return api_response(403, "Direct access not allowed")

    ua = (user_agent or "").lower()
    if any(kw in ua for kw in ("curl", "libcurl", "wget", "python-requests", "python-urllib", "go-http-client", "okhttp/", "axios/")):
        return api_response(403, "Automated requests not allowed")

    if not file.filename:
        return api_response(400, "No file selected")

    content_type = file.content_type or ""
    if content_type not in ALLOWED_MIME_TYPES:
        ext = Path(file.filename).suffix.lower()
        guessed = mimetypes.guess_type(file.filename)[0]
        if guessed not in ALLOWED_MIME_TYPES and ext not in (".webp", ".jpg", ".jpeg", ".png", ".gif", ".heic", ".heif"):
            return api_response(400, f"Unsupported image type: {content_type}")

    contents = await file.read()
    if len(contents) > MAX_IMAGE_SIZE:
        return api_response(400, "Image size exceeds 5MB limit")

    magic = contents[:12]
    if magic[:4] == b'\x89PNG':
        ext = '.png'
    elif magic[:2] == b'\xff\xd8':
        ext = '.jpg'
    elif magic[:4] == b'GIF8':
        ext = '.gif'
    elif magic[:4] == b'RIFF' and magic[8:12] == b'WEBP':
        ext = '.webp'
    elif magic[4:8] == b'ftyp' and (b'heic' in magic[8:12].lower() or b'heif' in magic[8:12].lower() or b'mif1' in magic[8:12].lower()):
        ext = '.heic'
    else:
        ext = Path(file.filename).suffix.lower()
        if ext not in ('.webp', '.jpg', '.jpeg', '.png', '.gif', '.heic', '.heif'):
            return api_response(400, "Cannot determine image type")

    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = MEDIA_DIR / filename
    with open(filepath, "wb") as f:
        f.write(contents)

    return api_response(200, "Upload success", {"url": f"/media/{filename}"})

@app.post("/admin/users")
async def create_user(
    request: CreateUserRequest,
    authorization: Optional[str] = Header(None)
):
    session, err = require_perm(authorization, "账户管理", "创建")
    if err: return err
        
    try:
        account_service.create_account(
            username=request.username,
            password=request.password,
            group_uid=request.group_uid
        )
        return api_response(200, "User created successfully")
    except AccountError as e:
        return api_response(400, str(e))
    except Exception as e:
        return api_response(500, f"Internal server error: {str(e)}")



# 2. 统一响应格式工具
def api_response(code: int, msg: str, data: Any = None):
    return JSONResponse(
        status_code=code, content={"code": code, "msg": msg, "data": data or []}
    )


# 3. 提取 Token 的工具函数
def get_token(authorization: str) -> str:
    if authorization.startswith("Bearer "):
        return authorization.split(" ")[1]
    return authorization

def require_perm(authorization: Optional[str], *path: str):
    if not authorization:
        return None, api_response(401, "Missing Authorization Header")
    token = get_token(authorization)
    session = account_service.get_login_session(token)
    if not session:
        return None, api_response(401, "Unauthorized")
    if not account_service._check_permission(session.user_uid, *path):
        return None, api_response(403, "您没有此操作权限")
    return session, None


@app.get("/admin/users")
async def get_users(
    authorization: Optional[str] = Header(None), 
    page: int = 1, 
    page_size: int = 20, 
    sort_by: Optional[str] = None, 
    order: str = "desc"
):
    session, err = require_perm(authorization, "账户管理", "查看")
    if err: return err

    users_data = account_service.get_all_users(page=page, page_size=page_size, sort_by=sort_by, order=order)
    # 计算总页数
    import math
    total_pages = math.ceil(users_data["total"] / page_size) if users_data["total"] > 0 else 1
    users_data["total_pages"] = total_pages
    return api_response(200, "Success", users_data)

@app.post("/auth/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    try:
        login_ip = request.client.host if request.client else "unknown"
        login_device = request.headers.get("user-agent", "unknown")

        session_uid = account_service.login(
            username=username,
            password=password,
            login_ip=login_ip,
            login_device=login_device,
        )
        return api_response(200, "Login successful", {"token": session_uid})

    except AccountAuthError as e:
        return api_response(401, str(e))
    except AccountError as e:
        return api_response(400, str(e))
    except Exception as e:
        return api_response(500, f"Internal server error: {str(e)}")


@app.get("/auth/check-login")
async def check_login(authorization: Optional[str] = Header(None)):
    if not authorization:
        return api_response(401, "Missing Authorization Header")

    token = get_token(authorization)
    session = account_service.get_login_session(token)

    if session:
        perms = account_service._get_user_permissions(session.user_uid)
        role = account_service._get_user_role(session.user_uid)
        group_name = account_service._get_user_group_name(session.user_uid)
        return api_response(
            200,
            "Authorized",
            {
                "username": session.username,
                "role": role,
                "group_name": group_name,
                "token": session.uid,
                "permissions": perms,
            },
        )
    return api_response(401, "Unauthorized")


@app.get("/admin/registrations")
async def get_registrations(
    authorization: Optional[str] = Header(None), 
    page: int = 1, 
    page_size: int = 20, 
    sort_by: Optional[str] = None, 
    order: str = "desc",
    running_app: Optional[str] = None,
    username: Optional[str] = None
):
    session, err = require_perm(authorization, "订单处理", "查看")
    if err: return err
    data = account_service.get_registrations(page=page, page_size=page_size, sort_by=sort_by, order=order, running_app=running_app, username=username)
    return api_response(200, "Success", data)

@app.get("/admin/registrations/stats")
async def get_registration_stats(authorization: Optional[str] = Header(None)):
    session, err = require_perm(authorization, "订单处理", "查看")
    if err: return err
    stats = account_service.get_registration_stats()
    return api_response(200, "Success", stats)

@app.post("/admin/registrations/{uid}/status")
async def update_registration_status(
    uid: str,
    status: str = Form(...),
    reject_reason: Optional[str] = Form(None),
    authorization: Optional[str] = Header(None)
):
    session, err = require_perm(authorization, "订单处理", status == 'approved' and "处理" or status == 'rejected' and "驳回" or "处理")
    if err: return err
        
    try:
        account_service.update_registration_status(uid, status, reject_reason)
        if status == 'rejected':
            with account_service._connect() as conn:
                cur = conn.cursor(dictionary=True)
                cur.execute("SELECT user_uid FROM registrations WHERE uid = %s", (uid,))
                reg = cur.fetchone()
                if reg:
                    account_service.create_notification(reg['user_uid'], 'registration_rejected', '登记被驳回', reject_reason or '您的登记已被驳回', uid)
                cur = conn.cursor(dictionary=True)
                cur.execute("SELECT user_uid FROM registrations WHERE uid = %s", (uid,))
                reg = cur.fetchone()
                if reg:
                    account_service.create_notification(reg['user_uid'], 'registration_rejected', '登记被驳回', reject_reason or '您的登记已被驳回', uid)
        return api_response(200, "Status updated successfully")
    except Exception as e:
        return api_response(500, f"Error updating status: {str(e)}")


@app.delete("/admin/registrations/{uid}")
async def delete_registration(
    uid: str,
    authorization: Optional[str] = Header(None)
):
    session, err = require_perm(authorization, "订单处理", "删除")
    if err: return err
        
    try:
        success = account_service.delete_registration(uid)
        if success:
            return api_response(200, "Registration deleted successfully")
        else:
            return api_response(404, "Registration not found")
    except Exception as e:
        return api_response(500, f"Error deleting registration: {str(e)}")


@app.delete("/admin/users/{uid}")
async def delete_user(
    uid: str,
    authorization: Optional[str] = Header(None)
):
    session, err = require_perm(authorization, "账户管理", "删除")
    if err: return err
    try:
        account_service.delete_account(uid)
        return api_response(200, "User deleted successfully")
    except AccountError as e:
        return api_response(400, str(e))
    except Exception as e:
        return api_response(500, f"Internal server error: {str(e)}")

@app.patch("/admin/users/{uid}")
async def update_user(
    uid: str,
    request: UpdateUserRequest,
    authorization: Optional[str] = Header(None)
):
    session, err = require_perm(authorization, "账户管理", "修改")
    if err: return err

    try:
        account_service.update_account(
            uid=uid,
            username=request.username,
            password=request.password
        )
        return api_response(200, "User updated successfully")
    except AccountError as e:
        return api_response(400, str(e))
    except Exception as e:
        return api_response(500, f"Internal server error: {str(e)}")


@app.post("/admin/users/{uid}/force-logout")
async def force_logout_user(
    uid: str,
    authorization: Optional[str] = Header(None)
):
    session, err = require_perm(authorization, "账户管理", "强制下线")
    if err: return err

    try:
        account_service.force_logout(uid)
        return api_response(200, "User forced logout successfully")
    except Exception as e:
        return api_response(500, f"Internal server error: {str(e)}")


@app.post("/admin/settings/fields")
async def save_fields(
    fields: list[dict[str, Any]],
    authorization: Optional[str] = Header(None)
):
    session, err = require_perm(authorization, "APP配置", "修改")
    if err: return err

@app.get("/admin/settings/fields")
async def get_fields(authorization: Optional[str] = Header(None)):
    session, err = require_perm(authorization, "APP配置", "查看")
    if err: return err
    fields = account_service.get_registration_fields()
    return api_response(200, "Success", fields)

@app.get("/admin/settings/running-apps")
async def get_running_apps(authorization: Optional[str] = Header(None)):
    session, err = require_perm(authorization, "APP配置", "查看")
    if err: return err
    apps = account_service.get_running_apps()
    return api_response(200, "Success", apps)

@app.post("/admin/settings/running-apps")
async def create_running_app(
    request: RunningAppRequest,
    authorization: Optional[str] = Header(None)
):
    session, err = require_perm(authorization, "APP配置", "修改")
    if err: return err
    try:
        app_id = account_service.create_running_app(request.name, request.note, request.accent_color, request.icon)
        return api_response(200, "Running app created", {'id': app_id})
    except Exception as e:
        return api_response(500, f"Error creating running app: {str(e)}")

@app.put("/admin/settings/running-apps/{app_id}")
async def update_running_app(
    app_id: int,
    request: RunningAppRequest,
    authorization: Optional[str] = Header(None)
):
    session, err = require_perm(authorization, "APP配置", "修改")
    if err: return err
    try:
        account_service.update_running_app(app_id, request.name, request.note, request.accent_color, request.icon)
        return api_response(200, "Running app updated")
    except Exception as e:
        return api_response(500, f"Error updating running app: {str(e)}")

@app.delete("/admin/settings/running-apps/{app_id}")
async def delete_running_app(app_id: int, authorization: Optional[str] = Header(None)):
    session, err = require_perm(authorization, "APP配置", "修改")
    if err: return err
    try:
        account_service.delete_running_app(app_id)
        return api_response(200, "Running app deleted")
    except Exception as e:
        return api_response(500, f"Error deleting running app: {str(e)}")

@app.post("/admin/settings/running-apps/bulk")
async def bulk_create_running_apps(
    apps: list[dict[str, Any]],
    authorization: Optional[str] = Header(None)
):
    session, err = require_perm(authorization, "APP配置", "修改")
    if err: return err
    try:
        count = account_service.bulk_create_running_apps(apps)
        return api_response(200, f"Successfully imported {count} running apps")
    except Exception as e:
        return api_response(500, f"Error bulk importing: {str(e)}")

def _get_app_id(app_uid: str) -> int:
    app = account_service.get_running_app_by_uid(app_uid)
    if not app:
        raise Exception("App not found")
    return app['id']

@app.get("/admin/balance-transactions")
async def get_balance_transactions(authorization: Optional[str] = Header(None), app_uid: str = "", page: int = 1, page_size: int = 20):
    session, err = require_perm(authorization, "APP配置", "查看")
    if err: return err
    data = account_service.get_balance_transactions(app_uid=app_uid, page=page, page_size=page_size)
    return api_response(200, "Success", data)

@app.get("/admin/dashboard/stats")
async def get_dashboard_stats(authorization: Optional[str] = Header(None)):
    session, err = require_perm(authorization, "订单处理", "查看")
    if err: return err
    stats = account_service.get_dashboard_stats()
    return api_response(200, "Success", stats)

@app.get("/admin/settings/running-apps/{app_uid}/templates")
async def get_app_templates(app_uid: str, authorization: Optional[str] = Header(None)):
    session, err = require_perm(authorization, "APP配置", "查看")
    if err: return err
    try:
        app_id = _get_app_id(app_uid)
        templates = account_service.get_app_templates(app_id)
        return api_response(200, "Success", templates)
    except Exception as e:
        return api_response(500, str(e))

@app.post("/admin/settings/running-apps/{app_uid}/templates")
async def create_app_template(app_uid: str, data: dict[str, Any], authorization: Optional[str] = Header(None)):
    if not authorization:
        return api_response(401, "Missing Authorization Header")
    token = get_token(authorization)
    if not account_service.verify_account_type(token, "admin"):
        return api_response(403, "您没有此操作权限")
    try:
        app_id = _get_app_id(app_uid)
        uid = account_service.create_app_template(app_id, data.get('version_name', ''), data.get('fields', []))
        return api_response(200, "Template created", {'uid': uid})
    except Exception as e:
        return api_response(500, str(e))

@app.put("/admin/settings/running-apps/{app_uid}/templates/{uid}")
async def update_app_template(app_uid: str, uid: str, data: dict[str, Any], authorization: Optional[str] = Header(None)):
    if not authorization:
        return api_response(401, "Missing Authorization Header")
    token = get_token(authorization)
    if not account_service.verify_account_type(token, "admin"):
        return api_response(403, "您没有此操作权限")
    try:
        account_service.update_app_template(uid, data.get('version_name', ''), data.get('fields', []))
        return api_response(200, "Template updated")
    except Exception as e:
        return api_response(500, str(e))

@app.delete("/admin/settings/running-apps/{app_uid}/templates/{uid}")
async def delete_app_template(app_uid: str, uid: str, authorization: Optional[str] = Header(None)):
    if not authorization:
        return api_response(401, "Missing Authorization Header")
    token = get_token(authorization)
    if not account_service.verify_account_type(token, "admin"):
        return api_response(403, "您没有此操作权限")
    try:
        account_service.delete_app_template(uid)
        return api_response(200, "Template deleted")
    except Exception as e:
        return api_response(500, str(e))

# --- 普通用户接口 ---

@app.get("/running-apps/{app_uid}/templates")
async def get_public_app_templates(app_uid: str):
    try:
        app_id = _get_app_id(app_uid)
        templates = account_service.get_app_templates(app_id)
        return api_response(200, "Success", templates)
    except Exception as e:
        return api_response(500, str(e))

@app.get("/fields")
async def get_public_fields():
    """获取登记字段（公开接口，仅限已登录用户或根据需求开放）"""
    try:
        fields = account_service.get_registration_fields()
        return api_response(200, "Success", fields)
    except Exception as e:
        return api_response(500, f"Error fetching fields: {str(e)}")

@app.get("/running-apps")
async def get_public_running_apps():
    """获取跑步APP列表（公开接口）"""
    try:
        apps = account_service.get_running_apps()
        return api_response(200, "Success", apps)
    except Exception as e:
        return api_response(500, f"Error fetching running apps: {str(e)}")

@app.get("/registrations")
async def get_user_registrations(
    authorization: Optional[str] = Header(None),
    page: int = 1, page_size: int = 20
):
    """获取当前用户的登记记录（分页）"""
    session, err = require_perm(authorization, "新建登记")
    if err: return err
    data = account_service.get_user_registrations(session.user_uid, page, page_size)
    return api_response(200, "Success", data)

@app.get("/registrations/{uid}")
async def get_registration_detail(uid: str, authorization: Optional[str] = Header(None)):
    """获取单条登记详情"""
    session, err = require_perm(authorization, "新建登记")
    if err: return err
    detail = account_service.get_registration_detail(uid, session.user_uid)
    if not detail:
        return api_response(404, "Registration not found")
    return api_response(200, "Success", detail)

@app.put("/registrations/{uid}")
async def resubmit_registration(
    uid: str,
    data: dict[str, Any],
    authorization: Optional[str] = Header(None)
):
    """重新提交被驳回的登记"""
    session, err = require_perm(authorization, "新建登记")
    if err: return err
    try:
        priority = data.pop('priority', 'low') if isinstance(data, dict) else 'low'
        template_uid = data.pop('template_uid', '') if isinstance(data, dict) else ''
        amount = data.pop('amount', None) if isinstance(data, dict) else None
        if amount is not None:
            amount = float(amount)
            app_name = data.get('跑步APP', '') if isinstance(data, dict) else ''
            if app_name and not account_service.check_app_balance(app_name, amount):
                return api_response(400, f"'{app_name}' 余额不足，无法重新提交")
        account_service.resubmit_registration(uid, session.user_uid, data, priority, template_uid, amount)
        return api_response(200, "Registration resubmitted successfully")
    except AccountError as e:
        return api_response(400, str(e))
    except Exception as e:
        return api_response(500, f"Error resubmitting registration: {str(e)}")

@app.get("/registrations/check")
async def check_registration_status(authorization: Optional[str] = Header(None)):
    session, err = require_perm(authorization, "新建登记")
    if err: return err
    exists = account_service.check_registration_exists(session.user_uid)
    return api_response(200, "Success", {"registered": exists})

@app.get("/registrations/latest")
async def get_latest_registration(authorization: Optional[str] = Header(None)):
    session, err = require_perm(authorization, "新建登记")
    if err: return err
    data = account_service.get_latest_registration(session.user_uid)
    return api_response(200, "Success", data or {})

@app.post("/registrations")
async def submit_registration(
    data: dict[str, Any],
    authorization: Optional[str] = Header(None)
):
    """提交登记数据"""
    if not authorization:
        return api_response(401, "Missing Authorization Header")
    
    token = get_token(authorization)
    session = account_service.get_login_session(token)
    if not session:
        return api_response(401, "Unauthorized")
    if not account_service._check_permission(session.user_uid, "新建登记"):
        return api_response(403, "您没有此操作权限")
        
    try:
        priority = data.pop('priority', 'low') if isinstance(data, dict) else 'low'
        template_uid = data.pop('template_uid', '') if isinstance(data, dict) else ''
        amount = data.pop('amount', None) if isinstance(data, dict) else None
        if amount is not None:
            amount = float(amount)
            app_name = data.get('跑步APP', '') if isinstance(data, dict) else ''
            if app_name and not account_service.check_app_balance(app_name, amount):
                return api_response(400, f"'{app_name}' 余额不足，无法创建登记")
        account_service.submit_registration(session.user_uid, data, priority, template_uid, amount)
        account_service.create_notification_for_admins("new_registration", f"新登记", f"用户 {session.username} 提交了新登记")
        return api_response(200, "Registration submitted successfully")
    except AccountError as e:
        return api_response(400, str(e))
    except Exception as e:
        return api_response(500, f"Error submitting registration: {str(e)}")

# --- 反馈/工单接口 ---

@app.post("/feedbacks")
async def create_feedback(
    title: str = Form(...),
    content: str = Form(...),
    authorization: Optional[str] = Header(None)
):
    session, err = require_perm(authorization, "新建工单")
    if err: return err
    try:
        uid = account_service.create_feedback(session.user_uid, title, content)
        account_service.create_notification_for_admins("new_feedback", "新工单", f"用户 {session.username} 提交了工单: {title}")
        return api_response(200, "Feedback created", {'id': uid})
    except Exception as e:
        return api_response(500, f"Error: {str(e)}")

@app.get("/feedbacks")
async def get_user_feedbacks(
    authorization: Optional[str] = Header(None),
    page: int = 1, page_size: int = 20
):
    session, err = require_perm(authorization, "新建工单")
    if err: return err
    data = account_service.get_user_feedbacks(session.user_uid, page, page_size)
    return api_response(200, "Success", data)

@app.get("/feedbacks/{uid}")
async def get_feedback(uid: str, authorization: Optional[str] = Header(None)):
    session, err = require_perm(authorization, "新建工单")
    if err: return err
    detail = account_service.get_feedback_detail(uid)
    if not detail: return api_response(404, "Not found")
    if not account_service._check_permission(session.user_uid, "工单处理", "查看") and detail['user_uid'] != session.user_uid:
        return api_response(403, 您没有此操作权限)
    return api_response(200, "Success", detail)

@app.post("/feedbacks/{uid}/reply")
async def reply_feedback(
    uid: str,
    content: str = Form(...),
    authorization: Optional[str] = Header(None)
):
    session, err = require_perm(authorization, "新建工单")
    if err: return err
    is_admin = account_service._check_permission(session.user_uid, "工单处理", "回复")
    try:
        detail = account_service.get_feedback_detail(uid)
        if not detail: return api_response(404, "Not found")
        if not is_admin and detail['user_uid'] != session.user_uid:
            return api_response(403, 您没有此操作权限)
        account_service.add_feedback_reply(uid, session.user_uid, content, is_admin)
        if is_admin:
            account_service.create_notification(detail['user_uid'], 'feedback_replied', '工单有新回复', f'管理员回复了您的工单: {detail["title"]}', uid)
        else:
            account_service.create_notification_for_admins('feedback_replied', '工单有新回复', f'用户 {session.username} 回复了工单: {detail["title"]}')
        return api_response(200, "Reply added")
    except Exception as e:
        return api_response(500, f"Error: {str(e)}")

# --- 管理员工单接口 ---

@app.get("/admin/feedbacks")
async def admin_get_feedbacks(
    authorization: Optional[str] = Header(None),
    page: int = 1, page_size: int = 20,
    username: Optional[str] = None
):
    session, err = require_perm(authorization, "工单处理", "查看")
    if err: return err
    data = account_service.get_all_feedbacks(page, page_size, username)
    return api_response(200, "Success", data)

@app.post("/admin/feedbacks/{uid}/status")
async def admin_update_feedback_status(
    uid: str,
    status: str = Form(...),
    authorization: Optional[str] = Header(None)
):
    session, err = require_perm(authorization, "工单处理", "解决")
    if err: return err
    try:
        account_service.update_feedback_status(uid, status)
        detail = account_service.get_feedback_detail(uid)
        if detail:
            st = {'resolved': '已处理', 'rejected': '已驳回', 'pending': '待处理'}.get(status, status)
            account_service.create_notification(detail['user_uid'], 'feedback_status', f'工单状态更新', f'您的工单 "{detail["title"]}" 状态已更新为: {st}', uid)
        return api_response(200, "Status updated")
    except Exception as e:
        return api_response(500, f"Error: {str(e)}")

@app.delete("/admin/feedbacks/{uid}")
async def admin_delete_feedback(uid: str, authorization: Optional[str] = Header(None)):
    session, err = require_perm(authorization, "工单处理", "删除")
    if err: return err
    try:
        account_service.delete_feedback(uid)
        return api_response(200, "Deleted")
    except Exception as e:
        return api_response(500, f"Error: {str(e)}")

# --- 通知接口 ---

# --- 账户组管理（超级管理员） ---

@app.get("/admin/groups")
async def get_groups(authorization: Optional[str] = Header(None)):
    session, err = require_perm(authorization, "账户组管理", "查看")
    if err: return err
    groups = account_service.get_user_groups()
    return api_response(200, "Success", groups)

@app.post("/admin/groups")
async def create_group(data: dict[str, Any], authorization: Optional[str] = Header(None)):
    session, err = require_perm(authorization, "账户组管理", "创建")
    if err: return err
    try:
        uid = account_service.create_user_group(data.get('name', ''), data.get('permissions', {}))
        return api_response(200, "Group created", {'uid': uid})
    except AccountError as e:
        return api_response(400, str(e))

@app.get("/admin/groups/{group_uid}")
async def get_group_detail(group_uid: str, authorization: Optional[str] = Header(None)):
    session, err = require_perm(authorization, "账户组管理", "查看")
    if err: return err
    groups = account_service.get_user_groups()
    grp = next((g for g in groups if g['uid'] == group_uid), None)
    if not grp:
        return api_response(404, "Group not found")
    return api_response(200, "Success", grp)

@app.patch("/admin/groups/{group_uid}")
async def update_group(group_uid: str, data: dict[str, Any], authorization: Optional[str] = Header(None)):
    session, err = require_perm(authorization, "账户组管理", "修改")
    if err: return err
    try:
        account_service.update_user_group(group_uid, data.get('name'), data.get('permissions'))
        return api_response(200, "Group updated")
    except AccountError as e:
        return api_response(400, str(e))

@app.delete("/admin/groups/{group_uid}")
async def delete_group(group_uid: str, authorization: Optional[str] = Header(None)):
    session, err = require_perm(authorization, "账户组管理", "删除")
    if err: return err
    try:
        account_service.delete_user_group(group_uid)
        return api_response(200, "Group deleted")
    except AccountError as e:
        return api_response(400, str(e))

@app.post("/admin/users/{uid}/group")
async def assign_user_group(uid: str, data: dict[str, Any], authorization: Optional[str] = Header(None)):
    session, err = require_perm(authorization, "账户管理", "修改")
    if err: return err
    try:
        account_service.assign_user_group(uid, data.get('group_uid', ''))
        return api_response(200, "User group assigned")
    except AccountError as e:
        return api_response(400, str(e))

@app.delete("/admin/users/{uid}/group")
async def remove_user_group(uid: str, authorization: Optional[str] = Header(None)):
    session, err = require_perm(authorization, "账户管理", "修改")
    if err: return err
    try:
        account_service.remove_user_group(uid)
        return api_response(200, "User group removed")
    except AccountError as e:
        return api_response(400, str(e))

# --- APP 余额管理 ---

@app.patch("/admin/running-apps/{app_uid}/balance")
async def update_app_balance(app_uid: str, data: dict[str, Any], authorization: Optional[str] = Header(None)):
    session, err = require_perm(authorization, "APP配置", "余额管理")
    if err: return err
    try:
        result = account_service.update_app_balance(
            app_uid,
            data.get('balance_mode'),
            data.get('adjust_amount')
        )
        return api_response(200, "Balance updated", result)
    except AccountError as e:
        return api_response(400, str(e))

# --- 充值申请 ---

@app.post("/balance-recharges")
async def create_recharge(data: dict[str, Any], authorization: Optional[str] = Header(None)):
    session, err = require_perm(authorization, "充值申请")
    if err: return err
    try:
        uid = account_service.create_balance_recharge(
            session.user_uid,
            data.get('app_uid', ''),
            float(data.get('amount', 0)),
            data.get('reason', '')
        )
        account_service.create_notification_for_admins("new_registration", "新充值申请", f"用户 {session.username} 申请充值")
        return api_response(200, "Recharge request submitted", {'uid': uid})
    except AccountError as e:
        return api_response(400, str(e))

@app.get("/balance-recharges")
async def get_my_recharges(authorization: Optional[str] = Header(None)):
    session, err = require_perm(authorization, "充值申请")
    if err: return err
    data = account_service.get_user_balance_recharges(session.user_uid)
    return api_response(200, "Success", data)

@app.get("/admin/balance-recharges")
async def get_all_recharges(authorization: Optional[str] = Header(None)):
    session, err = require_perm(authorization, "充值审批", "查看")
    if err: return err
    data = account_service.get_all_balance_recharges()
    return api_response(200, "Success", data)

@app.post("/admin/balance-recharges/{uid}/process")
async def process_recharge(uid: str, data: dict[str, Any], authorization: Optional[str] = Header(None)):
    session, err = require_perm(authorization, "充值审批", "处理")
    if err: return err
    try:
        account_service.process_balance_recharge(
            uid,
            data.get('status', 'approved'),
            data.get('reject_reason', ''),
            session.username
        )
        return api_response(200, "Recharge processed")
    except AccountError as e:
        return api_response(400, str(e))

# --- 通知接口 ---

@app.get("/notifications")
async def get_notifications(authorization: Optional[str] = Header(None)):
    if not authorization: return api_response(401, "Missing Authorization Header")
    token = get_token(authorization)
    session = account_service.get_login_session(token)
    if not session: return api_response(401, "Unauthorized")
    notifications = account_service.get_user_notifications(session.user_uid)
    return api_response(200, "Success", notifications)

@app.get("/notifications/unread-count")
async def unread_count(authorization: Optional[str] = Header(None)):
    if not authorization: return api_response(401, "Missing Authorization Header")
    token = get_token(authorization)
    session = account_service.get_login_session(token)
    if not session: return api_response(401, "Unauthorized")
    count = account_service.get_unread_notification_count(session.user_uid)
    return api_response(200, "Success", {'count': count})

@app.post("/notifications/{uid}/read")
async def mark_read(uid: str, authorization: Optional[str] = Header(None)):
    if not authorization: return api_response(401, "Missing Authorization Header")
    token = get_token(authorization)
    session = account_service.get_login_session(token)
    if not session: return api_response(401, "Unauthorized")
    account_service.mark_notification_read(uid)
    return api_response(200, "Marked read")

@app.post("/notifications/read-all")
async def mark_all_read(authorization: Optional[str] = Header(None)):
    if not authorization: return api_response(401, "Missing Authorization Header")
    token = get_token(authorization)
    session = account_service.get_login_session(token)
    if not session: return api_response(401, "Unauthorized")
    account_service.mark_all_notifications_read(session.user_uid)
    return api_response(200, "All marked read")

@app.post("/notifications/read-by-reference/{reference_id}")
async def mark_read_by_reference(reference_id: str, authorization: Optional[str] = Header(None)):
    if not authorization: return api_response(401, "Missing Authorization Header")
    token = get_token(authorization)
    session = account_service.get_login_session(token)
    if not session: return api_response(401, "Unauthorized")
    count = account_service.mark_notifications_read_by_reference(session.user_uid, reference_id)
    return api_response(200, "Marked read", { "count": count })

# --- 登记聊天 WebSocket ---

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, registration_uid: str, websocket: WebSocket):
        await websocket.accept()
        if registration_uid not in self.active_connections:
            self.active_connections[registration_uid] = []
        self.active_connections[registration_uid].append(websocket)

    def disconnect(self, registration_uid: str, websocket: WebSocket):
        if registration_uid in self.active_connections:
            try:
                self.active_connections[registration_uid].remove(websocket)
            except ValueError:
                pass

    async def broadcast(self, registration_uid: str, message: dict):
        if registration_uid in self.active_connections:
            for connection in self.active_connections[registration_uid][:]:
                try:
                    await connection.send_json(message)
                except Exception:
                    self.disconnect(registration_uid, connection)

manager = ConnectionManager()

@app.websocket("/ws/chat/{registration_uid}")
async def websocket_chat(websocket: WebSocket, registration_uid: str, token: str = Query(...)):
    session = account_service.get_login_session(token)
    if not session:
        await websocket.close(code=4001)
        return
    is_staff = account_service._check_permission(session.user_uid, "订单处理", "查看")
    can_chat = account_service._check_permission(session.user_uid, "新建登记")
    if not is_staff and not can_chat:
        await websocket.close(code=4003)
        return
    if not is_staff:
        detail = account_service.get_registration_detail(registration_uid)
        if not detail or detail['user_uid'] != session.user_uid:
            await websocket.close(code=4003)
            return
    await manager.connect(registration_uid, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get('type', 'text')
            msg = account_service.save_chat_message(registration_uid, session.user_uid, data.get('message', ''), msg_type)
            msg['username'] = session.username
            msg['is_admin'] = is_staff
            msg['msg_type'] = msg_type
            account_service.update_registration_status(registration_uid, 'pending')
            try:
                detail = account_service.get_registration_detail(registration_uid)
                if detail:
                    if is_staff:
                        account_service.create_notification(detail['user_uid'], 'chat_message', '登记聊天新消息', f'管理员回复了您的登记', registration_uid)
                    else:
                        account_service.create_notification_for_admins('chat_message', '登记聊天新消息', f'用户 {session.username} 发送了新消息', registration_uid)
            except Exception:
                pass
            await manager.broadcast(registration_uid, msg)
    except WebSocketDisconnect:
        manager.disconnect(registration_uid, websocket)
    except Exception:
        manager.disconnect(registration_uid, websocket)

@app.get("/chat/{registration_uid}")
async def get_chat_history(registration_uid: str, authorization: Optional[str] = Header(None)):
    if not authorization:
        return api_response(401, "Missing Authorization Header")
    token = get_token(authorization)
    session = account_service.get_login_session(token)
    if not session:
        return api_response(401, "Unauthorized")
    is_staff = account_service._check_permission(session.user_uid, "订单处理", "查看")
    can_chat = account_service._check_permission(session.user_uid, "新建登记")
    if not is_staff and not can_chat:
        return api_response(403, 您没有此操作权限)
    if not is_staff:
        detail = account_service.get_registration_detail(registration_uid)
        if not detail or detail['user_uid'] != session.user_uid:
            return api_response(403, 您没有此操作权限)
    messages = account_service.get_chat_history(registration_uid)
    return api_response(200, "Success", messages)

if __name__ == "__main__":

    uvicorn.run(app, host="0.0.0.0", port=8001)
