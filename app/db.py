from __future__ import annotations

import asyncio
from datetime import datetime
import json
import sqlite3
from typing import Any

from .constants import (
    MATCH_DECISION_DECLINED,
    MATCH_DECISION_LIKED,
    ORDER_STATUS_CLOSED,
)

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id INTEGER UNIQUE,
    phone TEXT UNIQUE,
    first_name TEXT,
    last_name TEXT,
    org_name TEXT,
    is_customer INTEGER NOT NULL DEFAULT 0,
    is_executor INTEGER NOT NULL DEFAULT 0,
    is_admin INTEGER NOT NULL DEFAULT 0,
    last_role TEXT,
    blocked INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS executor_profiles (
    user_id INTEGER PRIMARY KEY,
    experience TEXT,
    resume_link TEXT,
    resume_text TEXT,
    doc_types TEXT,
    construction_types TEXT,
    sections_capital TEXT,
    sections_linear TEXT,
    updated_at TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    doc_types TEXT NOT NULL,
    construction_types TEXT NOT NULL,
    sections_capital TEXT,
    sections_linear TEXT,
    description TEXT,
    deadline TEXT,
    price TEXT,
    expertise_required INTEGER,
    files_link TEXT,
    status TEXT NOT NULL,
    assigned_executor_id INTEGER,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(customer_id) REFERENCES users(id),
    FOREIGN KEY(assigned_executor_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    executor_id INTEGER NOT NULL,
    customer_decision TEXT,
    executor_decision TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(order_id, executor_id),
    FOREIGN KEY(order_id) REFERENCES orders(id),
    FOREIGN KEY(executor_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS ratings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    from_user_id INTEGER NOT NULL,
    to_user_id INTEGER NOT NULL,
    stars INTEGER NOT NULL,
    review TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(order_id, from_user_id, to_user_id),
    FOREIGN KEY(order_id) REFERENCES orders(id),
    FOREIGN KEY(from_user_id) REFERENCES users(id),
    FOREIGN KEY(to_user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS help_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_user_id INTEGER NOT NULL,
    role TEXT NOT NULL,
    text TEXT NOT NULL,
    created_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'new',
    FOREIGN KEY(from_user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS admin_whitelist (
    phone TEXT PRIMARY KEY,
    added_at TEXT NOT NULL
);
"""


def _now() -> str:
    return datetime.utcnow().isoformat()


def _json_dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _json_load(value: str | None) -> list[Any]:
    if not value:
        return []
    return json.loads(value)


def _row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return dict(row)


class Database:
    def __init__(self, path: str) -> None:
        self.path = path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    async def execute_script(self, script: str) -> None:
        def _run() -> None:
            with self._connect() as conn:
                conn.executescript(script)
        await asyncio.to_thread(_run)

    async def execute(self, query: str, params: tuple[Any, ...] = ()) -> int:
        def _run() -> int:
            with self._connect() as conn:
                cur = conn.execute(query, params)
                conn.commit()
                return cur.lastrowid
        return await asyncio.to_thread(_run)

    async def fetchone(self, query: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
        def _run() -> dict[str, Any] | None:
            with self._connect() as conn:
                cur = conn.execute(query, params)
                return _row_to_dict(cur.fetchone())
        return await asyncio.to_thread(_run)

    async def fetchall(self, query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        def _run() -> list[dict[str, Any]]:
            with self._connect() as conn:
                cur = conn.execute(query, params)
                return [dict(row) for row in cur.fetchall()]
        return await asyncio.to_thread(_run)

    async def init(self) -> None:
        await self.execute_script(SCHEMA_SQL)

    async def seed_admin_whitelist(self, phones: list[str]) -> None:
        if not phones:
            return
        for phone in phones:
            await self.execute(
                "INSERT OR IGNORE INTO admin_whitelist(phone, added_at) VALUES (?, ?)",
                (phone, _now()),
            )

    async def is_admin_phone(self, phone: str) -> bool:
        row = await self.fetchone("SELECT phone FROM admin_whitelist WHERE phone = ?", (phone,))
        return bool(row)

    async def add_admin_phone(self, phone: str) -> None:
        await self.execute(
            "INSERT OR IGNORE INTO admin_whitelist(phone, added_at) VALUES (?, ?)",
            (phone, _now()),
        )

    async def remove_admin_phone(self, phone: str) -> None:
        await self.execute("DELETE FROM admin_whitelist WHERE phone = ?", (phone,))

    async def get_user_by_phone(self, phone: str) -> dict[str, Any] | None:
        return await self.fetchone("SELECT * FROM users WHERE phone = ?", (phone,))

    async def get_user_by_tg_id(self, tg_id: int) -> dict[str, Any] | None:
        return await self.fetchone("SELECT * FROM users WHERE tg_id = ?", (tg_id,))

    async def get_user_by_id(self, user_id: int) -> dict[str, Any] | None:
        return await self.fetchone("SELECT * FROM users WHERE id = ?", (user_id,))

    async def create_user(self, tg_id: int, phone: str) -> dict[str, Any]:
        now = _now()
        await self.execute(
            """
            INSERT INTO users(tg_id, phone, created_at, updated_at)
            VALUES(?, ?, ?, ?)
            """,
            (tg_id, phone, now, now),
        )
        return await self.get_user_by_phone(phone)

    async def update_user_profile(
        self, user_id: int, first_name: str, last_name: str, org_name: str | None
    ) -> None:
        await self.execute(
            """
            UPDATE users
            SET first_name = ?, last_name = ?, org_name = ?, updated_at = ?
            WHERE id = ?
            """,
            (first_name, last_name, org_name, _now(), user_id),
        )

    async def update_user_tg(self, user_id: int, tg_id: int) -> None:
        await self.execute(
            "UPDATE users SET tg_id = ?, updated_at = ? WHERE id = ?",
            (tg_id, _now(), user_id),
        )

    async def set_user_roles(
        self,
        user_id: int,
        is_customer: bool | None = None,
        is_executor: bool | None = None,
        is_admin: bool | None = None,
    ) -> None:
        user = await self.get_user_by_id(user_id)
        if not user:
            return
        await self.execute(
            """
            UPDATE users
            SET is_customer = ?, is_executor = ?, is_admin = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                int(is_customer if is_customer is not None else user["is_customer"]),
                int(is_executor if is_executor is not None else user["is_executor"]),
                int(is_admin if is_admin is not None else user["is_admin"]),
                _now(),
                user_id,
            ),
        )

    async def set_last_role(self, user_id: int, role: str) -> None:
        await self.execute(
            "UPDATE users SET last_role = ?, updated_at = ? WHERE id = ?",
            (role, _now(), user_id),
        )

    async def set_blocked(self, user_id: int, blocked: bool) -> None:
        await self.execute(
            "UPDATE users SET blocked = ?, updated_at = ? WHERE id = ?",
            (int(blocked), _now(), user_id),
        )

    async def list_users(self) -> list[dict[str, Any]]:
        return await self.fetchall("SELECT * FROM users")

    async def list_customers(self) -> list[dict[str, Any]]:
        return await self.fetchall("SELECT * FROM users WHERE is_customer = 1")

    async def list_executors(self) -> list[dict[str, Any]]:
        return await self.fetchall("SELECT * FROM users WHERE is_executor = 1")

    async def upsert_executor_profile(
        self,
        user_id: int,
        experience: str,
        resume_link: str | None,
        resume_text: str | None,
        doc_types: list[str],
        construction_types: list[str],
        sections_capital: list[str],
        sections_linear: list[str],
    ) -> None:
        now = _now()
        await self.execute(
            """
            INSERT INTO executor_profiles(
                user_id, experience, resume_link, resume_text,
                doc_types, construction_types, sections_capital, sections_linear, updated_at
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                experience = excluded.experience,
                resume_link = excluded.resume_link,
                resume_text = excluded.resume_text,
                doc_types = excluded.doc_types,
                construction_types = excluded.construction_types,
                sections_capital = excluded.sections_capital,
                sections_linear = excluded.sections_linear,
                updated_at = excluded.updated_at
            """,
            (
                user_id,
                experience,
                resume_link,
                resume_text,
                _json_dump(doc_types),
                _json_dump(construction_types),
                _json_dump(sections_capital),
                _json_dump(sections_linear),
                now,
            ),
        )

    async def get_executor_profile(self, user_id: int) -> dict[str, Any] | None:
        row = await self.fetchone("SELECT * FROM executor_profiles WHERE user_id = ?", (user_id,))
        if not row:
            return None
        row["doc_types"] = _json_load(row.get("doc_types"))
        row["construction_types"] = _json_load(row.get("construction_types"))
        row["sections_capital"] = _json_load(row.get("sections_capital"))
        row["sections_linear"] = _json_load(row.get("sections_linear"))
        return row

    async def list_executor_profiles(self) -> list[dict[str, Any]]:
        rows = await self.fetchall(
            """
            SELECT e.*, u.first_name, u.last_name, u.org_name, u.phone, u.tg_id, u.blocked
            FROM executor_profiles e
            JOIN users u ON u.id = e.user_id
            WHERE u.is_executor = 1
            """
        )
        for row in rows:
            row["doc_types"] = _json_load(row.get("doc_types"))
            row["construction_types"] = _json_load(row.get("construction_types"))
            row["sections_capital"] = _json_load(row.get("sections_capital"))
            row["sections_linear"] = _json_load(row.get("sections_linear"))
        return rows

    async def create_order(self, customer_id: int, data: dict[str, Any]) -> dict[str, Any]:
        now = _now()
        order_id = await self.execute(
            """
            INSERT INTO orders(
                customer_id, name, doc_types, construction_types,
                sections_capital, sections_linear, description, deadline,
                price, expertise_required, files_link, status, assigned_executor_id,
                created_at, updated_at
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                customer_id,
                data["name"],
                _json_dump(data["doc_types"]),
                _json_dump(data["construction_types"]),
                _json_dump(data.get("sections_capital", [])),
                _json_dump(data.get("sections_linear", [])),
                data.get("description"),
                data.get("deadline"),
                data.get("price"),
                int(bool(data.get("expertise_required"))) if data.get("expertise_required") is not None else None,
                data.get("files_link"),
                data.get("status"),
                data.get("assigned_executor_id"),
                now,
                now,
            ),
        )
        return await self.get_order(order_id)

    async def update_order(self, order_id: int, data: dict[str, Any]) -> None:
        await self.execute(
            """
            UPDATE orders SET
                name = ?, doc_types = ?, construction_types = ?, sections_capital = ?, sections_linear = ?,
                description = ?, deadline = ?, price = ?, expertise_required = ?, files_link = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                data["name"],
                _json_dump(data["doc_types"]),
                _json_dump(data["construction_types"]),
                _json_dump(data.get("sections_capital", [])),
                _json_dump(data.get("sections_linear", [])),
                data.get("description"),
                data.get("deadline"),
                data.get("price"),
                int(bool(data.get("expertise_required"))) if data.get("expertise_required") is not None else None,
                data.get("files_link"),
                _now(),
                order_id,
            ),
        )

    async def set_order_status(self, order_id: int, status: str) -> None:
        await self.execute(
            "UPDATE orders SET status = ?, updated_at = ? WHERE id = ?",
            (status, _now(), order_id),
        )

    async def assign_executor(self, order_id: int, executor_id: int | None) -> None:
        await self.execute(
            "UPDATE orders SET assigned_executor_id = ?, updated_at = ? WHERE id = ?",
            (executor_id, _now(), order_id),
        )

    async def get_order(self, order_id: int) -> dict[str, Any] | None:
        row = await self.fetchone("SELECT * FROM orders WHERE id = ?", (order_id,))
        if not row:
            return None
        return self._deserialize_order(row)

    def _deserialize_order(self, row: dict[str, Any]) -> dict[str, Any]:
        row["doc_types"] = _json_load(row.get("doc_types"))
        row["construction_types"] = _json_load(row.get("construction_types"))
        row["sections_capital"] = _json_load(row.get("sections_capital"))
        row["sections_linear"] = _json_load(row.get("sections_linear"))
        return row

    async def list_orders_by_customer(self, customer_id: int) -> list[dict[str, Any]]:
        rows = await self.fetchall(
            "SELECT * FROM orders WHERE customer_id = ? ORDER BY created_at ASC",
            (customer_id,),
        )
        return [self._deserialize_order(row) for row in rows]

    async def list_open_orders(self) -> list[dict[str, Any]]:
        rows = await self.fetchall(
            "SELECT * FROM orders WHERE status != ? ORDER BY created_at ASC",
            (ORDER_STATUS_CLOSED,),
        )
        return [self._deserialize_order(row) for row in rows]

    async def list_orders_for_executor(self, executor_id: int) -> list[dict[str, Any]]:
        rows = await self.fetchall(
            """
            SELECT o.* FROM orders o
            JOIN matches m ON m.order_id = o.id
            WHERE m.executor_id = ?
              AND m.customer_decision = ?
              AND m.executor_decision = ?
              AND (o.assigned_executor_id IS NULL OR o.assigned_executor_id = ?)
            ORDER BY o.created_at ASC
            """,
            (executor_id, MATCH_DECISION_LIKED, MATCH_DECISION_LIKED, executor_id),
        )
        return [self._deserialize_order(row) for row in rows]

    async def list_closed_orders_for_user(self, user_id: int, role: str) -> list[dict[str, Any]]:
        if role == "customer":
            rows = await self.fetchall(
                "SELECT * FROM orders WHERE customer_id = ? AND status = ? ORDER BY created_at ASC",
                (user_id, ORDER_STATUS_CLOSED),
            )
        else:
            rows = await self.fetchall(
                """
                SELECT o.* FROM orders o
                WHERE o.assigned_executor_id = ? AND o.status = ?
                ORDER BY o.created_at ASC
                """,
                (user_id, ORDER_STATUS_CLOSED),
            )
        return [self._deserialize_order(row) for row in rows]

    async def upsert_match(
        self,
        order_id: int,
        executor_id: int,
        customer_decision: str | None = None,
        executor_decision: str | None = None,
    ) -> None:
        now = _now()
        await self.execute(
            """
            INSERT INTO matches(order_id, executor_id, customer_decision, executor_decision, created_at, updated_at)
            VALUES(?, ?, ?, ?, ?, ?)
            ON CONFLICT(order_id, executor_id) DO UPDATE SET
                customer_decision = COALESCE(excluded.customer_decision, matches.customer_decision),
                executor_decision = COALESCE(excluded.executor_decision, matches.executor_decision),
                updated_at = excluded.updated_at
            """,
            (order_id, executor_id, customer_decision, executor_decision, now, now),
        )

    async def update_match_decision(
        self,
        order_id: int,
        executor_id: int,
        customer_decision: str | None = None,
        executor_decision: str | None = None,
    ) -> None:
        await self.execute(
            """
            UPDATE matches
            SET customer_decision = COALESCE(?, customer_decision),
                executor_decision = COALESCE(?, executor_decision),
                updated_at = ?
            WHERE order_id = ? AND executor_id = ?
            """,
            (customer_decision, executor_decision, _now(), order_id, executor_id),
        )

    async def get_match(self, order_id: int, executor_id: int) -> dict[str, Any] | None:
        return await self.fetchone(
            "SELECT * FROM matches WHERE order_id = ? AND executor_id = ?",
            (order_id, executor_id),
        )

    async def list_matches_for_order(self, order_id: int) -> list[dict[str, Any]]:
        return await self.fetchall("SELECT * FROM matches WHERE order_id = ?", (order_id,))

    async def list_matches_for_executor(self, executor_id: int) -> list[dict[str, Any]]:
        return await self.fetchall("SELECT * FROM matches WHERE executor_id = ?", (executor_id,))

    async def list_customer_likes(self, order_id: int) -> list[dict[str, Any]]:
        return await self.fetchall(
            "SELECT * FROM matches WHERE order_id = ? AND customer_decision = ?",
            (order_id, MATCH_DECISION_LIKED),
        )

    async def list_customer_declines(self, order_id: int) -> list[dict[str, Any]]:
        return await self.fetchall(
            "SELECT * FROM matches WHERE order_id = ? AND customer_decision = ?",
            (order_id, MATCH_DECISION_DECLINED),
        )

    async def list_executor_likes_for_order(self, order_id: int) -> list[dict[str, Any]]:
        return await self.fetchall(
            "SELECT * FROM matches WHERE order_id = ? AND executor_decision = ?",
            (order_id, MATCH_DECISION_LIKED),
        )

    async def add_rating(
        self,
        order_id: int,
        from_user_id: int,
        to_user_id: int,
        stars: int,
        review: str | None,
    ) -> None:
        await self.execute(
            """
            INSERT INTO ratings(order_id, from_user_id, to_user_id, stars, review, created_at)
            VALUES(?, ?, ?, ?, ?, ?)
            ON CONFLICT(order_id, from_user_id, to_user_id) DO UPDATE SET
                stars = excluded.stars,
                review = excluded.review,
                created_at = excluded.created_at
            """,
            (order_id, from_user_id, to_user_id, stars, review, _now()),
        )

    async def get_rating_summary(self, user_id: int) -> tuple[float, int]:
        row = await self.fetchone(
            "SELECT AVG(stars) as avg_rating, COUNT(*) as cnt FROM ratings WHERE to_user_id = ?",
            (user_id,),
        )
        if not row or row["cnt"] == 0:
            return 0.0, 0
        return float(row["avg_rating"] or 0.0), int(row["cnt"])

    async def add_help_message(self, from_user_id: int, role: str, text: str) -> None:
        await self.execute(
            "INSERT INTO help_messages(from_user_id, role, text, created_at) VALUES(?, ?, ?, ?)",
            (from_user_id, role, text, _now()),
        )

    async def count_stats(self) -> dict[str, int]:
        users = await self.fetchone("SELECT COUNT(*) as cnt FROM users")
        customers = await self.fetchone("SELECT COUNT(*) as cnt FROM users WHERE is_customer = 1")
        executors = await self.fetchone("SELECT COUNT(*) as cnt FROM users WHERE is_executor = 1")
        orders = await self.fetchone("SELECT COUNT(*) as cnt FROM orders")
        in_work = await self.fetchone(
            "SELECT COUNT(*) as cnt FROM orders WHERE status != ?",
            (ORDER_STATUS_CLOSED,),
        )
        return {
            "users": int(users["cnt"] if users else 0),
            "customers": int(customers["cnt"] if customers else 0),
            "executors": int(executors["cnt"] if executors else 0),
            "orders": int(orders["cnt"] if orders else 0),
            "in_work": int(in_work["cnt"] if in_work else 0),
        }
