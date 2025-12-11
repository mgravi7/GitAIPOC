# GitLab Integration with Claude for Code Reviews

A proof-of-concept project demonstrating automated AI-powered code reviews using GitLab Community Edition and Anthropic's Claude Sonnet 4.5 API, with optional SonarQube integration for static code analysis.

## 🎯 Project Objectives

This POC demonstrates:
1. **GitLab CE Deployment** - Self-hosted GitLab server running in Docker
2. **AI-Powered Code Review** - Automated code review using Claude Sonnet 4.5 during merge requests
3. **Cost Management** - API usage tracking and cost optimization strategies
4. **Static Analysis (Stretch Goal)** - SonarQube Community Edition integration

## 🏗️ Architecture Overview

```
┌─────────────────┐
│   GitLab CE     │
│   (Docker)      │
└────────┬────────┘
         │
         │ Webhook Trigger on MR
         ▼
┌─────────────────┐
│  Review Service │──────► Anthropic Claude API
│   (Python)      │        (Sonnet 4.5)
└────────┬────────┘
         │
         │ Post Review Comments
         ▼
┌─────────────────┐
│  Merge Request  │
│   in GitLab     │
└─────────────────┘

(Optional: SonarQube)
```

## 📋 Prerequisites

- **Docker Desktop** - Running on Windows 11 Professional with WSL2
- **System Requirements**:
  - Minimum 8GB RAM (16GB recommended)
  - 20GB free disk space
  - Docker Desktop configured to use WSL2 backend
- **API Access**:
  - Anthropic API key (Claude Sonnet 4.5 access)
  - Budget allocated for API usage
- **Network**:
  - Ports available: 80, 443 (GitLab), 9000 (SonarQube optional)

## 🚀 Implementation Phases

### Phase 1: GitLab Server Setup

**Objective**: Deploy GitLab Community Edition in a Docker container

**Steps**:
1. Create Docker Compose configuration for GitLab CE
2. Configure persistent volumes for GitLab data
3. Set up initial admin credentials
4. Create test repository (Python-based)
5. Configure GitLab webhooks for merge request events

**Deliverables**:
- Running GitLab instance accessible via localhost
- Test repository with sample Python code
- Webhook configuration ready for integration

---

### Phase 2: Claude AI Code Review Integration

**Objective**: Implement automated code review using Claude Sonnet 4.5 API

**Steps**:
1. Develop webhook listener service (Python)
2. Integrate Anthropic API client
3. Implement merge request diff extraction
4. Design Claude prompt for code review (Python-specific)
5. Post review comments back to GitLab
6. Implement API usage tracking and cost monitoring

**Key Features**:
- Automatic code review on merge request creation/update
- Contextual inline comments on code changes
- Summary review comment with findings
- Cost tracking per review session
- Configurable review depth/thoroughness

**Cost Management Strategies**:
- Token usage estimation before API calls
- Configurable max tokens per review
- Rate limiting to prevent runaway costs
- Daily/monthly API budget alerts
- Cost per merge request reporting

---

### Phase 3: SonarQube Integration (Stretch Goal)

**Objective**: Add static code analysis with SonarQube Community Edition

**Steps**:
1. Deploy SonarQube in Docker container
2. Configure SonarQube scanner for Python
3. Integrate SonarQube with GitLab CI/CD
4. Combine Claude AI insights with SonarQube metrics
5. Create unified quality gate reporting

**Deliverables**:
- SonarQube instance analyzing Python code
- Combined AI + static analysis reports
- Quality metrics dashboard

---

## 📁 Project Structure

```
GitAIPOC/
├── README.md                    # This file
├── docker-compose.yml           # Container orchestration
├── gitlab/                      # GitLab configuration
│   └── config/                  # GitLab settings
├── review-service/              # Claude integration service
│   ├── app.py                   # Webhook listener
│   ├── claude_reviewer.py       # Claude API integration
│   ├── gitlab_client.py         # GitLab API client
│   ├── cost_tracker.py          # API cost monitoring
│   ├── requirements.txt         # Python dependencies
│   └── Dockerfile               # Service container
├── sonarqube/                   # SonarQube configuration (Phase 3)
│   └── config/
└── test-repo/                   # Sample Python repository
    └── (sample Python code)
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# GitLab Configuration
GITLAB_ROOT_PASSWORD=your_secure_password
GITLAB_HOST=http://localhost
GITLAB_API_TOKEN=your_gitlab_api_token

# Anthropic API Configuration
ANTHROPIC_API_KEY=your_anthropic_api_key
ANTHROPIC_MODEL=claude-sonnet-4.5-20241022
MAX_TOKENS_PER_REVIEW=4000

# Cost Management
DAILY_API_BUDGET_USD=5.00
MONTHLY_API_BUDGET_USD=100.00
ALERT_THRESHOLD_PERCENT=80

# SonarQube (Optional - Phase 3)
SONARQUBE_HOST=http://localhost:9000
SONARQUBE_TOKEN=your_sonarqube_token
```

## 💰 Cost Considerations

### Anthropic Claude API Pricing (as of project start)
- **Claude Sonnet 4.5**: ~$3 per million input tokens, ~$15 per million output tokens
- **Estimated costs**:
  - Small PR (~500 lines): $0.05 - $0.15
  - Medium PR (~1500 lines): $0.15 - $0.40
  - Large PR (~3000 lines): $0.30 - $0.80

### Cost Optimization Techniques
1. **Diff-only analysis** - Review only changed lines, not entire files
2. **Smart chunking** - Split large PRs into reviewable segments
3. **Caching** - Avoid re-reviewing unchanged code
4. **Configurable depth** - Quick scan vs. deep review options
5. **Budget alerts** - Stop reviews when budget threshold reached

### Cost Tracking Features
- Per-review cost calculation
- Daily/weekly/monthly usage reports
- Token usage statistics
- Budget remaining dashboard
- Cost per repository analytics

## 🔧 Usage Guide

### Starting the Environment

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Creating a Merge Request for Review

1. Push code changes to a feature branch
2. Create merge request in GitLab
3. Claude review automatically triggers via webhook
4. Review comments appear within 30-60 seconds
5. Review cost summary posted in MR description

### Interpreting Claude Reviews

Claude will provide:
- **Inline Comments**: Specific suggestions on code changes
- **Security Issues**: Potential vulnerabilities
- **Best Practices**: Python-specific recommendations
- **Performance**: Optimization opportunities
- **Maintainability**: Code clarity and structure feedback

## 🐛 Troubleshooting

### GitLab Container Issues
```bash
# Check container status
docker ps

# View GitLab logs
docker logs gitlab

# Restart GitLab
docker-compose restart gitlab
```

### Webhook Not Triggering
- Verify webhook URL is accessible from GitLab container
- Check GitLab webhook logs (Settings > Webhooks > Recent Deliveries)
- Ensure review service is running: `docker ps | grep review-service`

### API Cost Overruns
- Check current usage: Review cost tracker dashboard
- Adjust `MAX_TOKENS_PER_REVIEW` in `.env`
- Enable `STRICT_BUDGET_MODE` to halt reviews at threshold

### Claude API Errors
- Verify API key in `.env` file
- Check Anthropic API status
- Review rate limit settings
- Examine review-service logs for error details

## 📊 Success Metrics

- ✅ GitLab CE running and accessible
- ✅ Automated code reviews on all merge requests
- ✅ Average review time < 60 seconds
- ✅ API costs stay within budget ($100/month target)
- ✅ Actionable feedback on Python code quality
- ✅ (Stretch) SonarQube integration operational

## 🚧 Future Enhancements

- Multi-language support (beyond Python)
- Custom review rules and guidelines
- Integration with other AI models (comparison testing)
- Review quality feedback mechanism
- Historical trend analysis
- Team-specific coding standards enforcement
- Integration with Slack/Teams for notifications

## 📚 References

- [GitLab CE Docker Documentation](https://docs.gitlab.com/ee/install/docker.html)
- [Anthropic Claude API Documentation](https://docs.anthropic.com/)
- [SonarQube Docker Setup](https://docs.sonarqube.org/latest/setup/install-server/)
- [GitLab Webhooks](https://docs.gitlab.com/ee/user/project/integrations/webhooks.html)

## 📝 License

This is a proof-of-concept project for evaluation purposes.

---

**Status**: 🔴 Planning Phase  
**Next Step**: Phase 1 - GitLab Server Setup  
**Last Updated**: 2024
