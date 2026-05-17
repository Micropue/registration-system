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
from urllib.parse import urlparse

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

    @staticmethod
    def _parse_db_url(url: str) -> tuple[str, str]:
        if not url:
            return "", ""
        try:
            if "://" in url:
                parsed = urlparse(url)
                return parsed.hostname or "", str(parsed.port or "")
            else:
                host, _, port_str = url.partition(":")
                return host, port_str
        except Exception:
            return "", ""

    @staticmethod
    def _new_uid() -> str:
        return uuid.uuid4().hex

    @staticmethod
    def _now() -> datetime:
        return datetime.now()

    @staticmethod
    def _hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def _parse_sessions(raw: str | None) -> list[str]:
        if not raw:
            return []
        try:
            return cast(list[str], json.loads(raw))
        except Exception:
            return []

    def _connect(self, include_db: bool = True) -> MySQLConnection:
        config: dict[str, Any] = {
            "host": self.host, "port": self.port, "user": self.user,
            "password": self.password, "charset": "utf8mb4", "autocommit": False,
            "time_zone": "+08:00"
        }
        if include_db:
            config["database"] = self.database
        return cast(MySQLConnection, mysql.connector.connect(**config))

    def _validate_username(self, username: str) -> None:
        if not username or len(username) < 1 or len(username) > 20:
            raise AccountValidationError("用户名长度必须在 1-20 之间")

    def _validate_password(self, password: str) -> None:
        if len(password) < 6 or len(password) > 16:
            raise AccountValidationError("密码长度必须在 6-16 之间")
        if not self._PASSWORD_PATTERN.match(password):
            raise AccountValidationError("密码只能包含字母、数字和短横线 (-)")

    @staticmethod
    def _validate_account_type(account_type: str) -> None:
        if account_type not in AccountService._ACCOUNT_TYPES:
            raise AccountValidationError("账户类型不正确")

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
            self._init_settings_tables(cursor)
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
            cursor.execute("SHOW COLUMNS FROM registrations LIKE 'reject_reason'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE registrations ADD COLUMN reject_reason TEXT")
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

    def _init_settings_tables(self, cursor: Any) -> None:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS running_apps (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                normal_price DECIMAL(10,2) NOT NULL DEFAULT 0,
                morning_price DECIMAL(10,2) NOT NULL DEFAULT 0,
                note TEXT,
                accent_color VARCHAR(7) DEFAULT '#1976D2'
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
        """)
        try:
            cursor.execute("ALTER TABLE running_apps ADD COLUMN accent_color VARCHAR(7) DEFAULT '#1976D2'")
        except:
            pass
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedbacks (
                id INT AUTO_INCREMENT PRIMARY KEY,
                uid VARCHAR(64) UNIQUE NOT NULL,
                user_uid VARCHAR(64) NOT NULL,
                title VARCHAR(500) NOT NULL,
                content TEXT NOT NULL,
                status ENUM('pending', 'resolved', 'rejected') DEFAULT 'pending',
                create_time DATETIME NOT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback_replies (
                id INT AUTO_INCREMENT PRIMARY KEY,
                uid VARCHAR(64) UNIQUE NOT NULL,
                feedback_uid VARCHAR(64) NOT NULL,
                user_uid VARCHAR(64) NOT NULL,
                is_admin BOOLEAN DEFAULT FALSE,
                content TEXT NOT NULL,
                create_time DATETIME NOT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INT AUTO_INCREMENT PRIMARY KEY,
                uid VARCHAR(64) UNIQUE NOT NULL,
                user_uid VARCHAR(64) NOT NULL,
                type VARCHAR(50) NOT NULL,
                reference_id VARCHAR(64),
                title VARCHAR(500) NOT NULL,
                content TEXT,
                is_read BOOLEAN DEFAULT FALSE,
                create_time DATETIME NOT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS registration_chats (
                id INT AUTO_INCREMENT PRIMARY KEY,
                uid VARCHAR(64) UNIQUE NOT NULL,
                registration_uid VARCHAR(64) NOT NULL,
                sender_uid VARCHAR(64) NOT NULL,
                message TEXT NOT NULL,
                created_at DATETIME NOT NULL,
                msg_type VARCHAR(30) DEFAULT 'text',
                FOREIGN KEY (registration_uid) REFERENCES registrations(uid) ON DELETE CASCADE,
                FOREIGN KEY (sender_uid) REFERENCES users(uid) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
        """)
        try:
            cursor.execute("ALTER TABLE registration_chats ADD COLUMN msg_type VARCHAR(30) DEFAULT 'text'")
        except:
            pass

    # ---- Auth ----

    def create_account(self, username: str, password: str, account_type: str = "default") -> str:
        self._validate_username(username)
        self._validate_password(password)
        self._validate_account_type(account_type)
        user_uid = self._new_uid()
        password_hash = self._hash_password(password)
        now = self._now()
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT uid FROM users WHERE username = %s LIMIT 1", (username,))
            if cursor.fetchone():
                raise AccountValidationError("用户名已存在")
            cursor.execute("INSERT INTO users (uid, username, password, login_sessions, type, register_time, last_login_time, login_ip, login_device) VALUES (%s, %s, %s, %s, %s, %s, NULL, %s, %s)", (user_uid, username, password_hash, json.dumps([], ensure_ascii=False), account_type, now, "127.0.0.1", "server"))
            connection.commit()
        return user_uid

    def login(self, username: str, password: str, login_ip: str = "unknown", login_device: str = "unknown") -> str:
        password_hash = self._hash_password(password)
        now = self._now()
        with self._connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT uid, password, login_sessions, type FROM users WHERE username = %s LIMIT 1", (username,))
            user = cursor.fetchone()
            if not user or user["password"] != password_hash:
                raise AccountAuthError("用户名或密码错误")
            sessions = self._parse_sessions(user["login_sessions"])
            token = secrets.token_hex(32)
            sessions.append(token)
            if len(sessions) > 5:
                sessions = sessions[-5:]
            session_uid = self._new_uid()
            cursor.execute("UPDATE users SET login_sessions = %s, last_login_time = %s, login_ip = %s, login_device = %s WHERE uid = %s", (json.dumps(sessions, ensure_ascii=False), now, login_ip, login_device, user["uid"]))
            cursor.execute("INSERT INTO login_sessions (uid, token, user_uid, create_time) VALUES (%s, %s, %s, %s)", (session_uid, token, user["uid"], now))
            connection.commit()
        return session_uid

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
        if session is None:
            return False
        if session.account_type == required_type:
            return True
        return allow_admin and session.account_type == "admin"

    def force_logout(self, uid: str) -> None:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute("UPDATE users SET login_sessions = %s WHERE uid = %s", (json.dumps([], ensure_ascii=False), uid))
            cursor.execute("DELETE FROM login_sessions WHERE user_uid = %s", (uid,))
            connection.commit()

    # ---- Users ----

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
            items = [{
                "uid": row["uid"], "username": row["username"],
                "session_count": len(self._parse_sessions(row["login_sessions"])),
                "type": row["type"], "register_time": row["register_time"].isoformat(),
                "last_login_time": row["last_login_time"].isoformat() if row["last_login_time"] else None,
                "login_ip": row["login_ip"], "login_device": row["login_device"] or ""
            } for row in rows]
        return {"total": total, "page": page, "page_size": page_size, "items": items}

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
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute(f"UPDATE users SET {', '.join(updates)} WHERE uid = %s", tuple(params))
            connection.commit()
            return cursor.rowcount > 0

    # ---- Registration Fields ----

    def get_registration_fields(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT id, label, type, required, default_val, options, sort_order FROM registration_fields ORDER BY sort_order ASC")
            rows = cursor.fetchall()
        return [{
            "id": row["id"], "label": row["label"], "type": row["type"],
            "required": bool(row["required"]),
            "default": json.loads(row["default_val"]) if row["default_val"] else None,
            "options": json.loads(row["options"]) if row["options"] else None,
            "sort_order": row["sort_order"]
        } for row in rows]

    def save_registration_fields(self, fields: list[dict[str, Any]]) -> None:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM registration_fields")
            for i, f in enumerate(fields):
                cursor.execute("INSERT INTO registration_fields (label, type, required, default_val, options, sort_order) VALUES (%s, %s, %s, %s, %s, %s)",
                    (f["label"], f["type"], f.get("required", False),
                     json.dumps(f.get("default"), ensure_ascii=False) if f.get("default") is not None else None,
                     json.dumps(f.get("options"), ensure_ascii=False) if f.get("options") else None, i))
            connection.commit()

    # ---- Registrations ----

    def submit_registration(self, user_uid: str, data: dict[str, Any]) -> str:
        uid = self._new_uid()
        now = self._now()
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute("INSERT INTO registrations (uid, user_uid, data, create_time, status) VALUES (%s, %s, %s, %s, 'pending')", (uid, user_uid, json.dumps(data, ensure_ascii=False), now))
            connection.commit()
        return uid

    def get_user_registrations(self, user_uid: str, page: int = 1, page_size: int = 20) -> dict[str, Any]:
        offset = (page - 1) * page_size
        with self._connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT COUNT(*) as total FROM registrations WHERE user_uid = %s", (user_uid,))
            total = cursor.fetchone()["total"]
            cursor.execute("SELECT uid, data, create_time, status, reject_reason FROM registrations WHERE user_uid = %s ORDER BY create_time DESC LIMIT %s OFFSET %s", (user_uid, page_size, offset))
            rows = cursor.fetchall()
        items = [{
            "id": row["uid"], "created_at": row["create_time"].isoformat(),
            "status": row["status"], "data": json.loads(row["data"]),
            "reject_reason": row.get("reject_reason") or ""
        } for row in rows]
        return {"total": total, "page": page, "page_size": page_size, "items": items}

    def get_registration_detail(self, uid: str, user_uid: str | None = None) -> dict[str, Any] | None:
        with self._connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT r.uid, r.data, r.create_time, r.status, r.reject_reason, u.username, r.user_uid FROM registrations r JOIN users u ON r.user_uid = u.uid WHERE r.uid = %s", (uid,))
            row = cursor.fetchone()
            if not row:
                return None
            if user_uid and row["user_uid"] != user_uid:
                return None
        return {
            "id": row["uid"], "username": row["username"], "user_uid": row["user_uid"],
            "created_at": row["create_time"].isoformat(), "status": row["status"],
            "data": json.loads(row["data"]),
            "reject_reason": row.get("reject_reason") or ""
        }

    def check_registration_exists(self, user_uid: str) -> bool:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) as cnt FROM registrations WHERE user_uid = %s", (user_uid,))
            return cursor.fetchone()[0] > 0

    def get_latest_registration(self, user_uid: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT uid, data, create_time, status, reject_reason FROM registrations WHERE user_uid = %s ORDER BY create_time DESC LIMIT 1", (user_uid,))
            row = cursor.fetchone()
        if not row:
            return None
        return {
            "id": row["uid"], "created_at": row["create_time"].isoformat(),
            "status": row["status"], "data": json.loads(row["data"]),
            "reject_reason": row.get("reject_reason") or ""
        }

    def resubmit_registration(self, uid: str, user_uid: str, data: dict[str, Any]) -> None:
        now = self._now()
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT user_uid FROM registrations WHERE uid = %s", (uid,))
            row = cursor.fetchone()
            if not row or row[0] != user_uid:
                raise AccountError("登记记录不存在")
            cursor.execute("UPDATE registrations SET data = %s, create_time = %s, status = 'pending', reject_reason = NULL WHERE uid = %s", (json.dumps(data, ensure_ascii=False), now, uid))
            connection.commit()

    # ---- Admin Registrations ----

    def get_registrations(self, page: int = 1, page_size: int = 20, sort_by: str | None = None, order: str = "desc", running_app: str | None = None, username: str | None = None) -> dict[str, Any]:
        offset = (page - 1) * page_size
        params: list[Any] = []
        where_parts: list[str] = []
        if running_app:
            where_parts.append("JSON_EXTRACT(r.data, '$.跑步APP') = %s")
            params.append(running_app)
        if username:
            where_parts.append("u.username = %s")
            params.append(username)
        where_clause = (" WHERE " + " AND ".join(where_parts)) if where_parts else ""
        with self._connect() as connection:
            cursor = connection.cursor(dictionary=True)
            count_sql = "SELECT COUNT(*) as total FROM registrations r" + where_clause
            cursor.execute(count_sql, tuple(params))
            total = cursor.fetchone()["total"]
            sql = f"""
                SELECT r.uid, r.data, r.create_time, r.status, r.reject_reason, u.username
                FROM registrations r
                JOIN users u ON r.user_uid = u.uid
                {where_clause}
                ORDER BY CASE r.status WHEN 'pending' THEN 0 ELSE 1 END ASC, r.create_time DESC
                LIMIT {page_size} OFFSET {offset}
            """
            cursor.execute(sql, tuple(params))
            rows = cursor.fetchall()
        items = [{
            "id": row["uid"], "username": row["username"],
            "created_at": row["create_time"].isoformat(), "status": row["status"],
            "registration_info": json.loads(row["data"]),
            "reject_reason": row.get("reject_reason") or ""
        } for row in rows]
        return {"total": total, "page": page, "page_size": page_size, "items": items}

    def update_registration_status(self, registration_uid: str, status: str, reject_reason: str | None = None) -> None:
        with self._connect() as connection:
            cursor = connection.cursor()
            if reject_reason is not None:
                cursor.execute("UPDATE registrations SET status = %s, reject_reason = %s WHERE uid = %s", (status, reject_reason, registration_uid))
            else:
                cursor.execute("UPDATE registrations SET status = %s WHERE uid = %s", (status, registration_uid))
            connection.commit()

    def delete_registration(self, registration_uid: str) -> bool:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM registrations WHERE uid = %s", (registration_uid,))
            connection.commit()
            return cursor.rowcount > 0

    def get_registration_stats(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT JSON_UNQUOTE(JSON_EXTRACT(r.data, '$.跑步APP')) as app, r.status, COUNT(*) as cnt
                FROM registrations r GROUP BY app, r.status
            """)
            rows = cursor.fetchall()
        app_map: dict[str, dict[str, int]] = {}
        for row in rows:
            app_name = row['app'] or ''
            if app_name not in app_map:
                app_map[app_name] = {'pending': 0, 'approved': 0, 'rejected': 0}
            app_map[app_name][row['status']] = row['cnt']
        return [{'app': name, **counts} for name, counts in app_map.items()]

    # ---- Registration Chat ----

    def save_chat_message(self, registration_uid: str, sender_uid: str, message: str, msg_type: str = 'text') -> dict[str, Any]:
        uid = self._new_uid()
        now = self._now()
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute("INSERT INTO registration_chats (uid, registration_uid, sender_uid, message, created_at, msg_type) VALUES (%s, %s, %s, %s, %s, %s)", (uid, registration_uid, sender_uid, message, now, msg_type))
            connection.commit()
        return {"id": uid, "registration_uid": registration_uid, "sender_uid": sender_uid, "message": message, "created_at": now.isoformat(), "msg_type": msg_type}

    def get_chat_history(self, registration_uid: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT c.uid, c.registration_uid, c.sender_uid, c.message, c.msg_type, c.created_at, u.username,
                       CASE WHEN u.type = 'admin' THEN TRUE ELSE FALSE END as is_admin
                FROM registration_chats c
                JOIN users u ON c.sender_uid = u.uid
                WHERE c.registration_uid = %s
                ORDER BY c.created_at ASC
            """, (registration_uid,))
            rows = cursor.fetchall()
        return [{
            "id": row["uid"], "registration_uid": row["registration_uid"],
            "sender_uid": row["sender_uid"], "username": row["username"],
            "is_admin": bool(row["is_admin"]), "message": row["message"],
            "msg_type": row.get("msg_type", "text"),
            "created_at": row["created_at"].isoformat()
        } for row in rows]

    # ---- Running Apps ----

    def get_running_apps(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT id, name, normal_price, morning_price, note, accent_color FROM running_apps ORDER BY id ASC")
            rows = cursor.fetchall()
        return [{
            'id': row['id'], 'name': row['name'],
            'normal_price': float(row['normal_price']),
            'morning_price': float(row['morning_price']),
            'note': row['note'] or '',
            'accent_color': row['accent_color'] or '#1976D2'
        } for row in rows]

    def create_running_app(self, name: str, normal_price: float, morning_price: float, note: str, accent_color: str = '#1976D2') -> int:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute("INSERT INTO running_apps (name, normal_price, morning_price, note, accent_color) VALUES (%s, %s, %s, %s, %s)", (name, normal_price, morning_price, note, accent_color))
            connection.commit()
            return cursor.lastrowid or 0

    def update_running_app(self, app_id: int, name: str, normal_price: float, morning_price: float, note: str, accent_color: str) -> bool:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute("UPDATE running_apps SET name = %s, normal_price = %s, morning_price = %s, note = %s, accent_color = %s WHERE id = %s", (name, normal_price, morning_price, note, accent_color, app_id))
            connection.commit()
            return cursor.rowcount > 0

    def delete_running_app(self, app_id: int) -> bool:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM running_apps WHERE id = %s", (app_id,))
            connection.commit()
            return cursor.rowcount > 0

    def bulk_create_running_apps(self, apps: list[dict[str, Any]]) -> int:
        with self._connect() as connection:
            cursor = connection.cursor()
            count = 0
            for app in apps:
                cursor.execute("INSERT INTO running_apps (name, normal_price, morning_price, note, accent_color) VALUES (%s, %s, %s, %s, %s)", (app['name'], app['normal_price'], app['morning_price'], app.get('note', ''), app.get('accent_color', '#1976D2')))
                count += 1
            connection.commit()
            return count

    # ---- Feedbacks ----

    def create_feedback(self, user_uid: str, title: str, content: str) -> str:
        uid = self._new_uid()
        now = self._now()
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute("INSERT INTO feedbacks (uid, user_uid, title, content, status, create_time) VALUES (%s, %s, %s, %s, 'pending', %s)", (uid, user_uid, title, content, now))
            connection.commit()
        return uid

    def get_user_feedbacks(self, user_uid: str, page: int = 1, page_size: int = 20) -> dict[str, Any]:
        offset = (page - 1) * page_size
        with self._connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT COUNT(*) as total FROM feedbacks WHERE user_uid = %s", (user_uid,))
            total = cursor.fetchone()["total"]
            cursor.execute("SELECT f.uid, f.title, f.content, f.status, f.create_time, (SELECT COUNT(*) FROM feedback_replies WHERE feedback_uid = f.uid) as reply_count FROM feedbacks f WHERE f.user_uid = %s ORDER BY f.create_time DESC LIMIT %s OFFSET %s", (user_uid, page_size, offset))
            rows = cursor.fetchall()
        return {'total': total, 'page': page, 'page_size': page_size, 'items': [{
            'id': row['uid'], 'title': row['title'], 'content': row['content'],
            'status': row['status'], 'created_at': row['create_time'].isoformat(),
            'reply_count': row['reply_count']
        } for row in rows]}

    def get_all_feedbacks(self, page: int = 1, page_size: int = 20, username: str | None = None) -> dict[str, Any]:
        offset = (page - 1) * page_size
        where_clause = ""
        params: list[Any] = []
        if username:
            where_clause = " WHERE u.username = %s"
            params.append(username)
        with self._connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT COUNT(*) as total FROM feedbacks f JOIN users u ON f.user_uid = u.uid" + where_clause, tuple(params))
            total = cursor.fetchone()["total"]
            cursor.execute("SELECT f.uid, f.title, f.content, f.status, f.create_time, u.username FROM feedbacks f JOIN users u ON f.user_uid = u.uid" + where_clause + " ORDER BY CASE f.status WHEN 'pending' THEN 0 ELSE 1 END ASC, f.create_time DESC LIMIT %s OFFSET %s", tuple(params) + (page_size, offset))
            rows = cursor.fetchall()
        return {'total': total, 'page': page, 'page_size': page_size, 'items': [{
            'id': row['uid'], 'username': row['username'], 'title': row['title'],
            'content': row['content'], 'status': row['status'],
            'created_at': row['create_time'].isoformat()
        } for row in rows]}

    def get_feedback_detail(self, uid: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT f.uid, f.title, f.content, f.status, f.create_time, f.user_uid, u.username FROM feedbacks f JOIN users u ON f.user_uid = u.uid WHERE f.uid = %s", (uid,))
            row = cursor.fetchone()
            if not row:
                return None
            cursor.execute("SELECT uid, content, is_admin, create_time FROM feedback_replies WHERE feedback_uid = %s ORDER BY create_time ASC", (uid,))
            replies = [{'id': r['uid'], 'content': r['content'], 'is_admin': bool(r['is_admin']), 'created_at': r['create_time'].isoformat()} for r in cursor.fetchall()]
        return {'id': row['uid'], 'username': row['username'], 'user_uid': row['user_uid'], 'title': row['title'], 'content': row['content'], 'status': row['status'], 'created_at': row['create_time'].isoformat(), 'replies': replies}

    def add_feedback_reply(self, feedback_uid: str, user_uid: str, content: str, is_admin: bool = False) -> str:
        uid = self._new_uid()
        now = self._now()
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute("INSERT INTO feedback_replies (uid, feedback_uid, user_uid, is_admin, content, create_time) VALUES (%s, %s, %s, %s, %s, %s)", (uid, feedback_uid, user_uid, is_admin, content, now))
            connection.commit()
        return uid

    def update_feedback_status(self, uid: str, status: str) -> None:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute("UPDATE feedbacks SET status = %s WHERE uid = %s", (status, uid))
            connection.commit()

    def delete_feedback(self, uid: str) -> None:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM feedback_replies WHERE feedback_uid = %s", (uid,))
            cursor.execute("DELETE FROM feedbacks WHERE uid = %s", (uid,))
            connection.commit()

    # ---- Notifications ----

    def create_notification(self, user_uid: str, type: str, title: str, content: str = "", reference_id: str = "") -> str:
        uid = self._new_uid()
        now = self._now()
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute("INSERT INTO notifications (uid, user_uid, type, reference_id, title, content, is_read, create_time) VALUES (%s, %s, %s, %s, %s, %s, FALSE, %s)", (uid, user_uid, type, reference_id, title, content, now))
            connection.commit()
        return uid

    def get_user_notifications(self, user_uid: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT uid, type, reference_id, title, content, is_read, create_time FROM notifications WHERE user_uid = %s ORDER BY is_read ASC, create_time DESC LIMIT 50", (user_uid,))
            return [{'id': row['uid'], 'type': row['type'], 'reference_id': row['reference_id'], 'title': row['title'], 'content': row['content'] or '', 'is_read': bool(row['is_read']), 'created_at': row['create_time'].isoformat()} for row in cursor.fetchall()]

    def get_unread_notification_count(self, user_uid: str) -> int:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) as cnt FROM notifications WHERE user_uid = %s AND is_read = FALSE", (user_uid,))
            row = cursor.fetchone()
            return row[0] if row else 0

    def mark_notification_read(self, uid: str) -> None:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute("UPDATE notifications SET is_read = TRUE WHERE uid = %s", (uid,))
            connection.commit()

    def mark_all_notifications_read(self, user_uid: str) -> None:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute("UPDATE notifications SET is_read = TRUE WHERE user_uid = %s", (user_uid,))
            connection.commit()

    def create_notification_for_admins(self, type: str, title: str, content: str = "") -> None:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT uid FROM users WHERE type = 'admin'")
            admins = cursor.fetchall()
            for (admin_uid,) in admins:
                uid = self._new_uid()
                now = self._now()
                cursor.execute("INSERT INTO notifications (uid, user_uid, type, title, content, is_read, create_time) VALUES (%s, %s, %s, %s, %s, FALSE, %s)", (uid, admin_uid, type, title, content, now))
            connection.commit()
