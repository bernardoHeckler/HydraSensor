# HydraSensor

HydraSensor e um sistema de controle de acesso para uma sala de seguranca usando Raspberry Pi 4, leitor RFID, LEDs, buzzer, API Flask, SQLite, CSV, PubNub e painel web React.

O projeto foi organizado para atender ao trabalho de Hardware Architecture: controlar acesso fisico, registrar entradas/saidas, identificar acessos negados e invasoes, exibir monitoramento em tempo real e gerar dados para analise com Pandas.

## Visao Geral

Fluxo principal:

```text
RFID na Raspberry Pi
        |
        v
backend/button.py
        |
        | HTTP
        v
backend/app.py
        |
        +--> SQLite
        +--> CSV
        +--> PubNub
                 |
                 v
frontend React
```

Componentes:

- `backend/`: API Flask, banco SQLite, regras de acesso, leitor RFID, exportacao CSV e PubNub.
- `frontend/`: painel React/Vite para login, monitoramento, colaboradores e logs.
- `backend/analysis_access_logs.ipynb`: notebook Pandas para analise dos logs.
- `README-PRINCIPAL.md`: guia completo para rodar tudo na Raspberry Pi 4.

## O Que O Sistema Faz

- Le tag RFID no Raspberry Pi.
- Verifica se a tag esta cadastrada.
- Verifica se o colaborador esta ativo.
- Verifica se o colaborador tem acesso a sala.
- Registra `entrada` e `saida`.
- Registra `acesso_negado` para colaborador cadastrado sem permissao ou inativo.
- Registra `invasao` para tag desconhecida.
- Aciona LED verde, LED vermelho e buzzer conforme o resultado.
- Salva eventos em SQLite e CSV.
- Publica eventos no PubNub para o frontend em tempo real.
- Permite cadastrar, editar, listar e inativar colaboradores.
- Exporta logs para analise com Pandas.
- Mantem cache local no leitor RFID para perda temporaria de conexao.

## Estrutura Do Projeto

```text
HydraSensor/
  backend/
    app.py
    button.py
    database.py
    pubsub.py
    routes/
    services/
    analysis_access_logs.ipynb
    README.md
  frontend/
    src/
    package.json
    vite.config.ts
    README.md
  README.md
  README-PRINCIPAL.md
```

## Como Rodar Rapidamente

Backend:

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
APP_HOST=0.0.0.0 APP_PORT=5000 .venv/bin/python app.py
```

Frontend:

```bash
cd frontend
npm install
VITE_API_PROXY_TARGET=http://127.0.0.1:5000 npm run dev -- --host 0.0.0.0
```

Leitor RFID na Raspberry:

```bash
cd backend
API_BASE_URL=http://127.0.0.1:5000 .venv/bin/python button.py
```

Acesse:

```text
http://IP_DA_RASPBERRY:5173
```

Credenciais iniciais:

```text
usuario: admin
senha: admin123
```

## Fluxo De Demonstracao

1. Suba o backend.
2. Suba o frontend.
3. Suba o leitor RFID.
4. Acesse o painel.
5. Faca login.
6. Cadastre um colaborador com tag RFID.
7. Aproxime a tag autorizada e demonstre `entrada`.
8. Aproxime novamente e demonstre `saida`.
9. Cadastre ou edite um colaborador sem permissao e demonstre `acesso_negado`.
10. Aproxime uma tag nao cadastrada e demonstre `invasao`.
11. Abra a aba `Logs` e exporte o CSV.

## Documentacao

- Guia principal de uso na Raspberry Pi: [README-PRINCIPAL.md](README-PRINCIPAL.md)
- Backend: [backend/README.md](backend/README.md)
- Frontend: [frontend/README.md](frontend/README.md)

## Aderencia Ao PDF

Atendido no codigo:

- aplicacao embarcada com Raspberry Pi, RFID, LED e buzzer;
- verificacao de tag, permissao, ativo/inativo e tags desconhecidas;
- identificacao de entrada e saida;
- monitoramento de permanencia por relatorio diario;
- registro de tentativas nao permitidas;
- registro de tentativas de invasao;
- backend Flask com SQLite;
- comunicacao HTTP entre leitor e backend;
- painel web com login;
- CRUD de colaboradores, tags e permissoes;
- pagina de monitoramento em tempo real;
- cache local para perda de conexao;
- exportacao CSV;
- notebook Pandas.

Pendencias de entrega fora do codigo:

- executar o notebook e salvar as saidas das celulas;
- testar fisicamente na Raspberry Pi 4;
- preparar documentacao final em PDF;
- preparar apresentacao final em PDF;
- incluir fotos reais do MVP.

