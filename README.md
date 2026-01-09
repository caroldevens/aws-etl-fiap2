# AWS ETL Fiap

Este projeto implementa um pipeline de ETL (Extração, Transformação e Carga) para dados do mercado financeiro, utilizando serviços da AWS. O objetivo é extrair dados de ações, processá-los e armazená-los no Amazon S3 de forma estruturada.

## Arquitetura

A arquitetura utiliza os seguintes serviços da AWS:

- **EventBridge**: Utilizado para iniciar a execução agendada da máquina de estado do Step Functions, permitindo execuções periódicas do pipeline (ex: diariamente).
- **AWS Step Functions**: Orquestra o fluxo de trabalho ETL, gerenciando a execução de cada etapa de forma coordenada e resiliente.
- **Amazon S3 (Simple Storage Service)**: Armazena os dados em diferentes estágios do processo ETL.


### Estrutura do S3

Os dados são organizados no S3 da seguinte maneira:

- `s3://fiap-etl/raw/`: Armazena os dados brutos extraídos da fonte (Yahoo Finance).
- `s3://fiap-etl/interim/`: Armazena os dados após a etapa de transformação.
- `s3://fiap-etl/final/`: Armazena os dados finais, prontos para consumo por outras aplicações ou para análise.

## Execução

O coração do ETL é o script `etl.py`, que é executado em um ambiente containerizado com Docker. A imagem Docker é construída a partir do `Dockerfile` no projeto.

O AWS Step Functions é configurado para executar este container como uma tarefa, passando os parâmetros necessários para a execução do script.

### Script `etl.py`

Este script utiliza a biblioteca `yfinance` para extrair dados históricos de ações. Atualmente, está configurado para extrair dados do ticker `ITUB4.SA`.

## Dependências

As dependências Python do projeto estão listadas no arquivo `requirements.txt`:

- `yfinance`: Para extração de dados do Yahoo Finance.
- `matplotlib`: Para visualização de dados (usado para testes locais).
