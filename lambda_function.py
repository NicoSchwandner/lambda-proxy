import boto3
import json
from urllib.parse import parse_qs
from config import LUNCH_MENU_FETCHER_NAME, LUNCH_PATH_ROOT_SEGMENT

print('Creating Lambda client...')
lambda_client = boto3.client('lambda')
print('Lambda client created!')

class Response:
    def __init__(self, status_code: int = 200, body: str = "Loading...", response_type: str = "ephemeral"):
        self.status_code = status_code
        self.body = body
        self.response_type = response_type # ephemeral | in_channel

def determine_secondary_lambda_name(path_segments: list[str]) -> str:
    if len(path_segments) >= 1:
        resource = path_segments[0]
        if resource == 'lunch':
            return LUNCH_MENU_FETCHER_NAME
    return ''

def call_secondary_lambda(function_name: str, payload: dict):
    print(f'Calling secondary lambda: {function_name}')
    lambda_client.invoke(
        FunctionName=function_name,
        InvocationType='Event',
        Payload=json.dumps(payload)
    )
    print('Secondary lambda called!')

def parse_body(event) -> tuple[str, str]:
    if event.get('isBase64Encoded'):
        import base64
        body_str = base64.b64decode(event['body']).decode('utf-8')
    else:
        body_str = event.get('body', '')

    parsed_body = parse_qs(body_str)
    proxy_path = event.get('pathParameters', {}).get('proxy', '')
    response_url = parsed_body.get('response_url', [None])[0]

    return proxy_path, response_url

def get_response_string(response: Response) -> str:
    return {
        'statusCode': response.status_code,
        'body': json.dumps({
            'response_type': response.response_type,
            'text': response.body
        })
    }

def lambda_handler(event, context):
    proxy_path, response_url = parse_body(event)
    path_segments = proxy_path.split('/')
    print(f'Raw path: {proxy_path}')

    response = Response()
    lambda_payload = {}
    lambda_payload['response_url'] = response_url

    print(f'Lambda payload: {lambda_payload}')

    if len(path_segments) < 1:
        response.status_code = 200 # not using 404 to be able to display the message in Slack
        response.body = f'Proxy path contains no segments. Proxy path: {proxy_path}'

        print(f'Response: {get_response_string(response)}')
        return get_response_string(response)

    resource = path_segments[0]

    if resource == LUNCH_PATH_ROOT_SEGMENT:
        print('Lunch time! Fetching menu...')
        lambda_name = determine_secondary_lambda_name(path_segments)
        call_secondary_lambda(lambda_name, lambda_payload)
        response.body = 'Fetching lunch menu...'
    else:
        response.status_code = 200 # not using 404 to be able to display the message in Slack
        response.body = f'No lambda handler found for path {proxy_path}'

    print(f'Response: {get_response_string(response)}')
    return get_response_string(response)
