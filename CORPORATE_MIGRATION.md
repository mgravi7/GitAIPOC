# Corporate GitLab Migration Guide

**Version:** 1.2.0  
**Date:** December 13, 2025  
**Status:** Production-Ready ✅

---

## Overview

This guide explains how to migrate the GitLab Code Review Agent from GitHub (POC) to your corporate GitLab instance for production use.

**Timeline:** ~30 minutes  
**Downtime:** None (fresh deployment)

---

## Prerequisites

Before starting, ensure you have:
- ✅ Access to corporate GitLab instance
- ✅ Permissions to create new repositories
- ✅ Anthropic API key for production
- ✅ Docker or Kubernetes environment for deployment
- ✅ Service account created in GitLab (`gitlab-ai-reviewer`)

---

## Step 1: Create Corporate GitLab Repository

### 1.1 Create New Project

1. Log in to corporate GitLab
2. Click **"New project"** → **"Create blank project"**
3. **Project name:** `gitlab-code-review-agent`
4. **Visibility:** Internal (recommended) or Private
5. **Initialize with README:** ☐ Unchecked (we'll push existing code)
6. Click **"Create project"**

### 1.2 Note the Git URL

Copy the repository URL:
```
https://gitlab.yourcompany.com/platform-team/gitlab-code-review-agent.git
```

---

## Step 2: Push Code to Corporate GitLab

### 2.1 Add Corporate Remote

From your local repository:

```bash
cd C:\Repos\GitAIPOC

# Add corporate GitLab as new remote
git remote add corporate https://gitlab.yourcompany.com/platform-team/gitlab-code-review-agent.git

# Verify remotes
git remote -v
```

**Expected output:**
```
origin       https://github.com/mgravi7/GitAIPOC (fetch)
origin       https://github.com/mgravi7/GitAIPOC (push)
corporate    https://gitlab.yourcompany.com/platform-team/gitlab-code-review-agent.git (fetch)
corporate    https://gitlab.yourcompany.com/platform-team/gitlab-code-review-agent.git (push)
```

### 2.2 Push v1.2.0 Release

```bash
# Push main/master branch
git push corporate feature/hardening:main

# Push all tags (including v1.2.0)
git push corporate --tags
```

### 2.3 Set Default Branch (in GitLab UI)

1. Go to corporate GitLab repository
2. **Settings** → **Repository** → **Default branch**
3. Select `main`
4. Save changes

---

## Step 3: Production Configuration

### 3.1 Create Production .env File

**Do NOT commit `.env` to repository!**

Create `production.env` on your deployment server:

```env
# ===== Corporate GitLab Configuration =====
GITLAB_URL=https://gitlab.yourcompany.com
GITLAB_TOKEN=glpat-XXXXXXXXXXXXXXXXXXXXX  # Service account token
GITLAB_WEBHOOK_SECRET=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX  # Random 32-char string
GITLAB_TRIGGER_LABEL=ai-review

# ===== Anthropic Configuration =====
ANTHROPIC_API_KEY=sk-ant-XXXXXXXXXXXXXXXXXXXXXXXX  # Production API key
ANTHROPIC_MODEL=claude-sonnet-4-20250514
ANTHROPIC_MAX_TOKENS=4096

# ===== Application Configuration =====
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=INFO

# ===== Rate Limiting =====
RATE_LIMIT_ENABLED=true
MAX_REVIEWS_PER_HOUR=50  # Adjust based on team size

# ===== Review Configuration =====
REVIEW_TIMEOUT=120
MAX_DIFF_SIZE_LINES=10000

# ===== Retry Configuration =====
MAX_RETRIES=3
RETRY_INITIAL_DELAY=1.0
RETRY_BACKOFF_FACTOR=2.0
RETRY_MAX_DELAY=10.0

# ===== Token Budget Configuration =====
TOKEN_BUDGET_ENABLED=true
TOKEN_DAILY_LIMIT=1000000
TOKEN_WARNING_THRESHOLD=800000
TOKEN_DATA_DIR=/app/data/tokens
TOKEN_SUMMARY_RETENTION_DAYS=90
TOKEN_LOG_RETENTION_DAYS=365
```

### 3.2 Security Best Practices

**Secrets Management:**
- ✅ Use Kubernetes Secrets or Vault for sensitive values
- ✅ Rotate API keys every 90 days
- ✅ Use different API keys for dev/staging/prod
- ✅ Never commit `.env` files to Git

**Example Kubernetes Secret:**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: code-review-agent-secrets
type: Opaque
stringData:
  GITLAB_TOKEN: glpat-XXXXXXXXXXXXXXXXXXXXX
  ANTHROPIC_API_KEY: sk-ant-XXXXXXXXXXXXXXXXXXXXXXXX
  GITLAB_WEBHOOK_SECRET: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

---

## Step 4: Deployment

### Option A: Docker Compose (Simple)

```bash
# Clone from corporate GitLab
git clone https://gitlab.yourcompany.com/platform-team/gitlab-code-review-agent.git
cd gitlab-code-review-agent

# Copy production config
cp production.env .env

# Deploy
docker-compose -f org-gitlab-testing/docker-compose.yml up -d
```

### Option B: Kubernetes (Recommended for Production)

See: `docs/deployment/production-kubernetes.md` (to be created)

**Basic deployment:**
```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/pvc.yaml  # For token data persistence
```

---

## Step 5: Verify Deployment

### 5.1 Health Check

```bash
curl https://code-review-agent.yourcompany.com/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-12-13T...",
  "version": "1.2.0"
}
```

### 5.2 Budget Status

```bash
curl https://code-review-agent.yourcompany.com/budget/status
```

**Expected response:**
```json
{
  "enabled": true,
  "stats": {
    "date": "2025-12-13",
    "total_tokens": 0,
    "request_count": 0,
    ...
  }
}
```

### 5.3 Test Review

1. Create test project in corporate GitLab
2. Add `gitlab-ai-reviewer` service account as Developer
3. Configure webhook pointing to agent
4. Create MR and add `ai-review` label
5. Verify review appears

---

## Step 6: Team Rollout

### 6.1 Pilot Projects (Week 1)

**Select 1-2 pilot repositories:**
- Active projects with frequent MRs
- Teams willing to provide feedback
- Low-risk if issues arise

**Configure:**
1. Add service account to project
2. Add webhook
3. Create `ai-review` label
4. Document in project README

**Monitor:**
- Review quality
- Response times
- Token usage
- Developer feedback

### 6.2 Gradual Rollout (Week 2-3)

**Expand to more teams:**
- 5-10 repositories per week
- Monitor costs and usage
- Adjust rate limits if needed
- Gather feedback

### 6.3 Full Production (Week 4+)

**Make available to all teams:**
- Self-service onboarding
- Documentation in company wiki
- Slack channel for support
- Regular cost reports

---

## Step 7: Monitoring & Maintenance

### Daily Monitoring

```bash
# Check budget status
curl https://code-review-agent.yourcompany.com/budget/status

# View logs
kubectl logs -f deployment/code-review-agent

# Check token usage
kubectl exec -it deployment/code-review-agent -- cat /app/data/tokens/daily-summaries/$(date +%Y-%m-%d).json
```

### Weekly Tasks

- Review token usage trends
- Check error logs
- Verify budget projections
- Collect team feedback

### Monthly Tasks

- Export and analyze CSV logs
- Review costs vs. budget
- Update documentation
- Plan improvements

---

## Rollback Plan

**If issues arise, quick rollback:**

1. **Disable agent temporarily:**
   ```bash
   kubectl scale deployment code-review-agent --replicas=0
   ```

2. **Investigate logs:**
   ```bash
   kubectl logs deployment/code-review-agent --tail=1000
   ```

3. **Fix and redeploy:**
   ```bash
   kubectl scale deployment code-review-agent --replicas=1
   ```

**No impact on existing MRs** - reviews are stateless.

---

## Success Criteria

**Week 1:**
- ✅ Deployment successful
- ✅ Health check passing
- ✅ 2 pilot projects onboarded
- ✅ 10+ reviews completed
- ✅ No major issues

**Month 1:**
- ✅ 20+ projects using agent
- ✅ 200+ reviews completed
- ✅ Costs within budget ($50-100/month)
- ✅ Positive team feedback
- ✅ No production incidents

---

## Support Contacts

**Technical Issues:**
- Platform Team: `platform-team@yourcompany.com`
- Slack: `#ai-code-review`

**API Issues:**
- Anthropic Support: https://support.anthropic.com/

**Budget/Cost Questions:**
- Finance Team: `finance@yourcompany.com`

---

## Next Steps After Migration

1. **Update GitHub Repo:** Add note that corporate GitLab is primary repo
2. **Disable GitHub Webhooks:** Prevent accidental POC usage
3. **Archive GitHub Repo:** Mark as archived for reference
4. **Document in Company Wiki:** Add agent to platform services
5. **Create Runbook:** Operational procedures for on-call team

---

## Differences: POC vs. Production

| Aspect | POC (GitHub) | Production (Corporate GitLab) |
|--------|--------------|-------------------------------|
| **Repository** | `github.com/mgravi7/GitAIPOC` | `gitlab.yourcompany.com/.../gitlab-code-review-agent` |
| **GitLab Instance** | Local Docker CE | Corporate GitLab (self-hosted) |
| **API Key** | Dev key | Production key (budget limits) |
| **Deployment** | Docker Compose | Kubernetes |
| **Monitoring** | Manual logs | Prometheus + Grafana |
| **Support** | You | Platform team |
| **Rate Limits** | 50/hour (testing) | Adjusted per team size |
| **Token Budget** | 1M/day (test) | Tuned based on usage |

---

## FAQ

**Q: Can we use the GitHub repo for reference?**  
A: Yes! Keep it as reference, but corporate GitLab is the source of truth.

**Q: Do we need to migrate git history?**  
A: Git history comes with the code push. All commits and tags are preserved.

**Q: What about open issues/PRs on GitHub?**  
A: Migrate any open issues to GitLab issues. Close GitHub issues with link to GitLab.

**Q: Can we still pull updates from GitHub?**  
A: Yes, you can keep `origin` remote for reference, but all development should happen in corporate GitLab.

**Q: What if we want to contribute back to open source?**  
A: Fork corporate repo, make changes, then push to GitHub separately (after security review).

---

**Migration Prepared By:** Platform Team  
**Date:** December 13, 2025  
**Version:** 1.2.0  
**Status:** ✅ Ready for Production

