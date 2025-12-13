# Corporate GitLab Testing Guide

Test the code review agent against your corporate GitLab instance.

## Prerequisites

- Corporate VPN connection
- Access to corporate GitLab
- Docker Desktop installed
- Anthropic API key
- Corporate network allows access to `api.anthropic.com`

## Setup

### 1. Configure Environment

```bash
cd org-gitlab-testing
cp .env.example .env
```

Edit `.env` and set:
- `GITLAB_URL` - Your corporate GitLab URL (e.g., `https://gitlab.yourcompany.com`)
- `GITLAB_TOKEN` - Service account token (from DevOps team)
- `GITLAB_WEBHOOK_SECRET` - Generate a random string
- `ANTHROPIC_API_KEY` - Your Anthropic API key

### 2. Service Account Setup

Work with your DevOps team to create a service account in corporate GitLab.

See: [Service Account Setup Guide](../development/service-account-setup.md)

**Service Account Requirements:**
- Username: `gitlab-ai-reviewer` (recommended)
- Scopes: `api`, `read_api`, `read_repository`, `write_repository`
- Access: Developer role on projects to be reviewed

### 3. Start Agent

```bash
# Connect to VPN first!
docker-compose up -d
```

Verify it's running:
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status":"healthy","timestamp":"...","version":"1.0.0"}
```

### 4. Configure Webhook in Corporate GitLab

For testing locally (from your machine):

**Option A: Local Testing (Agent on Docker Desktop)**
- URL: `http://host.docker.internal:8000/webhook/gitlab`
- Secret: (your `GITLAB_WEBHOOK_SECRET`)
- Trigger: Merge request events

**Note**: This only works while your Docker Desktop is running and VPN is connected.

**Option B: Production Deployment**

For permanent deployment, work with DevOps to deploy to Kubernetes.
See: [Production Deployment Guide](production-kubernetes.md)

### 5. Test with Real MR

1. Create a test branch in a corporate project
2. Make some code changes
3. Create a merge request
4. Add label: `ai-review`
5. Watch for review comment (30-90 seconds)

## Monitoring

### View Agent Logs

```bash
docker-compose logs -f code-review-agent
```

### Check Agent Health

```bash
curl http://localhost:8000/health
```

### Test Webhook Manually

```bash
curl -X POST http://localhost:8000/webhook/gitlab \
  -H "X-Gitlab-Token: your-webhook-secret" \
  -H "Content-Type: application/json" \
  -d '{
    "object_kind": "merge_request",
    "object_attributes": {
      "iid": 1,
      "action": "update"
    },
    "project": {
      "id": 1
    },
    "labels": [
      {"title": "ai-review"}
    ]
  }'
```

## Troubleshooting

### Can't connect to corporate GitLab
- ? VPN connected?
- ? GitLab URL correct?
- ? Token valid?
- Test: `curl -H "PRIVATE-TOKEN: your-token" https://gitlab.yourcompany.com/api/v4/user`

### Webhook not triggered
- ? Webhook URL correct?
- ? Secret matches?
- ? Merge request events enabled?
- Check webhook logs in GitLab UI

### Review not posted
- ? Service account has Developer access to project?
- ? Token has correct scopes?
- ? Agent logs show API errors?
- Check agent logs for detailed error messages

### Can't reach Anthropic API
- ? Corporate proxy configured?
- ? Firewall allows `api.anthropic.com`?
- Test: `curl https://api.anthropic.com`

## Network Configuration

If corporate network requires proxy:

Add to `.env`:
```bash
HTTP_PROXY=http://proxy.yourcompany.com:8080
HTTPS_PROXY=http://proxy.yourcompany.com:8080
NO_PROXY=gitlab.yourcompany.com
```

And update docker-compose.yml:
```yaml
services:
  code-review-agent:
    environment:
      - HTTP_PROXY=${HTTP_PROXY}
      - HTTPS_PROXY=${HTTPS_PROXY}
      - NO_PROXY=${NO_PROXY}
```

## Cost Tracking

Monitor your Anthropic API usage:
- Each review costs ~$0.10-0.20
- Track usage in Anthropic Console
- Set up budget alerts

## Next Steps

Once corporate testing is successful:
1. Work with DevOps for Kubernetes deployment
2. Set up webhook on permanent agent URL
3. Roll out to more projects
4. Collect team feedback

See: [Production Deployment Guide](production-kubernetes.md)
