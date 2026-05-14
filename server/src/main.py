import uvicorn
from fastapi import FastAPI, Form, Request, Header, HTTPException
from fastapi.responses import JSONResponse
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

class CreateUserRequest(BaseModel):
    username: str
    password: str
    type: str

class UpdateUserRequest(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None

@app.post("/admin/users")
async def create_user(
    request: CreateUserRequest,
    authorization: Optional[str] = Header(None)
):
    if not authorization:
        return api_response(401, "Missing Authorization Header")

    token = get_token(authorization)
    if not account_service.verify_account_type(token, "admin"):
        return api_response(403, "Forbidden: Admin access required")
        
    try:
        account_service.create_account(
            username=request.username,
            password=request.password,
            account_type=cast(Any, request.type)
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


# --- 路由开始 ---

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
        return api_response(
            200,
            "Authorized",
            {
                "username": session.username,
                "type": session.account_type,
                "token": session.uid,
            },
        )
    return api_response(401, "Unauthorized")


@app.get("/admin/users")
async def get_users(
    authorization: Optional[str] = Header(None), 
    page: int = 1, 
    page_size: int = 20, 
    sort_by: Optional[str] = None, 
    order: str = "desc"
):
    if not authorization:
        return api_response(401, "Missing Authorization Header")

    token = get_token(authorization)
    # 验证管理员权限
    if not account_service.verify_account_type(token, "admin"):
        return api_response(403, "Forbidden: Admin access required")

    users_data = account_service.get_all_users(page=page, page_size=page_size, sort_by=sort_by, order=order)
    # 计算总页数
    import math
    total_pages = math.ceil(users_data["total"] / page_size) if users_data["total"] > 0 else 1
    users_data["total_pages"] = total_pages
    return api_response(200, "Success", users_data)


@app.delete("/admin/users/{uid}")
async def delete_user(
    uid: str,
    authorization: Optional[str] = Header(None)
):
    if not authorization:
        return api_response(401, "Missing Authorization Header")

    token = get_token(authorization)
    # 验证管理员权限
    if not account_service.verify_account_type(token, "admin"):
        return api_response(403, "Forbidden: Admin access required")

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
    if not authorization:
        return api_response(401, "Missing Authorization Header")

    token = get_token(authorization)
    # 验证管理员权限
    if not account_service.verify_account_type(token, "admin"):
        return api_response(403, "Forbidden: Admin access required")

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
    if not authorization:
        return api_response(401, "Missing Authorization Header")

    token = get_token(authorization)
    # 验证管理员权限
    if not account_service.verify_account_type(token, "admin"):
        return api_response(403, "Forbidden: Admin access required")

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
    if not authorization:
        return api_response(401, "Missing Authorization Header")
    
    token = get_token(authorization)
    if not account_service.verify_account_type(token, "admin"):
        return api_response(403, "Forbidden: Admin access required")
        
    try:
        account_service.save_registration_fields(fields)
        return api_response(200, "Fields configuration saved successfully")
    except Exception as e:
        return api_response(500, f"Error saving fields: {str(e)}")

@app.get("/admin/settings/fields")
async def get_fields(authorization: Optional[str] = Header(None)):
    if not authorization:
        return api_response(401, "Missing Authorization Header")
        
    token = get_token(authorization)
    if not account_service.verify_account_type(token, "admin"):
        return api_response(403, "Forbidden: Admin access required")
        
    fields = account_service.get_registration_fields()
    return api_response(200, "Success", fields)

if __name__ == "__main__":

    uvicorn.run(app, host="0.0.0.0", port=8000)
