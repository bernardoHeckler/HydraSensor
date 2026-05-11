import csv
import time
from datetime import datetime

import requests
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Portas mantidas
LED_VERDE = 17      # pino fisico 11
LED_VERMELHO = 27   # pino fisico 13
BUZZER = 22         # pino fisico 15

GPIO.setup(LED_VERDE, GPIO.OUT)
GPIO.setup(LED_VERMELHO, GPIO.OUT)
GPIO.setup(BUZZER, GPIO.OUT)

GPIO.output(LED_VERDE, GPIO.LOW)
GPIO.output(LED_VERMELHO, GPIO.LOW)
GPIO.output(BUZZER, GPIO.LOW)

buzzer_pwm = GPIO.PWM(BUZZER, 440)
leitor_rfid = SimpleMFRC522()

API_URL = "http://127.0.0.1:5000/access-events"
BACKUP_CSV = "rfid_reader_backup.csv"

# Cadastre aqui as tags e permissoes
COLABORADORES = {
    498103025204: {"nome": "Bernardo", "autorizado": True},
    # 123456789012: {"nome": "Maria", "autorizado": False},
    # 987654321098: {"nome": "Joao", "autorizado": True},
}

registros_diarios = {}
tentativas_nao_autorizadas = {}
tentativas_invasao = 0
log_eventos = []

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


def registrar_backup_local(evento):
    file_exists = False
    try:
        with open(BACKUP_CSV, "r", encoding="utf-8"):
            file_exists = True
    except FileNotFoundError:
        file_exists = False

    with open(BACKUP_CSV, "a", newline="", encoding="utf-8") as csv_file:
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
            ],
        )
        if not file_exists:
            writer.writeheader()
        writer.writerow(evento)


def leitura_repetida(tag_id):
    agora = time.time()
    mesma_tag = ultima_leitura["tag"] == tag_id
    dentro_janela = (agora - ultima_leitura["instante"]) < JANELA_ANTI_REPETICAO

    ultima_leitura["tag"] = tag_id
    ultima_leitura["instante"] = agora
    return mesma_tag and dentro_janela


def definir_evento(tag_id, autorizado):
    global tentativas_invasao

    if not autorizado:
        tentativas_nao_autorizadas[tag_id] = tentativas_nao_autorizadas.get(tag_id, 0) + 1
        tentativas_invasao += 1
        return "tentativa_negada"

    em_area = registros_diarios.get(tag_id, False)
    registros_diarios[tag_id] = not em_area
    return "saida" if em_area else "entrada"


def montar_payload(tag_id):
    colaborador = COLABORADORES.get(tag_id, {"nome": "Nao cadastrado", "autorizado": False})
    autorizado = colaborador["autorizado"]
    evento = definir_evento(tag_id, autorizado)
    lido_em = datetime.now().isoformat(timespec="seconds")

    mensagem = (
        f"{colaborador['nome']} registrou {evento}."
        if autorizado
        else f"Tag {tag_id} nao autorizada."
    )

    payload = {
        "tag_id": tag_id,
        "nome": colaborador["nome"],
        "autorizado": autorizado,
        "evento": evento,
        "origem": "raspberry-rfid",
        "mensagem": mensagem,
        "lido_em": lido_em,
    }

    log_eventos.append(payload)
    return payload


def enviar_evento(payload):
    try:
        response = requests.post(API_URL, json=payload, timeout=5)
        response.raise_for_status()
        print(f"Evento enviado: {payload['mensagem']}")
        return True
    except requests.RequestException as exc:
        print(f"Falha ao enviar para a API: {exc}")
        registrar_backup_local(payload)
        return False


def sinalizar_autorizado():
    tocar_buzzer(vezes=1, duracao=0.08, intervalo=0.05, frequencia=1200)
    piscar_led(LED_VERDE, duracao=0.35)


def sinalizar_nao_autorizado():
    tocar_buzzer(vezes=2, duracao=0.12, intervalo=0.08, frequencia=440)
    piscar_led(LED_VERMELHO, duracao=0.45)


def iniciar_leitura():
    print("Aproxime a tag RFID do leitor.")
    try:
        while True:
            tag_id, _ = leitor_rfid.read()

            if leitura_repetida(tag_id):
                print(f"Leitura ignorada para a tag {tag_id} por anti-repeticao.")
                continue

            payload = montar_payload(tag_id)
            enviado = enviar_evento(payload)

            if payload["autorizado"]:
                sinalizar_autorizado()
            else:
                sinalizar_nao_autorizado()

            print(payload)
            if not enviado:
                print("Evento salvo apenas no backup local.")

            time.sleep(0.3)
    except KeyboardInterrupt:
        print("Leitura encerrada pelo usuario.")
    finally:
        buzzer_pwm.stop()
        GPIO.cleanup()


if __name__ == "__main__":
    iniciar_leitura()
