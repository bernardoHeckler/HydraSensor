import sqlite3
from datetime import datetime

from database import connect_db


def parse_bool(value, default=False):
    if value is None:
        return default

    if isinstance(value, bool):
        return value

    if isinstance(value, int):
        return value == 1

    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "sim", "yes", "ativo")

    return default


def normalize_collaborator_payload(payload, partial=False):
    fields = {}

    name = payload.get("name") or payload.get("nome")
    registration = payload.get("registration") or payload.get("matricula")
    rfid_tag = payload.get("rfid_tag") or payload.get("tag_rfid")
    role = payload.get("role") or payload.get("cargo")

    if name is not None:
        fields["name"] = str(name).strip()

    if registration is not None:
        fields["registration"] = str(registration).strip()

    if rfid_tag is not None:
        rfid_tag = str(rfid_tag).strip()
        fields["rfid_tag"] = rfid_tag or None

    if role is not None:
        fields["role"] = str(role).strip()

    if "has_room_access" in payload or "possui_acesso" in payload:
        fields["has_room_access"] = int(parse_bool(
            payload.get("has_room_access", payload.get("possui_acesso"))
        ))

    if "is_active" in payload or "ativo" in payload:
        fields["is_active"] = int(parse_bool(
            payload.get("is_active", payload.get("ativo")),
            default=True
        ))

    if not partial:
        required_fields = ["name", "registration", "role"]
        missing_fields = [field for field in required_fields if not fields.get(field)]

        if missing_fields:
            raise ValueError(f"Campos obrigatorios ausentes: {', '.join(missing_fields)}")

        fields.setdefault("rfid_tag", None)
        fields.setdefault("has_room_access", 0)
        fields.setdefault("is_active", 1)

    return fields


def list_collaborators(limit=20, offset=0):
    limit = min(max(limit, 1), 100)
    offset = max(offset, 0)

    with connect_db() as conn:
        conn.row_factory = sqlite3.Row

        total = conn.execute(
            "SELECT COUNT(*) AS total FROM collaborators"
        ).fetchone()["total"]

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
                created_at,
                updated_at
            FROM collaborators
            ORDER BY name ASC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        ).fetchall()

    return [dict(row) for row in rows], {
        "total": total,
        "limit": limit,
        "offset": offset
    }


def get_collaborator(collaborator_id):
    with connect_db() as conn:
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
                is_active,
                created_at,
                updated_at
            FROM collaborators
            WHERE id = ?
            """,
            (collaborator_id,),
        ).fetchone()

    if row is None:
        return None

    return dict(row)


def create_collaborator(payload):
    fields = normalize_collaborator_payload(payload)
    now = datetime.now().isoformat(timespec="seconds")

    with connect_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO collaborators (
                name,
                registration,
                rfid_tag,
                role,
                has_room_access,
                is_active,
                created_at,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                fields["name"],
                fields["registration"],
                fields["rfid_tag"],
                fields["role"],
                fields["has_room_access"],
                fields["is_active"],
                now,
                now,
            ),
        )
        conn.commit()

        collaborator_id = cursor.lastrowid

    return {
        "id": collaborator_id,
        **fields,
        "created_at": now,
        "updated_at": now
    }


def update_collaborator(collaborator_id, payload):
    fields = normalize_collaborator_payload(payload, partial=True)

    if not fields:
        raise ValueError("Nenhum campo enviado para atualizacao.")

    fields["updated_at"] = datetime.now().isoformat(timespec="seconds")

    assignments = ", ".join(f"{field} = ?" for field in fields.keys())
    values = list(fields.values())
    values.append(collaborator_id)

    with connect_db() as conn:
        cursor = conn.execute(
            f"""
            UPDATE collaborators
            SET {assignments}
            WHERE id = ?
            """,
            values,
        )
        conn.commit()

    if cursor.rowcount == 0:
        return None

    return get_collaborator(collaborator_id)


def delete_collaborator(collaborator_id):
    now = datetime.now().isoformat(timespec="seconds")

    with connect_db() as conn:
        cursor = conn.execute(
            """
            UPDATE collaborators
            SET is_active = 0,
                updated_at = ?
            WHERE id = ?
            """,
            (now, collaborator_id),
        )
        conn.commit()

    return cursor.rowcount > 0


def is_integrity_error(error):
    return isinstance(error, sqlite3.IntegrityError)
