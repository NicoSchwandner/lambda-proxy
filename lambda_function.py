def lambda_handler(event, context):
    # Extract the raw path
    raw_path = event.get('rawPath', '')

    # Alternatively, using requestContext
    # raw_path = event.get('requestContext', {}).get('http', {}).get('path', '')

    # Remove leading slash and split
    path_segments = raw_path.lstrip('/').split('/')

    status_code = 200
    body = 'Loading...'

    # Example: /users/123 -> ['users', '123']
    if len(path_segments) >= 1:
        resource = path_segments[0]
        if resource == 'lunch':
            print('Lunch time! Fetching menu...')
            pass
        else:
            status_code = 200 # not using 404 to be able to display the message in Slack
            body = f'Resource not found at {raw_path}'
    else:
        status_code = 200 # not using 404 to be able to display the message in Slack
        body = f'Resource not found at {raw_path}'

    print(f'Raw path: {raw_path}')
    print(f'Status code: {status_code}')
    print(f'Body: {body}')

    return {
        'statusCode': status_code,
        'body': body
    }
