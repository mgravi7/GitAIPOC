# Testing Walkthrough Guide

Complete step-by-step guide for testing the GitLab Code Review Agent from scratch.

## Overview

This guide will walk you through:
1. Setting up a local GitLab instance
2. Creating a service account
3. Creating a test project with sample code
4. Triggering an AI code review
5. Verifying the results
6. Troubleshooting common issues

**Expected Time:** 30-45 minutes (first time), 10-15 minutes (subsequent tests)

---

## Prerequisites

Before starting, ensure you have:
- ✅ Docker Desktop installed and running
- ✅ At least 4GB RAM allocated to Docker
- ✅ 20GB free disk space
- ✅ Anthropic API key (from https://console.anthropic.com/)
- ✅ Git repository cloned: `C:\Repos\GitAIPOC`

---

## Phase 1: Environment Setup (5 minutes)

### Step 1: Configure Environment Variables

```powershell
# Navigate to local-testing directory
cd C:\Repos\GitAIPOC\local-testing

# Copy environment template
cp .env.example .env
```

### Step 2: Edit `.env` File

Open `local-testing\.env` in your editor and configure:

```bash
# Docker Compose Configuration
COMPOSE_PROJECT_NAME=gitaipoc-local

# GitLab CE Configuration
GITLAB_ROOT_PASSWORD=<your-secure-password>

# GitLab API Configuration (will update later)
GITLAB_URL=http://gitlab
GITLAB_TOKEN=glpat-PLACEHOLDER
GITLAB_WEBHOOK_SECRET=<generate-random-32-char-string>
GITLAB_TRIGGER_LABEL=ai-review

# Anthropic Configuration
ANTHROPIC_API_KEY=sk-ant-<your-actual-api-key>
ANTHROPIC_MODEL=claude-sonnet-4-20250514
ANTHROPIC_MAX_TOKENS=4096
ANTHROPIC_API_VERSION=2023-06-01

# Application Configuration
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=INFO

# Rate Limiting
RATE_LIMIT_ENABLED=true
MAX_REVIEWS_PER_HOUR=50

# Review Configuration
REVIEW_TIMEOUT=120
MAX_DIFF_SIZE_LINES=10000
```

**Important:** 
- `COMPOSE_PROJECT_NAME` sets the project name in Docker Desktop (you'll see "gitaipoc-local" instead of "local-testing")
- Replace `<your-secure-password>` with your own strong password (min 8 chars)
- Replace `sk-ant-<your-actual-api-key>` with your real Anthropic API key
- Replace `<generate-random-32-char-string>` with a randomly generated secret (use PowerShell below)
- Keep `GITLAB_TOKEN=glpat-PLACEHOLDER` for now (we'll update it in Phase 2)

**Generate Random Webhook Secret (PowerShell):**
```powershell
-join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})
```

### Step 3: Start Services

```powershell
# Start GitLab and Code Review Agent
docker-compose up -d
```

**Expected Output:**
```
[+] Running 2/2
 ✔ Container gitlab-local             Started
 ✔ Container code-review-agent-local  Started
```

### Step 4: Wait for GitLab Initialization

GitLab takes 2-3 minutes to start up on first run.

**Monitor progress:**
```powershell
docker-compose logs -f gitlab
```

**Look for this message:**
```
gitlab Reconfigured!
```

**Press Ctrl+C** to stop following logs once you see this message.

### Step 5: Verify Services are Running

```powershell
docker-compose ps
```

**Expected Output:**
```
NAME                       STATUS
gitlab-local               Up (healthy)
code-review-agent-local    Up (healthy)
```

---

## Phase 2: GitLab Configuration (10 minutes)

### Step 1: Access GitLab

Open your browser and navigate to: http://localhost

**Login Credentials:**
- **Username:** `root`
- **Password:** (the `GITLAB_ROOT_PASSWORD` from your `.env` file)

### Step 2: Create Service Account

#### 2.1: Navigate to Admin Area

1. Click the **menu icon** (☰) in the top-left
2. Select **"Admin"** from the dropdown
3. You should see the Admin Area dashboard

#### 2.2: Create User

1. In left sidebar: **Overview** → **Users**
2. Click **"New user"** button (top-right)

#### 2.3: Fill in User Details

```
Name:              GitLab AI Review Bot
Username:          gitlab-ai-reviewer
Email:             ai-reviewer@localhost
```

**Important Settings:**
- **Access level:** Regular
- **External:** ☐ Unchecked
- **Can create group:** ☐ Unchecked
- **Projects limit:** 0

Click **"Create user"**

#### 2.4: Set Password

1. After creation, you'll be on the user's detail page
2. Click **"Edit"** button (top-right)
3. Scroll to **"Password"** section
4. Set a strong password (min 8 characters with mix of upper, lower, numbers, symbols)
5. **Uncheck:** "User must change password at next sign-in"
6. Click **"Save changes"**

**Note:** Remember this password - you'll need it in the next step to log in as this user.

#### 2.4.1: First Login as Service Account

**Important:** You must log in as the service account to activate it before generating tokens.

1. **Log out** from the root account (click your avatar → Sign out)
2. Log in with the service account:
   - **Username:** `gitlab-ai-reviewer`
   - **Password:** (the password you just set in step 2.4)
3. GitLab may prompt you to change your password - you can keep the same password or set a new one
4. After successful login, you'll see the GitLab homepage as `gitlab-ai-reviewer`
5. **Keep this window open** - you'll generate the token while logged in as this user

**Tip:** You can open a new browser window or incognito/private window to stay logged in as root in another session if needed.

#### 2.5: Generate Personal Access Token

**Note:** Make sure you're logged in as `gitlab-ai-reviewer` (from step 2.4.1).

1. Click your **avatar** (top-right) → **Preferences**
2. In left sidebar, click **Access Tokens**
3. Click **"Add new token"**

**Token Configuration:**
```
Token name:       Code Review Agent
Expiration date:  (leave blank or 1 year)
```

**Select Scopes:** (check these boxes)
- ✅ `api`
- ✅ `read_api`
- ✅ `read_repository`
- ✅ `write_repository`

Click **"Create personal access token"**

#### 2.6: Copy Token

**⚠️ CRITICAL:** The token will only be shown once!

**Example format:** `glpat-xxXXxxXXxxXXxxXXxxXX`

**Copy this token immediately** and update your `.env` file:

```bash
GITLAB_TOKEN=glpat-<your-actual-token>
```

**Save the `.env` file.**

#### 2.6.1: Log Back In as Root

1. **Log out** from the `gitlab-ai-reviewer` account (avatar → Sign out)
2. **Log back in as root:**
   - **Username:** `root`
   - **Password:** (your `GITLAB_ROOT_PASSWORD` from `.env` file)
3. You'll need root access for the next configuration steps

#### 2.7: Enable Local Network Webhooks

**Note:** Make sure you're logged in as `root` for this admin configuration.

1. Admin Area → **Settings** → **Network**
2. Expand **"Outbound requests"**
3. ✅ Check **"Allow requests to the local network from webhooks and integrations"**
4. Click **"Save changes"**

### Step 3: Restart Code Review Agent

With the updated token, restart the agent:

```powershell
docker-compose up -d --force-recreate code-review-agent
```

**Note:** We use `--force-recreate` instead of `restart` to ensure the updated `.env` file is reloaded. A simple restart doesn't reload environment variables.

**Verify it's running:**
```powershell
curl http://localhost:8000/health
```

**Expected Response:**
```json
{"status":"healthy","timestamp":"2025-12-13T...","version":"1.0.0"}
```

---

## Phase 3: Create Test Project (10 minutes)

### Step 1: Create New Project

1. In GitLab (logged in as `root`), click **"+"** → **"New project/repository"**
2. Select **"Create blank project"**

**Project Details:**
```
Project name:        python-test-app
Project URL:         Select "root" from the dropdown
Visibility Level:    Private
```

**Initialize repository:**
- ✅ Check **"Initialize repository with a README"**

Click **"Create project"**

**Note:** The full project URL will be `http://localhost/root/python-test-app`

### Step 2: Add Service Account to Project

1. In project sidebar: **Manage** → **Members**
2. Click **"Invite members"**
3. Search for: `gitlab-ai-reviewer`
4. **Role:** Developer
5. Click **"Invite"**

**Verify:** You should see `gitlab-ai-reviewer` listed as a Developer.

### Step 3: Configure Webhook

1. In project sidebar: **Settings** → **Webhooks**
2. Click **"Add new webhook"**

**Webhook Configuration:**
```
URL:     http://code-review-agent:8000/webhook/gitlab
Secret:  <use-same-secret-from-your-.env-file>
```

**Trigger:**
- ✅ Check **"Merge request events"**

**SSL verification:**
- ☐ Uncheck (for local testing)

Click **"Add webhook"**

**Note:** The webhook secret must match `GITLAB_WEBHOOK_SECRET` in your `.env` file.

#### 3.1: Test Webhook

1. Find your webhook in the list
2. Click **"Test"** → **"Merge request events"**

**Expected Result:**
- You may see: **"Hook execution failed: Ensure the project has merge requests."**
- This is **normal** - you haven't created a merge request yet!
- The webhook will work when you create an actual MR in Phase 4

**Alternative:** You can skip this test and verify the webhook works when you add the `ai-review` label to your merge request in Phase 4, Step 3.

**If you see `HTTP 200`:**
- Great! The webhook configuration is correct (though test data may be limited)

**If you see other errors:**
- Verify "Allow local network" is enabled (Phase 2, Step 2.7)
- Verify the URL is correct: `http://code-review-agent:8000/webhook/gitlab`
- Check agent logs: `docker-compose logs code-review-agent`

### Step 4: Create Project Label

1. In project sidebar: **Settings** → **Labels**
2. Click **"New label"**
3. **Title:** `ai-review`
4. **Description:** `Trigger AI code review`
5. **Color:** Choose any color (e.g., blue or green)
6. Click **"Create label"**

**Note:** This label will be used to trigger code reviews on merge requests.

### Step 5: Create Feature Branch

1. In project, click **Code** → **Branches**
2. Click **"New branch"**
3. **Branch name:** `feature/add-authentication`
4. **Create from:** `main`
5. Click **"Create branch"**

### Step 6: Add Test Code Files

We'll create two Python files with intentional issues for Claude to find.

#### File 1: `app.py`

1. In project, ensure you're on `feature/add-authentication` branch
2. Click **"+"** → **"New file"**
3. **File name:** `app.py`
4. **Paste this code:**

```python
import sqlite3

def authenticate_user(username, password):
    # SQL Injection vulnerability - intentional for testing
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    cursor.execute(query)
    
    user = cursor.fetchone()
    conn.close()
    
    return user is not None

def process_user_data(users):
    # Performance issue - string concatenation in loop
    result = ""
    for user in users:
        result = result + user['name'] + ","
    
    return result

def fetch_user_profile(user_id):
    # Missing error handling and type hints
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,))
    profile = cursor.fetchone()
    return profile

# Hardcoded credentials - security issue
ADMIN_PASSWORD = "admin123"
API_KEY = "sk-1234567890abcdef"

class UserManager:
    def __init__(self):
        self.users = []
    
    def add_user(self, username, password):
        # No input validation
        self.users.append({
            'username': username,
            'password': password
        })
```

5. **Commit message:** `Add user authentication module`
6. **Target branch:** `feature/add-authentication`
7. Click **"Commit changes"**

#### File 2: `utils.py`

1. Click **"+"** → **"New file"**
2. **File name:** `utils.py`
3. **Paste this code:**

```python
def calculate_total(items):
    # Missing type hints
    total = 0
    for item in items:
        # Unsafe type conversion
        total += int(item)
    return total

def process_file(filename):
    # Missing error handling - file might not exist
    with open(filename, 'r') as f:
        data = f.read()
    return data.split('\n')

# Inefficient algorithm - O(n²)
def find_duplicates(numbers):
    duplicates = []
    for i in range(len(numbers)):
        for j in range(i + 1, len(numbers)):
            if numbers[i] == numbers[j]:
                duplicates.append(numbers[i])
    return duplicates
```

4. **Commit message:** `Add utility functions`
5. **Target branch:** `feature/add-authentication`
6. Click **"Commit changes"**

---

## Phase 4: Create Merge Request (5 minutes)

### Step 1: Create MR

1. Go to **Merge requests** in left sidebar
2. Click **"New merge request"**
3. **Source branch:** `feature/add-authentication`
4. **Target branch:** `main`
5. You'll see the merge request creation form with the diff preview

### Step 2: Fill in MR Details and Add Label

On the merge request creation page:

```
Title:        Add user authentication module
Description:  Implementing authentication features for the application
```

**Before clicking "Create merge request":**
1. Scroll down to the **"Labels"** section
2. Click in the labels dropdown
3. Select the **`ai-review`** label (created in Phase 3, Step 4)

Click **"Create merge request"**

**⏱️ The webhook is now triggered!**

---

## Phase 5: Monitor Review Process (2-5 minutes)

### Step 1: Watch Agent Logs

In your PowerShell terminal:

```powershell
docker-compose logs -f code-review-agent
```

**What to look for:**

```
INFO - Received MR event: project=1, MR=1, action=update
INFO - Starting code review for MR 1 in project 1
INFO - Requesting review from Claude for MR 1
```

### Step 2: Wait for Review

**Expected time:** 30-90 seconds

**Process:**
1. Webhook received (< 1 second)
2. MR fetched from GitLab (~1 second)
3. Diff sent to Claude (~30-60 seconds)
4. Review posted back to GitLab (~1 second)

### Step 3: Check for Review Comment

Refresh your merge request page in GitLab.

**You should see a comment from `gitlab-ai-reviewer` that includes:**

✅ **Summary Section**
- Overview of issues found
- Severity breakdown

✅ **Critical Issues (🔴)**
- SQL Injection vulnerability
- Hardcoded credentials
- Plain text password storage

✅ **Warning Issues (⚠️)**
- Resource leaks (unclosed connections)
- Performance issues (string concatenation, O(n²) algorithm)
- Missing error handling

✅ **Info Issues (ℹ️)**
- Missing type hints
- No input validation
- Code style issues

✅ **Recommendations**
- Specific fixes for each issue
- Code examples
- Best practices

---

## Phase 6: Verify Success ✅

### Checklist

Use this checklist to confirm everything worked:

- [ ] GitLab started successfully
- [ ] Service account created (`gitlab-ai-reviewer`)
- [ ] Personal access token generated and saved
- [ ] Agent restarted with token
- [ ] Test project created (`python-test-app`)
- [ ] Service account added as Developer
- [ ] Webhook configured and tested (HTTP 200)
- [ ] Feature branch created
- [ ] Test files (`app.py`, `utils.py`) committed
- [ ] Merge request created
- [ ] `ai-review` label added
- [ ] Review comment posted by `gitlab-ai-reviewer`
- [ ] Review identifies all major issues

---

## Expected Review Output

### Summary Example

```markdown
## 🤖 AI Code Review (Claude Sonnet 4)

### Code Review Summary
This merge request introduces a user authentication module with multiple 
critical security vulnerabilities and performance issues that must be 
addressed before merging.

### Issues Found

#### 🔴 Critical Issues
1. **SQL Injection Vulnerability (app.py:8)**
   - Risk: Allows arbitrary SQL execution
   - Fix: Use parameterized queries

2. **Hardcoded Secrets (app.py:32-34)**
   - Risk: Credentials exposed in source control
   - Fix: Use environment variables

[... more detailed issues ...]

### Verdict
❌ REJECT - Critical security vulnerabilities must be resolved before merging.
```

---

## Troubleshooting Guide

### Issue: GitLab Not Starting

**Symptoms:**
- Container shows "unhealthy" status
- Can't access http://localhost

**Diagnostic Steps:**
```powershell
# Check logs
docker-compose logs gitlab

# Check container status
docker-compose ps
```

**Common Causes:**
1. Insufficient Docker memory (need 4GB+)
2. Port 80 already in use
3. First startup taking longer (wait 5 minutes)

**Solutions:**
- Increase Docker memory allocation
- Stop other services using port 80
- Wait longer and check logs

### Issue: Webhook Returns 401 Unauthorized

**Symptoms:**
- Webhook test shows "401 Unauthorized"
- No review posted

**Diagnostic Steps:**
```powershell
# Check agent logs
docker-compose logs code-review-agent

# Verify webhook secret is set
Get-Content .env | Select-String "WEBHOOK_SECRET"
```

**Common Causes:**
1. Webhook secret mismatch between `.env` and GitLab webhook
2. Agent not restarted after token update

**Solutions:**
- Verify secret matches in `.env` and GitLab webhook configuration
- Restart agent: `docker-compose restart code-review-agent`

### Issue: Webhook Returns 404 Not Found

**Symptoms:**
- Webhook test shows "404 Not Found"

**Diagnostic Steps:**
```powershell
# Check if agent is running
curl http://localhost:8000/health

# Check container logs
docker-compose logs code-review-agent
```

**Common Causes:**
1. Agent not running
2. Wrong webhook URL

**Solutions:**
- Verify URL: `http://code-review-agent:8000/webhook/gitlab`
- Restart agent if needed

### Issue: No Review Posted

**Symptoms:**
- Webhook returns 200 OK
- No comment appears on MR

**Diagnostic Steps:**
```powershell
# Check agent logs for errors
docker-compose logs code-review-agent | Select-String "ERROR"

# Verify service account access
# Check in GitLab: Settings → Members
```

**Common Causes:**
1. Service account doesn't have Developer access
2. Token has wrong scopes
3. Anthropic API key invalid
4. Rate limit exceeded

**Solutions:**
- Add service account to project as Developer
- Regenerate token with correct scopes
- Verify Anthropic API key
- Check rate limit settings

### Issue: Review Posted But Shows Error

**Symptoms:**
- Comment posted saying "AI Code Review Failed"

**Diagnostic Steps:**
```powershell
# Check detailed error in logs
docker-compose logs code-review-agent --tail 100

# Look for Anthropic API errors
docker-compose logs code-review-agent | Select-String "anthropic"
```

**Common Causes:**
1. Invalid Anthropic API key
2. Insufficient API credits
3. Model name incorrect
4. Network issues reaching api.anthropic.com

**Solutions:**
- Verify API key at https://console.anthropic.com/
- Check API usage/credits
- Verify model name: `claude-sonnet-4-20250514`
- Check internet connectivity

### Issue: Agent Using Old Environment Variables

**Symptoms:**
- Updated `.env` file but agent still shows old behavior
- 401 errors after updating `GITLAB_TOKEN`
- Agent not picking up configuration changes

**Diagnostic Steps:**
```powershell
# Check if container has the updated token
docker exec code-review-agent-local env | Select-String "GITLAB_TOKEN"
```

**Common Cause:**
- Using `docker-compose restart` which doesn't reload `.env` file
- Docker only loads environment variables during `docker-compose up`

**Solution:**
```powershell
# Force recreate the container to reload .env
docker-compose up -d --force-recreate code-review-agent
```

**Important:** Always use `--force-recreate` after updating `.env` file!

---

## Cost Tracking

For this test, you should expect:

**Tokens Used:**
- Input: ~800 tokens (the code diff)
- Output: ~1,200 tokens (the review)

**Cost Calculation:**
- Input: (800 tokens / 1,000,000) × $3.00 = $0.0024
- Output: (1,200 tokens / 1,000,000) × $15.00 = $0.018
- **Total: ~$0.02 per review**

**Pricing (Claude Sonnet 4):**
- Input tokens: $3.00 per million
- Output tokens: $15.00 per million

**Note:** Actual costs may vary based on diff size and review complexity. Check your usage at: https://console.anthropic.com/

---

### Realistic Production Cost Estimates

**Typical Team Usage (20 developers, 1 review/day each):**

**Average MR (2,500 lines):**
- Input: ~12,500 tokens (2,500 lines × ~5 tokens/line)
- Output: ~2,000 tokens (good code = shorter review)
- **Cost per review: ~$0.07**

**Daily costs:**
- 20 reviews/day × $0.07 = **$1.40/day**

**Monthly costs:**
- $1.40/day × 22 working days = **~$31/month**

**Annual costs:**
- $31/month × 12 months = **~$370/year**

---

### Cost Breakdown by MR Size

| MR Size | Lines | Input Tokens | Output Tokens | Cost/Review |
|---------|-------|--------------|---------------|-------------|
| **Small** | 500 | 2,500 | 1,200 | $0.03 |
| **Medium** | 2,500 | 12,500 | 2,000 | $0.07 |
| **Large** | 5,000 | 25,000 | 3,000 | $0.12 |
| **Very Large** | 10,000 | 50,000 | 4,000 | $0.21 |

**Note:** Good code typically results in shorter reviews (fewer output tokens), reducing costs. Poor code with many issues generates longer, more detailed reviews.

---

### Monthly Budget Scenarios

**Conservative (10 reviews/day):**
- Daily: $0.70
- Monthly (22 days): **~$15**
- Annual: **~$185**

**Realistic (20 reviews/day):**
- Daily: $1.40
- Monthly (22 days): **~$31**
- Annual: **~$370**

**High Volume (50 reviews/day):**
- Daily: $3.50
- Monthly (22 days): **~$77**
- Annual: **~$925**

---

### Cost Optimization Tips

1. **Good code = Lower costs** - Clean code with fewer issues results in shorter reviews
2. **Smaller MRs** - Encourage breaking large changes into smaller, focused MRs
3. **Rate limiting** - Current setting: 50 reviews/hour prevents accidental cost spikes
4. **Monitor usage** - Track costs at https://console.anthropic.com/
5. **Diff size limit** - Current: 10,000 lines prevents extremely expensive reviews
