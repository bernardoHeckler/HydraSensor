import csv
import os
import sqlite3
from datetime import datetime

from flask import Flask, jsonify, request, send_from_directory

from pubsub import PubSubClient

DB_PATH = os.getenv("APP_DB_PATH", "rfid_access.db")
CSV_PATH = os.getenv("APP_CSV_PATH", "rfid_access_log.csv")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
pubsub = None


def connect_db():
    return sqlite3.connect(DB_PATH)


def create_table():
    with connect_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS access_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tag_id INTEGER NOT NULL,
                nome TEXT NOT NULL,
                autorizado INTEGER NOT NULL,
                evento TEXT NOT NULL,
                origem TEXT NOT NULL,
                mensagem TEXT NOT NULL,
                lido_em TEXT NOT NULL,
                criado_em TEXT NOT NULL
            )
            """
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
                "nome",
                "autorizado",
                "evento",
                "origem",
                "mensagem",
                "lido_em",
                "criado_em",
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
                nome,
                autorizado,
                evento,
                origem,
                mensagem,
                lido_em,
                criado_em
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event["tag_id"],
                event["nome"],
                int(event["autorizado"]),
                event["evento"],
                event["origem"],
                event["mensagem"],
                event["lido_em"],
                event["criado_em"],
            ),
        )
        conn.commit()


def normalize_payload(payload):
    tag_id = payload.get("tag_id")
    if tag_id is None:
        raise ValueError("tag_id is required")

    read_at = payload.get("lido_em") or datetime.now().isoformat(timespec="seconds")

    return {
        "tag_id": int(tag_id),
        "nome": str(payload.get("nome") or "Desconhecido"),
        "autorizado": bool(payload.get("autorizado")),
        "evento": str(payload.get("evento") or "leitura"),
        "origem": str(payload.get("origem") or "rfid-reader"),
        "mensagem": str(payload.get("mensagem") or "Leitura recebida"),
        "lido_em": read_at,
        "criado_em": datetime.now().isoformat(timespec="seconds"),
    }


create_table()

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
            return jsonify({"message": "Evento registrado com sucesso", "event": event}), 201
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        except Exception as exc:
            return jsonify({"error": str(exc)}), 500

    with connect_db() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT tag_id, nome, autorizado, evento, origem, mensagem, lido_em, criado_em
            FROM access_events
            ORDER BY id DESC
            LIMIT 50
            """
        ).fetchall()

    events = [dict(row) for row in rows]
    return jsonify(events), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
