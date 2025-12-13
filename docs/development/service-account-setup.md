# Production Service Account Setup for GitLab AI Review Agent

## Overview

This guide documents the production-ready approach for creating a dedicated service account for the GitLab AI Review Agent. This approach follows enterprise best practices and can be handed off to DevOps teams.

---

## Why Use a Service Account?

### Benefits

✅ **Security**: Separate from human user accounts  
✅ **Audit Trail**: Reviews appear from "gitlab-ai-reviewer" bot  
✅ **Lifecycle Management**: Account persists when humans leave  
✅ **Least Privilege**: Grant only required permissions  
✅ **Compliance**: Meets enterprise security requirements  

### Comparison: Personal Token vs. Service Account

| Aspect | Personal Token (POC Only) | Service Account (Production) |
|--------|---------------------------|------------------------------|
| **Security** | ❌ Tied to human account | ✅ Dedicated non-human account |
| **Audit Trail** | ❌ Shows as user's activity | ✅ Shows as bot activity |
| **Permissions** | ❌ User's full permissions | ✅ Minimal required permissions |
| **Lifecycle** | ❌ Expires with user | ✅ Independent lifecycle |
| **Best Practice** | ❌ Not recommended | ✅ Enterprise standard |

---

## Prerequisites

- GitLab administrator access (or DevOps team with admin rights)
- Ability to create new users
- Ability to manage user permissions

---

## Step-by-Step Setup

### Step 1: Access GitLab Admin Area

1. Log in to GitLab as an administrator
2. Click the **menu icon** (☰) in the top-left
3. Select **"Admin"** from the menu
4. You should now see the Admin Area dashboard

### Step 2: Create Service Account User

1. In Admin Area, navigate to:
   - **Overview** → **Users**

2. Click **"New user"** button (top-right)

3. Fill in the user creation form:

   ```
   Name:              GitLab AI Review Bot
   Username:          gitlab-ai-reviewer
   Email:             ai-reviewer@yourcompany.com
   ```

   **Important Settings:**
   - **Access level**: Regular
   - **External**: ☐ Unchecked
   - **Can create group**: ☐ Unchecked (optional)
   - **Projects limit**: 0 (service account doesn't own projects)
   - ✅ **"Create user without sending activation email"** (check this)

4. Click **"Create user"**

### Step 3: Set Service Account Password

1. After creation, you'll be on the user's detail page
2. Click **"Edit"** button (top-right)
3. Scroll to **"Password"** section
4. Set a strong password:
   ```
   Minimum 8 characters
   Mix of upper/lower case, numbers
   Store securely (e.g., in password manager or secrets vault)
   ```
5. Click **"Save changes"**

**Note**: This password is rarely used (mainly for emergency access). The access token is what the agent uses.

### Step 4: Generate Personal Access Token

1. On the service account's user page, click **"Personal Access Tokens"** (left sidebar or top tab)

2. Click **"Add new token"**

3. Configure the token:

   ```
   Token name:       Code Review Agent Production
   Expiration date:  1 year from now (or per your security policy)
   ```

4. **Select scopes** (check these boxes):
   - ✅ `api` - Full API access (required for posting comments)
   - ✅ `read_api` - Read API access
   - ✅ `read_repository` - Read repository contents
   - ✅ `write_repository` - Post review comments

   **Optional scopes** (do NOT enable):
   - ☐ `sudo` - Not needed
   - ☐ `admin_mode` - Not needed
   - ☐ `create_runner` - Not needed
   - ☐ `manage_runner` - Not needed

5. Click **"Create personal access token"**

6. **⚠️ CRITICAL**: Copy the token immediately!
   - Token format: `glpat-xxxxxxxxxxxxxxxxxxxxx`
   - You will only see this once
   - Store securely in your secrets management system

### Step 5: Grant Service Account Project Access

The service account needs access to repositories it will review.

**Option A: Grant Access to Specific Projects** (Recommended)

For each project that needs AI reviews:

1. Go to the project → **Settings** → **Members**
2. Click **"Invite members"**
3. Search for `gitlab-ai-reviewer`
4. **Role**: `Developer` (minimum required)
   - Developer role allows reading code and posting comments
   - Reporter role is too limited (can't post comments)
   - Maintainer/Owner is excessive
5. Click **"Invite"**

**Option B: Grant Access to All Projects** (Use with caution)

For admin-level access (only if reviewing ALL projects):

1. In Admin Area → **Users** → Find `gitlab-ai-reviewer`
2. Click **"Edit"**
3. Set **Access level** to `Admin` (⚠️ Use only if necessary)
4. Click **"Save changes"**

**Recommendation**: Use Option A for production (least privilege principle)

### Step 6: Document Service Account Details

Create a document (store securely) with:

```yaml
Service Account Details:
  Name: GitLab AI Review Bot
  Username: gitlab-ai-reviewer
  Email: ai-reviewer@yourcompany.com
  Purpose: Automated AI code reviews via Claude Sonnet 4.5
  Token Name: Code Review Agent Production
  Token Created: YYYY-MM-DD
  Token Expiration: YYYY-MM-DD
  Scopes: api, read_api, read_repository, write_repository
  
Access Token:
  Value: glpat-xxxxxxxxxxxxxxxxxxxxx
  Storage Location: [Your secrets management system]
  
Permissions:
  - Developer access to: [list of projects]
  
Rotation Schedule:
  - Token rotation: Every 90 days (or per policy)
  - Password rotation: Every 180 days (or per policy)
  
Owner:
  - Team: DevOps / Platform Engineering
  - Contact: devops-team@yourcompany.com
```

---

## Configuration in Review Agent

### Update .env File

```bash
# GitLab API Configuration (Service Account)
GITLAB_URL=https://gitlab.yourcompany.com
GITLAB_TOKEN=glpat-xxxxxxxxxxxxxxxxxxxxx  # Service account token
GITLAB_WEBHOOK_SECRET=your-webhook-secret
GITLAB_TRIGGER_TAG=ai-review
```

### For POC (Localhost)

```bash
GITLAB_URL=http://gitlab
GITLAB_TOKEN=glpat-xxxxxxxxxxxxxxxxxxxxx  # Service account token from above
```

---

## Security Best Practices

### Token Management

✅ **DO:**
- Store token in secrets management system (Vault, AWS Secrets Manager, etc.)
- Use environment variables (never hardcode)
- Rotate tokens every 90 days
- Audit token usage regularly
- Revoke old tokens immediately

❌ **DON'T:**
- Commit tokens to Git
- Share tokens via email/Slack
- Use personal account tokens in production
- Leave tokens without expiration
- Grant more permissions than needed

### Access Control

✅ **DO:**
- Use service account (not personal account)
- Grant minimal required permissions (Developer role)
- Limit access to specific projects if possible
- Monitor API usage
- Enable 2FA for the service account (if supported)

❌ **DON'T:**
- Use admin-level access unless absolutely necessary
- Grant write access to all repositories
- Share service account credentials with developers
- Use the same token across multiple environments

### Monitoring & Auditing

✅ **DO:**
- Log all API calls from the review agent
- Monitor for unusual patterns
- Set up alerts for failed authentication
- Review access logs monthly
- Track token expiration dates

---

## Token Rotation Procedure

### When to Rotate

- Every 90 days (recommended)
- When a team member with access leaves
- After a suspected security incident
- When changing environments (dev → staging → prod)

### Rotation Steps

1. **Generate new token** (follow Step 4 above)
2. **Update .env file** with new token
3. **Test in staging** before production
4. **Deploy updated configuration**
5. **Verify agent connectivity**
6. **Revoke old token** in GitLab:
   - Admin Area → Users → gitlab-ai-reviewer
   - Personal Access Tokens
   - Click "Revoke" on old token
7. **Document rotation** in change log

---

## Troubleshooting

### Service Account Can't Access Project

**Symptom**: Agent can't fetch merge request details

**Solution**:
1. Verify service account has Developer access to project
2. Check token scopes include `read_repository`
3. Verify token hasn't expired
4. Check GitLab audit logs for permission denials

### Can't Post Review Comments

**Symptom**: Reviews run but comments don't appear

**Solution**:
1. Verify service account has Developer role (not just Reporter)
2. Check token scopes include `api` and `write_repository`
3. Verify webhook secret matches between GitLab and agent
4. Check review agent logs for API errors

### Token Authentication Failed

**Symptom**: Agent can't authenticate with GitLab

**Solution**:
1. Verify token copied correctly (no extra spaces)
2. Check token hasn't been revoked
3. Verify token hasn't expired
4. Test token with curl:
   ```bash
   curl -H "PRIVATE-TOKEN: glpat-xxx" https://gitlab.yourcompany.com/api/v4/user
   ```

---

## Handoff to DevOps Team

### Information to Provide

When handing off to DevOps team, provide:

1. ✅ This document
2. ✅ Service account requirements:
   - Username: `gitlab-ai-reviewer`
   - Scopes: `api`, `read_api`, `read_repository`, `write_repository`
   - Role: Developer (per project) or Admin (if global)
3. ✅ List of projects requiring AI review
4. ✅ Webhook configuration requirements
5. ✅ Network requirements (agent needs access to gitlab.yourcompany.com)
6. ✅ Security requirements (token storage, rotation policy)

### DevOps Team Checklist

- [ ] Service account created: `gitlab-ai-reviewer`
- [ ] Password set and stored securely
- [ ] Personal access token generated
- [ ] Token stored in secrets management system
- [ ] Token scopes verified: `api`, `read_api`, `read_repository`, `write_repository`
- [ ] Service account granted Developer access to required projects
- [ ] Token rotation schedule documented (90 days recommended)
- [ ] Monitoring/alerting configured for service account activity
- [ ] Token provided to review agent deployment
- [ ] Review agent tested and verified working
- [ ] Documentation updated with service account details

---

## Comparison: POC vs. Production

| Configuration Item | POC (localhost) | Production (team) |
|-------------------|-----------------|-------------------|
| **Account Type** | Service account | Service account |
| **Username** | `gitlab-ai-reviewer` | `gitlab-ai-reviewer` |
| **GitLab URL** | `http://gitlab` | `https://gitlab.yourcompany.com` |
| **Token Storage** | `.env` file (gitignored) | Secrets management system |
| **Token Rotation** | Manual | Automated (90-day schedule) |
| **Access Scope** | All projects (local POC) | Specific projects only |
| **Monitoring** | Basic logs | Full audit logging |
| **Security** | Basic | Enterprise-grade |

---

## Next Steps

After creating the service account:

1. ✅ Copy the access token
2. ✅ Update `.env` file with `GITLAB_TOKEN=glpat-xxx`
3. ✅ Restart review agent: `docker-compose restart gitlab-ai-reviewer`
4. ✅ Verify agent can connect to GitLab
5. ✅ Create test project
6. ✅ Configure webhook
7. ✅ Test AI code review

---

**Document Version**: 1.0  
**Last Updated**: December 13, 2025  
**Author**: GitAIPOC Team  
**Status**: Production-Ready
