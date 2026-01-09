# GEMINI.md: AWS ETL Fiap

## Project Overview

This project is a Python-based ETL (Extract, Transform, Load) pipeline designed to fetch financial market data and process it using AWS services. The primary goal is to extract stock data from an external source (Yahoo Finance), process it, and store it in a structured way on Amazon S3.

The project appears to be an implementation of a larger set of requirements detailed in `requisitos.txt`, which outlines a more complex architecture involving AWS Glue, Lambda, and Athena. This current implementation focuses on the "Extract" part of the ETL process.

**Core Technologies:**
*   **Python:** The language used for the ETL script.
*   **yfinance:** A Python library for accessing financial data from Yahoo Finance.
*   **Docker:** Used for containerizing the application for consistent execution.
*   **AWS:** The target cloud platform. The `README.md` mentions EventBridge, Step Functions, and S3 as part of the intended architecture.

## Building and Running

The application is designed to be run as a Docker container, which is likely orchestrated by AWS services like Step Functions or AWS Batch in a production environment.

### Docker

**1. Build the Docker image:**
```bash
docker build -t aws-etl-fiap .
```

**2. Run the Docker container:**
```bash
docker run aws-etl-fiap
```
This will execute the `etl.py` script and print the extracted stock data to the console.

### Local Execution

To run the script directly on your local machine, first install the dependencies:

```bash
pip install -r requirements.txt
```

Then, run the ETL script:

```bash
python etl.py
```
This will print the extracted stock data to the console.

## Development Conventions

*   The main logic is contained in `etl.py`.
*   The core extraction logic is in the `extract_stock_data` function, which is a good practice for modularity and testing.
*   A `if __name__ == "__main__":` block is used to provide a simple execution example when the script is run directly.
*   Dependencies are managed in `requirements.txt`.
*   The `Dockerfile` provides a clean, reproducible environment for the application, following good practices like using a non-root user.
*   The `README.md` file provides a good overview of the project's architecture and purpose.
