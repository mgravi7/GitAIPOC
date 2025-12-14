# Code Review Agent

Simple, focused AI code review agent for GitLab merge requests using Claude Sonnet 4.

## Features

✅ **Simple & Focused** - Code reviews only, no unnecessary complexity  
✅ **Direct Anthropic API** - Uses tested Claude Sonnet 4 API pattern  
✅ **Environment-based Config** - All settings via environment variables  
✅ **Token Budget Control** - Daily token limits with Excel-friendly logging  
✅ **Rate Limiting** - Built-in protection against excessive API usage  
✅ **Retry Logic** - Automatic retry with exponential backoff for reliability  
✅ **Error Handling** - Graceful failures with helpful error messages  
✅ **GitLab Integration** - Webhook-based, triggered by labels  

## Architecture

```
GitLab Webhook → FastAPI App → Claude Sonnet 4 → GitLab Comment
                      ↓
                Token Tracker
                      ↓
          Daily Summaries + Monthly CSV Logs
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

# Token Budget (Optional - recommended for production)
TOKEN_BUDGET_ENABLED=true
TOKEN_DAILY_LIMIT=1000000
TOKEN_WARNING_THRESHOLD=800000
TOKEN_DATA_DIR=/app/data/tokens

# Retry Configuration (Optional)
MAX_RETRIES=3
RETRY_INITIAL_DELAY=1.0
RETRY_BACKOFF_FACTOR=2.0
RETRY_MAX_DELAY=10.0
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
| `MAX_DIFF_SIZE_LINES` | `10000` | Max diff size (lines) |
| `MAX_RETRIES` | `3` | Maximum retry attempts |
| `RETRY_INITIAL_DELAY` | `1.0` | Initial retry delay (seconds) |
| `RETRY_BACKOFF_FACTOR` | `2.0` | Exponential backoff multiplier |
| `RETRY_MAX_DELAY` | `10.0` | Maximum retry delay (seconds) |
| `TOKEN_BUDGET_ENABLED` | `true` | Enable token budget tracking |
| `TOKEN_DAILY_LIMIT` | `1000000` | Daily token limit (all projects) |
| `TOKEN_WARNING_THRESHOLD` | `800000` | Warning threshold (80%) |
| `TOKEN_DATA_DIR` | `/app/data/tokens` | Token data directory |
| `TOKEN_SUMMARY_RETENTION_DAYS` | `90` | Daily summary retention |
| `TOKEN_LOG_RETENTION_DAYS` | `365` | Monthly log retention |

## Token Budget & Cost Control

### Overview

The agent tracks token usage to control costs and prevent budget overruns:

- **Daily Limit**: Hard stop when daily limit is reached
- **Excel-Friendly Logs**: Monthly CSV files for easy analysis
- **Fast Checks**: In-memory caching (<10ms budget checks)
- **Automatic Cleanup**: Old logs deleted after retention period

### File Structure

```
/app/data/tokens/
├── daily-summaries/
│   ├── 2025-12-13.json    # Today's summary (fast checks)
│   └── ...                 # 90 days retention
└── token-logs/
    ├── 2025-12.csv        # December 2025 logs
    └── ...                 # 365 days retention
```

### Monthly CSV Format (Excel-Ready!)

```csv
year,month,day,time,project_id,project_name,mr_iid,username,input_tokens,output_tokens,total_tokens,model,duration_ms
2025,12,13,09:15:32,42,backend-api,123,john.doe,12450,18230,30680,claude-sonnet-4,2340
2025,12,13,09:47:18,42,backend-api,124,jane.smith,8920,12150,21070,claude-sonnet-4,1890
```

**Excel Analysis Tips:**
- Separate year/month/day columns for easy filtering
- Pivot tables: Group by project, user, or date
- Formulas: `=SUM(K:K)` for total tokens
- Charts: Token usage over time

### Timestamps & Time Zones

**All timestamps are in UTC (Coordinated Universal Time).**

**Why UTC?**
- **Industry Standard**: Production logging best practice
- **No DST Confusion**: Avoids daylight saving time complexity
- **Portable**: Works consistently across all deployments
- **Simple**: No time zone conversion bugs

**Budget Reset**: Midnight UTC (4 PM Pacific / 5 PM Pacific Daylight Time)

**Converting to Local Time (if needed):**
- Excel formula for Pacific Time: `=TIME_COLUMN-TIME(8,0,0)` (PST) or `=TIME_COLUMN-TIME(7,0,0)` (PDT)
- Most analysis (grouping by day/project/user) works fine with UTC

### Budget Enforcement

When daily limit is reached:
1. New reviews are rejected with clear message
2. Comment posted to MR explaining the situation
3. Reviews automatically resume the next day
4. No manual intervention needed

**Example Budget Message:**
```
⚠️ Daily Token Budget Exhausted

The AI code review service has reached its daily token limit 
(1,000,000 tokens). Reviews will automatically resume tomorrow.

Remove and re-add the 'ai-review' label tomorrow to trigger a review.
```

### Monitoring Budget

Check current budget status:

```bash
curl http://localhost:8000/budget/status
```

**Response:**
```json
{
  "enabled": true,
  "stats": {
    "date": "2025-12-13",
    "total_tokens": 847230,
    "request_count": 17,
    "budget_limit": 1000000,
    "budget_used_percent": 84.7,
    "budget_remaining": 152770,
    "budget_exhausted": false,
    "avg_tokens_per_review": 49837
  }
}
```

### Cost Estimation

**Based on Claude Sonnet 4 Pricing:**
- Input: $3/million tokens
- Output: $15/million tokens

**Example: 20 reviews/day**
- Average: 50K tokens/review
- Daily: 1M tokens
- Monthly cost: ~$30-50

## Retry Logic

The agent includes automatic retry logic with exponential backoff for both GitLab and Anthropic API calls:

- **Automatic Retries**: Up to 3 attempts by default
- **Exponential Backoff**: Delays increase exponentially (1s → 2s → 4s)
- **Smart Retry**: Only retries on server errors (5xx) and network issues
- **Configurable**: All retry parameters can be customized via environment variables

**Retry Behavior:**
- 5xx errors from GitLab or Anthropic → Retry
- Network timeouts or connection errors → Retry
- 4xx client errors (authentication, not found) → No retry
- Success on any attempt → Returns immediately

**Example Retry Sequence:**
```
Attempt 1 → Network Error → Wait 1.0s
Attempt 2 → 503 Service Unavailable → Wait 2.0s
Attempt 3 → Success ✓
```

## API Endpoints

- `GET /health` - Health check
- `GET /budget/status` - Current token budget status
- `POST /webhook/gitlab` - GitLab webhook receiver

## Docker Volume Setup

Mount a volume for persistent token data:

```yaml
services:
  code-review-agent:
    volumes:
      - token-data:/app/data/tokens
    environment:
      - TOKEN_DATA_DIR=/app/data/tokens

volumes:
  token-data:
```

## Future Enhancements

Planned iterative improvements:
- [ ] Enhanced prompts (from gitlab-cr-agent patterns)
- [ ] Cost reporting dashboard
- [ ] Review statistics
- [ ] Custom review rules
- [ ] Multi-file reviews with context
- [ ] Configurable review focus areas

## Development

### Run Locally

```bash
cd gitlab-code-review-agent
pip install -r requirements.txt
python -m src.app
```

### View Logs

```bash
docker logs code-review-agent -f
```

### Access Token Logs

```bash
# View monthly log
docker exec code-review-agent cat /app/data/tokens/token-logs/2025-12.csv

# View daily summary
docker exec code-review-agent cat /app/data/tokens/daily-summaries/2025-12-13.json
```

## Troubleshooting

### Reviews Failing Intermittently

If reviews occasionally fail due to network issues:
1. Check logs for retry attempts
2. Increase `MAX_RETRIES` if needed
3. Adjust `RETRY_MAX_DELAY` for longer waits
4. Verify network connectivity to GitLab and api.anthropic.com

### All Retries Exhausted

If you see "Error calling Anthropic API" or "GitLab API error" after 3 attempts:
1. Check API credentials are valid
2. Verify network connectivity
3. Check service status (status.anthropic.com)
4. Review logs for specific error codes

### Budget Exhausted Mid-Day

If budget runs out before end of day:
1. Check `/budget/status` for usage breakdown
2. Review token logs to identify heavy users/projects
3. Consider increasing `TOKEN_DAILY_LIMIT`
4. Analyze CSV logs in Excel for patterns

### Token Logs Not Recording

If token usage isn't being logged:
1. Check `TOKEN_BUDGET_ENABLED=true`
2. Verify directory permissions: `/app/data/tokens`
3. Check disk space
4. Review agent logs for errors

## License

POC Project - Internal Use
