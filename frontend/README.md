# Frontend HydraSensor

O frontend e o painel web do HydraSensor. Ele permite login, gerenciamento de colaboradores, monitoramento em tempo real e consulta/exportacao de logs.

## 1. Tecnologias

- React 18.
- TypeScript.
- Vite.
- React Router.
- PubNub JavaScript SDK.
- Lucide React para icones.

## 2. Estrutura

```text
frontend/
  src/
    App.tsx
    main.tsx
    services/api.ts
    types.ts
    pages/
      Login/
      Register/
      Dashboard/
    components/
      Button/
      Input/
      EventCard/
```

Arquivos principais:

- `src/App.tsx`: rotas do frontend.
- `src/services/api.ts`: chamadas HTTP para o backend.
- `src/types.ts`: tipos compartilhados do frontend.
- `src/pages/Login/Login.tsx`: login.
- `src/pages/Register/Register.tsx`: cadastro de usuario.
- `src/pages/Dashboard/Dashboard.tsx`: painel principal.

## 3. Como Funciona

O frontend conversa com o backend de duas formas:

1. HTTP via `/v1/...` para buscar historico, colaboradores, logs e resumos.
2. PubNub para receber eventos em tempo real.

Durante desenvolvimento, o Vite faz proxy das chamadas `/v1` para o backend:

```text
frontend -> /v1/access-events -> backend Flask
```

O token de login e salvo em `localStorage` e enviado como:

```text
Authorization: Bearer <token>
```

## 4. Telas

### Login

Entrada do sistema.

Credenciais iniciais:

```text
usuario: admin
senha: admin123
```

### Dashboard

O dashboard possui tres abas:

- `Monitoramento`: ultimas leituras, entradas, saidas, acessos negados, invasoes, pessoas dentro da sala e alertas recentes.
- `Colaboradores`: cadastro, listagem, edicao e inativacao de colaboradores.
- `Logs`: historico de eventos e botao para exportar CSV.

## 5. Instalar Dependencias

```bash
cd frontend
npm install
```

## 6. Rodar Em Desenvolvimento

Com o backend rodando em `http://127.0.0.1:5000`:

```bash
cd frontend
VITE_API_PROXY_TARGET=http://127.0.0.1:5000 VITE_PUBNUB_CHANNEL=meu_canal npm run dev -- --host 0.0.0.0
```

Acessar:

```text
http://127.0.0.1:5173
```

Na rede local:

```text
http://IP_DA_RASPBERRY:5173
```

## 7. Build

```bash
cd frontend
npm run build
```

Saida gerada em:

```text
frontend/dist/
```

`dist/` nao deve ser commitado.

## 8. Variaveis De Ambiente

```bash
VITE_API_PROXY_TARGET=http://127.0.0.1:5000
VITE_PUBNUB_SUBSCRIBE_KEY=sua_subscribe_key
VITE_PUBNUB_CHANNEL=meu_canal
```

Notas:

- `VITE_API_PROXY_TARGET` so afeta o proxy do Vite em desenvolvimento.
- `VITE_PUBNUB_CHANNEL` precisa ser igual ao `PUBNUB_CHANNEL` do backend.
- Se o PubNub estiver indisponivel, o botao `Atualizar` ainda busca dados pela API.

## 9. Tutorial De Uso

1. Abra o painel.
2. Faca login.
3. Entre em `Colaboradores`.
4. Cadastre nome, matricula, cargo e tag RFID.
5. Marque ou desmarque permissao de acesso a sala.
6. Volte para `Monitoramento`.
7. Aproxime a tag no leitor RFID.
8. Veja o evento aparecer em tempo real.
9. Entre em `Logs` para consultar historico.
10. Exporte CSV quando precisar analisar no Pandas.

## 10. Eventos Mostrados No Painel

| Evento | Quando aparece |
| --- | --- |
| `entrada` | colaborador autorizado entra na sala |
| `saida` | colaborador autorizado sai da sala |
| `acesso_negado` | colaborador cadastrado esta inativo ou sem permissao |
| `invasao` | tag nao cadastrada |

