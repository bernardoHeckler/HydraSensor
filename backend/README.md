# Backend HydraSensor

O backend e a API central do HydraSensor. Ele recebe leituras RFID, consulta permissoes, registra eventos, exporta logs e envia atualizacoes em tempo real para o frontend via PubNub.

## 1. Arquivos Principais

```text
backend/
  app.py
  config.py
  database.py
  button.py
  simulate_reader.py
  pubsub.py
  routes/
  services/
  analysis_access_logs.ipynb
```

- `app.py`: inicializa Flask, cria banco e registra rotas.
- `config.py`: centraliza variaveis de ambiente.
- `database.py`: cria tabelas SQLite e usuario inicial.
- `button.py`: script do leitor RFID na Raspberry Pi.
- `simulate_reader.py`: simula uma leitura RFID sem hardware.
- `pubsub.py`: publica eventos no PubNub.
- `routes/`: camada HTTP.
- `services/`: regras de negocio.
- `analysis_access_logs.ipynb`: analise Pandas.

## 2. Como Funciona

Quando o leitor RFID envia uma tag:

1. `routes/access_event_routes.py` recebe `POST /v1/access-events`.
2. `services/access_event_service.py` normaliza o payload.
3. O backend consulta `collaborators` pelo `rfid_tag`.
4. O backend decide o tipo do evento.
5. O evento e salvo no SQLite.
6. O evento e adicionado ao CSV.
7. O evento e publicado no PubNub.
8. O frontend recebe o evento em tempo real.

Regras de evento:

| Condicao | Evento |
| --- | --- |
| Tag nao encontrada | `invasao` |
| Colaborador inativo | `acesso_negado` |
| Colaborador sem permissao | `acesso_negado` |
| Colaborador autorizado e fora da sala | `entrada` |
| Colaborador autorizado e dentro da sala | `saida` |

## 3. Banco De Dados

Arquivo padrao:

```text
backend/rfid_access.db
```

Tabelas:

- `users`: usuarios do painel.
- `collaborators`: colaboradores, matriculas, cargos, tags e permissoes.
- `access_events`: entradas, saidas, acessos negados e invasoes.

O usuario inicial e criado automaticamente:

```text
usuario: admin
senha: admin123
```

## 4. Instalar Dependencias

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
```

`requirements.txt` contem dependencias da API, Pandas e hardware RFID/GPIO.

## 5. Rodar A API

```bash
cd backend
APP_HOST=0.0.0.0 APP_PORT=5000 .venv/bin/python app.py
```

Teste:

```bash
curl http://127.0.0.1:5000/health
```

Resposta:

```json
{
  "status": "ok"
}
```

## 6. Rotas Principais

Autenticacao:

- `POST /v1/auth/login`
- `POST /v1/auth/register`

Colaboradores:

- `GET /v1/collaborators`
- `POST /v1/collaborators`
- `GET /v1/collaborators/<id>`
- `PUT /v1/collaborators/<id>`
- `DELETE /v1/collaborators/<id>`

Eventos:

- `GET /v1/access-events`
- `POST /v1/access-events`
- `POST /v1/access-events/sync`
- `GET /v1/access-events/export.csv`

Dispositivo e monitoramento:

- `GET /v1/device/bootstrap`
- `GET /v1/monitoring/summary`
- `GET /v1/reports/daily-presence`

Rotas de colaboradores exigem:

```text
Authorization: Bearer admin-demo-token
```

O frontend recebe esse token ao fazer login.

## 7. Rodar O Leitor RFID

Com a API rodando:

```bash
cd backend
API_BASE_URL=http://127.0.0.1:5000 .venv/bin/python button.py
```

Se houver erro de GPIO/SPI:

```bash
cd backend
sudo API_BASE_URL=http://127.0.0.1:5000 .venv/bin/python button.py
```

Pinos usados:

| Componente | GPIO BCM |
| --- | --- |
| LED verde | 17 |
| LED vermelho | 27 |
| Buzzer | 22 |

## 8. Testar Sem RFID

Use o simulador:

```bash
cd backend
.venv/bin/python simulate_reader.py 498103025204
```

Se a tag existir em `collaborators`, o backend aplica as regras reais. Se nao existir, registra `invasao`.

## 9. PubNub

Variaveis:

```bash
PUBNUB_SUBSCRIBE_KEY=sua_subscribe_key
PUBNUB_PUBLISH_KEY=sua_publish_key
PUBNUB_CHANNEL=meu_canal
```

O backend publica no canal configurado. O frontend deve assinar o mesmo canal.

Se o PubNub falhar, o evento continua salvo no SQLite/CSV. O tempo real pode falhar, mas os dados nao sao perdidos.

## 10. CSV E Analise

Exportar logs:

```text
GET /v1/access-events/export.csv
```

Relatorio diario:

```text
GET /v1/reports/daily-presence?date=YYYY-MM-DD
```

O notebook `analysis_access_logs.ipynb` pode ler o CSV ou consultar dados exportados para responder:

- quantas pessoas entraram;
- quantas sairam;
- tempo de permanencia;
- tentativas negadas;
- tentativas de invasao;
- ranking de colaboradores sem autorizacao.

## 11. Variaveis De Ambiente

```bash
APP_HOST=0.0.0.0
APP_PORT=5000
APP_DB_PATH=rfid_access.db
APP_CSV_PATH=rfid_access_log.csv
ADMIN_TOKEN=admin-demo-token
PUBNUB_SUBSCRIBE_KEY=sua_subscribe_key
PUBNUB_PUBLISH_KEY=sua_publish_key
PUBNUB_CHANNEL=meu_canal
```

