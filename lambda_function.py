import boto3
import json
from config import LUNCH_MENU_FETCHER_NAME

def determine_lambda_name(path_segments: list[str]) -> str:
    if len(path_segments) >= 1:
        resource = path_segments[0]
        if resource == 'lunch':
            return LUNCH_MENU_FETCHER_NAME
    return ''

def call_secondary_lambda(function_name: str, payload: dict):
    lambda_client = boto3.client('lambda')

    print(f'Calling secondary lambda: {function_name}')
    lambda_client.invoke(
        FunctionName=function_name,
        InvocationType='Event',
        Payload=json.dumps(payload)
    )

def lambda_handler(event, context):
    proxy_path = event.get('pathParameters', {}).get('proxy', '')
    response_url = event.get('response_url')

    # Split the path into segments
    path_segments = proxy_path.split('/')

    status_code = 200
    body = 'Loading...'
    lambda_payload = {}
    lambda_payload['response_url'] = response_url

    print(f'Lambda payload: {lambda_payload}')

    if len(path_segments) >= 1:
        resource = path_segments[0]
        if resource == 'lunch':
            print('Lunch time! Fetching menu...')
            lambda_name = determine_lambda_name(path_segments)
            call_secondary_lambda(lambda_name, lambda_payload)
            pass
        else:
            status_code = 200 # not using 404 to be able to display the message in Slack
            body = f'Resource not found at {proxy_path}'
    else:
        status_code = 200 # not using 404 to be able to display the message in Slack
        body = f'Resource not found at {proxy_path}'

    print(f'Raw path: {proxy_path}')
    print(f'Status code: {status_code}')
    print(f'Body: {body}')

    return {
        'statusCode': status_code,
        'body': json.dumps({
            'response_type': 'ephemeral',
            'text': body
        })
    }
