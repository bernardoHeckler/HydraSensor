import sqlite3
from datetime import datetime

from werkzeug.security import generate_password_hash

from config import DB_PATH


def connect_db():
    return sqlite3.connect(DB_PATH)


def init_db():
    now = datetime.now().isoformat(timespec="seconds")

    with connect_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS collaborators (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                registration TEXT NOT NULL UNIQUE,
                rfid_tag TEXT UNIQUE,
                role TEXT NOT NULL,
                has_room_access INTEGER NOT NULL DEFAULT 0,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS access_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tag_id TEXT NOT NULL,
                collaborator_id INTEGER,
                collaborator_name TEXT,
                registration TEXT,
                authorized INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                origin TEXT NOT NULL,
                message TEXT NOT NULL,
                read_at TEXT NOT NULL,
                created_at TEXT NOT NULL,
                synced INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (collaborator_id) REFERENCES collaborators(id)
            )
            """
        )

        admin_exists = conn.execute(
            "SELECT id FROM users WHERE username = ?",
            ("admin",),
        ).fetchone()

        if not admin_exists:
            conn.execute(
                """
                INSERT INTO users (username, password_hash, created_at)
                VALUES (?, ?, ?)
                """,
                ("admin", generate_password_hash("admin123"), now),
            )

        conn.commit()
