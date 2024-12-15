# Slack Slash Command Proxy Lambda

This Lambda function acts as a proxy for Slack slash commands that require asynchronous processing. The general idea is:

- Slack sends the slash command payload to this Lambda via an API Gateway `/proxy/*` route.
- This Lambda responds quickly (within Slack’s 3-second timeout) with a "Loading..." or similar message.
- Meanwhile, it triggers a secondary Lambda function that handles the long-running process (e.g., fetching a lunch menu - [lunch-menu-fetcher](https://github.com/NicoSchwandner/lunch-menu-fetcher)).
- Once the secondary Lambda finishes, it can send the results directly back to Slack using the `response_url` provided in the initial request.

## Why This Matters

Slack slash commands have a time limit: if you take too long to respond, Slack thinks your command failed. But sometimes, what you need to do—like fetching a complex lunch menu—takes more than a few seconds. This Lambda setup offloads the slow work to another Lambda function that can run asynchronously. The first Lambda returns right away with a "Loading..." message, keeping Slack happy. When the second Lambda finishes the heavy lifting, it posts the final result to Slack.

## How It Works

1. **Slack Command Trigger**:
   The user runs a slash command in Slack (e.g. `/lunch`).
2. **API Gateway Route**:
   The command is routed to an AWS API Gateway endpoint: `/proxy/*`.
3. **Lambda Proxy Handler** (the code you see here):
   - Parses the Slack request payload.
   - Determines which secondary Lambda function to call based on the path segments. For `/lunch` commands, it invokes the lunch menu fetcher Lambda.
   - Returns a quick "Fetching lunch menu..." response to Slack.
4. **Asynchronous Processing**:
   - The secondary Lambda runs in the background, does its work (e.g., fetching today's menu), then uses the `response_url` to send a formatted message back to Slack.

## Code Overview

- **`parse_body`**: Decodes the incoming request from Slack, extracts the `response_url` and the path.
- **`get_secondary_lambda_name_for_path`**: Given a path like `/lunch/...`, it resolves the correct secondary Lambda's name.
- **`call_secondary_lambda`**: Invokes the secondary Lambda function asynchronously.
- **`lambda_handler`**: The main entry point. It ties everything together, responding immediately and kicking off the asynchronous process.

## Environment & Configuration

- **Environment Variables / Config**:
  - `LUNCH_MENU_FETCHER_NAME`: The name of the Lambda function that will fetch the lunch menu.
  - `LUNCH_PATH_ROOT_SEGMENT`: The root path segment for the lunch command (e.g., `lunch`).

These are defined and imported from a `config` module.
Make sure they match the names of your secondary Lambda functions and your intended URL structure.

## Example Setup

1. **Set Up API Gateway**:
   Create an API Gateway endpoint (HTTP or REST) with a route `/proxy/{proxy+}` that triggers this Lambda.

2. **Slack Slash Command**:
   In Slack's App configuration:
   - Set your slash command to hit the API Gateway URL (e.g. `https://your-api-id.execute-api.region.amazonaws.com/prod/proxy/lunch`).
