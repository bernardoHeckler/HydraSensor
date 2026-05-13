import sqlite3
from datetime import datetime

from database import connect_db


def fetch_device_bootstrap_data():
    with connect_db() as conn:
        conn.row_factory = sqlite3.Row

        rows = conn.execute(
            """
            SELECT
                id,
                name,
                registration,
                rfid_tag,
                role,
                has_room_access,
                is_active,
                updated_at
            FROM collaborators
            WHERE is_active = 1
              AND rfid_tag IS NOT NULL
              AND TRIM(rfid_tag) != ''
            ORDER BY name ASC
            """
        ).fetchall()

    collaborators = [dict(row) for row in rows]

    tags = {
        collaborator["rfid_tag"]: {
            "collaborator_id": collaborator["id"],
            "name": collaborator["name"],
            "registration": collaborator["registration"],
            "role": collaborator["role"],
            "has_room_access": bool(collaborator["has_room_access"]),
            "is_active": bool(collaborator["is_active"]),
            "updated_at": collaborator["updated_at"],
        }
        for collaborator in collaborators
    }

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "collaborators": collaborators,
        "tags": tags,
    }
