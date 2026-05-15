from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal, TypedDict, cast

import mysql.connector
from mysql.connector.connection import MySQLConnection

AccountType = Literal["admin", "default"]

class UserRow(TypedDict):
    uid: str
    username: str
    password: str
    login_sessions: str
    type: AccountType
    login_device: str | None

class SessionRow(TypedDict):
    session_uid: str
    token: str
    user_uid: str
    login_sessions: str
    type: AccountType

class AccountError(Exception):
    pass

class AccountValidationError(AccountError):
    pass

class AccountAuthError(AccountError):
    pass

@dataclass(frozen=True)
class LoginSession:
    uid: str
    token: str
    user_uid: str
    username: str
    account_type: AccountType

class AccountService:
    _PASSWORD_PATTERN = re.compile(r"^[A-Za-z0-9-]+$")
    _ACCOUNT_TYPES: set[str] = {"admin", "default"}

    def __init__(self, host: str | None = None, port: int | None = None, database: str | None = None, user: str | None = None, password: str | None = None) -> None:
        env_host, env_port = self._parse_db_url(os.getenv("DB_URL", ""))
        self.host = host or os.getenv("DB_HOST") or env_host or "localhost"
        self.port = port or int(os.getenv("DB_PORT") or env_port or "3308")
        self.database = database or os.getenv("DB_NAME", "huhurun")
        self.user = user or os.getenv("DB_USERNAME", "root")
        self.password = password or os.getenv("DB_PASSWORD", "root")

    def init_db(self) -> None:
        with self._connect(include_db=False) as connection:
            cursor = connection.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
            connection.commit()
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute("""CREATE TABLE IF NOT EXISTS users (id INT AUTO_INCREMENT PRIMARY KEY, uid VARCHAR(64) UNIQUE NOT NULL, username VARCHAR(255) NOT NULL, password VARCHAR(255) NOT NULL, login_sessions JSON, type ENUM('admin', 'default') DEFAULT 'default', register_time DATETIME NOT NULL, last_login_time DATETIME, login_ip VARCHAR(64), login_device VARCHAR(255)) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""")
            cursor.execute("SHOW COLUMNS FROM users LIKE 'login_device'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE users ADD COLUMN login_device VARCHAR(255)")
            cursor.execute("""CREATE TABLE IF NOT EXISTS login_sessions (id INT AUTO_INCREMENT PRIMARY KEY, uid VARCHAR(64) UNIQUE NOT NULL, token VARCHAR(255) NOT NULL, user_uid VARCHAR(64) NOT NULL, create_time DATETIME NOT NULL, FOREIGN KEY (user_uid) REFERENCES users(uid) ON DELETE CASCADE) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""")
            self._init_fields_table(cursor)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS registrations (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    uid VARCHAR(64) UNIQUE NOT NULL,
                    user_uid VARCHAR(64) NOT NULL,
                    data JSON NOT NULL,
                    create_time DATETIME NOT NULL,
                    status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
                    FOREIGN KEY (user_uid) REFERENCES users(uid) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            connection.commit()
        try:
            self.create_account("admin", "admin-123456", account_type="admin")
        except AccountValidationError as e:
            if "用户名已存在" not in str(e):
                raise

    def _init_fields_table(self, cursor: Any) -> None:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS registration_fields (
                id INT AUTO_INCREMENT PRIMARY KEY,
                label VARCHAR(255) NOT NULL,
                type ENUM('text', 'textarea', 'date', 'date-range', 'number', 'number-range', 'time-range', 'radio', 'checkbox', 'select') NOT NULL,
                required BOOLEAN DEFAULT FALSE,
                default_val JSON,
                options JSON,
                sort_order INT DEFAULT 0
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)

    def save_registration_fields(self, fields: list[dict[str, Any]]) -> None:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute("TRUNCATE TABLE registration_fields")
            for idx, field in enumerate(fields):
                cursor.execute("""
                    INSERT INTO registration_fields (label, type, required, default_val, options, sort_order)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (field['label'], field['type'], field['required'], 
                      json.dumps(field.get('default')), json.dumps(field.get('options')), idx))
            connection.commit()

    def get_registration_fields(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM registration_fields ORDER BY sort_order ASC")
            rows = cursor.fetchall()
            return [{
                'label': row['label'],
                'type': row['type'],
                'required': bool(row['required']),
                'default': json.loads(row['default_val']) if row['default_val'] else '',
                'options': json.loads(row['options']) if row['options'] else []
            } for row in rows]

    def get_latest_registration(self, user_uid: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT data, status FROM registrations 
                WHERE user_uid = %s 
                ORDER BY create_time DESC LIMIT 1
            """, (user_uid,))
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "status": row["status"],
                "data": json.loads(row["data"])
            }

    def submit_registration(self, user_uid: str, data: dict[str, Any]) -> str:
        # 允许提交：没有记录，或者最后一条记录被拒绝
        latest = self.get_latest_registration(user_uid)
        if latest:
            if latest["status"] == "pending":
                raise AccountError("已存在待处理的登记，无法重复登记")
            if latest["status"] == "approved":
                raise AccountError("您的登记已审核通过，无法重复登记")
            
        reg_uid = self._new_uid()
        now = self._now()
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO registrations (uid, user_uid, data, create_time, status)
                VALUES (%s, %s, %s, %s, 'pending')
            """, (reg_uid, user_uid, json.dumps(data, ensure_ascii=False), now))
            connection.commit()
        return reg_uid

    def check_registration_exists(self, user_uid: str) -> bool:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT id FROM registrations WHERE user_uid = %s AND status IN ('pending', 'approved') LIMIT 1", (user_uid,))
            return cursor.fetchone() is not None

    def create_account(self, username: str, password: str, account_type: AccountType = "default", login_ip: str = "", login_device: str = "") -> str:
        self._validate_username(username)
        self._validate_password(password)
        self._validate_account_type(account_type)
        user_uid = self._new_uid()
        password_hash = self._hash_password(password)
        now = self._now()
        with self._connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT id FROM users WHERE username = %s LIMIT 1", (username,))
            if cursor.fetchone() is not None:
                raise AccountValidationError("用户名已存在")
            cursor.execute("INSERT INTO users (uid, username, password, login_sessions, type, register_time, last_login_time, login_ip, login_device) VALUES (%s, %s, %s, %s, %s, %s, NULL, %s, %s)", (user_uid, username, password_hash, json.dumps([], ensure_ascii=False), account_type, now, login_ip, login_device))
            connection.commit()
        return user_uid

    def login(self, username: str, password: str, login_ip: str = "", login_device: str = "") -> str:
        password_hash = self._hash_password(password)
        session_uid = self._new_uid()
        token = secrets.token_hex(32)
        now = self._now()
        with self._connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT uid, password, login_sessions, type FROM users WHERE username = %s LIMIT 1", (username,))
            user = cast(UserRow | None, cursor.fetchone())
            if user is None or user["password"] != password_hash:
                raise AccountAuthError("用户名或密码错误")
            sessions = self._parse_sessions(user["login_sessions"])
            sessions.append(token)
            cursor.execute("UPDATE users SET login_sessions = %s, last_login_time = %s, login_ip = %s, login_device = %s WHERE uid = %s", (json.dumps(sessions, ensure_ascii=False), now, login_ip, login_device, user["uid"]))
            cursor.execute("INSERT INTO login_sessions (uid, token, user_uid, create_time) VALUES (%s, %s, %s, %s)", (session_uid, token, user["uid"], now))
            connection.commit()
        return session_uid

    def is_logged_in(self, session_uid: str) -> bool:
        return self.get_login_session(session_uid) is not None

    def get_login_session(self, session_uid: str) -> LoginSession | None:
        with self._connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT ls.uid AS session_uid, ls.token, ls.user_uid, u.username, u.login_sessions, u.type FROM login_sessions ls INNER JOIN users u ON u.uid = ls.user_uid WHERE ls.uid = %s LIMIT 1", (session_uid,))
            row = cast(Any, cursor.fetchone())
        if row is None:
            return None
        sessions = self._parse_sessions(row["login_sessions"])
        if row["token"] not in sessions:
            return None
        return LoginSession(uid=row["session_uid"], token=row["token"], user_uid=row["user_uid"], username=row["username"], account_type=row["type"])

    def verify_account_type(self, session_uid: str, required_type: AccountType, *, allow_admin: bool = True) -> bool:
        self._validate_account_type(required_type)
        session = self.get_login_session(session_uid)
        if session is None: return False
        if session.account_type == required_type: return True
        return allow_admin and session.account_type == "admin"

    def get_all_users(self, page: int = 1, page_size: int = 20, sort_by: str | None = None, order: str = "desc", filters: dict[str, Any] | None = None) -> dict[str, Any]:
        offset = (page - 1) * page_size
        allowed_sort = {"register_time", "last_login_time", "session_count"}
        sort_clause = ""
        if sort_by in allowed_sort:
            if sort_by == "session_count":
                 sort_dir = "DESC" if order == "desc" else "ASC"
                 sort_clause = f"ORDER BY JSON_LENGTH(login_sessions) {sort_dir}"
            else:
                 sort_dir = "DESC" if order == "desc" else "ASC"
                 sort_clause = f"ORDER BY {sort_by} {sort_dir}"
        where_clauses = []
        params = []
        if filters:
            for key, value in filters.items():
                if value:
                    if key == "username":
                        where_clauses.append("username LIKE %s")
                        params.append(f"%{value}%")
                    elif key == "type" and value != "全部":
                        where_clauses.append("type = %s")
                        params.append("admin" if value == "管理员" else "default")
        where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        with self._connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(f"SELECT COUNT(*) as total FROM users {where_sql}", tuple(params))
            total = cursor.fetchone()["total"]
            limit_clause = f"LIMIT {page_size} OFFSET {offset}" if page_size != -1 else ""
            sql = f"SELECT uid, username, login_sessions, type, register_time, last_login_time, login_ip, login_device FROM users {where_sql} {sort_clause} {limit_clause}"
            cursor.execute(sql, tuple(params))
            rows = cursor.fetchall()
        result = []
        for row in rows:
            sessions = self._parse_sessions(row["login_sessions"])
            result.append({"uid": row["uid"], "username": row["username"], "session_count": len(sessions), "type": row["type"], "register_time": row["register_time"].isoformat() if row["register_time"] else None, "last_login_time": row["last_login_time"].isoformat() if row["last_login_time"] else None, "login_ip": row["login_ip"], "login_device": self._format_device(row["login_device"])})
        return {"total": total, "page": page, "page_size": page_size, "items": result}

    def delete_account(self, uid: str) -> bool:
        with self._connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT username FROM users WHERE uid = %s LIMIT 1", (uid,))
            user = cursor.fetchone()
            if not user:
                raise AccountError("用户不存在")
            if user["username"] == "admin":
                raise AccountError("不能删除系统管理员账户")
            
            cursor.execute("DELETE FROM users WHERE uid = %s", (uid,))
            connection.commit()
            return cursor.rowcount > 0

    def update_account(self, uid: str, username: str | None = None, password: str | None = None) -> bool:
        if not username and not password:
            return False
            
        updates = []
        params = []
        
        if username:
            self._validate_username(username)
            # 检查用户名是否冲突（排除自身）
            with self._connect() as connection:
                cursor = connection.cursor()
                cursor.execute("SELECT uid FROM users WHERE username = %s AND uid != %s", (username, uid))
                if cursor.fetchone():
                    raise AccountValidationError("用户名已存在")
            updates.append("username = %s")
            params.append(username)
            
        if password:
            self._validate_password(password)
            updates.append("password = %s")
            params.append(self._hash_password(password))
            
        params.append(uid)
        sql = f"UPDATE users SET {', '.join(updates)} WHERE uid = %s"
        
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute(sql, tuple(params))
            connection.commit()
            return cursor.rowcount > 0

    def force_logout(self, uid: str) -> bool:
        with self._connect() as connection:
            cursor = connection.cursor()
            # 1. 清空 users 表中的 login_sessions JSON
            cursor.execute("UPDATE users SET login_sessions = %s WHERE uid = %s", (json.dumps([], ensure_ascii=False), uid))
            # 2. 删除 login_sessions 表中对应的记录
            cursor.execute("DELETE FROM login_sessions WHERE user_uid = %s", (uid,))
            connection.commit()
            return True

    @staticmethod
    def _format_device(ua_string: str | None) -> str:
        if not ua_string: return "未登录设备"
        if "Windows" in ua_string: return "Windows"
        if "Macintosh" in ua_string or "Mac OS X" in ua_string: return "macOS"
        if "iPhone" in ua_string: return "iOS (iPhone)"
        if "Android" in ua_string: return "Android"
        if "Mobile" in ua_string: return "Mobile Device"
        return "Desktop"

    @classmethod
    def _validate_username(cls, username: str) -> None:
        if not 1 <= len(username) <= 20: raise AccountValidationError("用户名长度必须为1-20个字符")

    @classmethod
    def _validate_password(cls, password: str) -> None:
        if not 6 <= len(password) <= 16: raise AccountValidationError("密码长度必须为6-16位")
        if cls._PASSWORD_PATTERN.fullmatch(password) is None: raise AccountValidationError("密码仅支持字母、数字和短横线")

    @classmethod
    def _validate_account_type(cls, account_type: str) -> None:
        if account_type not in cls._ACCOUNT_TYPES: raise AccountValidationError("账户类型必须是管理员或普通用户")

    @staticmethod
    def _parse_sessions(raw_sessions: Any) -> list[str]:
        if raw_sessions in (None, ""): return []
        if isinstance(raw_sessions, list): return [str(item) for item in cast(list[Any], raw_sessions)]
        if isinstance(raw_sessions, (bytes, bytearray)): raw_sessions = raw_sessions.decode("utf-8")
        if isinstance(raw_tokens := json.loads(raw_sessions) if isinstance(raw_sessions, str) else raw_sessions, list): return [str(item) for item in cast(list[Any], raw_tokens)]
        return []

    @staticmethod
    def _new_uid() -> str: return uuid.uuid4().hex

    @staticmethod
    def _hash_password(password: str) -> str: return hashlib.sha256(password.encode("utf-8")).hexdigest()

    @staticmethod
    def _now() -> datetime:
        from datetime import timezone, timedelta
        return datetime.now(timezone(timedelta(hours=8))).replace(tzinfo=None)

    @staticmethod
    def _parse_db_url(db_url: str) -> tuple[str | None, str | None]:
        if not db_url: return None, None
        host, separator, port = db_url.rpartition(":")
        if separator and host and port.isdigit(): return host, port
        return db_url, None

    def _connect(self, include_db: bool = True) -> MySQLConnection:
        config: dict[str, Any] = {"host": self.host, "port": self.port, "user": self.user, "password": self.password, "charset": "utf8mb4", "autocommit": False, "time_zone": "+08:00"}
        if include_db: config["database"] = self.database
        return cast(MySQLConnection, mysql.connector.connect(**config))

    def get_registrations(self, page: int = 1, page_size: int = 20, sort_by: str | None = None, order: str = "desc") -> dict[str, Any]:
        offset = (page - 1) * page_size
        sort_clause = f"ORDER BY {sort_by} {order}" if sort_by in {"create_time", "status"} else "ORDER BY create_time DESC"
        
        with self._connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT COUNT(*) as total FROM registrations")
            total = cursor.fetchone()["total"]
            
            sql = f"""
                SELECT r.uid, r.data, r.create_time, r.status, u.username
                FROM registrations r
                JOIN users u ON r.user_uid = u.uid
                {sort_clause}
                LIMIT {page_size} OFFSET {offset}
            """
            cursor.execute(sql)
            rows = cursor.fetchall()
            
        items = [{
            "id": row["uid"],
            "username": row["username"],
            "created_at": row["create_time"].isoformat(),
            "status": row["status"],
            "registration_info": json.loads(row["data"])
        } for row in rows]
        
        return {"total": total, "page": page, "page_size": page_size, "items": items}

    def update_registration_status(self, registration_uid: str, status: str) -> None:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute("UPDATE registrations SET status = %s WHERE uid = %s", (status, registration_uid))
            connection.commit()

    def delete_registration(self, registration_uid: str) -> bool:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM registrations WHERE uid = %s", (registration_uid,))
            connection.commit()
            return cursor.rowcount > 0
