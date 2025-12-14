# Local Testing Guide

Test the code review agent with a local GitLab CE instance running in Docker.

## Prerequisites

- Docker Desktop installed and running
- At least 4GB RAM allocated to Docker
- 20GB free disk space
- Anthropic API key

## Quick Start

### 1. Configure Environment

```bash
cd local-testing
cp .env.example .env
```

Edit `.env` and set:
- `GITLAB_ROOT_PASSWORD` - Password for GitLab root user (min 8 chars)
- `ANTHROPIC_API_KEY` - Your Anthropic API key

### 2. Start Services

```bash
docker-compose up -d
```

Wait 2-3 minutes for GitLab to initialize. Monitor with:
```bash
docker-compose logs -f gitlab
```

Look for: `"gitlab Reconfigured!"` message

### 3. Access GitLab

Open browser: http://localhost

**Login:**
- Username: `root`
- Password: (your `GITLAB_ROOT_PASSWORD`)

### 4. Create Service Account

Follow the guide: [Service Account Setup](../development/service-account-setup.md)

**Summary:**
1. Admin Area → Users → New user
2. Username: `gitlab-ai-reviewer`
3. Email: `ai-reviewer@localhost`
4. Generate Personal Access Token with scopes: `api`, `read_api`, `read_repository`, `write_repository`
5. Copy token to `.env` file as `GITLAB_TOKEN`

### 5. Restart Agent

```bash
docker-compose restart code-review-agent
```

### 6. Configure Webhook

In your test project:

1. Settings → Webhooks
2. URL: `http://code-review-agent:8000/webhook/gitlab`
3. Secret: (your `GITLAB_WEBHOOK_SECRET` from `.env`)
4. Trigger: Merge request events
5. Click "Add webhook"

Enable local network webhooks:
- Admin Area → Settings → Network → Outbound requests
- ✅ Allow requests to the local network from webhooks

### 7. Create Test Project & MR

1. Create new project: `python-test-app`
2. Create branch: `feature/test-review`
3. Add Python files with intentional issues
4. Create merge request
5. Add label: `ai-review`

Within 30-90 seconds, Claude's review will appear as a comment!

## Useful Commands

```bash
# View logs
docker-compose logs -f code-review-agent

# Restart agent
docker-compose restart code-review-agent

# Stop everything
docker-compose down

# Remove all data (WARNING: deletes GitLab data!)
docker-compose down -v

# Check status
docker-compose ps
```

## Troubleshooting

### GitLab not starting
- Check Docker has enough memory (4GB+)
- Check logs: `docker-compose logs gitlab`
- Wait longer (first start can take 3-5 minutes)

### Webhook fails
- Ensure "Allow local network" is enabled
- Check webhook secret matches
- Test webhook in GitLab UI

### No review posted
- Check agent logs: `docker-compose logs code-review-agent`
- Verify service account has Developer access to project
- Check Anthropic API key is valid

## Next Steps

Once local testing works, try [Corporate GitLab Testing](corporate-testing.md).
