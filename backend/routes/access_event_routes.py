from flask import Blueprint, Response, request

from routes.helpers import json_data, json_error
from services.access_event_service import (
    fetch_access_events_for_export,
    get_signal,
    list_recent_events,
    register_event,
    sync_events,
)

access_event_bp = Blueprint("access_events", __name__)


@access_event_bp.route("/access-events", methods=["POST", "GET"])
@access_event_bp.route("/v1/access-events", methods=["POST", "GET"])
def access_events():
    if request.method == "POST":
        try:
            payload = request.get_json(silent=True) or {}
            event = register_event(payload)

            return json_data(
                {
                    "message": "Evento registrado com sucesso",
                    "event": event,
                    "signal": get_signal(event["event_type"], event["authorized"]),
                },
                status=201
            )

        except ValueError as exc:
            return json_error("INVALID_INPUT", str(exc), status=400)

        except Exception as exc:
            return json_error("INTERNAL_ERROR", str(exc), status=500)

    return json_data(list_recent_events(limit=50))


@access_event_bp.route("/v1/access-events/sync", methods=["POST"])
def sync_access_events():
    try:
        payload = request.get_json(silent=True) or {}
        events_payload = payload.get("events")

        if not isinstance(events_payload, list):
            return json_error(
                "INVALID_INPUT",
                "Campo events deve ser uma lista.",
                status=400
            )

        synced_events, failed_events = sync_events(events_payload)
        status = 207 if failed_events else 201

        return json_data(
            {
                "synced_count": len(synced_events),
                "failed_count": len(failed_events),
                "synced_events": synced_events,
                "failed_events": failed_events,
            },
            status=status
        )

    except Exception as exc:
        return json_error("INTERNAL_ERROR", str(exc), status=500)


@access_event_bp.route("/v1/access-events/export.csv", methods=["GET"])
def export_access_events_csv():
    events = fetch_access_events_for_export()

    fieldnames = [
        "id",
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
    ]

    output = []
    output.append(",".join(fieldnames))

    for event in events:
        row = []

        for field in fieldnames:
            value = event.get(field)

            if value is None:
                value = ""

            value = str(value).replace('"', '""')

            if "," in value or "\n" in value or '"' in value:
                value = f'"{value}"'

            row.append(value)

        output.append(",".join(row))

    csv_content = "\n".join(output) + "\n"

    return Response(
        csv_content,
        mimetype="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=access_events.csv"
        }
    )
