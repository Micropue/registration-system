from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import JSONResponse

try:
    from .account_service import AccountService, AccountError, AccountAuthError
except ImportError:
    from account_service import AccountService, AccountError, AccountAuthError
from typing import Any

app = FastAPI()
account_service = AccountService()


@app.on_event("startup")
async def startup_event():
    # Initialize database on startup
    try:
        account_service.init_db()
    except Exception as e:
        print(f"Error initializing database: {e}")


def api_response(code: int, msg: str, data: Any = None):
    if data is None:
        data = []
    return JSONResponse(
        status_code=code, content={"code": code, "msg": msg, "data": data}
    )


@app.get("/")
def read_root():
    return api_response(200, "Hello World")


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
        import traceback

        traceback.print_exc()
        return api_response(500, f"Internal server error: {str(e)}")


@app.get("/auth/check-login")
async def check_login(token: str):
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
