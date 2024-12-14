import logging
import json
import base64
from urllib.parse import parse_qs
import boto3
from config import LUNCH_MENU_FETCHER_NAME, LUNCH_PATH_ROOT_SEGMENT

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(levelname)s - %(asctime)s - %(name)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

lambda_client = boto3.client('lambda')

class Response:
    def __init__(self, status_code: int = 200, body: str = "Loading...", response_type: str = "ephemeral"):
        self.status_code = status_code
        self.body = body
        self.response_type = response_type

    def to_dict(self) -> dict:
        return {
            'statusCode': self.status_code,
            'body': json.dumps({
                'response_type': self.response_type,
                'text': self.body
            })
        }

def get_secondary_lambda_name_for_path(path_segments: list[str]) -> str:
    if len(path_segments) >= 1:
        resource = path_segments[0]
        if resource == 'lunch':
            return LUNCH_MENU_FETCHER_NAME
    return ''

def call_secondary_lambda(function_name: str, payload: dict):
    logger.info("Invoking secondary lambda: %s with payload: %s", function_name, payload)
    lambda_client.invoke(
        FunctionName=function_name,
        InvocationType='Event',
        Payload=json.dumps(payload)
    )

def parse_body(event: dict) -> tuple[str, str]:
    body_str = event.get('body', '')
    if event.get('isBase64Encoded'):
        body_str = base64.b64decode(body_str).decode('utf-8')

    parsed_body = parse_qs(body_str)
    proxy_path = event.get('pathParameters', {}).get('proxy', '')
    response_url = parsed_body.get('response_url', [None])[0]

    return proxy_path, response_url

def lambda_handler(event, context):
    logger.info("Starting lambda handler with event: %s", event)
    proxy_path, response_url = parse_body(event)
    path_segments = proxy_path.split('/')
    logger.info("Parsed proxy path: %s", proxy_path)

    response = Response()
    lambda_payload = {
        'response_url': response_url
    }
    logger.debug("Lambda payload: %s", lambda_payload)

    if not path_segments:
        logger.warning("Proxy path contains no segments.")
        response.body = f"Proxy path contains no segments. Proxy path: {proxy_path}"
        return response.to_dict()

    resource = path_segments[0]

    if resource == LUNCH_PATH_ROOT_SEGMENT:
        logger.info("Handling LUNCH resource...")
        lambda_name = get_secondary_lambda_name_for_path(path_segments)
        call_secondary_lambda(lambda_name, lambda_payload)
        response.body = "Fetching lunch menu..."
    else:
        logger.warning("No lambda handler found for path: %s", proxy_path)
        response.body = f"No lambda handler found for path {proxy_path}"

    return response.to_dict()
