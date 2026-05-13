import sqlite3

from database import connect_db


def fetch_events_by_type(event_types, limit=10):
    placeholders = ", ".join("?" for _ in event_types)

    with connect_db() as conn:
        conn.row_factory = sqlite3.Row

        rows = conn.execute(
            f"""
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
            WHERE event_type IN ({placeholders})
            ORDER BY read_at DESC, id DESC
            LIMIT ?
            """,
            (*event_types, limit),
        ).fetchall()

    return [dict(row) for row in rows]


def fetch_recent_alerts(limit=10):
    return fetch_events_by_type(["acesso_negado", "invasao"], limit=limit)


def fetch_people_inside():
    with connect_db() as conn:
        conn.row_factory = sqlite3.Row

        rows = conn.execute(
            """
            SELECT
                c.id,
                c.name,
                c.registration,
                c.rfid_tag,
                c.role,
                MAX(ae.read_at) AS entered_at
            FROM collaborators c
            INNER JOIN access_events ae
                ON ae.collaborator_id = c.id
            WHERE c.is_active = 1
              AND ae.authorized = 1
              AND ae.event_type IN ('entrada', 'saida')
            GROUP BY c.id
            HAVING (
                SELECT last_event.event_type
                FROM access_events last_event
                WHERE last_event.collaborator_id = c.id
                  AND last_event.authorized = 1
                  AND last_event.event_type IN ('entrada', 'saida')
                ORDER BY last_event.read_at DESC, last_event.id DESC
                LIMIT 1
            ) = 'entrada'
            ORDER BY entered_at DESC
            """
        ).fetchall()

    return [dict(row) for row in rows]


def get_monitoring_summary():
    return {
        "latest_entries": fetch_events_by_type(["entrada"], limit=10),
        "latest_exits": fetch_events_by_type(["saida"], limit=10),
        "denied_attempts": fetch_events_by_type(["acesso_negado"], limit=10),
        "intrusion_attempts": fetch_events_by_type(["invasao"], limit=10),
        "people_inside": fetch_people_inside(),
        "recent_alerts": fetch_recent_alerts(limit=10),
    }
