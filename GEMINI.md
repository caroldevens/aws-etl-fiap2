# GEMINI.md: Project Overview for aws-etl-fiap

This document provides a comprehensive overview of the `aws-etl-fiap` project, designed to facilitate understanding and future development.

## Project Overview

This project implements an end-to-end ETL (Extract, Transform, Load) pipeline on AWS for financial market data. Its primary purpose is to collect daily stock data from the Brazilian stock exchange (B3), process it, and make it available for SQL-based analysis via Amazon Athena.

### Core Technologies

*   **Infrastructure as Code:** Terraform
*   **Cloud Provider:** Amazon Web Services (AWS)
*   **Key AWS Services:**
    *   **AWS Glue:** For serverless Spark-based data extraction and transformation (ETL).
    *   **AWS Lambda:** For event-driven orchestration (triggering the Glue transformation job).
    *   **Amazon S3:** For data storage (raw and refined data lakes) and hosting scripts.
    *   **Amazon Athena:** For interactive querying of the refined data using standard SQL.
    *   **Amazon EventBridge:** For scheduling the start of the daily pipeline.
*   **Primary Language:** Python
*   **Core Libraries:**
    *   **PySpark:** The Python API for Apache Spark, used within AWS Glue to perform large-scale, distributed data processing during the transformation phase.
    *   **Pandas:** Used in the collection script for initial data handling and structuring after fetching it from the `yfinance` API.
    *   **yfinance:** The library used to extract financial market data from Yahoo Finance.
    *   **Boto3:** The AWS SDK for Python, enabling the Lambda function to programmatically interact with other AWS services, specifically to start the Glue transformation job.

### Architecture

The architecture is a decoupled, event-driven pipeline:

1.  **Scheduled Trigger:** An Amazon EventBridge rule is configured to run daily, which starts the initial data collection process.
2.  **Extraction (Glue Job):** The `b3_collector.py` script runs as an AWS Glue job. It uses the `yfinance` library to fetch historical stock data for a predefined list of tickers. The raw data is then saved in Parquet format to `s3://<bucket-name>/raw/`, partitioned by the processing date.
3.  **S3 Trigger & Orchestration (Lambda):** The arrival of a new object in the `raw/` S3 prefix automatically triggers the `glue_starter_lambda_function.py` Lambda function. This function's sole responsibility is to start the next stage of the pipeline.
4.  **Transformation (Glue Job):** The Lambda function invokes a second AWS Glue job running the `b3_transform.py` script. This job reads the raw data, performs transformations (e.g., renames columns, calculates price variations over time), and cleans the data.
5.  **Load (S3 & Glue Catalog):** The transformed, refined data is written in Parquet format to `s3://<bucket-name>/refined/`, partitioned by both processing date and stock ticker for efficient querying. The Glue job also creates or updates tables in the AWS Glue Data Catalog, making the datasets schema-aware and ready for querying.
6.  **Analysis (Athena):** End-users can query the refined data directly using standard SQL through Amazon Athena.

## Building and Running

The project's infrastructure and deployment are managed via Terraform. The Python scripts are executed within the AWS Glue and Lambda services.

### Infrastructure Deployment

1.  **Navigate to the infrastructure directory:**
    ```bash
    cd infra/<module_directory> 
    # e.g., cd infra/s3
    ```

2.  **Initialize Terraform:**
    This command downloads the necessary provider plugins. It only needs to be run once per module or after configuration changes.
    ```bash
    terraform init
    ```

3.  **Plan the deployment:**
    This command shows you what changes will be made to your AWS infrastructure. It's a safe way to preview changes.
    ```bash
    terraform plan
    ```

4.  **Apply the changes:**
    This command provisions the resources in your AWS account as defined in the Terraform files.
    ```bash
    terraform apply
    ```

### Running the Pipeline

The pipeline is designed to run automatically.
1.  **Automated Start:** The EventBridge schedule will trigger the `b3_collector` job at its configured time.
2.  **Event-Driven Flow:** The rest of the pipeline (Lambda trigger and `b3_transform` job) executes automatically in response to data being written to S3.
3.  **Manual Trigger:** You can manually start the pipeline by running the `b3_collector` Glue job from the AWS Management Console.

## Development Conventions

*   **Modular Terraform:** The Terraform code is organized into modules (`infra/s3`, `infra/iam`, etc.) to promote reusability and maintainability. Each module is responsible for a specific component of the architecture.
*   **Python Scripts:**
    *   `b3_collector.py`: Handles data extraction. It uses `yfinance` and converts the data into a PySpark DataFrame before saving to S3.
    *   `b3_transform.py`: Handles the transformation logic using PySpark DataFrame operations. It fulfills specific business requirements like renaming columns and calculating new fields based on date logic.
    *   `glue_starter_lambda_function.py`: A simple Python function for AWS Lambda responsible for starting a Glue job.
*   **Data Partitioning:**
    *   Raw data is partitioned by `dataproc` (processing date).
    *   Refined data is partitioned by `dataproc` and `ticker` to optimize analytical queries in Athena.
