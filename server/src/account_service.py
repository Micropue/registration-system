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
    account_type: AccountType


class AccountService:
    """Account operations backed by the users and login_sessions MySQL tables."""

    _PASSWORD_PATTERN = re.compile(r"^[A-Za-z0-9-]+$")
    _ACCOUNT_TYPES: set[str] = {"admin", "default"}

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        database: str | None = None,
        user: str | None = None,
        password: str | None = None,
    ) -> None:
        env_host, env_port = self._parse_db_url(os.getenv("DB_URL", ""))
        self.host = host or os.getenv("DB_HOST") or env_host or "localhost"
        self.port = port or int(os.getenv("DB_PORT") or env_port or "3308")
        self.database = database or os.getenv("DB_NAME", "huhurun")
        self.user = user or os.getenv("DB_USERNAME", "root")
        self.password = password or os.getenv("DB_PASSWORD", "root")

    def create_account(
        self,
        username: str,
        password: str,
        account_type: AccountType = "default",
        login_ip: str = "",
    ) -> str:
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
                raise AccountValidationError("username already exists")

            cursor.execute(
                """
                INSERT INTO users
                    (uid, username, password, login_sessions, type, register_time,
                     last_login_time, login_ip)
                VALUES
                    (%s, %s, %s, %s, %s, %s, NULL, %s)
                """,
                (
                    user_uid,
                    username,
                    password_hash,
                    json.dumps([], ensure_ascii=False),
                    account_type,
                    now,
                    login_ip,
                ),
            )
            connection.commit()

        return user_uid

    def login(self, username: str, password: str, login_ip: str = "") -> str:
        password_hash = self._hash_password(password)
        session_uid = self._new_uid()
        token = secrets.token_hex(32)
        now = self._now()

        with self._connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT uid, password, login_sessions, type
                FROM users
                WHERE username = %s
                LIMIT 1
                """,
                (username,),
            )
            user = cast(UserRow | None, cursor.fetchone())
            if user is None or user["password"] != password_hash:
                raise AccountAuthError("invalid username or password")

            sessions = self._parse_sessions(user["login_sessions"])
            sessions.append(token)

            cursor.execute(
                """
                UPDATE users
                SET login_sessions = %s,
                    last_login_time = %s,
                    login_ip = %s
                WHERE uid = %s
                """,
                (json.dumps(sessions, ensure_ascii=False), now, login_ip, user["uid"]),
            )
            cursor.execute(
                """
                INSERT INTO login_sessions (uid, token, user_uid, create_time)
                VALUES (%s, %s, %s, %s)
                """,
                (session_uid, token, user["uid"], now),
            )
            connection.commit()

        return session_uid

    def is_logged_in(self, session_uid: str) -> bool:
        return self.get_login_session(session_uid) is not None

    def get_login_session(self, session_uid: str) -> LoginSession | None:
        with self._connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    ls.uid AS session_uid,
                    ls.token,
                    ls.user_uid,
                    u.login_sessions,
                    u.type
                FROM login_sessions ls
                INNER JOIN users u ON u.uid = ls.user_uid
                WHERE ls.uid = %s
                LIMIT 1
                """,
                (session_uid,),
            )
            row = cast(SessionRow | None, cursor.fetchone())

        if row is None:
            return None

        sessions = self._parse_sessions(row["login_sessions"])
        if row["token"] not in sessions:
            return None

        return LoginSession(
            uid=row["session_uid"],
            token=row["token"],
            user_uid=row["user_uid"],
            account_type=row["type"],
        )

    def verify_account_type(
        self,
        session_uid: str,
        required_type: AccountType,
        *,
        allow_admin: bool = True,
    ) -> bool:
        self._validate_account_type(required_type)
        session = self.get_login_session(session_uid)
        if session is None:
            return False
        if session.account_type == required_type:
            return True
        return allow_admin and session.account_type == "admin"

    def _connect(self) -> MySQLConnection:
        conn = mysql.connector.connect(
            host=self.host,
            port=self.port,
            database=self.database,
            user=self.user,
            password=self.password,
            charset="utf8mb4",
            autocommit=False,
        )
        return cast(MySQLConnection, conn)

    @staticmethod
    def _hash_password(password: str) -> str:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    @classmethod
    def _validate_username(cls, username: str) -> None:
        if not 1 <= len(username.encode("utf-8")) <= 20:
            raise AccountValidationError("username length must be 1-20 UTF-8 bytes")

    @classmethod
    def _validate_password(cls, password: str) -> None:
        if not 6 <= len(password) <= 16:
            raise AccountValidationError("password length must be 6-16 characters")
        if cls._PASSWORD_PATTERN.fullmatch(password) is None:
            raise AccountValidationError(
                "password may only contain letters, numbers, and hyphens"
            )

    @classmethod
    def _validate_account_type(cls, account_type: str) -> None:
        if account_type not in cls._ACCOUNT_TYPES:
            raise AccountValidationError("account_type must be admin or default")

    @staticmethod
    def _parse_sessions(raw_sessions: Any) -> list[str]:
        if raw_sessions in (None, ""):
            return []
        if isinstance(raw_sessions, list):
            return [str(item) for item in cast(list[Any], raw_sessions)]
        if isinstance(raw_sessions, (bytes, bytearray)):
            raw_sessions = raw_sessions.decode("utf-8")
        if isinstance(raw_sessions, str):
            sessions = json.loads(raw_sessions)
            if not isinstance(sessions, list):
                raise AccountValidationError("login_sessions must be a JSON array")
            return [str(item) for item in cast(list[Any], sessions)]
        return []

    @staticmethod
    def _new_uid() -> str:
        return uuid.uuid4().hex

    @staticmethod
    def _now() -> datetime:
        return datetime.now()

    @staticmethod
    def _parse_db_url(db_url: str) -> tuple[str | None, str | None]:
        if not db_url:
            return None, None
        host, separator, port = db_url.rpartition(":")
        if separator and host and port.isdigit():
            return host, port
        return db_url, None
