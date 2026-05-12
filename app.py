import csv
import os
import sqlite3
from datetime import datetime

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.security import generate_password_hash

from pubsub import PubSubClient

DB_PATH = os.getenv("APP_DB_PATH", "rfid_access.db")
CSV_PATH = os.getenv("APP_CSV_PATH", "rfid_access_log.csv")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
pubsub = None


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


def get_pubsub():
    global pubsub
    if pubsub is None:
        pubsub = PubSubClient(user_id="rfid-flask-app")
    return pubsub


def append_csv(event):
    file_exists = os.path.exists(CSV_PATH)

    with open(CSV_PATH, "a", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "tag_id",
                "collaborator_id",
                "collaborator_name",
                "registration",
                "authorized",
                "event_type",
                "origin",
                "message",
                "read_at",
                "created_at",
                "synced",
            ],
        )

        if not file_exists:
            writer.writeheader()

        writer.writerow(event)


def save_event(event):
    with connect_db() as conn:
        conn.execute(
            """
            INSERT INTO access_events (
                tag_id,
                collaborator_id,
                collaborator_name,
                registration,
                authorized,
                event_type,
                origin,
                message,
                read_at,
                created_at,
                synced
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event["tag_id"],
                event.get("collaborator_id"),
                event.get("collaborator_name"),
                event.get("registration"),
                int(event["authorized"]),
                event["event_type"],
                event["origin"],
                event["message"],
                event["read_at"],
                event["created_at"],
                int(event["synced"]),
            ),
        )
        conn.commit()


def normalize_payload(payload):
    tag_id = payload.get("tag_id")
    if tag_id is None:
        raise ValueError("tag_id is required")

    read_at = (
        payload.get("read_at")
        or payload.get("lido_em")
        or datetime.now().isoformat(timespec="seconds")
    )

    return {
        "tag_id": str(tag_id),
        "collaborator_id": payload.get("collaborator_id"),
        "collaborator_name": str(
            payload.get("collaborator_name")
            or payload.get("nome")
            or "Desconhecido"
        ),
        "registration": payload.get("registration"),
        "authorized": bool(payload.get("authorized", payload.get("autorizado", False))),
        "event_type": str(payload.get("event_type") or payload.get("evento") or "leitura"),
        "origin": str(payload.get("origin") or payload.get("origem") or "rfid-reader"),
        "message": str(payload.get("message") or payload.get("mensagem") or "Leitura recebida"),
        "read_at": read_at,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "synced": bool(payload.get("synced", True)),
    }


init_db()


@app.route("/", methods=["GET"])
def index():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/access-events", methods=["POST", "GET"])
def access_events():
    if request.method == "POST":
        try:
            payload = request.get_json(silent=True) or {}
            event = normalize_payload(payload)

            save_event(event)
            append_csv(event)
            get_pubsub().publish(event)

            return jsonify(
                {
                    "message": "Evento registrado com sucesso",
                    "event": event,
                }
            ), 201

        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

        except Exception as exc:
            return jsonify({"error": str(exc)}), 500

    with connect_db() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT
                tag_id,
                collaborator_id,
                collaborator_name,
                registration,
                authorized,
                event_type,
                origin,
                message,
                read_at,
                created_at,
                synced
            FROM access_events
            ORDER BY id DESC
            LIMIT 50
            """
        ).fetchall()

    events = [dict(row) for row in rows]
    return jsonify(events), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)