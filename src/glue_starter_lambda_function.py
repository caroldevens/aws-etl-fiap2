import boto3
import os
import urllib.parse

def handler(event, context):
    """
    Lambda function triggered by an S3 event. It starts a specific AWS Glue job.
    """
    # Get the Glue job name from environment variables
    glue_job_name = os.environ['GLUE_JOB_NAME']
    
    # Information about the S3 object that triggered this function
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    
    print(f"S3 object created: s3://{bucket}/{key}")
    print(f"Attempting to start Glue job: {glue_job_name}")

    client = boto3.client('glue')
    
    try:
        # Start the Glue job, passing the S3 object info as arguments
        response = client.start_job_run(
            JobName=glue_job_name,
            Arguments={
                '--s3_source_path': f"s3://{bucket}/{key}"
            }
        )
        run_id = response['JobRunId']
        print(f"Successfully started Glue job '{glue_job_name}'. Run ID: {run_id}")
        return {'statusCode': 200, 'body': f"Started Glue job. Run ID: {run_id}"}
        
    except Exception as e:
        print(f"Error starting Glue job '{glue_job_name}': {e}")
        raise e
