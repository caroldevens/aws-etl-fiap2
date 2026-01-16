import yfinance as yf
import pandas as pd
import boto3
import os
from datetime import datetime

def handler(event, context):
    """
    Lambda function to extract stock data from Yahoo Finance, format it,
    and save it to an S3 bucket in Parquet format with daily partitions.
    """
    # Get environment variables
    TICKER = os.environ.get('TICKER', 'PETR4.SA')
    BUCKET_NAME = os.environ['BUCKET_NAME']
    
    print(f"Starting extraction for ticker: {TICKER}")
    
    # Extract data for the last day
    data = yf.download(TICKER, period="1d", progress=False)
    
    if data.empty:
        print(f"No data downloaded for {TICKER}. This might be a weekend or holiday.")
        return {'statusCode': 204, 'body': f'No data for {TICKER}.'}

    # Add partition columns and ticker info
    today = datetime.utcnow()
    data['year'] = today.year
    data['month'] = today.month
    data['day'] = today.day
    data['ticker'] = TICKER
    
    # Reset index to make date a column
    data.reset_index(inplace=True)

    # Save to S3 in Parquet format
    s3_path = f"s3://{BUCKET_NAME}/raw/ticker={TICKER}/year={today.year}/month={today.month}/day={today.day}/{today.strftime('%Y-%m-%d')}.parquet"
    
    print(f"Saving data to {s3_path}")
    data.to_parquet(s3_path, engine='pyarrow', index=False)
    
    print(f"Successfully saved data to {s3_path}")
    return {
        'statusCode': 200,
        'body': f'Successfully saved data to {s3_path}'
    }
