# README Principal - HydraSensor

Este e o guia principal para apresentar, instalar e executar o HydraSensor em uma Raspberry Pi 4.

## 1. Apresentacao Do Projeto

HydraSensor controla o acesso fisico a uma sala restrita. Uma Raspberry Pi 4 le crachas RFID, consulta permissoes no backend, aciona LEDs/buzzer e registra todos os eventos para monitoramento em tempo real e analise futura.

O sistema foi feito para o cenario do PDF: uma sala de seguranca de um estudio de jogos com materiais protegidos por NDA.

## 2. Componentes

```text
Raspberry Pi + RFID + LEDs + buzzer
        |
        | HTTP
        v
Backend Flask
        |
        +--> SQLite
        +--> CSV
        +--> PubNub
                 |
                 v
Frontend React
```

Processos que rodam na Raspberry:

- API Flask em `backend/app.py`.
- Painel React/Vite em `frontend/`.
- Leitor RFID em `backend/button.py`.

## 3. Requisitos

Hardware:

- Raspberry Pi 4.
- Leitor RFID MFRC522.
- Tags RFID.
- LED verde.
- LED vermelho.
- Buzzer.
- Resistores para LEDs.

Software:

- Raspberry Pi OS.
- Python 3.10+.
- Node.js 18+.
- Git.
- SPI habilitado.

## 4. Preparar A Raspberry Pi

Atualize o sistema:

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y git python3 python3-venv python3-pip python3-dev build-essential sqlite3 nodejs npm
```

Confira as versoes:

```bash
python3 --version
node --version
npm --version
```

Se o Node estiver abaixo da versao 18, atualize antes de rodar o frontend.

## 5. Habilitar SPI

```bash
sudo raspi-config
```

No menu:

1. `Interface Options`
2. `SPI`
3. `Enable`
4. Reinicie a Raspberry Pi.

Valide:

```bash
ls /dev/spidev*
```

Resultado esperado:

```text
/dev/spidev0.0  /dev/spidev0.1
```

## 6. Ligacao Do Hardware

O codigo usa numeracao BCM.

RFID MFRC522:

| MFRC522 | Raspberry Pi 4 |
| --- | --- |
| 3.3V | 3.3V, pino fisico 1 |
| GND | GND, pino fisico 6 |
| SDA/SS | GPIO8/CE0, pino fisico 24 |
| SCK | GPIO11/SCLK, pino fisico 23 |
| MOSI | GPIO10/MOSI, pino fisico 19 |
| MISO | GPIO9/MISO, pino fisico 21 |
| RST | GPIO25, pino fisico 22 |
| IRQ | Nao conectar |

Atuadores:

| Componente | GPIO BCM | Pino fisico |
| --- | --- | --- |
| LED verde | GPIO17 | 11 |
| LED vermelho | GPIO27 | 13 |
| Buzzer | GPIO22 | 15 |

Use 3.3V no MFRC522. Nao alimente o leitor RFID com 5V.

## 7. Baixar O Projeto

```bash
mkdir -p ~/projetos
cd ~/projetos
git clone URL_DO_REPOSITORIO HydraSensor
cd HydraSensor
```

Se o repositorio ja existir:

```bash
cd ~/projetos/HydraSensor
git pull
```

## 8. Configurar Backend

```bash
cd ~/projetos/HydraSensor/backend
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
```

Teste a API:

```bash
APP_HOST=0.0.0.0 APP_PORT=5000 .venv/bin/python app.py
```

Em outro terminal:

```bash
curl http://127.0.0.1:5000/health
```

Resposta esperada:

```json
{
  "status": "ok"
}
```

## 9. Configurar Frontend

```bash
cd ~/projetos/HydraSensor/frontend
npm install
```

Rodar o painel:

```bash
VITE_API_PROXY_TARGET=http://127.0.0.1:5000 VITE_PUBNUB_CHANNEL=meu_canal npm run dev -- --host 0.0.0.0
```

Acessos:

```text
Na Raspberry: http://127.0.0.1:5173
Na rede:      http://IP_DA_RASPBERRY:5173
```

Descobrir o IP:

```bash
hostname -I
```

## 10. Rodar O Sistema Completo

Use tres terminais.

Terminal 1 - backend:

```bash
cd ~/projetos/HydraSensor/backend
APP_HOST=0.0.0.0 APP_PORT=5000 .venv/bin/python app.py
```

Terminal 2 - frontend:

```bash
cd ~/projetos/HydraSensor/frontend
VITE_API_PROXY_TARGET=http://127.0.0.1:5000 VITE_PUBNUB_CHANNEL=meu_canal npm run dev -- --host 0.0.0.0
```

Terminal 3 - RFID:

```bash
cd ~/projetos/HydraSensor/backend
API_BASE_URL=http://127.0.0.1:5000 .venv/bin/python button.py
```

Se houver erro de permissao no GPIO/SPI:

```bash
cd ~/projetos/HydraSensor/backend
sudo API_BASE_URL=http://127.0.0.1:5000 .venv/bin/python button.py
```

## 11. Como Usar O Painel

Login inicial:

```text
usuario: admin
senha: admin123
```

Abas:

- `Monitoramento`: ultimas leituras, entradas, saidas, pessoas dentro da sala e alertas.
- `Colaboradores`: cadastro e edicao de nome, matricula, cargo, tag RFID, permissao e status.
- `Logs`: historico completo e exportacao CSV.

## 12. Como Cadastrar E Testar Uma Tag

1. Abra o frontend.
2. Faca login.
3. Entre em `Colaboradores`.
4. Cadastre nome, matricula, cargo e tag RFID.
5. Marque `Possui acesso a sala do projeto` quando o colaborador for autorizado.
6. Salve.
7. Aproxime a tag no leitor.
8. Veja o evento no `Monitoramento`.

Regras:

| Situacao | Evento |
| --- | --- |
| Tag desconhecida | `invasao` |
| Colaborador inativo | `acesso_negado` |
| Colaborador ativo sem permissao | `acesso_negado` |
| Colaborador autorizado fora da sala | `entrada` |
| Colaborador autorizado dentro da sala | `saida` |
| Colaborador autorizado entrando de novo no mesmo dia | `entrada` com mensagem de retorno |

## 13. Dados E Logs

Arquivos gerados pelo backend:

- SQLite: `backend/rfid_access.db`
- CSV: `backend/rfid_access_log.csv`
- Cache do leitor: `backend/rfid_cache.json`
- Backup offline do leitor: `backend/rfid_reader_backup.csv`

Exportacao pelo navegador:

```text
http://IP_DA_RASPBERRY:5000/v1/access-events/export.csv
```

## 14. Perda De Conexao

Ao iniciar, o leitor chama:

```text
GET /v1/device/bootstrap
```

Ele salva colaboradores e permissoes em `rfid_cache.json`.

Se a API cair:

- a validacao continua com o cache local;
- leituras pendentes sao salvas em `rfid_reader_backup.csv`;
- ao reiniciar com conexao, o leitor tenta sincronizar em `/v1/access-events/sync`.

Limitacao do MVP: mudancas de permissao feitas enquanto o leitor esta offline so chegam ao leitor quando ele conseguir atualizar o cache.

## 15. Variaveis De Ambiente

Backend:

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

Frontend:

```bash
VITE_API_PROXY_TARGET=http://127.0.0.1:5000
VITE_PUBNUB_SUBSCRIBE_KEY=sua_subscribe_key
VITE_PUBNUB_CHANNEL=meu_canal
```

Leitor:

```bash
API_BASE_URL=http://127.0.0.1:5000
```

## 16. Roteiro De Apresentacao

1. Mostrar a arquitetura.
2. Subir backend, frontend e leitor.
3. Acessar o painel.
4. Cadastrar colaborador autorizado.
5. Ler tag e mostrar `entrada`.
6. Ler a mesma tag e mostrar `saida`.
7. Mostrar colaborador sem permissao gerando `acesso_negado`.
8. Mostrar tag desconhecida gerando `invasao`.
9. Mostrar pessoas dentro da sala e alertas recentes.
10. Exportar CSV.
11. Abrir o notebook Pandas.

## 17. Pendencias Para Entrega Final

- Testar fisicamente na Raspberry Pi 4.
- Executar o notebook e salvar as saidas das celulas.
- Gerar a documentacao final em PDF.
- Gerar a apresentacao final em PDF.
- Inserir fotos reais do MVP.

