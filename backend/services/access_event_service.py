import csv
import os
import sqlite3
from datetime import datetime

from config import CSV_PATH
from database import connect_db
from pubsub import PubSubClient

pubsub = None


def get_pubsub():
    global pubsub
    if pubsub is None:
        pubsub = PubSubClient(user_id="rfid-flask-app")
    return pubsub


def publish_event(event):
    try:
        get_pubsub().publish(event)
        return True
    except Exception as exc:
        print(f"Falha ao publicar evento no PubNub: {exc}")
        return False


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


def get_collaborator_by_tag(conn, tag_id):
    conn.row_factory = sqlite3.Row

    row = conn.execute(
        """
        SELECT
            id,
            name,
            registration,
            rfid_tag,
            role,
            has_room_access,
            is_active
        FROM collaborators
        WHERE rfid_tag = ?
        """,
        (tag_id,),
    ).fetchone()

    if row is None:
        return None

    return dict(row)


def is_collaborator_inside(conn, collaborator_id):
    conn.row_factory = sqlite3.Row

    row = conn.execute(
        """
        SELECT event_type
        FROM access_events
        WHERE collaborator_id = ?
          AND authorized = 1
          AND event_type IN ('entrada', 'saida')
        ORDER BY read_at DESC, id DESC
        LIMIT 1
        """,
        (collaborator_id,),
    ).fetchone()

    return row is not None and row["event_type"] == "entrada"


def has_entered_today(conn, collaborator_id, read_at):
    date_ref = str(read_at)[:10]

    row = conn.execute(
        """
        SELECT id
        FROM access_events
        WHERE collaborator_id = ?
          AND event_type = 'entrada'
          AND substr(read_at, 1, 10) = ?
        LIMIT 1
        """,
        (collaborator_id, date_ref),
    ).fetchone()

    return row is not None


def get_signal(event_type, authorized):
    if event_type == "invasao":
        return "intrusion"

    if authorized:
        return "allowed"

    return "denied"


def normalize_payload(payload):
    tag_id = payload.get("tag_id")

    if tag_id is None:
        raise ValueError("tag_id is required")

    tag_id = str(tag_id).strip()

    if not tag_id:
        raise ValueError("tag_id cannot be empty")

    read_at = (
        payload.get("read_at")
        or payload.get("lido_em")
        or datetime.now().isoformat(timespec="seconds")
    )

    origin = str(payload.get("origin") or payload.get("origem") or "rfid-reader")
    synced = bool(payload.get("synced", True))

    with connect_db() as conn:
        collaborator = get_collaborator_by_tag(conn, tag_id)

        if collaborator is None:
            event_type = "invasao"
            authorized = False
            message = f"Tag {tag_id} desconhecida. Possivel tentativa de invasao."

            return {
                "tag_id": tag_id,
                "collaborator_id": None,
                "collaborator_name": "Desconhecido",
                "registration": None,
                "authorized": authorized,
                "event_type": event_type,
                "origin": origin,
                "message": message,
                "read_at": read_at,
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "synced": synced,
            }

        if not collaborator["is_active"]:
            event_type = "acesso_negado"
            authorized = False
            message = f"Colaborador inativo tentou acessar a sala: {collaborator['name']}."

        elif not collaborator["has_room_access"]:
            event_type = "acesso_negado"
            authorized = False
            message = f"Colaborador sem permissao tentou acessar a sala: {collaborator['name']}."

        else:
            authorized = True
            inside = is_collaborator_inside(conn, collaborator["id"])

            if inside:
                event_type = "saida"
                message = f"Saida registrada para {collaborator['name']}."
            else:
                event_type = "entrada"

                if has_entered_today(conn, collaborator["id"], read_at):
                    message = f"Bem-vindo de volta, {collaborator['name']}."
                else:
                    message = f"Bem-vindo, {collaborator['name']}."

        return {
            "tag_id": tag_id,
            "collaborator_id": collaborator["id"],
            "collaborator_name": collaborator["name"],
            "registration": collaborator["registration"],
            "authorized": authorized,
            "event_type": event_type,
            "origin": origin,
            "message": message,
            "read_at": read_at,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "synced": synced,
        }


def normalize_sync_event(payload):
    event = normalize_payload({
        **payload,
        "synced": True,
    })

    return event


def register_event(payload):
    event = normalize_payload(payload)

    save_event(event)
    append_csv(event)
    publish_event(event)

    return event


def sync_events(events_payload):
    synced_events = []
    failed_events = []

    for index, event_payload in enumerate(events_payload):
        try:
            event = normalize_sync_event(event_payload)

            save_event(event)
            append_csv(event)
            publish_event(event)

            synced_events.append({
                "index": index,
                "event": event,
                "signal": get_signal(event["event_type"], event["authorized"]),
            })

        except Exception as exc:
            failed_events.append({
                "index": index,
                "error": str(exc),
                "payload": event_payload,
            })

    return synced_events, failed_events


def list_recent_events(limit=50):
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
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [dict(row) for row in rows]


def fetch_access_events_for_export():
    with connect_db() as conn:
        conn.row_factory = sqlite3.Row

        rows = conn.execute(
            """
            SELECT
                id,
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
            ORDER BY read_at ASC, id ASC
            """
        ).fetchall()

    return [dict(row) for row in rows]
