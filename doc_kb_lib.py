# anthropic.claude-v2:1
# anthropic.claude-3-sonnet-20240229-v1:0
# anthropic.claude-3-haiku-20240307-v1:0
# anthropic.claude-3-5-sonnet-20240620-v1:0
# %%
import os
import boto3
from botocore.client import Config
from io import StringIO
import sys
import textwrap
import json
import pprint
from dotenv import dotenv_values
from datetime import datetime
from botocore.exceptions import ClientError
import tiktoken
from langdetect import detect
import kb_meta_data_db 

boto3_session = boto3.session.Session()
region = boto3_session.region_name

config = dotenv_values('.env')

# kb_id = config["KB_ID"]
# model_id = config["MODEL_ID"]
# model_arn = f'arn:aws:bedrock:{region}::foundation-model/{model_id}'
guardrail_id = config["GUARDRAIL_ID"]
guardrail_version = config["GUARDRAIL_VERSION"]

bedrock_config = Config(connect_timeout=int(config["BEDROCK_CONFIG_TIMEOUT"]), read_timeout=int(config["BEDROCK_CONFIG_TIMEOUT"]),
                        retries={'max_attempts': int(config["BEDROCK_CONFIG__MAX_ATTEMPS"])},
                        region_name=region)
bedrock_agent_runtime_client = boto3.client('bedrock-agent-runtime',config=bedrock_config)

maxRelevantResults = int(config["MAX_RELEVANT_RESULTS"])
max_tokens = int(config["MAX_TOKEN_1"]) # 512,1024,2048,2560
temperature =float(config["TEMP_1"]) # 0.0-1.0

def print_ww(*args, width: int = 100, **kwargs):
    """Like print(), but wraps output to `width` characters (default 100)"""
    buffer = StringIO()
    try:
        _stdout = sys.stdout
        sys.stdout = buffer
        print(*args, **kwargs)
        output = buffer.getvalue()
    finally:
        sys.stdout = _stdout
    for line in output.splitlines():
        print("\n".join(textwrap.wrap(line, width=width)))


#master1_template_prompt_kb
def get_kb_prompt(type_name):
    if type_name =="":
        _prompt=kb_meta_data_db.get_default_prompt()
    else:
        dfPrompt=kb_meta_data_db.list_all_prompt_doc_type()
        dfPromptByType=dfPrompt.query("type_name==@type_name")
        if dfPromptByType.empty==False:
            _prompt=dfPromptByType.iloc[0]['prompt_description']
            if _prompt == "" or _prompt is None:
                _prompt=kb_meta_data_db.get_default_prompt()
        else:
             _prompt=kb_meta_data_db.get_default_prompt()

    print(_prompt)
    return _prompt

def generate_presigned_url(bucket_uri):
    s3 = boto3.client('s3')
    try:
        bucket_name, key = bucket_uri.split('/', 2)[-1].split('/', 1)
        presigned_url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': key},
            ExpiresIn=3600  # URL expires in 1 hour
        )
        return presigned_url
    except ClientError as e:
        print(f"Error generating presigned URL: {e}")
        return None    

#call lambda
def invoke_lambda_function(payload):
    # Get function name and region from config
    function_name = config["LAMBDA_FUNCTION_NAME"]
    region = config.get("AWS_REGION", "us-east-1")  # Use a default region if not set

    client = boto3.client('lambda', region_name=region)  # Use your specific region
    try:
        # Convert the payload to JSON format
        response = client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )

        # Read the response from the Lambda function
        response_payload = json.loads(response['Payload'].read())
        
        return response_payload
    except Exception as e:
        print(f"Error calling Lambda function: {e}")
        return None

# %%
import tiktoken
def count_char_tokens(text, encoding_name=config["TOKEN_COUNTER_ENCODING_NAME"]):
    encoding = tiktoken.get_encoding(encoding_name)
    tokens = encoding.encode(text)
    x_chars= len(text)
    x_tokens= len(tokens)
    return x_chars,x_tokens


# if __name__ == "__main__":
#     main()

