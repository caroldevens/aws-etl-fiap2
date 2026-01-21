# Tech Challenge FIAP — Fase 2  
## Pipeline Batch B3 na AWS (S3 + Glue + Lambda + Athena) — Raw → Refined em Parquet

Este repositório implementa um pipeline **batch** para coletar dados diários de ações da B3, armazenar em um **Data Lake no S3** (camadas **raw** e **refined**), executar transformações no **AWS Glue (PySpark)**, acionar o fluxo via **S3 → Lambda → Glue**, **catalogar no Glue Data Catalog** e consultar via **SQL no Amazon Athena**.

---

## ✅ Requisitos do Pipeline (mapeamento 1:1 com o enunciado)

| Requisito | Como atendemos |
|---|---|
| **R1** – Coletar dados de ações/índices B3 (granularidade diária) | Glue Job `src/b3_collector.py` coleta via `yfinance` (dados diários) |
| **R2** – Ingerir dados brutos no S3 em Parquet com partição diária | `s3://<bucket>/raw/` em Parquet particionado por `dataproc=yyyyMMdd` |
| **R3** – Bucket aciona Lambda que chama o job Glue | Evento `ObjectCreated` em `raw/` dispara Lambda |
| **R4** – Lambda apenas inicia o job Glue | Lambda chama `glue:StartJobRun` do job `b3_transform` |
| **R5** – Glue com transformações obrigatórias (A/B/C) | Implementadas no `src/b3_transform.py` (detalhadas abaixo) |
| **R6** – Refined em Parquet na pasta `refined/` particionado por data e ticker | `s3://<bucket>/refined/` particionado por `dataproc` e `ticker` |
| **R7** – Catalogar no Glue Catalog e criar tabela | Jobs criam/atualizam tabelas no Glue Catalog + `MSCK REPAIR TABLE` |
| **R8** – Consultar via SQL no Athena | Consultas em `b3_data.stocks_refined` |

---

## 🏗️ Arquitetura

![Diagrama de Arquitetura](docs/arquitetura.png)

**Fluxo ponta a ponta:**
1. **EventBridge (agendamento)** inicia o pipeline (executa o Glue Collector).
2. **Glue Collector (`b3_collector.py`)** coleta dados (yfinance) e grava no S3 em **raw** (Parquet, partição diária).
3. **S3 Event Notification** em `raw/` aciona a **Lambda**.
4. **Lambda (`glue_starter_lambda_function.py`)** apenas inicia o Glue Transform.
5. **Glue Transform (`b3_transform.py`)** lê `raw/`, aplica A/B/C e grava em **refined** (Parquet, partição por `dataproc` e `ticker`).
6. **Glue Data Catalog** é atualizado e as partições são descobertas.
7. **Athena** consulta os dados refinados via SQL.

---

## 🪣 Data Lake no S3 (raw/refined)

> No ambiente de teste, usamos o bucket: `tc2-carol-224328871288` (o nome pode variar por conta).

### Raw (R2)
- **Path:** `s3://<bucket>/raw/`
- **Formato:** Parquet (SNAPPY)
- **Partição:** `dataproc=yyyyMMdd`

Exemplo:
- `s3://<bucket>/raw/dataproc=20260120/part-000.parquet`

### Refined (R6)
- **Path:** `s3://<bucket>/refined/`
- **Formato:** Parquet (SNAPPY)
- **Partições:** `dataproc=yyyyMMdd` e `ticker=<CODIGO>`

Exemplo:
- `s3://<bucket>/refined/dataproc=20260120/ticker=PETR4/part-000.parquet`

---

## 🧾 Schema (visão geral)

### Raw (saída do Collector)
Colunas principais:
- `date`, `open`, `high`, `low`, `close`, `volume`, `dividends`, `stock-splits`, `ticker`
- `dataproc` (**partição**, string `yyyyMMdd`)

### Refined (saída do Transform)
Além das colunas do raw, inclui:
- `preco_fechamento` (**renomeada**)
- `volume_negociado` (**renomeada**)
- `year`, `month` (derivadas de `date`)
- `preco_7d_atras`, `preco_30d_atras`
- `variacao_7d`, `variacao_30d`

---

## 🔄 Transformações obrigatórias (R5) — A/B/C

As transformações foram implementadas no Glue Transform (`src/b3_transform.py`):

### **B) Renomear duas colunas**
- `close` → `preco_fechamento`
- `volume` → `volume_negociado`

### **C) Cálculo baseado em data (diferença entre períodos)**
Cálculo de variação percentual do preço de fechamento em relação a:
- **7 dias atrás** (`variacao_7d`)
- **30 dias atrás** (`variacao_30d`)

Fórmula:
`((preco_atual - preco_anterior) / preco_anterior) * 100`

Implementação:
- Janela por `ticker` ordenada por `date` (`Window.partitionBy("ticker").orderBy("date")`)
- `lag()` de 7 e 30 linhas + tratamento de nulos

### **A) Agrupamento numérico + sumarização/contagem/soma**
Sumarização mensal por `ticker`, `year` e `month` com:
- `count(*)` → `total_registros`
- `sum(volume_negociado)` → `volume_total_mes`
- `avg(preco_fechamento)` → `preco_medio_mes`
- `min(preco_fechamento)` e `max(preco_fechamento)`
- médias de `variacao_7d` e `variacao_30d`

> O job também registra no log exemplos de agregação, facilitando a validação.

---

## 🗂️ Glue Catalog e Athena (R7/R8)

Tabelas externas criadas/atualizadas no Glue Data Catalog:
- **Raw:** `b3_data.stocks`
- **Refined:** `b3_data.stocks_refined`

As partições são descobertas com:
- `MSCK REPAIR TABLE b3_data.stocks;`
- `MSCK REPAIR TABLE b3_data.stocks_refined;`

### Consultas de exemplo (Athena)
```sql
-- Preview refined
SELECT * FROM b3_data.stocks_refined LIMIT 10;

-- Consulta por partição (mais barata e rápida)
SELECT date, ticker, preco_fechamento, volume_negociado, variacao_7d, variacao_30d
FROM b3_data.stocks_refined
WHERE dataproc = 'YYYYMMDD' AND ticker = 'PETR4'
ORDER BY date;

-- Sumarização mensal (Requisito A)
SELECT ticker, year, month,
       COUNT(*) AS total_registros,
       SUM(volume_negociado) AS volume_total_mes,
       ROUND(AVG(preco_fechamento), 2) AS preco_medio_mes
FROM b3_data.stocks_refined
GROUP BY ticker, year, month
ORDER BY ticker, year, month;
'###

# 📁 Estrutura do repositório
.
├── docs/
│   └── arquitetura.png
├── infra/                         # Terraform (opcional, quando aplicável)
├── src/
│   ├── b3_collector.py
│   ├── b3_transform.py
│   └── glue_starter_lambda_function.py
└── README.md

# 🧰 Tecnologias

Terraform (IaC)
AWS Glue (PySpark)
AWS Lambda
Amazon S3
AWS Glue Data Catalog
Amazon Athena
Amazon EventBridge
Python / Pandas / yfinance / boto3

# 👥 Equipe

Hugo de Almeida Ribeiro
Matheus de Oliveira Silvestre
Carolina Devens Rabelo
Francisco Valterlan de Oliveira Dantas
