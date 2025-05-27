import boto3
import botocore
import json
import base64
import requests
from dotenv import load_dotenv
import os

load_dotenv(verbose=True)
region = os.getenv('region')


bedrock_client = boto3.client("bedrock-runtime",region_name=region)

def get_embedding_bedrock(model_id: str, text: str=''):
    input_body = {}
    if model_id.find('titan') >= 0 and len(text) > 0:
        input_body = {"inputText": text}
    elif model_id.find('cohere') >= 0:
        input_body = {"texts": [text], "input_type": "search_document"}
    body = json.dumps(input_body)

    try:
        response = bedrock_client.invoke_model(
            body=body,
            modelId=model_id,
            accept="*/*",
            contentType="application/json",
        )
        response_body = json.loads(response.get("body").read())
        if model_id.find('titan') >= 0:
            return response_body.get("embedding")
        elif model_id.find('cohere') >= 0:
            return response_body.get("embeddings")[0]
    except Exception as e:
        raise ValueError(f"Error raised by inference endpoint: {e}")
