# Slack Agent

A Flask-based Slack assistant that uses Anthropic Claude to explain alerts and investigate service health through custom query tools.

## Features

- Handles Slack slash commands and Events API requests.
- Uses `knowledge_base.txt` as reference material for responses.
- Queries latency and 5xx error information through the configured ADX gateway.
- Supports refreshing the reference file without restarting the service.
- Includes a Docker image and deployment configuration.

## Requirements

- Python 3.8+
- Slack app with a slash command or Events API subscription
- Anthropic API key
- Access to the ADX query gateway used by the tools

## Configuration

Create a local `.env` file (never commit it):

```dotenv
ANTHROPIC_API_KEY=your-anthropic-api-key
SLACK_BOT_TOKEN=your-slack-bot-token
SLACK_RESPONSE_URL=https://hooks.slack.com/services/your/response/url
ADX_API_ENDPOINT=http://localhost:8000/query/clusters/<cluster>/db/<database>
REFERENCE_FILE_PATH=knowledge_base.txt
PORT=5000
```

The application loads `knowledge_base.txt` by default. Set `REFERENCE_FILE_PATH` to use another file.

## Local development

Install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Start the service:

```bash
python slack-ai-agent-reference-file.py
```

The server listens on `http://localhost:5000` by default. Configure your Slack request URLs to point to:

- Slash command: `/hooks/slack-agent/slack/ai-assistant`
- Events API: `/hooks/slack-agent/slack/events`

The reference refresh endpoint is:

```text
POST /hooks/slack-agent/admin/refresh-reference
```

Protect this administrative endpoint before exposing it publicly.

## Docker

Build and run the image:

```bash
docker build -t slack-agent .
docker run --env-file .env -p 5000:5000 slack-agent
```

The included `server-config.yaml` contains an example deployment configuration.

## Security

Keep API keys, Slack tokens, and webhook URLs out of source control. Slash-command response URLs are taken from the incoming request payload; Events API responses use `SLACK_RESPONSE_URL`. The `.env` file is ignored by Git. Rotate any credentials that may previously have been exposed.

## License

No license has been specified yet.
