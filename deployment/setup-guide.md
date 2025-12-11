# GitAIPOC - Deployment Setup Guide

## 📋 Overview

This guide covers deployment of the GitLab AI Review Agent for both local POC and production team environments.

---

## 🔧 Local POC Deployment

### Prerequisites
- Docker Desktop installed and running on Windows 11
- WSL2 backend enabled
- Minimum 8GB RAM available for Docker
- Anthropic API key

### Step 1: Configure Environment

1. Copy the environment template:
```powershell
cd C:\Repos\GitAIPOC
cp .env.example .env
```

2. Edit `.env` file and configure:
   - `GITLAB_ROOT_PASSWORD` - Choose a secure password for GitLab admin
   - `ANTHROPIC_API_KEY` - Your Anthropic API key
   - `API_KEY` - Generate a random bearer token (e.g., using PowerShell):
     ```powershell
     -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | % {[char]$_})
     ```
   - `GITLAB_WEBHOOK_SECRET` - Generate another random string

3. Leave other settings at default for now

### Step 2: Start Services

```powershell
# Start GitLab CE and Review Agent
docker-compose up -d

# Wait 2-3 minutes for GitLab to initialize
docker-compose logs -f gitlab
# Look for: "gitlab Reconfigured!"
```

### Step 3: Access GitLab

1. Open browser: http://localhost
2. Login with:
   - Username: `root`
   - Password: (value from `GITLAB_ROOT_PASSWORD` in .env)

### Step 4: Generate GitLab Access Token

1. In GitLab UI, go to: **User Settings** (top-right avatar) → **Access Tokens**
2. Create new token:
   - Name: `AI Review Agent`
   - Scopes: Check `api`, `read_api`, `read_repository`, `write_repository`
   - Click **Create personal access token**
3. Copy the token (starts with `glpat-`)
4. Update `.env` file:
   ```bash
   GITLAB_TOKEN=glpat-your-copied-token-here
   ```
5. Restart review agent:
   ```powershell
   docker-compose restart gitlab-ai-reviewer
   ```

### Step 5: Configure Webhook

1. Create a test project in GitLab
2. Go to: **Project Settings** → **Webhooks**
3. Add webhook:
   - **URL**: `http://gitlab-ai-reviewer:8000/webhook/gitlab`
   - **Secret Token**: (value from `GITLAB_WEBHOOK_SECRET` in .env)
   - **Trigger**: Check `Merge request events`
   - **SSL verification**: Uncheck (for local development)
4. Click **Add webhook**
5. Test webhook: Click **Test** → **Merge request events**
6. Verify: Should see "HTTP 200" response

### Step 6: Test Code Review

1. Create a test file in your GitLab project
2. Create a feature branch
3. Make some code changes
4. Create a merge request
5. Add label `ai-review` to the MR
6. Wait 30-60 seconds
7. Check for AI review comment on the MR

---

## 🚀 Production Team Deployment

### Prerequisites
- Existing self-hosted GitLab CE instance
- Docker host on internal network
- Network access from GitLab to review agent
- Anthropic API key (production/team key)

### Step 1: Prepare Production Environment

1. Clone repository on production server:
```bash
git clone https://github.com/mgravi7/GitAIPOC.git
cd GitAIPOC
git submodule update --init --recursive
```

2. Navigate to production deployment:
```bash
cd deployment/production
```

3. Copy environment template:
```bash
cp .env.production.example .env
```

### Step 2: Configure Production Settings

Edit `.env` file:

```bash
# Team's GitLab CE URL
GITLAB_URL=https://gitlab.yourcompany.com

# Generate production GitLab token
# (Create in GitLab: User Settings → Access Tokens)
GITLAB_TOKEN=glpat-production-token

# Generate secure random strings
GITLAB_WEBHOOK_SECRET=$(openssl rand -hex 32)
API_KEY=$(openssl rand -hex 32)

# Team's Anthropic API key
ANTHROPIC_API_KEY=sk-ant-production-key

# Team settings
ALLOWED_ORIGINS=https://gitlab.yourcompany.com
COST_ALERT_EMAIL=team-lead@company.com
```

### Step 3: Deploy Review Agent

```bash
# Build and start review agent only (no GitLab CE)
docker-compose -f docker-compose.production.yml --env-file .env up -d

# Check status
docker-compose -f docker-compose.production.yml ps

# View logs
docker-compose -f docker-compose.production.yml logs -f
```

### Step 4: Configure Team GitLab Webhook

1. In your team's GitLab instance, go to **Admin Area** → **System Hooks**
   (or configure per-project under **Project Settings** → **Webhooks**)

2. Add webhook:
   - **URL**: `http://review-agent-hostname:8000/webhook/gitlab`
     (Replace with your actual internal hostname/IP)
   - **Secret Token**: (value from `GITLAB_WEBHOOK_SECRET` in .env)
   - **Trigger**: Check `Merge request events`
   - **SSL verification**: Enable if using HTTPS

3. Test webhook delivery

### Step 5: Pilot Projects

1. Select 1-2 pilot repositories
2. Configure webhooks for those repos specifically
3. Notify pilot team members to add `ai-review` label to MRs
4. Monitor cost and quality for 1-2 weeks
5. Gather feedback

### Step 6: Full Rollout

Once pilot is successful:
1. Enable webhook globally (Admin Area → System Hooks)
2. Conduct team training
3. Share usage documentation
4. Monitor costs via cost tracking dashboard

---

## 🔒 Security Checklist

### Local POC
- [ ] GitLab accessible only on localhost
- [ ] `.env` file never committed to Git
- [ ] Random webhook secret generated
- [ ] Random API bearer token generated
- [ ] Docker network isolated

### Production
- [ ] Review agent on internal network only
- [ ] HTTPS enabled for all external communication
- [ ] Separate production Anthropic API key
- [ ] Webhook secret verification enabled
- [ ] Bearer token authentication enabled
- [ ] Rate limiting configured
- [ ] Logging and monitoring enabled
- [ ] API key rotation schedule defined (every 90 days)
- [ ] Firewall rules configured
- [ ] Regular security updates scheduled

---

## 📊 Health Checks

### Verify GitLab (POC only)
```bash
curl http://localhost/-/health
```

### Verify Review Agent
```bash
# Without authentication (will fail if API_KEY is set)
curl http://localhost:8000/health/live

# With authentication
curl -H "Authorization: Bearer YOUR_API_KEY" http://localhost:8000/health/live
```

### Verify Webhook Connectivity
```bash
# From GitLab server
curl -X POST \
  -H "X-Gitlab-Token: YOUR_WEBHOOK_SECRET" \
  -H "Content-Type: application/json" \
  http://review-agent:8000/webhook/gitlab
```

---

## 🐛 Troubleshooting

### Issue: Review agent can't connect to GitLab

**Solution:**
1. Check Docker network: `docker network inspect gitaipoc-network`
2. Verify GITLAB_URL in .env (use `http://gitlab` for POC, not `http://localhost`)
3. Check GitLab logs: `docker logs gitlab`
4. Test connectivity: `docker exec gitlab-ai-reviewer ping gitlab`

### Issue: Webhook returns 401 Unauthorized

**Solution:**
1. Verify `API_KEY` is set in .env
2. Include Bearer token in webhook calls (if API_KEY is configured)
3. Check review agent logs: `docker logs gitlab-ai-reviewer`

### Issue: No review appears on MR

**Solution:**
1. Check MR has `ai-review` label
2. Verify webhook delivery in GitLab: Settings → Webhooks → Recent Deliveries
3. Check review agent logs for errors
4. Verify GITLAB_TOKEN has correct scopes
5. Test API connectivity to Anthropic

### Issue: High costs

**Solution:**
1. Review rate limiting settings
2. Lower `GLOBAL_RATE_LIMIT` in .env
3. Disable reviews for non-critical repos
4. Check cost tracking dashboard
5. Verify no runaway review loops

---

## 📞 Support

### POC Support
- Primary: POC owner
- Technical issues: gitlab-cr-agent GitHub Issues
- API issues: Anthropic Support

### Production Support
- Tier 1: DevOps team
- Tier 2: Platform team
- Escalation: See project-plan.md

---

**Last Updated:** December 11, 2025  
**Version:** 1.0
