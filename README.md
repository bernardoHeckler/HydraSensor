# HydraSensor

Projeto simples de controle de acesso com RFID, API Flask, persistencia em SQLite/CSV e painel web em tempo real via PubNub.

## O que existe no projeto

- `app.py`: API Flask que recebe eventos RFID, grava em SQLite e CSV e publica no PubNub.
- `button.py`: leitor RFID para Raspberry Pi com LEDs e buzzer.
- `pubsub.py`: cliente PubNub usado pela API.
- `index.html`: dashboard em tempo real servido pela propria API.

## Requisitos

- Python 3.9 ou 3.10
- `pip`
- Para usar o leitor RFID: Raspberry Pi com SPI habilitado

## 1. Instalar as dependencias

No diretorio do projeto:

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Linux / Raspberry Pi

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Subir a API

```bash
python app.py
```

A API inicia por padrao em:

- `http://127.0.0.1:5000`
- Dashboard: `http://127.0.0.1:5000/`
- Health check: `http://127.0.0.1:5000/health`

## 3. Executar o leitor RFID

Esse passo faz sentido no Raspberry Pi.

Antes de rodar, habilite o SPI:

```bash
sudo raspi-config
```

Depois acesse `Interface Options` -> `SPI` -> `Enable`.

Com a API rodando, execute:

```bash
python3 button.py
```

Se houver erro de permissao ao acessar GPIO/SPI, rode com permissao elevada.

## 4. Variaveis de ambiente opcionais

A API funciona com valores padrao, mas voce pode sobrescrever:

- `APP_DB_PATH`: caminho do banco SQLite. Padrao: `rfid_access.db`
- `APP_CSV_PATH`: caminho do CSV. Padrao: `rfid_access_log.csv`
- `PUBNUB_SUBSCRIBE_KEY`: chave subscribe do PubNub
- `PUBNUB_PUBLISH_KEY`: chave publish do PubNub
- `PUBNUB_CHANNEL`: nome do canal PubNub. Padrao: `meu_canal`

Exemplo no PowerShell:

```powershell
$env:PUBNUB_CHANNEL = "meu_canal"
python app.py
```

## 5. Fluxo rapido para testar

1. Inicie `app.py`.
2. Abra `http://127.0.0.1:5000/` no navegador.
3. Rode `button.py` no Raspberry Pi.
4. Aproxime uma tag RFID do leitor.
5. Veja o evento aparecer no painel em tempo real.

## Observacoes

- `button.py` depende de hardware e nao deve rodar normalmente no Windows.
- O `index.html` esta usando a chave subscribe e o canal direto no frontend. Se voce trocar o canal no backend, mantenha o mesmo valor no frontend.
- Os eventos ficam salvos em SQLite e tambem em CSV para consulta rapida.
