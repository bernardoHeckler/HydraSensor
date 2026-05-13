import os
import sys
from datetime import datetime

import requests

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:5000")
ACCESS_EVENTS_URL = f"{API_BASE_URL}/v1/access-events"


def simulate_read(tag_id):
    payload = {
        "tag_id": str(tag_id),
        "origin": "simulator",
        "read_at": datetime.now().isoformat(timespec="seconds"),
    }

    response = requests.post(ACCESS_EVENTS_URL, json=payload, timeout=5)
    response.raise_for_status()

    data = response.json()["data"]
    event = data["event"]

    print("Evento simulado enviado com sucesso")
    print(f"Tag: {event['tag_id']}")
    print(f"Colaborador: {event['collaborator_name']}")
    print(f"Tipo: {event['event_type']}")
    print(f"Autorizado: {event['authorized']}")
    print(f"Mensagem: {event['message']}")
    print(f"Signal: {data['signal']}")


def main():
    if len(sys.argv) < 2:
        print("Uso: python3 simulate_reader.py <tag_id>")
        print("Exemplo: python3 simulate_reader.py 498103025204")
        return

    tag_id = sys.argv[1]
    simulate_read(tag_id)


if __name__ == "__main__":
    main()