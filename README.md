# GitLab Code Review Agent

**AI-powered code reviews for GitLab merge requests using Claude Sonnet 4.**

Built for developers who want to understand how AI code review works, and for DevOps teams who need to deploy it in production.

---

## 🎯 What This Does

Automatically reviews code in GitLab merge requests when you add the `ai-review` label:
- 🔴 **Security Issues** - SQL injection, hardcoded secrets, vulnerabilities
- ⚠️ **Performance Problems** - Inefficient algorithms, resource leaks
- ℹ️ **Best Practices** - Type hints, error handling, code style
- ✅ **Actionable Recommendations** - Specific fixes for each issue

**Example review time**: 30-90 seconds  
**Cost**: ~$0.15 per review (~$30/month for 50 MRs/week)

---

## 🏗️ Architecture

```
GitLab Webhook → FastAPI Agent → Claude Sonnet 4 → GitLab Comment
```

**Components:**
- `gitlab-code-review-agent/` - Production agent code (450 LOC Python)
- `local-testing/` - Test with local GitLab CE
- `org-gitlab-testing/` - Test with corporate GitLab
- `docs/` - Comprehensive documentation

---

## 🚀 Quick Start (For Developers)

### 1. Local Testing

Test with a local GitLab instance:

```bash
cd local-testing
cp .env.example .env
# Edit .env with your Anthropic API key
docker-compose up -d
```

See: [Local Testing Guide](docs/deployment/local-testing.md)

### 2. Corporate Testing

Test with your company's GitLab:

```bash
cd org-gitlab-testing
cp .env.example .env
# Edit .env with corporate GitLab URL and token
docker-compose up -d
```

See: [Corporate Testing Guide](docs/deployment/corporate-testing.md)

---

## 📦 For DevOps Teams

### Docker Image

```bash
cd gitlab-code-review-agent
docker build -t gitlab-code-review-agent:1.0.0 .
```

### Required Configuration

| Variable | Description | Example |
|----------|-------------|---------|
| `GITLAB_URL` | GitLab instance URL | `https://gitlab.yourcompany.com` |
| `GITLAB_TOKEN` | Service account token | `glpat-xxxxx` |
| `ANTHROPIC_API_KEY` | Claude API key | `sk-ant-xxxxx` |
| `GITLAB_WEBHOOK_SECRET` | Webhook validation | Random string |

See: [Configuration Guide](docs/development/environment-variables.md)

### Required Access

**Service Account Needs:**
- **Scopes**: `api`, `read_api`, `read_repository`, `write_repository`
- **Role**: Developer on projects to review
- **Network**: Access to `api.anthropic.com`

See: [Service Account Setup](docs/development/service-account-setup.md)

### Kubernetes Deployment

See: [Production Deployment Guide](docs/deployment/production-kubernetes.md)

### Guardrails

Configure limits to control costs and usage:

```bash
# Rate limiting
RATE_LIMIT_ENABLED=true
MAX_REVIEWS_PER_HOUR=50

# Diff size limits
MAX_DIFF_SIZE_LINES=10000  # lines

# Timeout
REVIEW_TIMEOUT=120  # seconds
```

---

## 📚 Documentation

### For Developers
- [Local Testing](docs/deployment/local-testing.md) - Test with local GitLab
- [Development Guide](docs/development/local-development.md) - How to develop
- [Environment Variables](docs/development/environment-variables.md) - All configuration

### For DevOps
- [Corporate Testing](docs/deployment/corporate-testing.md) - Test with corp GitLab
- [Production Deployment](docs/deployment/production-kubernetes.md) - K8s deployment
- [Service Account Setup](docs/development/service-account-setup.md) - GitLab config

### Reference
- [Troubleshooting](docs/development/troubleshooting.md) - Common issues
- [Phase Reports](docs/phase-reports/) - Project journey

---

## 🛠️ Technology Stack

- **FastAPI** - Webhook listener
- **httpx** - Async HTTP client
- **Anthropic SDK** - Claude Sonnet 4 integration
- **Pydantic** - Configuration management
- **Python 3.11** - Runtime

---

## 💰 Cost & Performance

**Per Review:**
- Input tokens: ~800 (the diff)
- Output tokens: ~1,200 (the review)
- Cost: **~$0.15**
- Time: **30-90 seconds**

**Monthly Estimates:**
- 50 MRs/week: ~**$30/month**
- 100 MRs/week: ~**$60/month**
- 200 MRs/week: ~**$120/month**

---

## 🔒 Security

- ✅ Webhook secret validation
- ✅ Service account (not personal tokens)
- ✅ Kubernetes secrets for sensitive data
- ✅ No code storage (reviews in real-time)
- ✅ Rate limiting to prevent abuse

---

## 📈 Features

### Current (v1.0.0)
- ✅ GitLab webhook integration
- ✅ Claude Sonnet 4 reviews
- ✅ Security, performance, best practices analysis
- ✅ Markdown-formatted comments
- ✅ Rate limiting
- ✅ Error handling with user feedback
- ✅ Health check endpoint

### Roadmap (Future)
- [ ] Cost tracking dashboard
- [ ] Custom review rules per project
- [ ] Multi-language optimization
- [ ] Review statistics
- [ ] Slack/Teams notifications

---

## 🤝 Support & Contribution

**Issues?** Check [Troubleshooting Guide](docs/development/troubleshooting.md)

**Questions?** See documentation in `docs/`

**Corporate Deployment?** This project is designed for internal use. Once migrated to your corporate GitLab, it becomes your primary repository.

---

## 📄 License

Internal POC Project - Customize for your organization's needs.

---

## 🎓 Reference

This project uses `gitlab-cr-agent/` (git submodule) as a reference for advanced features. Our implementation is simpler and focused on Anthropic Claude models only.

---

**Version**: 1.0.0  
**Status**: Production-Ready  
**Last Updated**: December 2025
