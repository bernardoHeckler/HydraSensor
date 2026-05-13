import csv
import json
import os
import time
from datetime import datetime

import requests
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

LED_VERDE = 17
LED_VERMELHO = 27
BUZZER = 22

GPIO.setup(LED_VERDE, GPIO.OUT)
GPIO.setup(LED_VERMELHO, GPIO.OUT)
GPIO.setup(BUZZER, GPIO.OUT)

GPIO.output(LED_VERDE, GPIO.LOW)
GPIO.output(LED_VERMELHO, GPIO.LOW)
GPIO.output(BUZZER, GPIO.LOW)

buzzer_pwm = GPIO.PWM(BUZZER, 440)
leitor_rfid = SimpleMFRC522()

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:5000")
ACCESS_EVENTS_URL = f"{API_BASE_URL}/v1/access-events"
BOOTSTRAP_URL = f"{API_BASE_URL}/v1/device/bootstrap"
SYNC_URL = f"{API_BASE_URL}/v1/access-events/sync"

CACHE_PATH = "rfid_cache.json"
BACKUP_CSV = "rfid_reader_backup.csv"

ultima_leitura = {"tag": None, "instante": 0}
JANELA_ANTI_REPETICAO = 2.0


def tocar_buzzer(vezes=1, duracao=0.12, intervalo=0.08, frequencia=880):
    for _ in range(vezes):
        buzzer_pwm.ChangeFrequency(frequencia)
        buzzer_pwm.start(50)
        time.sleep(duracao)
        buzzer_pwm.stop()
        time.sleep(intervalo)


def piscar_led(pin, duracao=0.4):
    GPIO.output(pin, GPIO.HIGH)
    time.sleep(duracao)
    GPIO.output(pin, GPIO.LOW)


def sinalizar_autorizado():
    tocar_buzzer(vezes=1, duracao=0.08, intervalo=0.05, frequencia=1200)
    piscar_led(LED_VERDE, duracao=0.35)


def sinalizar_nao_autorizado():
    tocar_buzzer(vezes=2, duracao=0.12, intervalo=0.08, frequencia=440)
    piscar_led(LED_VERMELHO, duracao=0.45)


def sinalizar_invasao():
    tocar_buzzer(vezes=4, duracao=0.15, intervalo=0.05, frequencia=300)
    piscar_led(LED_VERMELHO, duracao=0.2)
    piscar_led(LED_VERMELHO, duracao=0.2)


def sinalizar_por_signal(signal):
    if signal == "allowed":
        sinalizar_autorizado()
    elif signal == "intrusion":
        sinalizar_invasao()
    else:
        sinalizar_nao_autorizado()


def leitura_repetida(tag_id):
    agora = time.time()
    mesma_tag = ultima_leitura["tag"] == tag_id
    dentro_janela = (agora - ultima_leitura["instante"]) < JANELA_ANTI_REPETICAO

    ultima_leitura["tag"] = tag_id
    ultima_leitura["instante"] = agora

    return mesma_tag and dentro_janela


def salvar_cache(data):
    with open(CACHE_PATH, "w", encoding="utf-8") as cache_file:
        json.dump(data, cache_file, ensure_ascii=False, indent=2)


def carregar_cache():
    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as cache_file:
            return json.load(cache_file)
    except FileNotFoundError:
        return {"tags": {}, "collaborators": [], "generated_at": None}


def buscar_bootstrap():
    try:
        response = requests.get(BOOTSTRAP_URL, timeout=5)
        response.raise_for_status()

        data = response.json()["data"]
        salvar_cache(data)

        print(f"Cache RFID atualizado em {data['generated_at']}.")
        return data

    except requests.RequestException as exc:
        print(f"Nao foi possivel buscar bootstrap na API: {exc}")
        print("Usando cache local, se existir.")
        return carregar_cache()


def montar_payload_leitura(tag_id):
    return {
        "tag_id": str(tag_id),
        "origin": "raspberry-rfid",
        "read_at": datetime.now().isoformat(timespec="seconds"),
    }


def registrar_backup_local(payload):
    file_exists = os.path.exists(BACKUP_CSV)

    with open(BACKUP_CSV, "a", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "tag_id",
                "origin",
                "read_at",
            ],
        )

        if not file_exists:
            writer.writeheader()

        writer.writerow(payload)


def decidir_signal_offline(payload, cache):
    tag_id = str(payload["tag_id"])
    tag_data = cache.get("tags", {}).get(tag_id)

    if tag_data is None:
        return "intrusion"

    if not tag_data.get("is_active") or not tag_data.get("has_room_access"):
        return "denied"

    return "allowed"


def enviar_evento(payload, cache):
    try:
        response = requests.post(ACCESS_EVENTS_URL, json=payload, timeout=5)
        response.raise_for_status()

        data = response.json()["data"]
        event = data["event"]
        signal = data["signal"]

        print(f"Evento enviado: {event['message']}")
        return True, signal

    except requests.RequestException as exc:
        print(f"Falha ao enviar para a API: {exc}")

        registrar_backup_local(payload)
        signal = decidir_signal_offline(payload, cache)

        print("Evento salvo no backup local para sincronizacao futura.")
        return False, signal


def carregar_eventos_backup():
    if not os.path.exists(BACKUP_CSV):
        return []

    with open(BACKUP_CSV, "r", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def limpar_backup_local():
    if os.path.exists(BACKUP_CSV):
        os.remove(BACKUP_CSV)


def sincronizar_backup_local():
    events = carregar_eventos_backup()

    if not events:
        return

    try:
        response = requests.post(SYNC_URL, json={"events": events}, timeout=10)
        response.raise_for_status()

        data = response.json()["data"]
        print(
            "Sincronizacao concluida: "
            f"{data['synced_count']} enviados, {data['failed_count']} falharam."
        )

        if data["failed_count"] == 0:
            limpar_backup_local()

    except requests.RequestException as exc:
        print(f"Nao foi possivel sincronizar backup local: {exc}")


def iniciar_leitura():
    cache = buscar_bootstrap()
    sincronizar_backup_local()

    print("Aproxime a tag RFID do leitor.")

    try:
        while True:
            tag_id, _ = leitor_rfid.read()

            if leitura_repetida(tag_id):
                print(f"Leitura ignorada para a tag {tag_id} por anti-repeticao.")
                continue

            payload = montar_payload_leitura(tag_id)
            enviado, signal = enviar_evento(payload, cache)

            sinalizar_por_signal(signal)

            print({
                "tag_id": payload["tag_id"],
                "enviado": enviado,
                "signal": signal,
            })

            time.sleep(0.3)

    except KeyboardInterrupt:
        print("Leitura encerrada pelo usuario.")

    finally:
        buzzer_pwm.stop()
        GPIO.cleanup()


if __name__ == "__main__":
    iniciar_leitura()