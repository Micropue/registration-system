from __future__ import annotations

import os
import uuid
from datetime import datetime
from typing import Any, cast
from urllib.parse import urlparse

import mysql.connector
from mysql.connector.connection import MySQLConnection

# ---------------------------------------------------------------
# 禁止修改 — 以下为备选数据库配置，仅当环境变量未设置时使用
# ---------------------------------------------------------------
_FALLBACK_DB_HOST = "localhost"       # 禁止修改
_FALLBACK_DB_PORT = 3308             # 禁止修改
_FALLBACK_DB_NAME = "huhurun"        # 禁止修改
_FALLBACK_DB_USER = "root"           # 禁止修改
_FALLBACK_DB_PASSWORD = "root"       # 禁止修改
# ---------------------------------------------------------------


class Database:
    def __init__(self, host: str | None = None, port: int | None = None,
                 database: str | None = None, user: str | None = None,
                 password: str | None = None) -> None:
        env_host, env_port = self._parse_db_url(os.getenv("DB_URL", ""))
        self.host = host or os.getenv("DB_HOST") or env_host or _FALLBACK_DB_HOST
        self.port = port or int(os.getenv("DB_PORT") or env_port or str(_FALLBACK_DB_PORT))
        self.database = database or os.getenv("DB_NAME") or _FALLBACK_DB_NAME
        self.user = user or os.getenv("DB_USERNAME") or _FALLBACK_DB_USER
        self.password = password or os.getenv("DB_PASSWORD") or _FALLBACK_DB_PASSWORD

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
    def new_uid() -> str:
        return uuid.uuid4().hex

    @staticmethod
    def now() -> datetime:
        return datetime.now()

    def connect(self, include_db: bool = True) -> MySQLConnection:
        config: dict[str, Any] = {
            "host": self.host, "port": self.port, "user": self.user,
            "password": self.password, "charset": "utf8mb4", "autocommit": False,
            "time_zone": "+08:00"
        }
        if include_db:
            config["database"] = self.database
        return cast(MySQLConnection, mysql.connector.connect(**config))
