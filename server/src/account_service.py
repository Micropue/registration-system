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

AccountType = Literal["admin", "default", "super_admin"]

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
    _ACCOUNT_TYPES: set[str] = {"admin", "default", "super_admin"}

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
            cursor.execute("""CREATE TABLE IF NOT EXISTS users (id INT AUTO_INCREMENT PRIMARY KEY, uid VARCHAR(64) UNIQUE NOT NULL, username VARCHAR(255) NOT NULL, password VARCHAR(255) NOT NULL, login_sessions JSON, register_time DATETIME NOT NULL, last_login_time DATETIME, login_ip VARCHAR(64), login_device VARCHAR(255)) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""")
            cursor.execute("SHOW COLUMNS FROM users LIKE 'login_device'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE users ADD COLUMN login_device VARCHAR(255)")
            cursor.execute("SHOW COLUMNS FROM users LIKE 'group_uid'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE users ADD COLUMN group_uid VARCHAR(64) DEFAULT NULL")
            try:
                cursor.execute("ALTER TABLE users DROP COLUMN type")
            except:
                pass
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
            cursor.execute("SHOW COLUMNS FROM registrations LIKE 'priority'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE registrations ADD COLUMN priority ENUM('low', 'medium', 'high') DEFAULT 'low'")
            cursor.execute("SHOW COLUMNS FROM registrations LIKE 'template_uid'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE registrations ADD COLUMN template_uid VARCHAR(64)")
            cursor.execute("SHOW COLUMNS FROM registrations LIKE 'amount'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE registrations ADD COLUMN amount DECIMAL(10,2) DEFAULT NULL")
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
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_groups (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    uid VARCHAR(64) UNIQUE NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    permissions JSON,
                    created_at DATETIME NOT NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS balance_recharges (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    uid VARCHAR(64) UNIQUE NOT NULL,
                    user_uid VARCHAR(64) NOT NULL,
                    app_uid VARCHAR(64) NOT NULL,
                    amount DECIMAL(12,2) NOT NULL,
                    reason TEXT,
                    status ENUM('pending','approved','rejected') DEFAULT 'pending',
                    reject_reason TEXT,
                    created_at DATETIME NOT NULL,
                    processed_by VARCHAR(64),
                    processed_at DATETIME
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS balance_transactions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    uid VARCHAR(64) UNIQUE NOT NULL,
                    app_uid VARCHAR(64) NOT NULL,
                    type ENUM('recharge','deduction','reversal') NOT NULL,
                    amount DECIMAL(12,2) NOT NULL,
                    balance_after DECIMAL(12,2) NOT NULL,
                    related_uid VARCHAR(64),
                    related_type VARCHAR(50),
                    note TEXT,
                    created_at DATETIME NOT NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_balances (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    uid VARCHAR(64) UNIQUE NOT NULL,
                    user_uid VARCHAR(64) NOT NULL,
                    app_uid VARCHAR(64) NOT NULL,
                    balance DECIMAL(12,2) DEFAULT 0,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL,
                    UNIQUE KEY uq_user_app (user_uid, app_uid),
                    FOREIGN KEY (user_uid) REFERENCES users(uid) ON DELETE CASCADE,
                    FOREIGN KEY (app_uid) REFERENCES running_apps(uid) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
            """)
            try:
                cursor.execute("ALTER TABLE balance_transactions ADD COLUMN user_uid VARCHAR(64) DEFAULT ''")
            except:
                pass
            self._init_default_groups(cursor)
            connection.commit()
            try:
                self.create_account("admin", "admin-123456", group_uid=self._get_default_super_admin_group_uid())
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
                note TEXT,
                accent_color VARCHAR(7) DEFAULT '#1976D2'
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
        """)
        try:
            cursor.execute("ALTER TABLE running_apps ADD COLUMN accent_color VARCHAR(7) DEFAULT '#1976D2'")
        except:
            pass
        try:
            cursor.execute("ALTER TABLE running_apps ADD COLUMN icon VARCHAR(500) DEFAULT ''")
        except:
            pass
        try:
            cursor.execute("ALTER TABLE running_apps ADD COLUMN balance_mode VARCHAR(20) DEFAULT ''")
        except:
            pass
        try:
            cursor.execute("ALTER TABLE running_apps ADD COLUMN balance DECIMAL(12,2) DEFAULT 0")
        except:
            pass
        try:
            cursor.execute("ALTER TABLE running_apps DROP COLUMN normal_price")
        except:
            pass
        try:
            cursor.execute("ALTER TABLE running_apps DROP COLUMN morning_price")
        except:
            pass
        try:
            cursor.execute("ALTER TABLE running_apps ADD COLUMN sort_order INT DEFAULT 0")
        except:
            pass
        cursor.execute("SHOW COLUMNS FROM running_apps LIKE 'uid'")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE running_apps ADD COLUMN uid VARCHAR(64) UNIQUE")
            cursor.execute("SELECT id FROM running_apps WHERE uid IS NULL")
            for (rid,) in cursor.fetchall():
                cursor.execute("UPDATE running_apps SET uid = %s WHERE id = %s", (self._new_uid(), rid))
            cursor.execute("ALTER TABLE running_apps MODIFY COLUMN uid VARCHAR(64) UNIQUE NOT NULL")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS app_templates (
                id INT AUTO_INCREMENT PRIMARY KEY,
                uid VARCHAR(64) UNIQUE NOT NULL,
                app_id INT NOT NULL,
                version_name VARCHAR(100) NOT NULL,
                fields JSON NOT NULL,
                create_time DATETIME NOT NULL,
                FOREIGN KEY (app_id) REFERENCES running_apps(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
        """)

    PERMISSION_TREE = {
        "账户管理": {"查看": True, "创建": True, "修改": True, "删除": True, "强制下线": True},
        "账户组管理": {"查看": True, "创建": True, "修改": True, "删除": True},
        "订单处理": {"查看": True, "处理": True, "驳回": True, "删除": True},
        "工单处理": {"查看": True, "回复": True, "解决": True, "删除": True},
        "APP配置": {"查看": True, "修改": True, "余额管理": True},
        "充值审批": {"查看": True, "处理": True},
        "新建登记": True,
        "新建工单": True,
        "充值申请": True,
        "余额查看": True,
    }

    def _init_default_groups(self, cursor: Any) -> None:
        now = self._now()
        cursor.execute("SELECT uid FROM user_groups WHERE name = '超级管理员'")
        if not cursor.fetchone():
            super_uid = self._new_uid()
            cursor.execute("INSERT INTO user_groups (uid, name, permissions, created_at) VALUES (%s, %s, %s, %s)",
                (super_uid, '超级管理员', json.dumps(self.PERMISSION_TREE, ensure_ascii=False), now))
        cursor.execute("SELECT uid FROM users WHERE username = 'admin' AND (group_uid IS NULL OR group_uid NOT IN (SELECT uid FROM user_groups WHERE name = '超级管理员'))")
        admin_row = cursor.fetchone()
        if admin_row:
            cursor.execute("SELECT uid FROM user_groups WHERE name = '超级管理员'")
            grp = cursor.fetchone()
            if grp:
                cursor.execute("UPDATE users SET group_uid = %s WHERE username = 'admin'", (grp[0],))

    def _get_default_super_admin_group_uid(self) -> str | None:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT uid FROM user_groups WHERE name = '超级管理员'")
            row = cursor.fetchone()
            return row[0] if row else None

    def _get_user_role(self, user_uid: str) -> str:
        with self._connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT group_uid FROM users WHERE uid = %s", (user_uid,))
            user = cursor.fetchone()
            if not user:
                return "default"
            if user["group_uid"]:
                cursor.execute("SELECT name FROM user_groups WHERE uid = %s", (user["group_uid"],))
                grp = cursor.fetchone()
                if grp:
                    name = grp["name"]
                    if name == "超级管理员":
                        return "super_admin"
            return "default"

    def _get_user_group_name(self, user_uid: str) -> str:
        with self._connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT group_uid FROM users WHERE uid = %s", (user_uid,))
            user = cursor.fetchone()
            if not user or not user["group_uid"]:
                return "未分配"
            cursor.execute("SELECT name FROM user_groups WHERE uid = %s", (user["group_uid"],))
            grp = cursor.fetchone()
            return grp["name"] if grp else "未分配"

    def _get_user_permissions(self, user_uid: str) -> dict:
        with self._connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT group_uid FROM users WHERE uid = %s", (user_uid,))
            user = cursor.fetchone()
            if not user:
                return {}
            if user["group_uid"]:
                cursor.execute("SELECT name, permissions FROM user_groups WHERE uid = %s", (user["group_uid"],))
                grp = cursor.fetchone()
                if grp and grp["name"] == "超级管理员":
                    return dict(self.PERMISSION_TREE)
                if grp and grp["permissions"]:
                    perms = json.loads(grp["permissions"]) if isinstance(grp["permissions"], str) else grp["permissions"]
                    return dict(perms)
            return {}

    def _check_permission(self, user_uid: str, *path: str) -> bool:
        perms = self._get_user_permissions(user_uid)
        current: Any = perms
        for key in path:
            if isinstance(current, dict):
                current = current.get(key, False)
            else:
                return False
        return bool(current)

    # ---- User Groups ----

    def get_user_groups(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT uid, name, permissions, created_at FROM user_groups ORDER BY created_at ASC")
            rows = cursor.fetchall()
        return [{
            "uid": row["uid"], "name": row["name"],
            "permissions": json.loads(row["permissions"]) if isinstance(row["permissions"], str) else row["permissions"],
            "created_at": row["created_at"].isoformat()
        } for row in rows]

    def create_user_group(self, name: str, permissions: dict) -> str:
        uid = self._new_uid()
        now = self._now()
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT uid FROM user_groups WHERE name = %s", (name,))
            if cursor.fetchone():
                raise AccountValidationError("账户组名称已存在")
            cursor.execute("INSERT INTO user_groups (uid, name, permissions, created_at) VALUES (%s, %s, %s, %s)",
                (uid, name, json.dumps(permissions, ensure_ascii=False), now))
            connection.commit()
        return uid

    def update_user_group(self, group_uid: str, name: str | None = None, permissions: dict | None = None) -> None:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT name FROM user_groups WHERE uid = %s", (group_uid,))
            grp = cursor.fetchone()
            if not grp:
                raise AccountError("账户组不存在")
            if grp[0] == "超级管理员" and name and name != "超级管理员":
                raise AccountError("超级管理员组不可改名")
            if grp[0] == "超级管理员" and permissions is not None:
                raise AccountError("超级管理员组权限不可修改")
            if name:
                cursor.execute("UPDATE user_groups SET name = %s WHERE uid = %s", (name, group_uid))
            if permissions is not None:
                cursor.execute("UPDATE user_groups SET permissions = %s WHERE uid = %s",
                    (json.dumps(permissions, ensure_ascii=False), group_uid))
            connection.commit()

    def delete_user_group(self, group_uid: str) -> None:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT name FROM user_groups WHERE uid = %s", (group_uid,))
            grp = cursor.fetchone()
            if not grp:
                raise AccountError("账户组不存在")
            if grp[0] == "超级管理员":
                raise AccountError("超级管理员组不可删除")
            cursor.execute("UPDATE users SET group_uid = NULL WHERE group_uid = %s", (group_uid,))
            cursor.execute("DELETE FROM user_groups WHERE uid = %s", (group_uid,))
            connection.commit()

    def assign_user_group(self, user_uid: str, group_uid: str) -> None:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT uid FROM user_groups WHERE uid = %s", (group_uid,))
            if not cursor.fetchone():
                raise AccountError("账户组不存在")
            cursor.execute("UPDATE users SET group_uid = %s WHERE uid = %s", (group_uid, user_uid))
            connection.commit()

    def remove_user_group(self, user_uid: str) -> None:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute("UPDATE users SET group_uid = NULL WHERE uid = %s", (user_uid,))
            connection.commit()

    # ---- Running Apps ----

    def get_running_apps(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            cursor = connection.cursor(dictionary=True)
            try:
                cursor.execute("SELECT id, uid, name, note, accent_color, icon, balance_mode, sort_order FROM running_apps ORDER BY sort_order ASC, id ASC")
            except Exception:
                cursor.execute("SELECT id, uid, name, note, accent_color, icon FROM running_apps ORDER BY id ASC")
            rows = cursor.fetchall()
        return [{
            "id": row["id"], "uid": row["uid"], "name": row["name"],
            "note": row["note"] or "",
            "accent_color": row.get("accent_color") or "#1976D2",
            "icon": row.get("icon") or "",
            "balance_mode": row.get("balance_mode") or "",
            "template_count": self.get_app_template_count(row["id"])
        } for row in rows]

    # ---- User Balances ----

    def _ensure_user_balance(self, user_uid: str, app_uid: str) -> None:
        now = self._now()
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT uid FROM user_balances WHERE user_uid = %s AND app_uid = %s", (user_uid, app_uid))
            if not cursor.fetchone():
                uid = self._new_uid()
                cursor.execute("INSERT INTO user_balances (uid, user_uid, app_uid, balance, created_at, updated_at) VALUES (%s, %s, %s, 0, %s, %s)",
                    (uid, user_uid, app_uid, now, now))
                connection.commit()

    def get_user_balance(self, user_uid: str, app_uid: str) -> dict[str, Any] | None:
        self._ensure_user_balance(user_uid, app_uid)
        with self._connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT ub.balance, ra.balance_mode FROM user_balances ub JOIN running_apps ra ON ra.uid = ub.app_uid WHERE ub.user_uid = %s AND ub.app_uid = %s", (user_uid, app_uid))
            row = cursor.fetchone()
            if not row:
                return None
            return {"balance": float(row["balance"] or 0), "balance_mode": row.get("balance_mode") or ""}

    def get_user_balances(self, user_uid: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT ub.uid, ub.app_uid, ub.balance, ra.name as app_name, ra.balance_mode, ra.icon
                FROM user_balances ub
                JOIN running_apps ra ON ra.uid = ub.app_uid
                WHERE ub.user_uid = %s
                ORDER BY ra.name ASC
            """, (user_uid,))
            rows = cursor.fetchall()
        return [{
            "id": row["uid"], "app_uid": row["app_uid"], "app_name": row["app_name"],
            "balance": float(row["balance"] or 0), "balance_mode": row.get("balance_mode") or "",
            "icon": row.get("icon") or ""
        } for row in rows]

    def get_app_user_balances(self, app_uid: str, page: int = 1, page_size: int = 20) -> dict[str, Any]:
        offset = (page - 1) * page_size
        with self._connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT COUNT(*) as total FROM users u
                LEFT JOIN user_balances ub ON ub.user_uid = u.uid AND ub.app_uid = %s
            """, (app_uid,))
            total = cursor.fetchone()["total"]
            cursor.execute("""
                SELECT u.uid as user_uid, u.username,
                       COALESCE(ub.balance, 0) as balance,
                       COALESCE(ub.updated_at, u.register_time) as updated_at,
                       ub.uid as balance_uid
                FROM users u
                LEFT JOIN user_balances ub ON ub.user_uid = u.uid AND ub.app_uid = %s
                ORDER BY balance DESC
                LIMIT %s OFFSET %s
            """, (app_uid, page_size, offset))
            rows = cursor.fetchall()
        items = [{
            "id": row["balance_uid"] or "", "user_uid": row["user_uid"], "app_uid": app_uid,
            "username": row["username"], "balance": float(row["balance"] or 0),
            "updated_at": row["updated_at"].isoformat()
        } for row in rows]
        return {"total": total, "page": page, "page_size": page_size, "items": items}

    def adjust_user_balance(self, user_uid: str, app_uid: str, amount: float, note: str = "") -> dict:
        self._ensure_user_balance(user_uid, app_uid)
        now = self._now()
        with self._connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT balance FROM user_balances WHERE user_uid = %s AND app_uid = %s", (user_uid, app_uid))
            row = cursor.fetchone()
            current = float(row["balance"] or 0) if row else 0
            new_balance = round(current + amount, 2)
            if new_balance < 0:
                ra = self.get_running_app_by_uid(app_uid)
                app_name = ra["name"] if ra else app_uid
                raise AccountValidationError(f"用户余额不足，当前余额 {current}，无法减少 {abs(amount)}")
            cursor.execute("UPDATE user_balances SET balance = %s, updated_at = %s WHERE user_uid = %s AND app_uid = %s",
                (new_balance, now, user_uid, app_uid))
            connection.commit()
            txn_type = "recharge" if amount > 0 else "deduction"
            self._record_balance_transaction(app_uid, txn_type, abs(amount),
                user_uid=user_uid, note=note)
        return {"balance": new_balance}

    def set_app_balance_mode(self, app_uid: str, balance_mode: str) -> None:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute("UPDATE running_apps SET balance_mode = %s WHERE uid = %s", (balance_mode, app_uid))
            connection.commit()

    def check_user_balance(self, user_uid: str, app_uid: str, amount: float) -> bool:
        bal = self.get_user_balance(user_uid, app_uid)
        if not bal:
            return False
        return bal["balance"] >= amount

    def _record_balance_transaction(self, app_uid: str, type: str, amount: float, user_uid: str = "", related_uid: str = "", related_type: str = "", note: str = "") -> str:
        uid = self._new_uid()
        now = self._now()
        with self._connect() as connection:
            cursor = connection.cursor(dictionary=True)
            if user_uid:
                cursor.execute("SELECT balance FROM user_balances WHERE user_uid = %s AND app_uid = %s", (user_uid, app_uid))
                ub = cursor.fetchone()
                current = float(ub["balance"] or 0) if ub else 0
            else:
                current = 0
            if type == 'recharge':
                balance_after = round(current + amount, 2)
            elif type == 'deduction':
                balance_after = round(current - amount, 2)
            elif type == 'reversal':
                balance_after = round(current + amount, 2)
            else:
                balance_after = current
            cursor.execute("INSERT INTO balance_transactions (uid, app_uid, user_uid, type, amount, balance_after, related_uid, related_type, note, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (uid, app_uid, user_uid, type, amount, balance_after, related_uid, related_type, note, now))
            connection.commit()
        return uid

    def get_balance_transactions(self, app_uid: str = "", user_uid: str = "", page: int = 1, page_size: int = 20) -> dict[str, Any]:
        offset = (page - 1) * page_size
        with self._connect() as connection:
            cursor = connection.cursor(dictionary=True)
            conditions = []
            params = []
            if app_uid:
                conditions.append("bt.app_uid = %s")
                params.append(app_uid)
            if user_uid:
                conditions.append("bt.user_uid = %s")
                params.append(user_uid)
            where_clause = ""
            if conditions:
                where_clause = "WHERE " + " AND ".join(conditions)
            cursor.execute(f"SELECT COUNT(*) as total FROM balance_transactions bt {where_clause}", tuple(params))
            total = cursor.fetchone()["total"]
            sql = f"""
                SELECT bt.uid, bt.app_uid, ra.name as app_name, ra.icon as app_icon, bt.type, bt.amount, bt.balance_after,
                       bt.related_uid, bt.related_type, bt.note, bt.user_uid, u2.username, bt.created_at
                FROM balance_transactions bt
                JOIN running_apps ra ON ra.uid = bt.app_uid
                LEFT JOIN users u2 ON bt.user_uid = u2.uid
                {where_clause}
                ORDER BY bt.created_at DESC
                LIMIT %s OFFSET %s
            """
            cursor.execute(sql, tuple(params) + (page_size, offset))
            rows = cursor.fetchall()
        items = [{
            "id": row["uid"], "app_uid": row["app_uid"], "app_name": row["app_name"],
            "app_icon": row.get("app_icon") or "",
            "type": row["type"], "amount": float(row["amount"]),
            "balance_after": float(row["balance_after"]),
            "related_uid": row["related_uid"] or "", "related_type": row["related_type"] or "",
            "note": row["note"] or "", "user_uid": row.get("user_uid") or "",
            "username": row.get("username") or "",
            "created_at": row["created_at"].isoformat()
        } for row in rows]
        return {"total": total, "page": page, "page_size": page_size, "items": items}

    def get_user_balance_transactions(self, user_uid: str, app_uid: str = "", page: int = 1, page_size: int = 20) -> dict[str, Any]:
        return self.get_balance_transactions(app_uid=app_uid, user_uid=user_uid, page=page, page_size=page_size)

    # ---- Balance Recharges ----

    def create_balance_recharge(self, user_uid: str, app_uid: str, amount: float, reason: str) -> str:
        uid = self._new_uid()
        now = self._now()
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT uid, balance_mode FROM running_apps WHERE uid = %s", (app_uid,))
            app = cursor.fetchone()
            if not app:
                raise AccountError("APP不存在")
            if amount <= 0:
                raise AccountValidationError("充值量必须大于0")
            cursor.execute("INSERT INTO balance_recharges (uid, user_uid, app_uid, amount, reason, status, created_at) VALUES (%s, %s, %s, %s, %s, 'pending', %s)",
                (uid, user_uid, app_uid, amount, reason, now))
            connection.commit()
        return uid

    def get_user_balance_recharges(self, user_uid: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT br.uid, br.amount, br.reason, br.status, br.reject_reason, br.created_at, br.processed_at,
                       ra.name as app_name, ra.balance_mode as app_balance_mode
                FROM balance_recharges br
                JOIN running_apps ra ON br.app_uid = ra.uid
                WHERE br.user_uid = %s ORDER BY br.created_at DESC
            """, (user_uid,))
            rows = cursor.fetchall()
        return [{
            "id": row["uid"], "app_name": row["app_name"], "app_balance_mode": row["app_balance_mode"],
            "amount": float(row["amount"]), "reason": row["reason"] or "",
            "status": row["status"], "reject_reason": row["reject_reason"] or "",
            "created_at": row["created_at"].isoformat(), "processed_at": row["processed_at"].isoformat() if row["processed_at"] else None
        } for row in rows]

    def get_all_balance_recharges(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT br.uid, br.amount, br.reason, br.status, br.reject_reason, br.created_at, br.processed_at,
                       ra.name as app_name, ra.balance_mode as app_balance_mode, u.username as username
                FROM balance_recharges br
                JOIN running_apps ra ON br.app_uid = ra.uid
                JOIN users u ON br.user_uid = u.uid
                ORDER BY br.status ASC, br.created_at DESC
            """)
            rows = cursor.fetchall()
        return [{
            "id": row["uid"], "username": row["username"], "app_name": row["app_name"],
            "app_balance_mode": row["app_balance_mode"],
            "amount": float(row["amount"]), "reason": row["reason"] or "",
            "status": row["status"], "reject_reason": row["reject_reason"] or "",
            "created_at": row["created_at"].isoformat(),
            "processed_at": row["processed_at"].isoformat() if row["processed_at"] else None
        } for row in rows]

    def process_balance_recharge(self, recharge_uid: str, status: str, reject_reason: str = "", processed_by: str = "") -> None:
        now = self._now()
        with self._connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT uid, app_uid, amount, status, user_uid FROM balance_recharges WHERE uid = %s", (recharge_uid,))
            recharge = cursor.fetchone()
            if not recharge:
                raise AccountError("充值申请不存在")
            if recharge["status"] != "pending":
                raise AccountError("该申请已处理")
            cursor.execute("UPDATE balance_recharges SET status = %s, reject_reason = %s, processed_by = %s, processed_at = %s WHERE uid = %s",
                (status, reject_reason, processed_by, now, recharge_uid))
            connection.commit()
        if status == "approved":
            self.adjust_user_balance(recharge["user_uid"], recharge["app_uid"], float(recharge["amount"]),
                note=f"充值审批通过")

    def get_balance_recharge(self, recharge_uid: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT br.uid, br.amount, br.status, br.user_uid, br.app_uid, ra.name as app_name FROM balance_recharges br JOIN running_apps ra ON ra.uid = br.app_uid WHERE br.uid = %s", (recharge_uid,))
            row = cursor.fetchone()
        if not row:
            return None
        return {
            'uid': row['uid'],
            'amount': row['amount'],
            'status': row['status'],
            'user_uid': row['user_uid'],
            'app_uid': row['app_uid'],
            'app_name': row['app_name']
        }

    # ---- Registration with Amount ----

    def create_account(self, username: str, password: str, group_uid: str | None = None) -> str:
        self._validate_username(username)
        self._validate_password(password)
        user_uid = self._new_uid()
        password_hash = self._hash_password(password)
        now = self._now()
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT uid FROM users WHERE username = %s LIMIT 1", (username,))
            if cursor.fetchone():
                raise AccountValidationError("用户名已存在")
            if group_uid:
                cursor.execute("SELECT uid FROM user_groups WHERE uid = %s", (group_uid,))
                if not cursor.fetchone():
                    raise AccountValidationError("账户组不存在")
            cursor.execute("INSERT INTO users (uid, username, password, login_sessions, register_time, last_login_time, login_ip, login_device, group_uid) VALUES (%s, %s, %s, %s, %s, NULL, %s, %s, %s)", (user_uid, username, password_hash, json.dumps([], ensure_ascii=False), now, "127.0.0.1", "server", group_uid))
            connection.commit()
        return user_uid

    def login(self, username: str, password: str, login_ip: str = "unknown", login_device: str = "unknown") -> str:
        password_hash = self._hash_password(password)
        now = self._now()
        with self._connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT uid, password, login_sessions FROM users WHERE username = %s LIMIT 1", (username,))
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
            cursor.execute("SELECT ls.uid AS session_uid, ls.token, ls.user_uid, u.username, u.login_sessions FROM login_sessions ls INNER JOIN users u ON u.uid = ls.user_uid WHERE ls.uid = %s LIMIT 1", (session_uid,))
            row = cast(Any, cursor.fetchone())
        if row is None:
            return None
        sessions = self._parse_sessions(row["login_sessions"])
        if row["token"] not in sessions:
            return None
        role = self._get_user_role(row["user_uid"])
        return LoginSession(uid=row["session_uid"], token=row["token"], user_uid=row["user_uid"], username=row["username"], account_type=cast(Any, role))

    def verify_account_type(self, session_uid: str, required_type: AccountType, *, allow_admin: bool = True) -> bool:
        self._validate_account_type(required_type)
        session = self.get_login_session(session_uid)
        if session is None:
            return False
        if session.account_type == "super_admin":
            return True
        if session.account_type == required_type:
            return True
        return allow_admin and session.account_type in ("admin", "super_admin")

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
                        where_clauses.append("u.username LIKE %s")
                        params.append(f"%{value}%")
                    elif key == "group_uid" and value != "全部":
                        where_clauses.append("group_uid = %s")
                        params.append(value)
                    elif key == "type" and value != "全部":
                        if value == "未分配":
                            where_clauses.append("u.group_uid IS NULL")
                        else:
                            where_clauses.append("ug.name = %s")
                            params.append(value)
        where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        with self._connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(f"SELECT COUNT(*) as total FROM users {where_sql}", tuple(params))
            total = cursor.fetchone()["total"]
            limit_clause = f"LIMIT {page_size} OFFSET {offset}" if page_size != -1 else ""
            sql = f"SELECT u.uid, u.username, u.login_sessions, u.register_time, u.last_login_time, u.login_ip, u.login_device, u.group_uid, ug.name as group_name FROM users u LEFT JOIN user_groups ug ON ug.uid = u.group_uid {where_sql} {sort_clause} {limit_clause}"
            cursor.execute(sql, tuple(params))
            rows = cursor.fetchall()
            items = [{
                "uid": row["uid"], "username": row["username"],
                "session_count": len(self._parse_sessions(row["login_sessions"])),
                "type": row.get("group_name") or "未分配", "register_time": row["register_time"].isoformat(),
                "last_login_time": row["last_login_time"].isoformat() if row["last_login_time"] else None,
                "login_ip": row["login_ip"], "login_device": row["login_device"] or "",
                "group_uid": row.get("group_uid") or ""
            } for row in rows]
        return {"total": total, "page": page, "page_size": page_size, "items": items}

    def delete_account(self, uid: str) -> bool:
        with self._connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT u.username, ug.name as group_name FROM users u LEFT JOIN user_groups ug ON ug.uid = u.group_uid WHERE u.uid = %s LIMIT 1", (uid,))
            user = cursor.fetchone()
            if not user:
                raise AccountError("用户不存在")
            if user.get("group_name") == "超级管理员":
                raise AccountError("不能删除超级管理员账户")
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

    def submit_registration(self, user_uid: str, data: dict[str, Any], priority: str = 'low', template_uid: str = '', amount: float | None = None) -> str:
        uid = self._new_uid()
        now = self._now()
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute("INSERT INTO registrations (uid, user_uid, data, create_time, status, priority, template_uid, amount) VALUES (%s, %s, %s, %s, 'pending', %s, %s, %s)", (uid, user_uid, json.dumps(data, ensure_ascii=False), now, priority, template_uid, amount))
            connection.commit()
        if amount and amount > 0:
            app_name = data.get('跑步APP', '')
            if app_name:
                app_uid = None
                with self._connect() as conn2:
                    cur = conn2.cursor(dictionary=True)
                    cur.execute("SELECT uid FROM running_apps WHERE name = %s", (app_name,))
                    app = cur.fetchone()
                    app_uid = app["uid"] if app else None
                if app_uid:
                    self._ensure_user_balance(user_uid, app_uid)
                    self.adjust_user_balance(user_uid, app_uid, -amount,
                        note=f"登记创建扣除")
        return uid

    def get_user_registrations(self, user_uid: str, page: int = 1, page_size: int = 20) -> dict[str, Any]:
        offset = (page - 1) * page_size
        with self._connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT COUNT(*) as total FROM registrations WHERE user_uid = %s", (user_uid,))
            total = cursor.fetchone()["total"]
            cursor.execute("SELECT r.uid, r.data, r.create_time, r.status, r.reject_reason, r.priority, r.template_uid, r.amount, at2.version_name as template_name FROM registrations r LEFT JOIN app_templates at2 ON at2.uid = r.template_uid WHERE r.user_uid = %s ORDER BY r.create_time DESC LIMIT %s OFFSET %s", (user_uid, page_size, offset))
            rows = cursor.fetchall()
        items = [{
            "id": row["uid"], "created_at": row["create_time"].isoformat(),
            "status": row["status"], "data": json.loads(row["data"]),
            "reject_reason": row.get("reject_reason") or "",
            "priority": row.get("priority") or "low",
            "template_uid": row.get("template_uid") or "",
            "template_name": row.get("template_name") or "",
            "amount": float(row["amount"]) if row.get("amount") else None
        } for row in rows]
        return {"total": total, "page": page, "page_size": page_size, "items": items}

    def get_registration_detail(self, uid: str, user_uid: str | None = None) -> dict[str, Any] | None:
        with self._connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT r.uid, r.data, r.create_time, r.status, r.reject_reason, r.priority, r.template_uid, r.amount, u.username, r.user_uid FROM registrations r JOIN users u ON r.user_uid = u.uid WHERE r.uid = %s", (uid,))
            row = cursor.fetchone()
            if not row:
                return None
            if user_uid and row["user_uid"] != user_uid:
                return None
        return {
            "id": row["uid"], "username": row["username"], "user_uid": row["user_uid"],
            "created_at": row["create_time"].isoformat(), "status": row["status"],
            "data": json.loads(row["data"]),
            "reject_reason": row.get("reject_reason") or "",
            "priority": row.get("priority") or "low",
            "template_uid": row.get("template_uid") or "",
            "amount": float(row["amount"]) if row.get("amount") else None
        }

    def check_registration_exists(self, user_uid: str) -> bool:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) as cnt FROM registrations WHERE user_uid = %s", (user_uid,))
            return cursor.fetchone()[0] > 0

    def get_latest_registration(self, user_uid: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT uid, data, create_time, status, reject_reason, priority, template_uid FROM registrations WHERE user_uid = %s ORDER BY create_time DESC LIMIT 1", (user_uid,))
            row = cursor.fetchone()
        if not row:
            return None
        return {
            "id": row["uid"], "created_at": row["create_time"].isoformat(),
            "status": row["status"], "data": json.loads(row["data"]),
            "reject_reason": row.get("reject_reason") or "",
            "priority": row.get("priority") or "low",
            "template_uid": row.get("template_uid") or ""
        }

    def resubmit_registration(self, uid: str, user_uid: str, data: dict[str, Any], priority: str = 'low', template_uid: str = '', amount: float | None = None) -> None:
        now = self._now()
        old_amount = None
        old_app_name = None
        with self._connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT amount, JSON_UNQUOTE(JSON_EXTRACT(data, '$.跑步APP')) as app_name FROM registrations WHERE uid = %s", (uid,))
            reg = cursor.fetchone()
            if reg:
                old_amount = reg.get("amount")
                old_app_name = reg.get("app_name")
            cursor = connection.cursor()
            cursor.execute("SELECT user_uid FROM registrations WHERE uid = %s", (uid,))
            row = cursor.fetchone()
            if not row or row[0] != user_uid:
                raise AccountError("登记记录不存在")
            cursor.execute("UPDATE registrations SET data = %s, create_time = %s, status = 'pending', reject_reason = NULL, priority = %s, template_uid = %s, amount = %s WHERE uid = %s", (json.dumps(data, ensure_ascii=False), now, priority, template_uid, amount, uid))
            connection.commit()
        if old_amount and old_app_name:
            app_uid = None
            with self._connect() as conn2:
                cur = conn2.cursor(dictionary=True)
                cur.execute("SELECT uid FROM running_apps WHERE name = %s", (old_app_name,))
                app = cur.fetchone()
                app_uid = app["uid"] if app else None
            if app_uid:
                self.adjust_user_balance(user_uid, app_uid, float(old_amount),
                    note="重新提交撤销原扣除")
        if amount and amount > 0:
            app_name = data.get('跑步APP', '')
            if app_name:
                app_uid2 = None
                with self._connect() as conn3:
                    cur = conn3.cursor(dictionary=True)
                    cur.execute("SELECT uid FROM running_apps WHERE name = %s", (app_name,))
                    app = cur.fetchone()
                    app_uid2 = app["uid"] if app else None
                if app_uid2:
                    self._ensure_user_balance(user_uid, app_uid2)
                    self.adjust_user_balance(user_uid, app_uid2, -amount,
                        note="登记重新提交扣除")

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
        if sort_by == 'priority':
            order_clause = "FIELD(r.priority, 'high', 'medium', 'low') ASC, r.create_time DESC"
        else:
            order_clause = "CASE r.status WHEN 'pending' THEN 0 ELSE 1 END ASC, r.create_time DESC"
        with self._connect() as connection:
            cursor = connection.cursor(dictionary=True)
            count_sql = "SELECT COUNT(*) as total FROM registrations r" + where_clause
            cursor.execute(count_sql, tuple(params))
            total = cursor.fetchone()["total"]
            sql = f"""
                SELECT r.uid, r.data, r.create_time, r.status, r.reject_reason, r.priority, r.template_uid, r.amount, u.username, at2.version_name as template_name
                FROM registrations r
                JOIN users u ON r.user_uid = u.uid
                LEFT JOIN app_templates at2 ON at2.uid = r.template_uid
                {where_clause}
                ORDER BY {order_clause}
                LIMIT {page_size} OFFSET {offset}
            """
            cursor.execute(sql, tuple(params))
            rows = cursor.fetchall()
        items = [{
            "id": row["uid"], "username": row["username"],
            "created_at": row["create_time"].isoformat(), "status": row["status"],
            "registration_info": json.loads(row["data"]),
            "reject_reason": row.get("reject_reason") or "",
            "priority": row.get("priority") or "low",
            "template_uid": row.get("template_uid") or "",
            "template_name": row.get("template_name") or "",
            "amount": float(row["amount"]) if row.get("amount") else None
        } for row in rows]
        return {"total": total, "page": page, "page_size": page_size, "items": items}

    def update_registration_status(self, registration_uid: str, status: str, reject_reason: str | None = None) -> None:
        reg_info = None
        with self._connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT r.status as old_status, r.amount, JSON_UNQUOTE(JSON_EXTRACT(r.data, '$.跑步APP')) as app_name, r.user_uid FROM registrations r WHERE r.uid = %s", (registration_uid,))
            reg = cursor.fetchone()
            if reg:
                reg_info = {"old_status": reg["old_status"], "amount": reg.get("amount"), "app_name": reg.get("app_name"), "user_uid": reg.get("user_uid")}
            if reject_reason is not None:
                cursor.execute("UPDATE registrations SET status = %s, reject_reason = %s WHERE uid = %s", (status, reject_reason, registration_uid))
            else:
                cursor.execute("UPDATE registrations SET status = %s WHERE uid = %s", (status, registration_uid))
            connection.commit()
        if reg_info and reg_info["amount"] and reg_info["app_name"] and reg_info.get("user_uid") and status != 'approved' and status != reg_info.get("old_status"):
            app_name = reg_info["app_name"]
            app_uid = None
            with self._connect() as conn2:
                cur = conn2.cursor(dictionary=True)
                cur.execute("SELECT uid FROM running_apps WHERE name = %s", (app_name,))
                app = cur.fetchone()
                app_uid = app["uid"] if app else None
            if app_uid and reg_info.get("user_uid"):
                self.adjust_user_balance(reg_info["user_uid"], app_uid, float(reg_info["amount"]),
                    note=f"登记状态变为{status}，撤销扣除")

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
                       CASE WHEN ug.name IN ('管理员','超级管理员') THEN TRUE ELSE FALSE END as is_admin
                FROM registration_chats c
                JOIN users u ON c.sender_uid = u.uid
                LEFT JOIN user_groups ug ON ug.uid = u.group_uid
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

    def get_running_app_by_uid(self, uid: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT id, uid, name FROM running_apps WHERE uid = %s", (uid,))
            row = cursor.fetchone()
        if not row:
            return None
        return {'id': row['id'], 'uid': row['uid'], 'name': row['name']}

    def get_running_app_by_name(self, name: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT id, uid, name FROM running_apps WHERE name = %s", (name,))
            row = cursor.fetchone()
        if not row:
            return None
        return {'id': row['id'], 'uid': row['uid'], 'name': row['name']}

    def create_running_app(self, name: str, note: str, accent_color: str = '#1976D2', icon: str = '', balance_mode: str = '') -> int:
        uid = self._new_uid()
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute("INSERT INTO running_apps (name, note, accent_color, icon, uid, balance_mode) VALUES (%s, %s, %s, %s, %s, %s)", (name, note, accent_color, icon, uid, balance_mode))
            connection.commit()
            return cursor.lastrowid or 0

    def update_running_app(self, app_id: int, name: str, note: str, accent_color: str, icon: str = '', balance_mode: str = '') -> bool:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute("UPDATE running_apps SET name = %s, note = %s, accent_color = %s, icon = %s, balance_mode = %s WHERE id = %s", (name, note, accent_color, icon, balance_mode, app_id))
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
                cursor.execute("INSERT INTO running_apps (name, note, accent_color, uid) VALUES (%s, %s, %s, %s)", (app['name'], app.get('note', ''), app.get('accent_color', '#1976D2'), self._new_uid()))
                count += 1
            connection.commit()
            return count

    def sort_running_apps(self, ordered_ids: list[int]) -> bool:
        with self._connect() as connection:
            cursor = connection.cursor()
            for idx, app_id in enumerate(ordered_ids):
                cursor.execute("UPDATE running_apps SET sort_order = %s WHERE id = %s", (idx, app_id))
            connection.commit()
        return True

    # ---- App Templates ----

    def create_app_template(self, app_id: int, version_name: str, fields: list[dict[str, Any]]) -> str:
        uid = self._new_uid()
        now = self._now()
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute("INSERT INTO app_templates (uid, app_id, version_name, fields, create_time) VALUES (%s, %s, %s, %s, %s)", (uid, app_id, version_name, json.dumps(fields, ensure_ascii=False), now))
            connection.commit()
        return uid

    def get_app_templates(self, app_id: int) -> list[dict[str, Any]]:
        with self._connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT uid, app_id, version_name, fields, create_time FROM app_templates WHERE app_id = %s ORDER BY create_time DESC", (app_id,))
            rows = cursor.fetchall()
        return [{
            'uid': row['uid'], 'app_id': row['app_id'],
            'version_name': row['version_name'],
            'fields': json.loads(row['fields']),
            'create_time': row['create_time'].isoformat()
        } for row in rows]

    def get_app_template(self, uid: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT uid, app_id, version_name, fields, create_time FROM app_templates WHERE uid = %s", (uid,))
            row = cursor.fetchone()
        if not row:
            return None
        return {
            'uid': row['uid'], 'app_id': row['app_id'],
            'version_name': row['version_name'],
            'fields': json.loads(row['fields']),
            'create_time': row['create_time'].isoformat()
        }

    def update_app_template(self, uid: str, version_name: str, fields: list[dict[str, Any]]) -> bool:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute("UPDATE app_templates SET version_name = %s, fields = %s WHERE uid = %s", (version_name, json.dumps(fields, ensure_ascii=False), uid))
            connection.commit()
            return cursor.rowcount > 0

    def delete_app_template(self, uid: str) -> bool:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM app_templates WHERE uid = %s", (uid,))
            connection.commit()
            return cursor.rowcount > 0

    def get_app_template_count(self, app_id: int) -> int:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM app_templates WHERE app_id = %s", (app_id,))
            return cursor.fetchone()[0]

    def get_dashboard_stats(self) -> dict[str, Any]:
        now = self._now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM registrations")
            total_registrations = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM registrations WHERE status = 'pending'")
            pending_registrations = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM feedbacks")
            total_feedbacks = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM feedbacks WHERE status = 'pending'")
            pending_feedbacks = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM registrations WHERE create_time >= %s", (today_start,))
            today_registrations = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM feedbacks WHERE create_time >= %s", (today_start,))
            today_feedbacks = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM running_apps")
            total_apps = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM registration_chats WHERE created_at >= %s", (today_start,))
            today_chats = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM balance_recharges")
            total_recharges = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM balance_recharges WHERE status = 'pending'")
            pending_recharges = cursor.fetchone()[0]
        return {
            'total_users': total_users,
            'total_registrations': total_registrations,
            'pending_registrations': pending_registrations,
            'total_feedbacks': total_feedbacks,
            'pending_feedbacks': pending_feedbacks,
            'total_recharges': total_recharges,
            'pending_recharges': pending_recharges,
            'today_registrations': today_registrations,
            'today_feedbacks': today_feedbacks,
            'total_apps': total_apps,
            'today_chats': today_chats
        }

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
            cursor.execute("SELECT fr.uid, fr.content, fr.is_admin, fr.create_time, u.username, ug.name as group_name FROM feedback_replies fr JOIN users u ON fr.user_uid = u.uid LEFT JOIN user_groups ug ON ug.uid = u.group_uid WHERE fr.feedback_uid = %s ORDER BY fr.create_time ASC", (uid,))
            replies = [{'id': r['uid'], 'content': r['content'], 'username': r['username'], 'group_name': r.get('group_name') or '未分配', 'is_admin': bool(r['is_admin']), 'created_at': r['create_time'].isoformat()} for r in cursor.fetchall()]
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

    def get_user_notifications(self, user_uid: str, read_within_days: int = 0, page: int = 0, page_size: int = 0) -> list[dict[str, Any]] | dict[str, Any]:
        with self._connect() as connection:
            cursor = connection.cursor(dictionary=True)
            where = "WHERE user_uid = %s"
            params: list[Any] = [user_uid]
            if read_within_days > 0:
                where += " AND (is_read = FALSE OR (is_read = TRUE AND create_time >= DATE_SUB(NOW(), INTERVAL %s DAY)))"
                params.append(read_within_days)
            if page > 0 and page_size > 0:
                offset = (page - 1) * page_size
                cursor.execute(f"SELECT COUNT(*) as total FROM notifications {where}", tuple(params))
                total = cursor.fetchone()["total"]
                cursor.execute(f"SELECT uid, type, reference_id, title, content, is_read, create_time FROM notifications {where} ORDER BY is_read ASC, create_time DESC LIMIT %s OFFSET %s", tuple(params) + (page_size, offset))
                rows = cursor.fetchall()
                items = [{'id': row['uid'], 'type': row['type'], 'reference_id': row['reference_id'], 'title': row['title'], 'content': row['content'] or '', 'is_read': bool(row['is_read']), 'created_at': row['create_time'].isoformat()} for row in rows]
                return {"total": total, "page": page, "page_size": page_size, "items": items}
            cursor.execute(f"SELECT uid, type, reference_id, title, content, is_read, create_time FROM notifications {where} ORDER BY is_read ASC, create_time DESC LIMIT 50", tuple(params))
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

    def mark_notifications_read_by_reference(self, user_uid: str, reference_id: str) -> int:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute("UPDATE notifications SET is_read = TRUE WHERE user_uid = %s AND reference_id = %s AND is_read = FALSE", (user_uid, reference_id))
            count = cursor.rowcount
            connection.commit()
            return count

    def create_notification_for_admins(self, type: str, title: str, content: str = "", reference_id: str = "") -> None:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT u.uid FROM users u INNER JOIN user_groups ug ON ug.uid = u.group_uid WHERE ug.name IN ('管理员','超级管理员')")
            admins = cursor.fetchall()
            for (admin_uid,) in admins:
                uid = self._new_uid()
                now = self._now()
                cursor.execute("INSERT INTO notifications (uid, user_uid, type, reference_id, title, content, is_read, create_time) VALUES (%s, %s, %s, %s, %s, %s, FALSE, %s)", (uid, admin_uid, type, reference_id, title, content, now))
            connection.commit()
