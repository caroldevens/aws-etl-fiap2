
# ADR-001: Arquitetura do Pipeline de Dados com Terraform

**Status:** Proposto

## Contexto

O objetivo é construir um pipeline de dados na AWS para atender aos requisitos do projeto. Este pipeline será responsável por extrair dados diários de ações, processá-los e disponibilizá-los para análise via SQL. A infraestrutura para este pipeline deve ser criada e gerenciada como código (IaC) utilizando Terraform.

## Requisitos do Pipeline

*   **Requisito 1:** Scrap de dados de ações ou índices da B3 (granularidade diária).
*   **Requisito 2:** Os dados brutos devem ser ingeridos no S3 em formato parquet com partição diária.
*   **Requisito 3:** O bucket deve acionar uma lambda, que por sua vez irá chamar o job de ETL no Glue.
*   **Requisito 4:** A lambda pode ser em qualquer linguagem. Ela apenas deverá iniciar o job Glue.
*   **Requisito 5:** O job Glue deve conter as seguintes transformações obrigatórias:
    *   A: Agrupamento numérico, sumarização, contagem ou soma.
    *   B: Renomear duas colunas existentes.
    *   C: Realizar um cálculo com base na data.
*   **Requisito 6:** Os dados refinados no job Glue devem ser salvos no formato parquet em uma pasta chamada `refined`, particionado por data e pelo nome ou código da ação/índice.
*   **Requisito 7:** O job Glue deve automaticamente catalogar o dado no Glue Catalog e criar uma tabela.
*   **Requisito 8:** Os dados devem estar disponíveis e serem consultados usando SQL através do Athena.

## Fluxo da Arquitetura Proposta

1.  **Agendamento (Diário):** O Amazon EventBridge Scheduler aciona uma função Lambda de extração (**Requisito 1**).
2.  **Extração (Lambda):** A função Lambda (`extractor_lambda`) busca os dados de ações usando a biblioteca `yfinance`.
3.  **Armazenamento (S3 Raw):** A Lambda salva os dados brutos em formato Parquet no bucket S3, no prefixo `raw/` com partição diária (**Requisito 2**).
4.  **Gatilho (S3/Lambda):** O novo objeto no S3 aciona uma segunda função Lambda (`glue_starter`) (**Requisito 3**).
5.  **Início do ETL (Lambda):** A função `glue_starter` inicia o job de ETL no AWS Glue (**Requisito 4**).
6.  **Transformação (Glue):** O job do Glue processa os dados, aplica as transformações (**Requisito 5**) e os salva no prefixo `refined/` com as partições corretas (**Requisito 6**).
7.  **Catálogo e Consulta (Glue/Athena):** O job do Glue atualiza o catálogo de dados (**Requisito 7**), tornando os dados refinados consultáveis via Amazon Athena (**Requisito 8**).

## Decisão

Adotaremos o Terraform para provisionar toda a infraestrutura na AWS. A estrutura será modular, alinhada com os componentes do pipeline:

1.  **Gerenciamento de Estado do Terraform (Backend S3):**
    *   Para garantir a segurança e a colaboração, o arquivo de estado do Terraform (`.tfstate`) será armazenado remotamente em um bucket S3 dedicado.
    *   Isso resolve a desvantagem do gerenciamento de estado local.

2.  **EventBridge:**
    *   Um `aws_scheduler_schedule` será criado para acionar a função Lambda de extração diariamente, cumprindo o **Requisito 1**.

3.  **S3 (Simple Storage Service):**
    *   Um único bucket S3 (`aws_s3_bucket`) será criado para armazenar os dados e os scripts da aplicação.
    *   O bucket terá os prefixos: `raw/` (**Requisito 2**), `refined/` (**Requisito 6**) e `scripts/`.

4.  **Funções Lambda:**
    *   **Lambda de Extração:** Uma função (`aws_lambda_function`) contendo o código de `src/extractor_lambda_function.py`.
    *   **Lambda de Início do Glue:** Uma segunda função (`aws_lambda_function`) com o código de `src/glue_starter_lambda_function.py`, acionada por eventos S3 para iniciar o job do Glue, atendendo ao **Requisito 3** e **Requisito 4**.
    *   As funções terão IAM Roles (`aws_iam_role`) com permissões específicas.

5.  **Glue (ETL e Catálogo de Dados):**
    *   **Glue Job:** Um `aws_glue_job` será provisionado. O script (`src/glue_etl.py`) conterá a lógica para o **Requisito 5**.
    *   **Glue Catalog:** Um banco de dados (`aws_glue_catalog_database`) será criado. O job do Glue será responsável por catalogar os dados refinados, conforme o **Requisito 7**.
    *   O job terá uma IAM Role com permissões para ler de `raw/`, escrever em `refined/` e gerenciar o catálogo.

6.  **Scripts da Aplicação:**
    *   `src/extractor_lambda_function.py`: Script Python para extrair os dados.
    *   `src/glue_starter_lambda_function.py`: Script Python para iniciar o job do Glue.
    *   `src/glue_etl.py`: Script PySpark para o Glue, contendo a lógica de ETL.

### Estrutura de Módulos Terraform Proposta

```
infra/
├── main.tf             # Orquestrador dos módulos
├── backend.tf          # Configuração do backend S3
├── ...
├── tf-backend/         # (Separado) Módulo para criar o bucket do .tfstate
│   └── main.tf
├── eventbridge/
│   └── main.tf         # Regra do EventBridge Scheduler
├── lambda-extractor/
│   └── main.tf         # Lambda de extração + IAM Role
├── lambda-glue-starter/
│   └── main.tf         # Lambda de início do Glue + IAM Role + Gatilho S3
├── glue/
│   └── main.tf         # Glue Job, Glue Database, IAM Role
└── s3/
    └── main.tf         # S3 Bucket para dados e scripts
```

## Consequências

### Vantagens
*   **Reprodutibilidade:** A infraestrutura pode ser recriada de forma consistente.
*   **Versionamento:** Toda a arquitetura é versionada no Git.
*   **Modularidade:** A separação de recursos facilita a manutenção.
*   **Automação:** O pipeline é totalmente agendado e automatizado.
*   **Estado Seguro:** O estado do Terraform é gerenciado de forma segura e remota.

### Desvantagens
*   **Complexidade Inicial:** A configuração do Terraform e dos módulos requer conhecimento da ferramenta.
*   **Custos:** Os recursos da AWS incorrerão em custos.
*   **Cold Start:** As funções Lambda podem ter um "cold start", mas isso não é crítico para um pipeline diário.
