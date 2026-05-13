import sqlite3
from collections import defaultdict
from datetime import datetime, time

from database import connect_db


def parse_datetime(value):
    return datetime.fromisoformat(str(value))


def seconds_to_hhmmss(total_seconds):
    total_seconds = int(total_seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def get_reference_datetime(date_ref):
    today = datetime.now().date().isoformat()

    if date_ref == today:
        return datetime.now()

    return datetime.combine(datetime.fromisoformat(date_ref).date(), time.max)


def fetch_daily_events(date_ref):
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
            WHERE substr(read_at, 1, 10) = ?
            ORDER BY read_at ASC, id ASC
            """,
            (date_ref,),
        ).fetchall()

    return [dict(row) for row in rows]


def calculate_daily_presence(date_ref=None, collaborator_id=None):
    date_ref = date_ref or datetime.now().date().isoformat()
    reference_datetime = get_reference_datetime(date_ref)
    events = fetch_daily_events(date_ref)

    if collaborator_id is not None:
        collaborator_id = int(collaborator_id)
        events = [
            event
            for event in events
            if event["collaborator_id"] == collaborator_id
        ]

    entries = [event for event in events if event["event_type"] == "entrada"]
    exits = [event for event in events if event["event_type"] == "saida"]
    denied_attempts = [
        event for event in events if event["event_type"] == "acesso_negado"
    ]
    intrusion_attempts = [
        event for event in events if event["event_type"] == "invasao"
    ]

    events_by_collaborator = defaultdict(list)
    for event in events:
        if event["collaborator_id"] is not None and event["event_type"] in ("entrada", "saida"):
            events_by_collaborator[event["collaborator_id"]].append(event)

    permanence = []

    for current_collaborator_id, collaborator_events in events_by_collaborator.items():
        open_entry = None
        intervals = []
        total_seconds = 0

        for event in collaborator_events:
            if event["event_type"] == "entrada":
                open_entry = event
                continue

            if event["event_type"] == "saida" and open_entry is not None:
                entry_datetime = parse_datetime(open_entry["read_at"])
                exit_datetime = parse_datetime(event["read_at"])
                duration_seconds = max(
                    int((exit_datetime - entry_datetime).total_seconds()),
                    0,
                )

                total_seconds += duration_seconds
                intervals.append({
                    "entry_at": open_entry["read_at"],
                    "exit_at": event["read_at"],
                    "duration_seconds": duration_seconds,
                    "duration_hhmmss": seconds_to_hhmmss(duration_seconds),
                    "closed": True,
                })
                open_entry = None

        if open_entry is not None:
            entry_datetime = parse_datetime(open_entry["read_at"])
            duration_seconds = max(
                int((reference_datetime - entry_datetime).total_seconds()),
                0,
            )

            total_seconds += duration_seconds
            intervals.append({
                "entry_at": open_entry["read_at"],
                "exit_at": None,
                "duration_seconds": duration_seconds,
                "duration_hhmmss": seconds_to_hhmmss(duration_seconds),
                "closed": False,
            })

        first_event = collaborator_events[0]
        permanence.append({
            "collaborator_id": current_collaborator_id,
            "collaborator_name": first_event["collaborator_name"],
            "registration": first_event["registration"],
            "total_seconds": total_seconds,
            "total_hhmmss": seconds_to_hhmmss(total_seconds),
            "intervals": intervals,
        })

    unauthorized_ranking_counter = defaultdict(lambda: {
        "collaborator_id": None,
        "collaborator_name": None,
        "registration": None,
        "attempts": 0,
    })

    for event in denied_attempts:
        key = event["collaborator_id"] or event["tag_id"]
        ranking_item = unauthorized_ranking_counter[key]
        ranking_item["collaborator_id"] = event["collaborator_id"]
        ranking_item["collaborator_name"] = event["collaborator_name"]
        ranking_item["registration"] = event["registration"]
        ranking_item["attempts"] += 1

    unauthorized_ranking = sorted(
        unauthorized_ranking_counter.values(),
        key=lambda item: item["attempts"],
        reverse=True,
    )

    return {
        "date": date_ref,
        "reference_at": reference_datetime.isoformat(timespec="seconds"),
        "entries_count": len(entries),
        "unique_entries_count": len({
            event["collaborator_id"] for event in entries if event["collaborator_id"] is not None
        }),
        "exits_count": len(exits),
        "unique_exits_count": len({
            event["collaborator_id"] for event in exits if event["collaborator_id"] is not None
        }),
        "denied_attempts_count": len(denied_attempts),
        "intrusion_attempts_count": len(intrusion_attempts),
        "permanence": permanence,
        "unauthorized_ranking": unauthorized_ranking,
    }
