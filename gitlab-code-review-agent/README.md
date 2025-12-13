# Code Review Agent

Simple, focused AI code review agent for GitLab merge requests using Claude Sonnet 4.

## Features

? **Simple & Focused** - Code reviews only, no unnecessary complexity  
? **Direct Anthropic API** - Uses tested Claude Sonnet 4 API pattern  
? **Environment-based Config** - All settings via environment variables  
? **Rate Limiting** - Built-in protection against excessive API usage  
? **Error Handling** - Graceful failures with helpful error messages  
? **GitLab Integration** - Webhook-based, triggered by labels  

## Architecture

```
GitLab Webhook ? FastAPI App ? Claude Sonnet 4 ? GitLab Comment
```

## Quick Start

### 1. Configure Environment

Update your `.env` file:

```sh
# GitLab
GITLAB_URL=http://gitlab
GITLAB_TOKEN=glpat-your-token
GITLAB_WEBHOOK_SECRET=your-secret
GITLAB_TRIGGER_LABEL=ai-review

# Anthropic
ANTHROPIC_API_KEY=sk-ant-your-key
ANTHROPIC_MODEL=claude-sonnet-4-20250514
```

### 2. Start the Agent

```bash
docker-compose up -d code-review-agent
```

### 3. Configure GitLab Webhook

- URL: `http://code-review-agent:8000/webhook/gitlab`
- Secret: (your `GITLAB_WEBHOOK_SECRET`)
- Trigger: Merge request events

### 4. Trigger Review

Add the `ai-review` label to any merge request!

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `GITLAB_URL` | - | GitLab instance URL |
| `GITLAB_TOKEN` | - | GitLab API token |
| `GITLAB_WEBHOOK_SECRET` | - | Webhook validation secret |
| `GITLAB_TRIGGER_LABEL` | `ai-review` | Label to trigger reviews |
| `ANTHROPIC_API_KEY` | - | Anthropic API key |
| `ANTHROPIC_MODEL` | `claude-sonnet-4-20250514` | Claude model |
| `ANTHROPIC_MAX_TOKENS` | `4096` | Max response tokens |
| `LOG_LEVEL` | `INFO` | Logging level |
| `RATE_LIMIT_ENABLED` | `true` | Enable rate limiting |
| `MAX_REVIEWS_PER_HOUR` | `50` | Max reviews per hour |
| `REVIEW_TIMEOUT` | `120` | Review timeout (seconds) |
| `MAX_DIFF_SIZE` | `10000` | Max diff size (lines) |

## API Endpoints

- `GET /health` - Health check
- `POST /webhook/gitlab` - GitLab webhook receiver

## Future Enhancements

Planned iterative improvements:
- [ ] Enhanced prompts (from gitlab-cr-agent patterns)
- [ ] Cost tracking
- [ ] Review statistics
- [ ] Custom review rules
- [ ] Multi-file reviews with context
- [ ] Configurable review focus areas

## Development

### Run Locally

```bash
cd code-review-agent
pip install -r requirements.txt
python app.py
```

### View Logs

```bash
docker logs code-review-agent -f
```

## License

POC Project - Internal Use
