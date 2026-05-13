import sqlite3

from werkzeug.security import check_password_hash, generate_password_hash

from database import connect_db


def get_user_by_username(username):
    with connect_db() as conn:
        conn.row_factory = sqlite3.Row

        row = conn.execute(
            """
            SELECT
                id,
                username,
                password_hash,
                created_at
            FROM users
            WHERE username = ?
            """,
            (username,),
        ).fetchone()

    if row is None:
        return None

    return dict(row)


def authenticate_user(username, password):
    user = get_user_by_username(username)

    if user is None or not check_password_hash(user["password_hash"], password):
        return None

    return {
        "id": user["id"],
        "username": user["username"],
        "created_at": user["created_at"],
    }


def create_user(username, password):
    username = str(username or "").strip()
    password = str(password or "")

    if not username or not password:
        raise ValueError("Usuario e senha sao obrigatorios.")

    with connect_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO users (username, password_hash, created_at)
            VALUES (?, ?, datetime('now'))
            """,
            (username, generate_password_hash(password)),
        )
        conn.commit()

    return {
        "id": cursor.lastrowid,
        "username": username,
        "created_at": None,
    }


def is_integrity_error(exc):
    return isinstance(exc, sqlite3.IntegrityError)
