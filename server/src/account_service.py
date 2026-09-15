from __future__ import annotations

import hashlib
import json
import math
import os
import re
import secrets
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal, TypedDict, cast

try:
    from .database import Database
except (ImportError, ModuleNotFoundError):
    from database import Database

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
    ws_push: Any = None

    def __init__(self, host: str | None = None, port: int | None = None, database: str | None = None, user: str | None = None, password: str | None = None) -> None:
        self.db = Database(host=host, port=port, database=database, user=user, password=password)

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
        with self.db.connect(include_db=False) as connection:
            cursor = connection.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.db.database}")
            connection.commit()
        with self.db.connect() as connection:
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
            self._init_daily_report_tables(cursor)
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
                cursor.execute("ALTER TABLE registrations ADD COLUMN amount DECIMAL(12,2) DEFAULT NULL")
            else:
                try:
                    cursor.execute("ALTER TABLE registrations MODIFY COLUMN amount DECIMAL(12,2) DEFAULT NULL")
                except Exception:
                    pass
            try:
                cursor.execute("ALTER TABLE registrations ADD COLUMN process_count INT DEFAULT 0")
            except:
                pass
            try:
                cursor.execute("SELECT is_secondary FROM registrations LIMIT 0")
                cursor.fetchall()
            except:
                try:
                    with self.db.connect() as alt_conn:
                        alt_cursor = alt_conn.cursor()
                        alt_cursor.execute("ALTER TABLE registrations ADD COLUMN is_secondary TINYINT(1) DEFAULT 0")
                        alt_conn.commit()
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
                CREATE TABLE IF NOT EXISTS announcements (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    uid VARCHAR(64) UNIQUE NOT NULL,
                    title VARCHAR(500) NOT NULL,
                    content TEXT NOT NULL,
                    publisher_uid VARCHAR(64) NOT NULL,
                    publisher_name VARCHAR(255) NOT NULL,
                    is_published BOOLEAN DEFAULT FALSE,
                    create_time DATETIME NOT NULL,
                    update_time DATETIME NOT NULL
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
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS global_chats (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    uid VARCHAR(64) UNIQUE NOT NULL,
                    sender_uid VARCHAR(64) NOT NULL,
                    message TEXT NOT NULL,
                    msg_type VARCHAR(30) DEFAULT 'text',
                    image_url VARCHAR(500) DEFAULT NULL,
                    created_at DATETIME NOT NULL,
                    FOREIGN KEY (sender_uid) REFERENCES users(uid) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
            """)
        try:
            cursor.execute("ALTER TABLE registration_chats ADD COLUMN msg_type VARCHAR(30) DEFAULT 'text'")
        except:
            pass
            try:
                cursor.execute("SELECT is_recalled FROM registration_chats LIMIT 0")
                cursor.fetchall()
            except:
                try:
                    with self.db.connect() as alt_conn:
                        alt_cursor = alt_conn.cursor()
                        alt_cursor.execute("ALTER TABLE registration_chats ADD COLUMN is_recalled TINYINT(1) DEFAULT 0")
                        alt_conn.commit()
                except:
                    pass
            try:
                cursor.execute("SELECT is_recalled FROM global_chats LIMIT 0")
                cursor.fetchall()
            except:
                try:
                    with self.db.connect() as alt_conn:
                        alt_cursor = alt_conn.cursor()
                        alt_cursor.execute("ALTER TABLE global_chats ADD COLUMN is_recalled TINYINT(1) DEFAULT 0")
                        alt_conn.commit()
                except:
                    pass
            try:
                cursor.execute("SELECT is_pinned FROM global_chats LIMIT 0")
                cursor.fetchall()
            except:
                try:
                    with self.db.connect() as alt_conn:
                        alt_cursor = alt_conn.cursor()
                        alt_cursor.execute("ALTER TABLE global_chats ADD COLUMN is_pinned TINYINT(1) DEFAULT 0")
                        alt_conn.commit()
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
                CREATE TABLE IF NOT EXISTS user_subordinates (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    uid VARCHAR(64) UNIQUE NOT NULL,
                    parent_uid VARCHAR(64) NOT NULL,
                    subordinate_uid VARCHAR(64) NOT NULL,
                    created_at DATETIME NOT NULL,
                    UNIQUE KEY uq_parent_sub (parent_uid, subordinate_uid),
                    FOREIGN KEY (parent_uid) REFERENCES users(uid) ON DELETE CASCADE,
                    FOREIGN KEY (subordinate_uid) REFERENCES users(uid) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS balance_delegations (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    uid VARCHAR(64) UNIQUE NOT NULL,
                    user_uid VARCHAR(64) NOT NULL,
                    parent_uid VARCHAR(64) NOT NULL,
                    app_uid VARCHAR(64) NOT NULL,
                    created_at DATETIME NOT NULL,
                    UNIQUE KEY uq_user_app_deleg (user_uid, app_uid),
                    FOREIGN KEY (user_uid) REFERENCES users(uid) ON DELETE CASCADE,
                    FOREIGN KEY (parent_uid) REFERENCES users(uid) ON DELETE CASCADE,
                    FOREIGN KEY (app_uid) REFERENCES running_apps(uid) ON DELETE CASCADE
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
            self._disable_feedback_permissions(cursor)
            connection.commit()
            try:
                self.create_account("admin", "admin-123456", group_uid=self._get_default_super_admin_group_uid())
            except AccountValidationError as e:
                if "用户名已存在" not in str(e):
                    raise

    def ensure_super_admin_permissions(self) -> None:
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT uid FROM user_groups WHERE name = '超级管理员'")
            row = cursor.fetchone()
            if row:
                cursor.execute("UPDATE user_groups SET permissions = %s WHERE uid = %s",
                    (json.dumps(self.PERMISSION_TREE, ensure_ascii=False), row[0]))
                connection.commit()

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
            cursor.execute("ALTER TABLE running_apps ADD COLUMN balance_round VARCHAR(20) DEFAULT ''")
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
                cursor.execute("UPDATE running_apps SET uid = %s WHERE id = %s", (self.db.new_uid(), rid))
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
        try:
            cursor.execute("ALTER TABLE feedbacks ADD COLUMN admin_unread INT DEFAULT 0")
        except:
            pass
        try:
            cursor.execute("ALTER TABLE feedbacks ADD COLUMN user_unread INT DEFAULT 0")
        except:
            pass
        try:
            cursor.execute("ALTER TABLE app_templates ADD COLUMN emphasis_config JSON DEFAULT NULL")
        except:
            pass

    def _init_daily_report_tables(self, cursor: Any) -> None:
        try:
            cursor.fetchall()
        except:
            pass
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_report_fields (
                id INT AUTO_INCREMENT PRIMARY KEY,
                label VARCHAR(255) NOT NULL,
                type ENUM('text', 'textarea', 'date', 'number', 'radio', 'checkbox', 'select') NOT NULL,
                required BOOLEAN DEFAULT FALSE,
                options JSON,
                sort_order INT DEFAULT 0
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_reports (
                id INT AUTO_INCREMENT PRIMARY KEY,
                uid VARCHAR(64) UNIQUE NOT NULL,
                user_uid VARCHAR(64) NOT NULL,
                report_date DATE NOT NULL,
                data JSON NOT NULL,
                create_time DATETIME NOT NULL,
                update_time DATETIME NOT NULL,
                UNIQUE KEY uq_user_date (user_uid, report_date)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
        """)

    DISABLED_PERM_KEYS = ['工单处理', '新建工单']

    def _sanitize_permissions(self, permissions: dict) -> dict:
        for key in self.DISABLED_PERM_KEYS:
            permissions[key] = False
        return permissions

    def _disable_feedback_permissions(self, cursor: Any) -> None:
        cursor.execute("SELECT uid, permissions FROM user_groups")
        rows = cursor.fetchall()
        if not rows:
            return
        updates: list[tuple[str, str]] = []
        for group_uid, perms_json in rows:
            if perms_json:
                perms = json.loads(perms_json)
                changed = False
                for key in self.DISABLED_PERM_KEYS:
                    if key in perms and perms[key]:
                        perms[key] = False
                        changed = True
                if changed:
                    updates.append((group_uid, json.dumps(perms, ensure_ascii=False)))
        for group_uid, perms_str in updates:
            cursor.execute("UPDATE user_groups SET permissions = %s WHERE uid = %s", (perms_str, group_uid))

    PERMISSION_TREE = {
        "账户管理": {"查看": {"下属用户": True, "其他用户": True}, "创建": True, "修改": True, "删除": True, "强制下线": True},
        "账户组管理": {"查看": True, "创建": True, "修改": True, "删除": True},
        "订单处理": {"查看": {"下属订单": True, "其他订单": True}, "处理": True, "驳回": True, "删除": True, "修改": True},
        "工单处理": {"查看": {"下属工单": True, "其他工单": True}, "回复": True, "解决": True, "删除": True},
        "APP配置": {"查看": True, "修改": True, "余额管理": True},
        "充值审批": {"查看": True, "处理": True},
        "下属管理": {"查看": True, "配置": True},
        "公告管理": {"查看": True, "编辑": True, "发布": True, "删除": True},
        "日报管理": {"查看": True, "字段配置": True, "填写报告": True, "无需填写": True},
        "新建登记": True,
        "新建工单": True,
        "充值申请": True,
        "余额查看": True,
        "聊天": True,
        "聊天室": True,
        "调整侧边栏位置": True,
    }

    def _init_default_groups(self, cursor: Any) -> None:
        now = self.db.now()
        cursor.execute("SELECT uid FROM user_groups WHERE name = '超级管理员'")
        row = cursor.fetchone()
        if not row:
            super_uid = self.db.new_uid()
            cursor.execute("INSERT INTO user_groups (uid, name, permissions, created_at) VALUES (%s, %s, %s, %s)",
                (super_uid, '超级管理员', json.dumps(self.PERMISSION_TREE, ensure_ascii=False), now))
        else:
            cursor.execute("UPDATE user_groups SET permissions = %s WHERE uid = %s",
                (json.dumps(self.PERMISSION_TREE, ensure_ascii=False), row[0]))
        cursor.execute("SELECT uid FROM users WHERE username = 'admin' AND (group_uid IS NULL OR group_uid NOT IN (SELECT uid FROM user_groups WHERE name = '超级管理员'))")
        admin_row = cursor.fetchone()
        if admin_row:
            cursor.execute("SELECT uid FROM user_groups WHERE name = '超级管理员'")
            grp = cursor.fetchone()
            if grp:
                cursor.execute("UPDATE users SET group_uid = %s WHERE username = 'admin'", (grp[0],))

    def _get_default_super_admin_group_uid(self) -> str | None:
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT uid FROM user_groups WHERE name = '超级管理员'")
            row = cursor.fetchone()
            return row[0] if row else None

    def _get_user_role(self, user_uid: str) -> str:
        with self.db.connect() as connection:
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
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT group_uid FROM users WHERE uid = %s", (user_uid,))
            user = cursor.fetchone()
            if not user or not user["group_uid"]:
                return "未分配"
            cursor.execute("SELECT name FROM user_groups WHERE uid = %s", (user["group_uid"],))
            grp = cursor.fetchone()
            return grp["name"] if grp else "未分配"

    def _get_user_permissions(self, user_uid: str) -> dict:
        with self.db.connect() as connection:
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
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT uid, name, permissions, created_at FROM user_groups ORDER BY created_at ASC")
            rows = cursor.fetchall()
        return [{
            "uid": row["uid"], "name": row["name"],
            "permissions": json.loads(row["permissions"]) if isinstance(row["permissions"], str) else row["permissions"],
            "created_at": row["created_at"].isoformat()
        } for row in rows]

    def create_user_group(self, name: str, permissions: dict) -> str:
        permissions = self._sanitize_permissions(permissions)
        uid = self.db.new_uid()
        now = self.db.now()
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT uid FROM user_groups WHERE name = %s", (name,))
            if cursor.fetchone():
                raise AccountValidationError("账户组名称已存在")
            cursor.execute("INSERT INTO user_groups (uid, name, permissions, created_at) VALUES (%s, %s, %s, %s)",
                (uid, name, json.dumps(permissions, ensure_ascii=False), now))
            connection.commit()
        return uid

    def update_user_group(self, group_uid: str, name: str | None = None, permissions: dict | None = None) -> None:
        if permissions is not None:
            permissions = self._sanitize_permissions(permissions)
        with self.db.connect() as connection:
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
        with self.db.connect() as connection:
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
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT uid FROM user_groups WHERE uid = %s", (group_uid,))
            if not cursor.fetchone():
                raise AccountError("账户组不存在")
            cursor.execute("UPDATE users SET group_uid = %s WHERE uid = %s", (group_uid, user_uid))
            connection.commit()

    def remove_user_group(self, user_uid: str) -> None:
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute("UPDATE users SET group_uid = NULL WHERE uid = %s", (user_uid,))
            connection.commit()

    # ---- Running Apps ----

    def get_running_apps(self) -> list[dict[str, Any]]:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            try:
                cursor.execute("SELECT id, uid, name, note, accent_color, icon, balance_mode, balance_round, sort_order FROM running_apps ORDER BY sort_order ASC, id ASC")
            except Exception:
                cursor.execute("SELECT id, uid, name, note, accent_color, icon FROM running_apps ORDER BY id ASC")
            rows = cursor.fetchall()
        return [{
            "id": row["id"], "uid": row["uid"], "name": row["name"],
            "note": row["note"] or "",
            "accent_color": row.get("accent_color") or "#1976D2",
            "icon": row.get("icon") or "",
            "balance_mode": row.get("balance_mode") or "",
            "balance_round": row.get("balance_round") or "",
            "template_count": self.get_app_template_count(row["id"])
        } for row in rows]

    # ---- User Balances ----

    def _ensure_user_balance(self, user_uid: str, app_uid: str) -> None:
        now = self.db.now()
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT uid FROM user_balances WHERE user_uid = %s AND app_uid = %s", (user_uid, app_uid))
            if not cursor.fetchone():
                uid = self.db.new_uid()
                cursor.execute("INSERT INTO user_balances (uid, user_uid, app_uid, balance, created_at, updated_at) VALUES (%s, %s, %s, 0, %s, %s)",
                    (uid, user_uid, app_uid, now, now))
                connection.commit()

    def get_user_balance(self, user_uid: str, app_uid: str) -> dict[str, Any] | None:
        owner_uid = self._resolve_balance_owner(user_uid, app_uid)
        self._ensure_user_balance(owner_uid, app_uid)
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT ub.balance, ra.balance_mode FROM user_balances ub JOIN running_apps ra ON ra.uid = ub.app_uid WHERE ub.user_uid = %s AND ub.app_uid = %s", (owner_uid, app_uid))
            row = cursor.fetchone()
            if not row:
                return None
            return {"balance": float(row["balance"] or 0), "balance_mode": row.get("balance_mode") or "", "owner_uid": owner_uid}

    def get_user_balances(self, user_uid: str) -> list[dict[str, Any]]:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT ub.uid, ub.app_uid, ub.balance, ra.name as app_name, ra.balance_mode, ra.icon
                FROM user_balances ub
                JOIN running_apps ra ON ra.uid = ub.app_uid
                WHERE ub.user_uid = %s
                ORDER BY ra.name ASC
            """, (user_uid,))
            rows = list(cursor.fetchall())
            seen_apps = {r["app_uid"] for r in rows}
            cursor.execute("SELECT app_uid FROM balance_delegations WHERE user_uid = %s", (user_uid,))
            for dr in cursor.fetchall():
                if dr["app_uid"] not in seen_apps:
                    seen_apps.add(dr["app_uid"])
                    cursor.execute("SELECT name, balance_mode, icon FROM running_apps WHERE uid = %s", (dr["app_uid"],))
                    ra = cursor.fetchone()
                    if ra:
                        rows.append({"uid": "", "app_uid": dr["app_uid"], "balance": 0, "app_name": ra["name"], "balance_mode": ra.get("balance_mode") or "", "icon": ra.get("icon") or ""})
        result = []
        for row in rows:
            app_uid = row["app_uid"]
            owner_uid = self._resolve_balance_owner(user_uid, app_uid)
            del_info = self.get_balance_delegation(user_uid, app_uid)
            item = {
                "id": row["uid"], "app_uid": app_uid, "app_name": row["app_name"],
                "balance": float(row["balance"] or 0), "balance_mode": row.get("balance_mode") or "",
                "icon": row.get("icon") or "", "is_delegated": bool(del_info),
                "delegated_to": del_info["parent_uid"] if del_info else None,
                "delegated_to_name": del_info["parent_name"] if del_info else None,
            }
            if owner_uid != user_uid:
                bal = self.get_user_balance(owner_uid, app_uid)
                if bal:
                    item["balance"] = bal["balance"]
                    item["is_delegated"] = True
            result.append(item)
        return result

    def get_app_user_balances(self, app_uid: str, page: int = 1, page_size: int = 20) -> dict[str, Any]:
        offset = (page - 1) * page_size
        with self.db.connect() as connection:
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
                       ub.uid as balance_uid,
                       bd.parent_uid as del_parent_uid,
                       u2.username as del_parent_name,
                       ug.name as group_name
                FROM users u
                LEFT JOIN user_balances ub ON ub.user_uid = u.uid AND ub.app_uid = %s
                LEFT JOIN balance_delegations bd ON bd.user_uid = u.uid AND bd.app_uid = %s
                LEFT JOIN users u2 ON u2.uid = bd.parent_uid
                LEFT JOIN user_groups ug ON ug.uid = u.group_uid
                ORDER BY balance DESC
                LIMIT %s OFFSET %s
            """, (app_uid, app_uid, page_size, offset))
            rows = cursor.fetchall()
            all_user_uids = [r["user_uid"] for r in rows]
            owner_map: dict[str, str] = {}
            visible_rows = {r["user_uid"]: r for r in rows}
            owner_uids: set[str] = set()
            if all_user_uids:
                placeholders = ",".join(["%s"] * len(all_user_uids))
                cursor.execute(
                    f"SELECT user_uid, parent_uid FROM balance_delegations WHERE user_uid IN ({placeholders}) AND app_uid = %s",
                    (*all_user_uids, app_uid),
                )
                deleg_rows = cursor.fetchall()
                deleg_map = {dr["user_uid"]: dr["parent_uid"] for dr in deleg_rows}
                for u_uid in all_user_uids:
                    current = u_uid
                    visited: set[str] = set()
                    resolved = u_uid
                    while current not in visited:
                        visited.add(current)
                        if current in deleg_map:
                            resolved = deleg_map[current]
                            current = resolved
                        else:
                            break
                    owner_map[u_uid] = resolved
                    if resolved != u_uid:
                        owner_uids.add(resolved)
            owner_balances: dict[str, dict[str, Any]] = {}
            if owner_uids:
                op = ",".join(["%s"] * len(owner_uids))
                cursor.execute(
                    f"SELECT ub.user_uid, ub.balance, ub.updated_at FROM user_balances ub WHERE ub.user_uid IN ({op}) AND ub.app_uid = %s",
                    (*owner_uids, app_uid),
                )
                for ob in cursor.fetchall():
                    owner_balances[ob["user_uid"]] = {
                        "balance": float(ob["balance"] or 0),
                        "updated_at": ob["updated_at"],
                    }
        items = []
        for row in rows:
            user_uid = row["user_uid"]
            owner_uid = owner_map.get(user_uid, user_uid)
            is_delegated = bool(row.get("del_parent_uid"))
            display_balance = float(row["balance"] or 0)
            display_updated_at = row["updated_at"]
            if owner_uid != user_uid:
                owner_info = owner_balances.get(owner_uid)
                if owner_info:
                    display_balance = owner_info["balance"]
                    display_updated_at = owner_info["updated_at"]
            items.append({
                "id": row["balance_uid"] or "", "user_uid": user_uid, "app_uid": app_uid,
                "username": row["username"], "balance": display_balance,
                "updated_at": display_updated_at.isoformat(),
                "is_delegated": is_delegated,
                "delegated_to": row.get("del_parent_uid") or None,
                "delegated_to_name": row.get("del_parent_name") or None,
                "group_name": row.get("group_name") or "",
            })
        return {"total": total, "page": page, "page_size": page_size, "items": items}

    def _round_balance_amount(self, app_uid: str, amount: float | None) -> float:
        if amount is None:
            return 0.0
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT balance_round FROM running_apps WHERE uid = %s", (app_uid,))
            row = cursor.fetchone()
        mode = (row or {}).get("balance_round") or ""
        if mode == "四舍五入":
            return float(math.floor(float(amount) + 0.5))
        if mode == "五舍六入":
            return float(math.ceil(float(amount) - 0.5))
        return float(amount)

    def adjust_user_balance(self, user_uid: str, app_uid: str, amount: float, note: str = "") -> dict:
        owner_uid = self._resolve_balance_owner(user_uid, app_uid)
        self._ensure_user_balance(owner_uid, app_uid)
        now = self.db.now()
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT balance FROM user_balances WHERE user_uid = %s AND app_uid = %s", (owner_uid, app_uid))
            row = cursor.fetchone()
            current = float(row["balance"] or 0) if row else 0
            new_balance = round(current + amount, 2)
            if new_balance < 0:
                ra = self.get_running_app_by_uid(app_uid)
                app_name = ra["name"] if ra else app_uid
                raise AccountValidationError(f"用户余额不足，当前余额 {current}，无法减少 {abs(amount)}")
            cursor.execute("UPDATE user_balances SET balance = %s, updated_at = %s WHERE user_uid = %s AND app_uid = %s",
                (new_balance, now, owner_uid, app_uid))
            connection.commit()
            txn_type = "recharge" if amount > 0 else "deduction"
            resolved_note = note
            if owner_uid != user_uid:
                resolved_note = f"{note}（经余额链接从用户 {user_uid} 扣除）" if note else f"经余额链接从用户 {user_uid} 扣除"
            self._record_balance_transaction(app_uid, txn_type, abs(amount),
                user_uid=owner_uid, note=resolved_note, balance_after=new_balance)
        return {"balance": new_balance, "owner_uid": owner_uid}

    def set_app_balance_mode(self, app_uid: str, balance_mode: str) -> None:
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute("UPDATE running_apps SET balance_mode = %s WHERE uid = %s", (balance_mode, app_uid))
            connection.commit()

    def check_user_balance(self, user_uid: str, app_uid: str, amount: float) -> bool:
        bal = self.get_user_balance(user_uid, app_uid)
        if not bal:
            return False
        return bal["balance"] >= amount

    def _record_balance_transaction(self, app_uid: str, type: str, amount: float, user_uid: str = "", related_uid: str = "", related_type: str = "", note: str = "", balance_after: float | None = None) -> str:
        uid = self.db.new_uid()
        now = self.db.now()
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            if balance_after is not None:
                pass
            elif user_uid:
                cursor.execute("SELECT balance FROM user_balances WHERE user_uid = %s AND app_uid = %s", (user_uid, app_uid))
                ub = cursor.fetchone()
                current = float(ub["balance"] or 0) if ub else 0
            else:
                current = 0
            if balance_after is None:
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
        with self.db.connect() as connection:
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
        if app_uid:
            owner_uid = self._resolve_balance_owner(user_uid, app_uid)
            return self.get_balance_transactions(app_uid=app_uid, user_uid=owner_uid, page=page, page_size=page_size)

        balances = self.get_user_balances(user_uid)
        if not balances:
            return {"total": 0, "page": page, "page_size": page_size, "items": []}

        pairs: list[tuple[str, str]] = []
        seen_pairs: set[tuple[str, str]] = set()
        for bal in balances:
            visible_app_uid = bal["app_uid"]
            owner_uid = self._resolve_balance_owner(user_uid, visible_app_uid)
            pair = (visible_app_uid, owner_uid)
            if pair not in seen_pairs:
                seen_pairs.add(pair)
                pairs.append(pair)

        offset = (page - 1) * page_size
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            if not pairs:
                return {"total": 0, "page": page, "page_size": page_size, "items": []}
            conditions = []
            params: list[Any] = []
            for app, owner in pairs:
                conditions.append("(bt.app_uid = %s AND bt.user_uid = %s)")
                params.extend([app, owner])
            where_clause = "WHERE " + " OR ".join(conditions)
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

    # ---- Balance Recharges ----

    def create_balance_recharge(self, user_uid: str, app_uid: str, amount: float, reason: str) -> str:
        if self.is_balance_delegated(user_uid, app_uid):
            raise AccountValidationError("您的余额已由上级管理，无法自行申请充值")
        uid = self.db.new_uid()
        now = self.db.now()
        with self.db.connect() as connection:
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
        with self.db.connect() as connection:
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
        with self.db.connect() as connection:
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
        now = self.db.now()
        with self.db.connect() as connection:
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
        with self.db.connect() as connection:
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
        user_uid = self.db.new_uid()
        password_hash = self._hash_password(password)
        now = self.db.now()
        with self.db.connect() as connection:
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
        now = self.db.now()
        with self.db.connect() as connection:
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
            session_uid = self.db.new_uid()
            cursor.execute("UPDATE users SET login_sessions = %s, last_login_time = %s, login_ip = %s, login_device = %s WHERE uid = %s", (json.dumps(sessions, ensure_ascii=False), now, login_ip, login_device, user["uid"]))
            cursor.execute("INSERT INTO login_sessions (uid, token, user_uid, create_time) VALUES (%s, %s, %s, %s)", (session_uid, token, user["uid"], now))
            connection.commit()
        return session_uid

    def get_login_session(self, session_uid: str) -> LoginSession | None:
        with self.db.connect() as connection:
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
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute("UPDATE users SET login_sessions = %s WHERE uid = %s", (json.dumps([], ensure_ascii=False), uid))
            cursor.execute("DELETE FROM login_sessions WHERE user_uid = %s", (uid,))
            connection.commit()

    # ---- Users ----

    def get_all_users(self, page: int = 1, page_size: int = 20, sort_by: str | None = None, order: str = "desc", filters: dict[str, Any] | None = None, current_user_uid: str | None = None) -> dict[str, Any]:
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
        if current_user_uid:
            perms = self._get_user_permissions(current_user_uid)
            view_perm = perms.get("账户管理", {}).get("查看", False)
            if isinstance(view_perm, dict):
                can_see_subordinates = view_perm.get("下属用户", False)
                can_see_others = view_perm.get("其他用户", False)
            else:
                can_see_subordinates = bool(view_perm)
                can_see_others = bool(view_perm)
            if not (can_see_subordinates and can_see_others):
                descendant_uids = self._get_all_descendant_uids(current_user_uid) if can_see_subordinates else []
                if can_see_subordinates and not can_see_others:
                    allowed_uids = [current_user_uid] + descendant_uids
                    placeholders = ",".join(["%s"] * len(allowed_uids))
                    where_clauses.append(f"u.uid IN ({placeholders})")
                    params.extend(allowed_uids)
                elif can_see_others and not can_see_subordinates:
                    exclude_uids = [d for d in descendant_uids if d != current_user_uid]
                    if exclude_uids:
                        placeholders = ",".join(["%s"] * len(exclude_uids))
                        where_clauses.append(f"u.uid NOT IN ({placeholders})")
                        params.extend(exclude_uids)
                else:
                    where_clauses.append("u.uid = %s")
                    params.append(current_user_uid)
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
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(f"SELECT COUNT(*) as total FROM users u LEFT JOIN user_groups ug ON ug.uid = u.group_uid {where_sql}", tuple(params))
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
        with self.db.connect() as connection:
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
            with self.db.connect() as connection:
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
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute(f"UPDATE users SET {', '.join(updates)} WHERE uid = %s", tuple(params))
            connection.commit()
            return cursor.rowcount > 0

    # ---- Registration Fields ----

    def get_registration_fields(self) -> list[dict[str, Any]]:
        with self.db.connect() as connection:
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
        with self.db.connect() as connection:
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
        uid = self.db.new_uid()
        now = self.db.now()
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute("INSERT INTO registrations (uid, user_uid, data, create_time, status, priority, template_uid, amount) VALUES (%s, %s, %s, %s, 'pending', %s, %s, %s)", (uid, user_uid, json.dumps(data, ensure_ascii=False), now, priority, template_uid, amount))
            connection.commit()
        if amount and amount > 0:
            app_name = data.get('跑步APP', '')
            if app_name:
                app_uid = None
                with self.db.connect() as conn2:
                    cur = conn2.cursor(dictionary=True)
                    cur.execute("SELECT uid FROM running_apps WHERE name = %s", (app_name,))
                    app = cur.fetchone()
                    app_uid = app["uid"] if app else None
                if app_uid:
                    self._ensure_user_balance(user_uid, app_uid)
                    self.adjust_user_balance(user_uid, app_uid, -self._round_balance_amount(app_uid, amount),
                        note=f"登记创建扣除")
        return uid

    def get_user_registrations(self, user_uid: str, page: int = 1, page_size: int = 20) -> dict[str, Any]:
        offset = (page - 1) * page_size
        with self.db.connect() as connection:
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
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT r.uid, r.data, r.create_time, r.status, r.reject_reason, r.priority, r.template_uid, r.amount, COALESCE(r.process_count, 0) as process_count, COALESCE(r.is_secondary, 0) as is_secondary, u.username, r.user_uid FROM registrations r JOIN users u ON r.user_uid = u.uid WHERE r.uid = %s", (uid,))
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
            "amount": float(row["amount"]) if row.get("amount") else None,
            "process_count": int(row.get("process_count") or 0),
            "is_secondary": bool(row.get("is_secondary") or 0),
        }

    def check_registration_exists(self, user_uid: str) -> bool:
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) as cnt FROM registrations WHERE user_uid = %s", (user_uid,))
            return cursor.fetchone()[0] > 0

    def get_latest_registration(self, user_uid: str) -> dict[str, Any] | None:
        with self.db.connect() as connection:
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
        now = self.db.now()
        old_amount = None
        old_app_name = None
        old_status = None
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT amount, status, JSON_UNQUOTE(JSON_EXTRACT(data, '$.跑步APP')) as app_name FROM registrations WHERE uid = %s", (uid,))
            reg = cursor.fetchone()
            if reg:
                old_amount = reg.get("amount")
                old_app_name = reg.get("app_name")
                old_status = reg.get("status")
            cursor = connection.cursor()
            cursor.execute("SELECT user_uid FROM registrations WHERE uid = %s", (uid,))
            row = cursor.fetchone()
            if not row or row[0] != user_uid:
                raise AccountError("登记记录不存在")
            cursor.execute("UPDATE registrations SET data = %s, create_time = %s, status = 'pending', reject_reason = NULL, priority = %s, template_uid = %s, amount = %s, is_secondary = 1 WHERE uid = %s", (json.dumps(data, ensure_ascii=False), now, priority, template_uid, amount, uid))
            connection.commit()
        if old_amount and old_app_name and old_status != 'rejected':
            app_uid = None
            with self.db.connect() as conn2:
                cur = conn2.cursor(dictionary=True)
                cur.execute("SELECT uid FROM running_apps WHERE name = %s", (old_app_name,))
                app = cur.fetchone()
                app_uid = app["uid"] if app else None
            if app_uid:
                self.adjust_user_balance(user_uid, app_uid, self._round_balance_amount(app_uid, float(old_amount)),
                    note="重新提交撤销原扣除")
        if amount and amount > 0:
            app_name = data.get('跑步APP', '')
            if app_name:
                app_uid2 = None
                with self.db.connect() as conn3:
                    cur = conn3.cursor(dictionary=True)
                    cur.execute("SELECT uid FROM running_apps WHERE name = %s", (app_name,))
                    app = cur.fetchone()
                    app_uid2 = app["uid"] if app else None
                if app_uid2:
                    self._ensure_user_balance(user_uid, app_uid2)
                    self.adjust_user_balance(user_uid, app_uid2, -self._round_balance_amount(app_uid2, amount),
                        note="登记重新提交扣除")

    def update_registration_data(self, uid: str, data: dict[str, Any], priority: str | None = None, template_uid: str | None = None, amount: float | None = None) -> None:
        old_amount = None
        old_app_name = None
        old_status = None
        user_uid = None
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT user_uid, status, amount, JSON_UNQUOTE(JSON_EXTRACT(data, '$.跑步APP')) as app_name FROM registrations WHERE uid = %s", (uid,))
            reg = cursor.fetchone()
            if not reg:
                raise AccountError("登记记录不存在")
            user_uid = reg["user_uid"]
            old_amount = reg.get("amount")
            old_app_name = reg.get("app_name")
            old_status = reg.get("status")
            updates = ["data = %s"]
            params: list[Any] = [json.dumps(data, ensure_ascii=False)]
            if priority is not None:
                updates.append("priority = %s")
                params.append(priority)
            if template_uid is not None:
                updates.append("template_uid = %s")
                params.append(template_uid)
            if amount is not None:
                updates.append("amount = %s")
                params.append(amount)
            updates.append("status = 'pending'")
            params.append(uid)
            cursor.execute(f"UPDATE registrations SET {', '.join(updates)} WHERE uid = %s", tuple(params))
            connection.commit()

        if old_amount and old_app_name and old_status != 'rejected':
            app_uid = None
            with self.db.connect() as conn2:
                cur = conn2.cursor(dictionary=True)
                cur.execute("SELECT uid FROM running_apps WHERE name = %s", (old_app_name,))
                app = cur.fetchone()
                app_uid = app["uid"] if app else None
            if app_uid and user_uid:
                try:
                    self.adjust_user_balance(user_uid, app_uid, self._round_balance_amount(app_uid, float(old_amount)),
                        note="订单修改，撤销原扣除")
                except Exception:
                    pass
        effective_amount = amount if amount is not None else old_amount
        if effective_amount and effective_amount > 0:
            app_name = data.get('跑步APP', old_app_name or '')
            if app_name:
                app_uid2 = None
                with self.db.connect() as conn3:
                    cur = conn3.cursor(dictionary=True)
                    cur.execute("SELECT uid FROM running_apps WHERE name = %s", (app_name,))
                    app = cur.fetchone()
                    app_uid2 = app["uid"] if app else None
                if app_uid2 and user_uid:
                    self._ensure_user_balance(user_uid, app_uid2)
                    self.adjust_user_balance(user_uid, app_uid2, -self._round_balance_amount(app_uid2, effective_amount),
                        note="订单修改，重新扣除")

    # ---- Admin Registrations ----

    def get_registrations(self, page: int = 1, page_size: int = 20, sort_by: str | None = None, order: str = "desc", running_app: str | None = None, username: str | None = None, current_user_uid: str | None = None, secondary: bool = False) -> dict[str, Any]:
        offset = (page - 1) * page_size
        params: list[Any] = []
        where_parts: list[str] = []
        if running_app:
            where_parts.append("JSON_EXTRACT(r.data, '$.跑步APP') = %s")
            params.append(running_app)
        if username:
            where_parts.append("u.username = %s")
            params.append(username)
        if current_user_uid:
            perms = self._get_user_permissions(current_user_uid)
            view_perm = perms.get("订单处理", {}).get("查看", False)
            if isinstance(view_perm, dict):
                can_see_subordinates = view_perm.get("下属订单", False)
                can_see_others = view_perm.get("其他订单", False)
            else:
                can_see_subordinates = bool(view_perm)
                can_see_others = bool(view_perm)
            if not (can_see_subordinates and can_see_others):
                descendant_uids = self._get_all_descendant_uids(current_user_uid) if can_see_subordinates else []
                if can_see_subordinates and not can_see_others:
                    allowed_uids = [current_user_uid] + descendant_uids
                    placeholders = ",".join(["%s"] * len(allowed_uids))
                    where_parts.append(f"r.user_uid IN ({placeholders})")
                    params.extend(allowed_uids)
                elif can_see_others and not can_see_subordinates:
                    exclude_uids = [d for d in descendant_uids if d != current_user_uid]
                    if exclude_uids:
                        placeholders = ",".join(["%s"] * len(exclude_uids))
                        where_parts.append(f"r.user_uid NOT IN ({placeholders})")
                        params.extend(exclude_uids)
                else:
                    where_parts.append("r.user_uid = %s")
                params.append(current_user_uid)
        if secondary:
            where_parts.append("COALESCE(r.is_secondary, 0) = 1")
        else:
            where_parts.append("COALESCE(r.is_secondary, 0) = 0")
        where_clause = (" WHERE " + " AND ".join(where_parts)) if where_parts else ""
        if sort_by == 'priority':
            order_clause = "FIELD(r.priority, 'high', 'medium', 'low') ASC, r.create_time DESC"
        else:
            order_clause = "CASE r.status WHEN 'pending' THEN 0 ELSE 1 END ASC, r.create_time DESC"
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            count_sql = "SELECT COUNT(*) as total FROM registrations r" + where_clause
            cursor.execute(count_sql, tuple(params))
            total = cursor.fetchone()["total"]
            sql = f"""
                SELECT r.uid, r.data, r.create_time, r.status, r.reject_reason, r.priority, r.template_uid, r.amount, COALESCE(r.process_count, 0) as process_count, COALESCE(r.is_secondary, 0) as is_secondary, u.username, at2.version_name as template_name
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
            "amount": float(row["amount"]) if row.get("amount") else None,
            "process_count": int(row.get("process_count") or 0),
            "is_secondary": bool(row.get("is_secondary") or 0),
        } for row in rows]
        return {"total": total, "page": page, "page_size": page_size, "items": items}

    def update_registration_status(self, registration_uid: str, status: str, reject_reason: str | None = None, refund_amount: float | None = None) -> None:
        reg_info = None
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT r.status as old_status, r.amount, JSON_UNQUOTE(JSON_EXTRACT(r.data, '$.跑步APP')) as app_name, r.user_uid FROM registrations r WHERE r.uid = %s", (registration_uid,))
            reg = cursor.fetchone()
            if reg:
                reg_info = {"old_status": reg["old_status"], "amount": reg.get("amount"), "app_name": reg.get("app_name"), "user_uid": reg.get("user_uid")}
            inc_count = status in ('approved', 'rejected') and reg_info and reg_info.get("old_status") not in ('approved', 'rejected')
            set_clauses = ["status = %s"]
            params: list = [status]
            if reject_reason is not None:
                set_clauses.append("reject_reason = %s")
                params.append(reject_reason)
            if inc_count:
                set_clauses.append("process_count = COALESCE(process_count, 0) + 1")
            if status == 'rejected':
                set_clauses.append("is_secondary = 1")
            elif status == 'pending':
                set_clauses.append("is_secondary = IF(COALESCE(process_count, 0) > 0, 1, COALESCE(is_secondary, 0))")
            sql = f"UPDATE registrations SET {', '.join(set_clauses)} WHERE uid = %s"
            params.append(registration_uid)
            cursor.execute(sql, tuple(params))
            connection.commit()
        if reg_info and reg_info["amount"] and reg_info["app_name"] and reg_info.get("user_uid") and status == 'rejected' and reg_info.get("old_status") != 'rejected':
            actual_refund = refund_amount if refund_amount is not None else float(reg_info["amount"])
            if actual_refund > 0:
                app_name = reg_info["app_name"]
                app_uid = None
                with self.db.connect() as conn2:
                    cur = conn2.cursor(dictionary=True)
                    cur.execute("SELECT uid FROM running_apps WHERE name = %s", (app_name,))
                    app = cur.fetchone()
                    app_uid = app["uid"] if app else None
                if app_uid and reg_info.get("user_uid"):
                    refund_value = self._round_balance_amount(app_uid, actual_refund)
                    self.adjust_user_balance(reg_info["user_uid"], app_uid, refund_value,
                        note=f"订单驳回，退回跑量{refund_value}")

    def delete_registration(self, registration_uid: str) -> bool:
        reg_info = None
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT r.amount, JSON_UNQUOTE(JSON_EXTRACT(r.data, '$.跑步APP')) as app_name, r.user_uid, r.status FROM registrations r WHERE r.uid = %s", (registration_uid,))
            reg = cursor.fetchone()
            if reg:
                reg_info = {"amount": reg.get("amount"), "app_name": reg.get("app_name"), "user_uid": reg.get("user_uid"), "status": reg.get("status")}
            cursor = connection.cursor()
            cursor.execute("DELETE FROM registrations WHERE uid = %s", (registration_uid,))
            deleted = cursor.rowcount > 0
            connection.commit()
        if deleted and reg_info and reg_info["amount"] and reg_info["app_name"] and reg_info.get("user_uid") and reg_info.get("status") == 'approved':
            with self.db.connect() as conn2:
                cur = conn2.cursor(dictionary=True)
                cur.execute("SELECT uid FROM running_apps WHERE name = %s", (reg_info["app_name"],))
                app = cur.fetchone()
                app_uid = app["uid"] if app else None
            if app_uid and reg_info.get("user_uid"):
                self.adjust_user_balance(reg_info["user_uid"], app_uid, self._round_balance_amount(app_uid, float(reg_info["amount"])),
                    note="登记记录已删除，撤销扣除")
        return deleted

    def get_registration_stats(self, secondary: bool = False, user_uid: str = '') -> list[dict[str, Any]]:
        conditions = ["COALESCE(r.is_secondary, 0) = 1" if secondary else "COALESCE(r.is_secondary, 0) = 0"]
        params: list[Any] = []
        if user_uid:
            perm_filter, perm_params = self._build_perm_filter(user_uid, "订单处理")
            perm_filter = perm_filter.replace("user_uid", "r.user_uid")
            conditions.append(perm_filter)
            params.extend(perm_params)
        where = "WHERE " + " AND ".join(conditions)
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(f"""
                SELECT JSON_UNQUOTE(JSON_EXTRACT(r.data, '$.跑步APP')) as app, r.status, COUNT(*) as cnt
                FROM registrations r {where} GROUP BY app, r.status
            """, params)
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
        uid = self.db.new_uid()
        now = self.db.now()
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute("INSERT INTO registration_chats (uid, registration_uid, sender_uid, message, created_at, msg_type) VALUES (%s, %s, %s, %s, %s, %s)", (uid, registration_uid, sender_uid, message, now, msg_type))
            cursor.execute("UPDATE registrations SET is_secondary = 1 WHERE uid = %s", (registration_uid,))
            affected = cursor.rowcount
            print(f"[CHAT] uid={uid} reg={registration_uid} secondary_set={affected}", flush=True)
            connection.commit()
        return {"id": uid, "registration_uid": registration_uid, "sender_uid": sender_uid, "message": message, "created_at": now.isoformat(), "msg_type": msg_type}

    def save_global_chat_message(self, sender_uid: str, message: str, msg_type: str = 'text', image_url: str | None = None) -> dict[str, Any]:
        uid = self.db.new_uid()
        now = self.db.now()
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute("INSERT INTO global_chats (uid, sender_uid, message, msg_type, image_url, created_at) VALUES (%s, %s, %s, %s, %s, %s)", (uid, sender_uid, message, msg_type, image_url, now))
            connection.commit()
        return {"id": uid, "sender_uid": sender_uid, "message": message, "msg_type": msg_type, "image_url": image_url, "created_at": now.isoformat()}

    def get_global_chat_history(self, limit: int = 100, before_uid: str | None = None) -> dict[str, Any]:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            params: list[Any] = []
            where = "WHERE c.is_recalled = 0"
            if before_uid:
                where += " AND c.id < (SELECT id FROM global_chats WHERE uid = %s)"
                params.append(before_uid)
            cursor.execute(f"""
                SELECT c.id AS seq, c.uid, c.sender_uid, c.message, c.msg_type, c.image_url, c.created_at, u.username,
                       CASE WHEN ug.name IN ('管理员','超级管理员') THEN TRUE ELSE FALSE END as is_admin
                FROM global_chats c
                JOIN users u ON c.sender_uid = u.uid
                LEFT JOIN user_groups ug ON ug.uid = u.group_uid
                {where}
                ORDER BY c.id DESC
                LIMIT %s
            """, tuple(params) + (limit + 1,))
            rows = cursor.fetchall()
        has_more = len(rows) > limit
        rows = list(reversed(rows[:limit]))
        items = [{
            "id": row["uid"], "sender_uid": row["sender_uid"], "username": row["username"],
            "is_admin": bool(row.get("is_admin", False)), "message": row["message"],
            "msg_type": row.get("msg_type", "text"), "image_url": row.get("image_url"),
            "created_at": row["created_at"].isoformat()
        } for row in rows]
        return {"items": items, "has_more": has_more}

    def recall_global_chat_message(self, message_uid: str, sender_uid: str) -> tuple[bool, str]:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT sender_uid, created_at, is_recalled FROM global_chats WHERE uid = %s", (message_uid,))
            msg = cursor.fetchone()
            if not msg:
                return False, "消息不存在"
            if msg['sender_uid'] != sender_uid:
                return False, "只能撤回自己发送的消息"
            if msg['is_recalled']:
                return False, "消息已被撤回"
            elapsed = (datetime.now() - msg['created_at']).total_seconds()
            if elapsed > 300:
                return False, "超过5分钟无法撤回"
            cursor.execute("UPDATE global_chats SET is_recalled = 1 WHERE uid = %s", (message_uid,))
            connection.commit()
        return True, "撤回成功"

    def pin_global_chat_message(self, message_uid: str) -> tuple[bool, str]:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT uid, message, sender_uid, is_recalled FROM global_chats WHERE uid = %s", (message_uid,))
            msg = cursor.fetchone()
            if not msg:
                return False, "消息不存在"
            if msg['is_recalled']:
                return False, "无法置顶已撤回的消息"
            cursor.execute("UPDATE global_chats SET is_pinned = 0")
            cursor.execute("UPDATE global_chats SET is_pinned = 1 WHERE uid = %s", (message_uid,))
            connection.commit()
        return True, "置顶成功"

    def unpin_global_chat_message(self) -> tuple[bool, str]:
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute("UPDATE global_chats SET is_pinned = 0 WHERE is_pinned = 1")
            affected = cursor.rowcount
            connection.commit()
        if affected == 0:
            return False, "当前没有置顶消息"
        return True, "取消置顶成功"

    def get_pinned_global_chat_message(self) -> dict[str, Any] | None:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT c.uid, c.sender_uid, c.message, c.msg_type, c.image_url, c.created_at, u.username,
                       CASE WHEN ug.name IN ('管理员','超级管理员') THEN TRUE ELSE FALSE END as is_admin
                FROM global_chats c
                JOIN users u ON c.sender_uid = u.uid
                LEFT JOIN user_groups ug ON ug.uid = u.group_uid
                WHERE c.is_pinned = 1 AND c.is_recalled = 0
                LIMIT 1
            """)
            row = cursor.fetchone()
        if not row:
            return None
        return {
            "id": row["uid"], "sender_uid": row["sender_uid"], "username": row["username"],
            "is_admin": bool(row.get("is_admin", False)), "message": row["message"],
            "msg_type": row.get("msg_type", "text"), "image_url": row.get("image_url"),
            "created_at": row["created_at"].isoformat()
        }

    def get_chat_history(self, registration_uid: str) -> list[dict[str, Any]]:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT c.uid, c.registration_uid, c.sender_uid, c.message, c.msg_type, c.created_at, c.is_recalled, u.username,
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
            "is_recalled": bool(row.get("is_recalled", 0)),
            "created_at": row["created_at"].isoformat()
        } for row in rows]

    def recall_chat_message(self, message_uid: str, sender_uid: str) -> tuple[bool, str]:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT sender_uid, created_at, is_recalled FROM registration_chats WHERE uid = %s", (message_uid,))
            msg = cursor.fetchone()
            if not msg:
                return False, "消息不存在"
            if msg['sender_uid'] != sender_uid:
                return False, "只能撤回自己发送的消息"
            if msg['is_recalled']:
                return False, "消息已被撤回"
            elapsed = (datetime.now() - msg['created_at']).total_seconds()
            if elapsed > 300:
                return False, "超过5分钟无法撤回"
            cursor.execute("UPDATE registration_chats SET is_recalled = 1 WHERE uid = %s", (message_uid,))
            connection.commit()
        return True, "撤回成功"

    # ---- Running Apps ----

    def get_running_app_by_uid(self, uid: str) -> dict[str, Any] | None:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT id, uid, name FROM running_apps WHERE uid = %s", (uid,))
            row = cursor.fetchone()
        if not row:
            return None
        return {'id': row['id'], 'uid': row['uid'], 'name': row['name']}

    def get_running_app_by_name(self, name: str) -> dict[str, Any] | None:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT id, uid, name FROM running_apps WHERE name = %s", (name,))
            row = cursor.fetchone()
        if not row:
            return None
        return {'id': row['id'], 'uid': row['uid'], 'name': row['name']}

    def create_running_app(self, name: str, note: str, accent_color: str = '#1976D2', icon: str = '', balance_mode: str = '', balance_round: str = '') -> int:
        uid = self.db.new_uid()
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute("INSERT INTO running_apps (name, note, accent_color, icon, uid, balance_mode, balance_round) VALUES (%s, %s, %s, %s, %s, %s, %s)", (name, note, accent_color, icon, uid, balance_mode, balance_round))
            connection.commit()
            return cursor.lastrowid or 0

    def update_running_app(self, app_id: int, name: str, note: str, accent_color: str, icon: str = '', balance_mode: str = '', balance_round: str = '') -> bool:
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute("UPDATE running_apps SET name = %s, note = %s, accent_color = %s, icon = %s, balance_mode = %s, balance_round = %s WHERE id = %s", (name, note, accent_color, icon, balance_mode, balance_round, app_id))
            connection.commit()
            return cursor.rowcount > 0

    def delete_running_app(self, app_id: int) -> bool:
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM running_apps WHERE id = %s", (app_id,))
            connection.commit()
            return cursor.rowcount > 0

    def bulk_create_running_apps(self, apps: list[dict[str, Any]]) -> int:
        with self.db.connect() as connection:
            cursor = connection.cursor()
            count = 0
            for app in apps:
                cursor.execute("INSERT INTO running_apps (name, note, accent_color, uid) VALUES (%s, %s, %s, %s)", (app['name'], app.get('note', ''), app.get('accent_color', '#1976D2'), self.db.new_uid()))
                count += 1
            connection.commit()
            return count

    def sort_running_apps(self, ordered_ids: list[int]) -> bool:
        with self.db.connect() as connection:
            cursor = connection.cursor()
            for idx, app_id in enumerate(ordered_ids):
                cursor.execute("UPDATE running_apps SET sort_order = %s WHERE id = %s", (idx, app_id))
            connection.commit()
        return True

    # ---- App Templates ----

    def create_app_template(self, app_id: int, version_name: str, fields: list[dict[str, Any]], emphasis_config: dict[str, Any] | None = None) -> str:
        uid = self.db.new_uid()
        now = self.db.now()
        with self.db.connect() as connection:
            cursor = connection.cursor()
            ec = json.dumps(emphasis_config, ensure_ascii=False) if emphasis_config else None
            cursor.execute("INSERT INTO app_templates (uid, app_id, version_name, fields, emphasis_config, create_time) VALUES (%s, %s, %s, %s, %s, %s)", (uid, app_id, version_name, json.dumps(fields, ensure_ascii=False), ec, now))
            connection.commit()
        return uid

    def get_app_templates(self, app_id: int) -> list[dict[str, Any]]:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT uid, app_id, version_name, fields, emphasis_config, create_time FROM app_templates WHERE app_id = %s ORDER BY create_time DESC", (app_id,))
            rows = cursor.fetchall()
        return [{
            'uid': row['uid'], 'app_id': row['app_id'],
            'version_name': row['version_name'],
            'fields': json.loads(row['fields']),
            'emphasis_config': json.loads(row['emphasis_config']) if row.get('emphasis_config') else None,
            'create_time': row['create_time'].isoformat()
        } for row in rows]

    def get_app_template(self, uid: str) -> dict[str, Any] | None:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT uid, app_id, version_name, fields, emphasis_config, create_time FROM app_templates WHERE uid = %s", (uid,))
            row = cursor.fetchone()
        if not row:
            return None
        return {
            'uid': row['uid'], 'app_id': row['app_id'],
            'version_name': row['version_name'],
            'fields': json.loads(row['fields']),
            'emphasis_config': json.loads(row['emphasis_config']) if row.get('emphasis_config') else None,
            'create_time': row['create_time'].isoformat()
        }

    def update_app_template(self, uid: str, version_name: str, fields: list[dict[str, Any]], emphasis_config: dict[str, Any] | None = None) -> bool:
        with self.db.connect() as connection:
            cursor = connection.cursor()
            ec = json.dumps(emphasis_config, ensure_ascii=False) if emphasis_config else None
            cursor.execute("UPDATE app_templates SET version_name = %s, fields = %s, emphasis_config = %s WHERE uid = %s", (version_name, json.dumps(fields, ensure_ascii=False), ec, uid))
            connection.commit()
            return cursor.rowcount > 0

    def delete_app_template(self, uid: str) -> bool:
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM app_templates WHERE uid = %s", (uid,))
            connection.commit()
            return cursor.rowcount > 0

    def clone_app_template(self, target_app_id: int, source_uid: str, version_name: str) -> str:
        source = self.get_app_template(source_uid)
        if not source:
            raise AccountError("源模板不存在")
        return self.create_app_template(target_app_id, version_name, source['fields'], source.get('emphasis_config'))

    def get_app_template_count(self, app_id: int) -> int:
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM app_templates WHERE app_id = %s", (app_id,))
            return cursor.fetchone()[0]

    # ---- Announcements ----

    def create_announcement(self, publisher_uid: str, publisher_name: str, title: str, content: str) -> str:
        uid = self.db.new_uid()
        now = self.db.now()
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute("INSERT INTO announcements (uid, title, content, publisher_uid, publisher_name, is_published, create_time, update_time) VALUES (%s, %s, %s, %s, %s, FALSE, %s, %s)",
                (uid, title, content, publisher_uid, publisher_name, now, now))
            connection.commit()
        return uid

    def get_announcements(self, include_unpublished: bool = False) -> list[dict[str, Any]]:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            if include_unpublished:
                cursor.execute("SELECT uid, title, content, publisher_name, is_published, create_time, update_time FROM announcements ORDER BY create_time DESC")
            else:
                cursor.execute("SELECT uid, title, content, publisher_name, is_published, create_time, update_time FROM announcements WHERE is_published = TRUE ORDER BY create_time DESC")
            rows = cursor.fetchall()
        return [{
            'uid': row['uid'], 'title': row['title'], 'content': row['content'],
            'publisher_name': row['publisher_name'], 'is_published': bool(row['is_published']),
            'create_time': row['create_time'].isoformat(), 'update_time': row['update_time'].isoformat()
        } for row in rows]

    def get_latest_announcement(self) -> dict[str, Any] | None:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT uid, title, content, publisher_name, create_time FROM announcements WHERE is_published = TRUE ORDER BY create_time DESC LIMIT 1")
            row = cursor.fetchone()
        if not row:
            return None
        return {
            'uid': row['uid'], 'title': row['title'], 'content': row['content'],
            'publisher_name': row['publisher_name'], 'create_time': row['create_time'].isoformat()
        }

    def get_announcement(self, uid: str) -> dict[str, Any] | None:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT uid, title, content, publisher_name, is_published, create_time, update_time FROM announcements WHERE uid = %s", (uid,))
            row = cursor.fetchone()
        if not row:
            return None
        return {
            'uid': row['uid'], 'title': row['title'], 'content': row['content'],
            'publisher_name': row['publisher_name'], 'is_published': bool(row['is_published']),
            'create_time': row['create_time'].isoformat(), 'update_time': row['update_time'].isoformat()
        }

    def update_announcement(self, uid: str, title: str, content: str) -> bool:
        now = self.db.now()
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute("UPDATE announcements SET title = %s, content = %s, update_time = %s WHERE uid = %s",
                (title, content, now, uid))
            connection.commit()
            return cursor.rowcount > 0

    def publish_announcement(self, uid: str) -> bool:
        now = self.db.now()
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute("UPDATE announcements SET is_published = TRUE, update_time = %s WHERE uid = %s", (now, uid))
            connection.commit()
            return cursor.rowcount > 0

    def unpublish_announcement(self, uid: str) -> bool:
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute("UPDATE announcements SET is_published = FALSE WHERE uid = %s", (uid,))
            connection.commit()
            return cursor.rowcount > 0

    def delete_announcement(self, uid: str) -> bool:
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM announcements WHERE uid = %s", (uid,))
            connection.commit()
            return cursor.rowcount > 0

    def _build_perm_filter(self, user_uid: str, module: str) -> tuple[str, tuple]:
        perms = self._get_user_permissions(user_uid)
        view_perm = perms.get(module, {})
        if isinstance(view_perm, dict):
            view_perm = view_perm.get("查看", False)
        if isinstance(view_perm, dict):
            can_sub = view_perm.get("下属订单", False) or view_perm.get("下属工单", False)
            can_other = view_perm.get("其他订单", False) or view_perm.get("其他工单", False)
        elif view_perm:
            can_sub = True
            can_other = True
        else:
            return "1=0", ()
        if can_sub and can_other:
            return "1=1", ()
        descendants = self._get_all_descendant_uids(user_uid)
        sub_uids = [user_uid] + list(descendants)
        if can_sub and not can_other:
            if not sub_uids:
                return "user_uid = %s", (user_uid,)
            ph = ",".join(["%s"] * len(sub_uids))
            return f"user_uid IN ({ph})", tuple(sub_uids)
        if can_other and not can_sub:
            if sub_uids:
                ph = ",".join(["%s"] * len(sub_uids))
                return f"user_uid NOT IN ({ph})", tuple(sub_uids)
            return "1=1", ()
        return "user_uid = %s", (user_uid,)

    def get_dashboard_stats(self, user_uid: str = '') -> dict[str, Any]:
        now = self.db.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        if user_uid:
            reg_where, reg_params = self._build_perm_filter(user_uid, "订单处理")
            fb_where, fb_params = self._build_perm_filter(user_uid, "工单处理")
        else:
            reg_where, reg_params = "1=1", ()
            fb_where, fb_params = "1=1", ()
        with self.db.connect() as connection:
            cursor = connection.cursor()
            def count(table: str, where: str = '', params: tuple = ()) -> int:
                sql = f"SELECT COUNT(*) FROM {table}"
                if where:
                    sql += " WHERE " + where
                cursor.execute(sql, params)
                return cursor.fetchone()[0]

            total_users = count("users")
            total_registrations = count("registrations", reg_where, reg_params)
            pending_registrations = count("registrations", f"{reg_where} AND status = 'pending' AND COALESCE(is_secondary, 0) = 0", reg_params)
            pending_secondary_registrations = count("registrations", f"{reg_where} AND status = 'pending' AND COALESCE(is_secondary, 0) = 1", reg_params)
            total_feedbacks = count("feedbacks", fb_where, fb_params)
            pending_feedbacks = count("feedbacks", f"{fb_where} AND status = 'pending'", fb_params)
            unread_feedbacks = count("feedbacks", f"{fb_where} AND COALESCE(admin_unread, 0) > 0", fb_params)
            today_registrations = count("registrations", f"{reg_where} AND create_time >= %s", reg_params + (today_start,))
            today_feedbacks = count("feedbacks", f"{fb_where} AND create_time >= %s", fb_params + (today_start,))
            total_apps = count("running_apps")
            today_chats = count("registration_chats", "created_at >= %s", (today_start,))
            total_recharges = count("balance_recharges", reg_where, reg_params)
            pending_recharges = count("balance_recharges", f"{reg_where} AND status = 'pending'", reg_params)
        return {
            'total_users': total_users,
            'total_registrations': total_registrations,
            'pending_registrations': pending_registrations,
            'pending_secondary_registrations': pending_secondary_registrations,
            'total_feedbacks': total_feedbacks,
            'pending_feedbacks': pending_feedbacks,
            'unread_feedbacks': unread_feedbacks,
            'total_recharges': total_recharges,
            'pending_recharges': pending_recharges,
            'today_registrations': today_registrations,
            'today_feedbacks': today_feedbacks,
            'total_apps': total_apps,
            'today_chats': today_chats
        }

    # ---- Feedbacks ----

    def create_feedback(self, user_uid: str, title: str, content: str) -> str:
        uid = self.db.new_uid()
        now = self.db.now()
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute("INSERT INTO feedbacks (uid, user_uid, title, content, status, create_time) VALUES (%s, %s, %s, %s, 'pending', %s)", (uid, user_uid, title, content, now))
            connection.commit()
        return uid

    def get_user_feedbacks(self, user_uid: str, page: int = 1, page_size: int = 20) -> dict[str, Any]:
        offset = (page - 1) * page_size
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT COUNT(*) as total FROM feedbacks WHERE user_uid = %s", (user_uid,))
            total = cursor.fetchone()["total"]
            cursor.execute("SELECT f.uid, f.title, f.content, f.status, f.create_time, f.user_unread, (SELECT COUNT(*) FROM feedback_replies WHERE feedback_uid = f.uid) as reply_count FROM feedbacks f WHERE f.user_uid = %s ORDER BY f.create_time DESC LIMIT %s OFFSET %s", (user_uid, page_size, offset))
            rows = cursor.fetchall()
        return {'total': total, 'page': page, 'page_size': page_size, 'items': [{
            'id': row['uid'], 'title': row['title'], 'content': row['content'],
            'status': row['status'], 'created_at': row['create_time'].isoformat(),
            'reply_count': row['reply_count'],
            'user_unread': row['user_unread'] or 0
        } for row in rows]}

    def get_all_feedbacks(self, page: int = 1, page_size: int = 20, username: str | None = None, current_user_uid: str | None = None) -> dict[str, Any]:
        offset = (page - 1) * page_size
        where_parts: list[str] = []
        params: list[Any] = []
        if username:
            where_parts.append("u.username = %s")
            params.append(username)
        if current_user_uid:
            perms = self._get_user_permissions(current_user_uid)
            view_perm = perms.get("工单处理", {}).get("查看", False)
            if isinstance(view_perm, dict):
                can_see_subordinates = view_perm.get("下属工单", False)
                can_see_others = view_perm.get("其他工单", False)
            else:
                can_see_subordinates = bool(view_perm)
                can_see_others = bool(view_perm)
            if not (can_see_subordinates and can_see_others):
                descendant_uids = self._get_all_descendant_uids(current_user_uid) if can_see_subordinates else []
                if can_see_subordinates and not can_see_others:
                    allowed_uids = [current_user_uid] + descendant_uids
                    placeholders = ",".join(["%s"] * len(allowed_uids))
                    where_parts.append(f"f.user_uid IN ({placeholders})")
                    params.extend(allowed_uids)
                elif can_see_others and not can_see_subordinates:
                    exclude_uids = [d for d in descendant_uids if d != current_user_uid]
                    if exclude_uids:
                        placeholders = ",".join(["%s"] * len(exclude_uids))
                        where_parts.append(f"f.user_uid NOT IN ({placeholders})")
                        params.extend(exclude_uids)
                else:
                    where_parts.append("f.user_uid = %s")
                    params.append(current_user_uid)
        where_clause = (" WHERE " + " AND ".join(where_parts)) if where_parts else ""
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT COUNT(*) as total FROM feedbacks f JOIN users u ON f.user_uid = u.uid" + where_clause, tuple(params))
            total = cursor.fetchone()["total"]
            cursor.execute("SELECT f.uid, f.title, f.content, f.status, f.create_time, f.admin_unread, u.username FROM feedbacks f JOIN users u ON f.user_uid = u.uid" + where_clause + " ORDER BY CASE f.status WHEN 'pending' THEN 0 ELSE 1 END ASC, f.create_time DESC LIMIT %s OFFSET %s", tuple(params) + (page_size, offset))
            rows = cursor.fetchall()
        return {'total': total, 'page': page, 'page_size': page_size, 'items': [{
            'id': row['uid'], 'username': row['username'], 'title': row['title'],
            'content': row['content'], 'status': row['status'],
            'created_at': row['create_time'].isoformat(),
            'admin_unread': row['admin_unread'] or 0
        } for row in rows]}

    def get_feedback_detail(self, uid: str) -> dict[str, Any] | None:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT f.uid, f.title, f.content, f.status, f.create_time, f.user_uid, u.username FROM feedbacks f JOIN users u ON f.user_uid = u.uid WHERE f.uid = %s", (uid,))
            row = cursor.fetchone()
            if not row:
                return None
            cursor.execute("SELECT fr.uid, fr.content, fr.is_admin, fr.create_time, u.username, ug.name as group_name FROM feedback_replies fr JOIN users u ON fr.user_uid = u.uid LEFT JOIN user_groups ug ON ug.uid = u.group_uid WHERE fr.feedback_uid = %s ORDER BY fr.create_time ASC", (uid,))
            replies = [{'id': r['uid'], 'content': r['content'], 'username': r['username'], 'group_name': r.get('group_name') or '未分配', 'is_admin': bool(r['is_admin']), 'created_at': r['create_time'].isoformat()} for r in cursor.fetchall()]
        return {'id': row['uid'], 'username': row['username'], 'user_uid': row['user_uid'], 'title': row['title'], 'content': row['content'], 'status': row['status'], 'created_at': row['create_time'].isoformat(), 'replies': replies}

    def add_feedback_reply(self, feedback_uid: str, user_uid: str, content: str, is_admin: bool = False) -> str:
        uid = self.db.new_uid()
        now = self.db.now()
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute("INSERT INTO feedback_replies (uid, feedback_uid, user_uid, is_admin, content, create_time) VALUES (%s, %s, %s, %s, %s, %s)", (uid, feedback_uid, user_uid, is_admin, content, now))
            cursor.execute("SELECT user_uid FROM feedbacks WHERE uid = %s", (feedback_uid,))
            fb = cursor.fetchone()
            if fb and fb[0] == user_uid:
                cursor.execute("UPDATE feedbacks SET admin_unread = COALESCE(admin_unread, 0) + 1 WHERE uid = %s", (feedback_uid,))
            else:
                cursor.execute("UPDATE feedbacks SET user_unread = COALESCE(user_unread, 0) + 1 WHERE uid = %s", (feedback_uid,))
            connection.commit()
        return uid

    def update_feedback_status(self, uid: str, status: str) -> None:
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute("UPDATE feedbacks SET status = %s WHERE uid = %s", (status, uid))
            connection.commit()

    def delete_feedback(self, uid: str) -> None:
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM feedback_replies WHERE feedback_uid = %s", (uid,))
            cursor.execute("DELETE FROM feedbacks WHERE uid = %s", (uid,))
            connection.commit()

    # ---- Notification: Aggregated pending items from business tables ----

    def get_pending_items_for_admin(self, page: int = 1, page_size: int = 20, user_uid: str = '') -> dict[str, Any]:
        reg_filter, reg_params_t = ("1=1", ()) if not user_uid else self._build_perm_filter(user_uid, "订单处理")
        fb_filter, fb_params_t = ("1=1", ()) if not user_uid else self._build_perm_filter(user_uid, "工单处理")
        reg_cond = f"status = 'pending' AND {reg_filter}".replace("user_uid", "r.user_uid")
        fb_cond = f"status = 'pending' AND {fb_filter}".replace("user_uid", "f.user_uid")
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)

            q_reg = f"SELECT uid as id, 'pending_registration' as type, uid as reference_id, '新订单申请' as title, CONCAT('用户 ', (SELECT u.username FROM users u WHERE u.uid = r.user_uid), ' 提交了新订单') as content, create_time as created_at FROM registrations r WHERE {reg_cond}"
            q_fb = f"SELECT uid as id, 'pending_feedback' as type, uid as reference_id, '新工单' as title, CONCAT('用户 ', (SELECT u.username FROM users u WHERE u.uid = f.user_uid), ' 提交了工单: ', f.title) as content, create_time as created_at FROM feedbacks f WHERE {fb_cond}"
            q_recharge = "SELECT br.uid as id, 'pending_recharge' as type, br.uid as reference_id, '新充值申请' as title, CONCAT('用户 ', (SELECT u.username FROM users u WHERE u.uid = br.user_uid), ' 申请充值 ', br.amount, ' 元') as content, br.created_at FROM balance_recharges br WHERE status = 'pending'"

            all_params = reg_params_t + fb_params_t
            union = f"({q_reg}) UNION ALL ({q_fb}) UNION ALL ({q_recharge}) ORDER BY created_at DESC"

            cursor.execute(f"SELECT COUNT(*) as total FROM ({union}) t", all_params)
            total = cursor.fetchone()["total"]

            offset = (page - 1) * page_size
            cursor.execute(f"SELECT * FROM ({union}) t LIMIT %s OFFSET %s", all_params + (page_size, offset))
            items = list(cursor.fetchall())
            for item in items:
                if item.get('created_at'):
                    item['created_at'] = item['created_at'].isoformat()

            cursor.execute(f"SELECT COUNT(*) as cnt FROM registrations r WHERE {reg_cond}", reg_params_t)
            pending_regs = cursor.fetchone()["cnt"]
            cursor.execute(f"SELECT COUNT(*) as cnt FROM feedbacks f WHERE {fb_cond}", fb_params_t)
            pending_fbs = cursor.fetchone()["cnt"]
            cursor.execute("SELECT COUNT(*) as cnt FROM balance_recharges WHERE status = 'pending'")
            pending_recs = cursor.fetchone()["cnt"]

            return {
                "total": total,
                "page": page,
                "page_size": page_size,
                "items": items,
                "counts": {
                    "订单处理": pending_regs,
                    "工单处理": pending_fbs,
                    "充值审批": pending_recs,
                }
            }

    def get_pending_notification_count_for_admin(self) -> int:
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM registrations WHERE status = 'pending'")
            r = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM feedbacks WHERE status = 'pending'")
            f = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM balance_recharges WHERE status = 'pending'")
            b = cursor.fetchone()[0]
            return r + f + b

    # ---- Notifications (actual notification records, not pending items) ----

    def create_notification(self, user_uid: str, ntype: str, title: str, content: str = "", reference_id: str = "") -> str:
        uid = self.db.new_uid()
        now = self.db.now()
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute("INSERT INTO notifications (uid, user_uid, type, reference_id, title, content, is_read, create_time) VALUES (%s, %s, %s, %s, %s, %s, FALSE, %s)",
                (uid, user_uid, ntype, reference_id, title, content, now))
            connection.commit()
        if AccountService.ws_push:
            AccountService.ws_push(user_uid, {'type': 'notification_update', 'id': uid, 'status': 'to_unread', 'notif_type': ntype, 'title': title, 'content': content, 'reference_id': reference_id, 'created_at': now.isoformat()})
        return uid

    def create_notification_for_admins(self, ntype: str, title: str, content: str = "", reference_id: str = "") -> None:
        ws_pushes: list[tuple[str, dict]] = []
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT u.uid FROM users u INNER JOIN user_groups ug ON ug.uid = u.group_uid WHERE ug.name IN ('管理员','超级管理员')")
            admins = cursor.fetchall()
            for (admin_uid,) in admins:
                uid = self.db.new_uid()
                now = self.db.now()
                cursor.execute("INSERT INTO notifications (uid, user_uid, type, reference_id, title, content, is_read, create_time) VALUES (%s, %s, %s, %s, %s, %s, FALSE, %s)",
                    (uid, admin_uid, ntype, reference_id, title, content, now))
                ws_pushes.append((admin_uid, {'type': 'notification_update', 'id': uid, 'status': 'to_unread', 'notif_type': ntype, 'title': title, 'content': content, 'reference_id': reference_id, 'created_at': now.isoformat()}))
            connection.commit()
        if AccountService.ws_push:
            for admin_uid, data in ws_pushes:
                AccountService.ws_push(admin_uid, data)

    def get_user_notifications(self, user_uid: str, page: int = 1, page_size: int = 20) -> dict[str, Any]:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT COUNT(*) as total FROM notifications WHERE user_uid = %s", (user_uid,))
            total = cursor.fetchone()["total"]
            offset = (page - 1) * page_size
            cursor.execute("SELECT uid, type, reference_id, title, content, is_read, create_time FROM notifications WHERE user_uid = %s ORDER BY is_read ASC, create_time DESC LIMIT %s OFFSET %s", (user_uid, page_size, offset))
            rows = cursor.fetchall()
            items = [{'id': row['uid'], 'type': row['type'], 'reference_id': row['reference_id'], 'title': row['title'], 'content': row['content'] or '', 'is_read': bool(row['is_read']), 'created_at': row['create_time'].isoformat()} for row in rows]
            return {"total": total, "page": page, "page_size": page_size, "items": items}

    def get_unread_notification_count(self, user_uid: str) -> int:
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM notifications WHERE user_uid = %s AND is_read = FALSE", (user_uid,))
            row = cursor.fetchone()
            return row[0] if row else 0

    def mark_notification_read(self, uid: str) -> None:
        user_uid = ''
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute("UPDATE notifications SET is_read = TRUE WHERE uid = %s", (uid,))
            cursor.execute("SELECT user_uid FROM notifications WHERE uid = %s", (uid,))
            row = cursor.fetchone()
            if row:
                user_uid = row[0]
            connection.commit()
        if AccountService.ws_push and user_uid:
            AccountService.ws_push(user_uid, {'type': 'notification_update', 'id': uid, 'status': 'to_read'})

    def mark_all_notifications_read(self, user_uid: str) -> None:
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute("UPDATE notifications SET is_read = TRUE WHERE user_uid = %s", (user_uid,))
            connection.commit()
        if AccountService.ws_push:
            AccountService.ws_push(user_uid, {'type': 'notification_update', 'status': 'all_read'})

    def mark_notifications_read_by_reference(self, user_uid: str, reference_id: str) -> int:
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute("UPDATE notifications SET is_read = TRUE WHERE user_uid = %s AND reference_id = %s AND is_read = FALSE", (user_uid, reference_id))
            count = cursor.rowcount
            connection.commit()
            return count

    def mark_notifications_read_by_types(self, user_uid: str, types: list[str]) -> int:
        if not types:
            return 0
        placeholders = ','.join(['%s'] * len(types))
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute(f"UPDATE notifications SET is_read = TRUE WHERE user_uid = %s AND type IN ({placeholders}) AND is_read = FALSE", [user_uid] + types)
            count = cursor.rowcount
            connection.commit()
        if AccountService.ws_push and count > 0:
            AccountService.ws_push(user_uid, {'type': 'notification_update', 'status': 'all_read'})
        return count

    # ---- Subordinate Management ----

    def is_balance_delegated(self, user_uid: str, app_uid: str = "") -> bool:
        with self.db.connect() as connection:
            cursor = connection.cursor()
            if app_uid:
                cursor.execute("SELECT uid FROM balance_delegations WHERE user_uid = %s AND app_uid = %s LIMIT 1", (user_uid, app_uid))
            else:
                cursor.execute("SELECT uid FROM balance_delegations WHERE user_uid = %s LIMIT 1", (user_uid,))
            return cursor.fetchone() is not None

    def is_balance_delegated_for_any_app(self, user_uid: str) -> list[str]:
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT app_uid FROM balance_delegations WHERE user_uid = %s", (user_uid,))
            return [row[0] for row in cursor.fetchall()]

    def _resolve_balance_owner(self, user_uid: str, app_uid: str) -> str:
        visited: set[str] = set()
        current = user_uid
        with self.db.connect() as connection:
            while current not in visited:
                visited.add(current)
                cursor = connection.cursor()
                cursor.execute("SELECT parent_uid FROM balance_delegations WHERE user_uid = %s AND app_uid = %s LIMIT 1", (current, app_uid))
                row = cursor.fetchone()
                if not row:
                    break
                current = row[0]
        return current

    def get_balance_delegation(self, user_uid: str, app_uid: str = "") -> dict[str, Any] | None:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            if app_uid:
                cursor.execute("SELECT bd.uid, bd.user_uid, bd.parent_uid, bd.app_uid, bd.created_at, u.username as parent_name FROM balance_delegations bd JOIN users u ON u.uid = bd.parent_uid WHERE bd.user_uid = %s AND bd.app_uid = %s LIMIT 1", (user_uid, app_uid))
            else:
                cursor.execute("SELECT bd.uid, bd.user_uid, bd.parent_uid, bd.app_uid, bd.created_at, u.username as parent_name FROM balance_delegations bd JOIN users u ON u.uid = bd.parent_uid WHERE bd.user_uid = %s LIMIT 1", (user_uid,))
            row = cursor.fetchone()
            if not row:
                return None
            return {"uid": row["uid"], "user_uid": row["user_uid"], "parent_uid": row["parent_uid"], "app_uid": row["app_uid"], "parent_name": row["parent_name"], "created_at": row["created_at"].isoformat()}

    def get_subordinates(self, parent_uid: str) -> list[dict[str, Any]]:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT us.uid as relation_id, us.subordinate_uid, us.created_at,
                       u.username, ug.name as group_name
                FROM user_subordinates us
                JOIN users u ON u.uid = us.subordinate_uid
                LEFT JOIN user_groups ug ON ug.uid = u.group_uid
                WHERE us.parent_uid = %s
                ORDER BY us.created_at ASC
            """, (parent_uid,))
            rows = cursor.fetchall()
            sub_uids = [r["subordinate_uid"] for r in rows]
            delegations: dict[str, dict[str, Any]] = {}
            if sub_uids:
                placeholders = ",".join(["%s"] * len(sub_uids))
                cursor.execute(f"SELECT bd.user_uid, bd.parent_uid, u.username as parent_name FROM balance_delegations bd JOIN users u ON u.uid = bd.parent_uid WHERE bd.user_uid IN ({placeholders})", tuple(sub_uids))
                for dr in cursor.fetchall():
                    delegations[dr["user_uid"]] = {"parent_uid": dr["parent_uid"], "parent_name": dr["parent_name"]}
        result = []
        for row in rows:
            sub_uid = row["subordinate_uid"]
            del_info = delegations.get(sub_uid)
            result.append({
                "relation_id": row["relation_id"],
                "uid": sub_uid,
                "username": row["username"],
                "group_name": row["group_name"] or "未分配",
                "created_at": row["created_at"].isoformat(),
                "is_delegated": bool(del_info),
                "delegated_to": del_info["parent_uid"] if del_info else None,
                "delegated_to_name": del_info["parent_name"] if del_info else None,
            })
        return result

    def add_subordinate(self, parent_uid: str, subordinate_uid: str) -> str:
        if parent_uid == subordinate_uid:
            raise AccountValidationError("不能将自己添加为自己的下属")
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT uid FROM user_subordinates WHERE parent_uid = %s AND subordinate_uid = %s LIMIT 1", (parent_uid, subordinate_uid))
            if cursor.fetchone():
                raise AccountValidationError("该用户已经是您的下属")
            cursor.execute("SELECT uid FROM user_subordinates WHERE subordinate_uid = %s LIMIT 1", (subordinate_uid,))
            if cursor.fetchone():
                raise AccountValidationError("该用户已是其他人的下属，不能重复添加")
            ancestors = self._get_all_descendant_uids(subordinate_uid)
            if parent_uid in ancestors:
                raise AccountValidationError("不能将上级账户添加为自己的下属")
            cursor.execute("SELECT uid FROM users WHERE uid = %s", (subordinate_uid,))
            if not cursor.fetchone():
                raise AccountValidationError("目标用户不存在")
            uid = self.db.new_uid()
            now = self.db.now()
            cursor.execute("INSERT INTO user_subordinates (uid, parent_uid, subordinate_uid, created_at) VALUES (%s, %s, %s, %s)", (uid, parent_uid, subordinate_uid, now))
            connection.commit()
        return uid

    def remove_subordinate(self, parent_uid: str, subordinate_uid: str) -> bool:
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM balance_delegations WHERE user_uid = %s AND parent_uid = %s", (subordinate_uid, parent_uid))
            cursor.execute("DELETE FROM user_subordinates WHERE parent_uid = %s AND subordinate_uid = %s", (parent_uid, subordinate_uid))
            connection.commit()
            return cursor.rowcount > 0

    def _get_all_descendant_uids(self, parent_uid: str) -> list[str]:
        result: list[str] = []
        queue: list[str] = [parent_uid]
        visited: set[str] = set()
        with self.db.connect() as connection:
            while queue:
                current = queue.pop(0)
                if current in visited:
                    continue
                visited.add(current)
                if current != parent_uid:
                    result.append(current)
                cursor = connection.cursor()
                cursor.execute("SELECT subordinate_uid FROM user_subordinates WHERE parent_uid = %s", (current,))
                for (sub_uid,) in cursor.fetchall():
                    if sub_uid not in visited:
                        queue.append(sub_uid)
        return result

    def get_subordinate_tree(self, parent_uid: str) -> list[dict[str, Any]]:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            all_sub_uids: list[str] = []
            queue: list[str] = [parent_uid]
            visited: set[str] = set()
            while queue:
                current = queue.pop(0)
                if current in visited:
                    continue
                visited.add(current)
                if current != parent_uid:
                    all_sub_uids.append(current)
                cursor.execute("SELECT subordinate_uid FROM user_subordinates WHERE parent_uid = %s", (current,))
                for (sub_uid,) in cursor.fetchall():
                    if sub_uid not in visited:
                        queue.append(sub_uid)
            delegations: dict[str, dict[str, Any]] = {}
            if all_sub_uids:
                placeholders = ",".join(["%s"] * len(all_sub_uids))
                cursor.execute(f"SELECT bd.user_uid, bd.parent_uid, bd.app_uid, u.username as parent_name FROM balance_delegations bd JOIN users u ON u.uid = bd.parent_uid WHERE bd.user_uid IN ({placeholders})", tuple(all_sub_uids))
                for dr in cursor.fetchall():
                    delegations[dr["user_uid"]] = {"parent_uid": dr["parent_uid"], "parent_name": dr["parent_name"], "app_uid": dr["app_uid"]}
            return self._build_tree(connection, parent_uid, delegations)

    def _build_tree(self, connection: Any, parent_uid: str, delegations: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT us.subordinate_uid, us.parent_uid, u.username,
                   ug.name as group_name
            FROM user_subordinates us
            JOIN users u ON u.uid = us.subordinate_uid
            LEFT JOIN user_groups ug ON ug.uid = u.group_uid
            WHERE us.parent_uid = %s
            ORDER BY us.created_at ASC
        """, (parent_uid,))
        direct_subs = cursor.fetchall()
        result: list[dict[str, Any]] = []
        for sub in direct_subs:
            sub_uid = sub["subordinate_uid"]
            del_info = delegations.get(sub_uid)
            item: dict[str, Any] = {
                "uid": sub_uid,
                "username": sub["username"],
                "group_name": sub["group_name"] or "未分配",
                "is_delegated": bool(del_info),
                "delegated_to": del_info["parent_uid"] if del_info else None,
                "delegated_to_name": del_info["parent_name"] if del_info else None,
                "delegated_app_uid": del_info["app_uid"] if del_info else None,
                "children": self._build_tree(connection, sub_uid, delegations),
            }
            result.append(item)
        return result

    def get_parent_of_subordinate(self, subordinate_uid: str) -> str | None:
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT parent_uid FROM user_subordinates WHERE subordinate_uid = %s LIMIT 1", (subordinate_uid,))
            row = cursor.fetchone()
            return row[0] if row else None

    def get_sibling_subordinates(self, parent_uid: str) -> list[dict[str, Any]]:
        all_desc = self._get_all_descendant_uids(parent_uid)
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            result = []
            for uid in all_desc:
                cursor.execute("SELECT username FROM users WHERE uid = %s", (uid,))
                user = cursor.fetchone()
                if user:
                    result.append({"uid": uid, "username": user["username"]})
        return result

    # ---- Balance Delegation ----

    def create_balance_delegation(self, user_uid: str, parent_uid: str, app_uid: str) -> str:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT uid FROM user_subordinates WHERE parent_uid = %s AND subordinate_uid = %s LIMIT 1", (parent_uid, user_uid))
            if not cursor.fetchone():
                raise AccountValidationError("该用户不是您的下属，无法建立余额链接")
            cursor.execute("SELECT uid FROM balance_delegations WHERE user_uid = %s AND app_uid = %s LIMIT 1", (user_uid, app_uid))
            if cursor.fetchone():
                raise AccountValidationError("该用户在此APP已有余额链接")
            ancestor = parent_uid
            visited: set[str] = {user_uid}
            while ancestor and ancestor not in visited:
                visited.add(ancestor)
                cursor.execute("SELECT parent_uid FROM balance_delegations WHERE user_uid = %s AND app_uid = %s LIMIT 1", (ancestor, app_uid))
                row = cursor.fetchone()
                ancestor = row["parent_uid"] if row else None
            if ancestor and ancestor in visited:
                raise AccountValidationError("不能建立循环余额链接")
            uid = self.db.new_uid()
            now = self.db.now()
            cursor.execute("INSERT INTO balance_delegations (uid, user_uid, parent_uid, app_uid, created_at) VALUES (%s, %s, %s, %s, %s)", (uid, user_uid, parent_uid, app_uid, now))
            connection.commit()
        return uid

    def remove_balance_delegation(self, user_uid: str, app_uid: str) -> bool:
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM balance_delegations WHERE user_uid = %s AND app_uid = %s", (user_uid, app_uid))
            connection.commit()
            return cursor.rowcount > 0

    def get_delegated_users(self, parent_uid: str) -> list[dict[str, Any]]:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT bd.uid, bd.user_uid, bd.app_uid, bd.created_at,
                       u.username, ra.name as app_name
                FROM balance_delegations bd
                JOIN users u ON u.uid = bd.user_uid
                JOIN running_apps ra ON ra.uid = bd.app_uid
                WHERE bd.parent_uid = %s
                ORDER BY bd.created_at ASC
            """, (parent_uid,))
            rows = cursor.fetchall()
        return [{"uid": row["uid"], "user_uid": row["user_uid"], "username": row["username"], "app_uid": row["app_uid"], "app_name": row["app_name"], "created_at": row["created_at"].isoformat()} for row in rows]

    def get_user_balance_delegations(self, user_uid: str) -> list[dict[str, Any]]:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT bd.uid, bd.parent_uid, bd.app_uid, bd.created_at,
                       u.username as parent_name, ra.name as app_name
                FROM balance_delegations bd
                JOIN users u ON u.uid = bd.parent_uid
                JOIN running_apps ra ON ra.uid = bd.app_uid
                WHERE bd.user_uid = %s
                ORDER BY bd.created_at ASC
            """, (user_uid,))
            rows = cursor.fetchall()
        return [{"uid": row["uid"], "parent_uid": row["parent_uid"], "parent_name": row["parent_name"], "app_uid": row["app_uid"], "app_name": row["app_name"], "created_at": row["created_at"].isoformat()} for row in rows]

    # ─── 日报管理 ───────────────────────────────────────────────

    def get_daily_report_fields(self) -> list[dict[str, Any]]:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM daily_report_fields ORDER BY sort_order ASC, id ASC")
            rows = cursor.fetchall()
        result = []
        for row in rows:
            options = row.get("options")
            if options and isinstance(options, str):
                options = json.loads(options)
            result.append({
                "id": row["id"],
                "label": row["label"],
                "type": row["type"],
                "required": bool(row["required"]),
                "options": options or [],
                "sort_order": row["sort_order"],
            })
        return result

    def save_daily_report_fields(self, fields: list[dict[str, Any]]) -> None:
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM daily_report_fields")
            for i, field in enumerate(fields):
                options = field.get("options")
                if options is not None and not isinstance(options, str):
                    options = json.dumps(options, ensure_ascii=False)
                cursor.execute(
                    "INSERT INTO daily_report_fields (label, type, required, options, sort_order) VALUES (%s, %s, %s, %s, %s)",
                    (field["label"], field["type"], field.get("required", False), options, i)
                )
            connection.commit()

    def get_daily_report_status(self, user_uid: str, report_date: str) -> dict[str, Any] | None:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT uid, data, create_time, update_time FROM daily_reports WHERE user_uid = %s AND report_date = %s", (user_uid, report_date))
            row = cursor.fetchone()
        if not row:
            return None
        data = row["data"]
        if isinstance(data, str):
            data = json.loads(data)
        return {
            "uid": row["uid"],
            "data": data,
            "create_time": row["create_time"].isoformat() if row["create_time"] else None,
            "update_time": row["update_time"].isoformat() if row["update_time"] else None,
        }

    def submit_daily_report(self, user_uid: str, data: dict[str, Any], report_date: str) -> str:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT uid FROM daily_reports WHERE user_uid = %s AND report_date = %s", (user_uid, report_date))
            existing = cursor.fetchone()
            now = self.db.now()
            data_json = json.dumps(data, ensure_ascii=False)
            if existing:
                cursor.execute("UPDATE daily_reports SET data = %s, update_time = %s WHERE uid = %s", (data_json, now, existing["uid"]))
                connection.commit()
                return existing["uid"]
            else:
                uid = self.db.new_uid()
                cursor.execute(
                    "INSERT INTO daily_reports (uid, user_uid, report_date, data, create_time, update_time) VALUES (%s, %s, %s, %s, %s, %s)",
                    (uid, user_uid, report_date, data_json, now, now)
                )
                connection.commit()
                return uid

    def get_daily_reports(self, page: int = 1, page_size: int = 20, date_from: str | None = None, date_to: str | None = None) -> dict[str, Any]:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            where = []
            params: list[Any] = []
            if date_from:
                where.append("dr.report_date >= %s")
                params.append(date_from)
            if date_to:
                where.append("dr.report_date <= %s")
                params.append(date_to)
            where_sql = ("WHERE " + " AND ".join(where)) if where else ""
            cursor.execute(f"SELECT COUNT(*) as total FROM daily_reports dr {where_sql}", params)
            total = cursor.fetchone()["total"]
            offset = (page - 1) * page_size
            cursor.execute(f"""
                SELECT dr.uid, dr.user_uid, dr.report_date, dr.data, dr.create_time, dr.update_time,
                       u.username
                FROM daily_reports dr
                JOIN users u ON u.uid = dr.user_uid
                {where_sql}
                ORDER BY dr.report_date DESC, dr.create_time DESC
                LIMIT %s OFFSET %s
            """, params + [page_size, offset])
            rows = cursor.fetchall()
        items = []
        for row in rows:
            data = row["data"]
            if isinstance(data, str):
                data = json.loads(data)
            items.append({
                "uid": row["uid"],
                "user_uid": row["user_uid"],
                "username": row["username"],
                "report_date": row["report_date"].isoformat() if row["report_date"] else None,
                "data": data,
                "create_time": row["create_time"].isoformat() if row["create_time"] else None,
                "update_time": row["update_time"].isoformat() if row["update_time"] else None,
            })
        return {"items": items, "total": total}

    def get_daily_report_statistics(self, report_date: str) -> dict[str, int]:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT ug.permissions FROM user_groups ug
                JOIN users u ON u.group_uid = ug.uid
            """)
            all_user_groups = cursor.fetchall()
            should_fill = 0
            for ug in all_user_groups:
                perms = ug["permissions"]
                if isinstance(perms, str):
                    perms = json.loads(perms)
                if not perms:
                    continue
                daily = perms.get("日报管理")
                if isinstance(daily, dict):
                    has_fill = daily.get("填写报告", False)
                    has_exempt = daily.get("无需填写", False)
                    if has_fill and not has_exempt:
                        should_fill += 1
            cursor.execute("SELECT COUNT(*) as cnt FROM daily_reports WHERE report_date = %s", (report_date,))
            filled = cursor.fetchone()["cnt"]
        return {
            "should_fill": should_fill,
            "filled": filled,
            "unfilled": max(0, should_fill - filled),
        }

    def get_daily_reports_for_export(self, date_from: str, date_to: str) -> list[dict[str, Any]]:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT dr.report_date, dr.data, u.username
                FROM daily_reports dr
                JOIN users u ON u.uid = dr.user_uid
                WHERE dr.report_date >= %s AND dr.report_date <= %s
                ORDER BY dr.report_date DESC, u.username ASC
            """, (date_from, date_to))
            rows = cursor.fetchall()
        items = []
        for row in rows:
            data = row["data"]
            if isinstance(data, str):
                data = json.loads(data)
            items.append({
                "username": row["username"],
                "report_date": row["report_date"].isoformat() if row["report_date"] else None,
                "data": data,
            })
        return items
