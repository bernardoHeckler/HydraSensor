# Análise de dados (logs de acesso)

Esta pasta concentra a **exportação do CSV** de eventos de acesso e um **notebook Jupyter** com análises em Pandas, alinhadas aos requisitos do projeto (entradas, saídas, permanência, negados, invasões e ranking de não autorizados).

## Conteúdo

| Item | Descrição |
|------|-----------|
| `exportar_csv.py` | Atualiza `dados/access_events.csv` a partir do ficheiro local do backend ou da API de export. |
| `analise_logs_acesso.ipynb` | Notebook com carregamento dos dados, parâmetros (dia e colaborador) e células que respondem a cada pergunta de análise. |
| `dados/exemplo_access_events.csv` | CSV de exemplo (com eventos fictícios) para o notebook produzir saídas mesmo sem dados reais. |
| `dados/access_events.csv` | Destino do export (gerado por ti; por defeito está no `.gitignore` para não versionar dados sensíveis). |
| `requirements.txt` | Dependências Python para Jupyter e Pandas. |

## Pré-requisitos

- Python 3.10 ou superior (recomendado).
- Na primeira vez, instalar dependências a partir da raiz do repositório ou desta pasta:

```bash
python -m pip install -r analise_dados/requirements.txt
```

## Como obter o CSV atualizado

O backend grava eventos no SQLite e, em paralelo, pode acrescentar linhas ao CSV configurado em `APP_CSV_PATH` (por defeito `backend/rfid_access_log.csv`). Existe ainda o export completo a partir da base de dados:

- **Rota:** `GET /v1/access-events/export.csv` (servidor Flask em execução).

### Opção A — Cópia do ficheiro local do backend

Copia o CSV que o leitor/backend vai preenchendo (mesmo formato de colunas que o registo em base, exceto que o export da API inclui sempre a coluna `id`).

```bash
cd analise_dados
python exportar_csv.py
```

Por defeito a origem é `../backend/rfid_access_log.csv`, ou o caminho definido na variável de ambiente `APP_CSV_PATH` se estiver definida ao correr o script.

### Opção B — Download via API (export a partir da base)

Garante que a API Flask está a correr (por exemplo `python app.py` dentro de `backend`). Depois:

```bash
cd analise_dados
python exportar_csv.py --api
```

URL por defeito: `http://127.0.0.1:5000/v1/access-events/export.csv`. Podes alterar com:

- variável de ambiente `HYDRA_EXPORT_URL`, ou
- argumento `--url "http://..."`.

## Como executar o notebook

1. Exporta ou copia os dados para `dados/access_events.csv` (passo anterior), **ou** deixa o notebook usar apenas o CSV de exemplo.
2. Abre o Jupyter a partir desta pasta (ou abre o ficheiro `.ipynb` no VS Code / Cursor):

```bash
cd analise_dados
jupyter notebook analise_logs_acesso.ipynb
```

3. Executa as células em ordem.
4. Na célula de **parâmetros**, ajusta:
   - `DIA_REFERENCIA` — data no formato `YYYY-MM-DD`;
   - `COLABORADOR_ID` — identificador numérico do colaborador na base;
   - `NOME_COLABORADOR` — apenas para legenda nos resultados.

### Comportamento se não houver `access_events.csv`

Se `dados/access_events.csv` não existir ou for demasiado pequeno, o notebook usa `dados/exemplo_access_events.csv` e mostra um aviso. O exemplo usa o dia `2026-05-10` para bater com os parâmetros por defeito.

## O que o notebook calcula

Corresponde aos tipos de evento gerados pelo backend: `entrada`, `saida`, `acesso_negado`, `invasao`.

1. **Pessoas que entraram num dia** — eventos `entrada` autorizados; mostra total de registos e quantidade de **colaboradores distintos** com pelo menos uma entrada.
2. **Pessoas que saíram num dia** — idem para `saida` autorizada.
3. **Tempo na sala de um colaborador num dia** — emparelha entradas e saídas por ordem de `read_at`; se ficar uma entrada sem saída, o intervalo em aberto vai até **23:59:59** desse dia (lógica alinhada ao relatório do backend).
4. **Tentativas de acesso negado** — contagem de `acesso_negado` no dia.
5. **Tentativas de invasão** — contagem de `invasao` no dia (por exemplo tag desconhecida).
6. **Ranking de não autorizados** — entre `acesso_negado`, agrupa por colaborador (ou por `tag_id` quando não há `collaborator_id`) e ordena por número de tentativas.

## Variáveis de ambiente úteis

| Variável | Efeito |
|----------|--------|
| `APP_CSV_PATH` | Caminho do CSV local usado por `exportar_csv.py` (sem `--api`). |
| `HYDRA_EXPORT_URL` | URL completa do `export.csv` usada por `exportar_csv.py --api`. |

## Versionar o CSV de produção

O ficheiro `dados/.gitignore` ignora `access_events.csv` para evitar commits acidentais com dados reais. Se o teu grupo quiser versionar um export concreto para entrega, remove essa linha do `.gitignore` ou renomeia o ficheiro (por exemplo `access_events_amostra.csv`) e aponta o notebook para esse nome na primeira célula de leitura.
