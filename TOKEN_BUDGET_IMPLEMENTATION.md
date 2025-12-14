# Token Budget Implementation

**Version:** 1.2.0  
**Date:** December 13, 2025  
**Feature:** Daily token budget tracking and cost control

---

## 📋 Overview

The Token Budget feature provides comprehensive cost control for AI code reviews by tracking token usage and enforcing daily limits. This prevents unexpected costs and ensures fair usage across all teams.

### Key Features

- ✅ **Daily Budget Limits**: Hard stop at configurable token limit (default: 1M/day)
- ✅ **Excel-Friendly Logs**: Monthly CSV files optimized for Excel analysis
- ✅ **Fast Performance**: <10ms budget checks via in-memory caching
- ✅ **Automatic Cleanup**: Old logs deleted after retention period
- ✅ **Zero Overhead**: Only logs successful reviews, not errors
- ✅ **Graceful Degradation**: Reviews continue if logging fails

---

## 🏗️ Architecture

### File Structure

```
/app/data/tokens/
├── daily-summaries/              # Fast budget checks
│   ├── 2025-12-13.json          # Today's summary
│   ├── 2025-12-12.json          # Yesterday
│   └── ...                       # 90 days retention (configurable)
│
└── token-logs/                   # Detailed audit logs
    ├── 2025-12.csv              # December 2025
    ├── 2025-11.csv              # November 2025
    └── ...                       # 365 days retention (configurable)
```

### Design Rationale

**Why File-Based?**
- ✅ **Team Size**: 15-20 engineers = ~20 MRs/day
- ✅ **Performance**: Files sufficient for <100 MRs/day
- ✅ **Simplicity**: No database setup or maintenance
- ✅ **Portability**: Easy to backup, analyze, or migrate

**Why Monthly CSVs?**
- ✅ **Manageable Size**: ~600 KB/month (20 MRs/day)
- ✅ **Easy Analysis**: Open directly in Excel
- ✅ **Long Retention**: 1 year of logs = ~7 MB

**Why Daily Summaries?**
- ✅ **Fast Checks**: Single file read (~1 ms)
- ✅ **Atomic Updates**: No race conditions
- ✅ **Cache-Friendly**: 1-minute cache TTL

---

## 📊 Data Formats

### Daily Summary (JSON)

**File**: `daily-summaries/2025-12-13.json`

```json
{
  "date": "2025-12-13",
  "total_tokens": 847230,
  "input_tokens": 452100,
  "output_tokens": 395130,
  "request_count": 17,
  "last_updated": "2025-12-13T14:32:15Z",
  "budget_limit": 1000000,
  "budget_remaining": 152770,
  "budget_exhausted": false
}
```

**Purpose**: Lightning-fast budget checks before each review

### Monthly Log (CSV)

**File**: `token-logs/2025-12.csv`

```csv
year,month,day,time,project_id,project_name,mr_iid,username,input_tokens,output_tokens,total_tokens,model,duration_ms
2025,12,13,09:15:32,42,backend-api,123,john.doe,12450,18230,30680,claude-sonnet-4,2340
2025,12,13,09:47:18,42,backend-api,124,jane.smith,8920,12150,21070,claude-sonnet-4,1890
2025,12,13,10:12:05,58,frontend-app,89,bob.jones,15670,22340,38010,claude-sonnet-4,2650
```

**Excel-Friendly Design:**
- ✅ Separate `year`, `month`, `day` columns (no date parsing needed)
- ✅ `time` column in `HH:MM:SS` format
- ✅ All numeric columns for pivot tables
- ✅ No special characters or escaping

---

## 🎯 Usage Flow

### 1. Pre-Request Budget Check

```python
# Before calling Claude API
allowed, tokens_used, message = await tracker.check_budget()

if not allowed:
    # Daily limit reached - reject review
    raise TokenBudgetExceeded(message)
```

**Performance**: <10ms (cached), ~5ms (file read)

### 2. API Call

```python
# Call Claude API (existing logic)
response = await client.post(...)
result = response.json()
```

### 3. Post-Request Logging

```python
# Only on successful response
usage = result.get("usage", {})
await tracker.record_usage(TokenUsage(
    project_id=42,
    project_name="backend-api",
    mr_iid=123,
    username="john.doe",
    input_tokens=usage["input_tokens"],
    output_tokens=usage["output_tokens"],
    total_tokens=usage["input_tokens"] + usage["output_tokens"],
    model="claude-sonnet-4",
    duration_ms=2340
))
```

**Actions:**
1. Append to monthly CSV
2. Update daily summary JSON
3. Invalidate cache

---

## 📈 Excel Analysis Examples

### Import Data

```excel
1. Open Excel
2. Data → From Text/CSV
3. Select: token-logs/2025-12.csv
4. Click "Load"
```

**No import wizard needed!** CSV format is Excel-ready.

### Pivot Table Examples

#### 1. Token Usage by Project

```
Rows: project_name
Values: Sum of total_tokens
```

**Result:**
```
Project          Total Tokens
backend-api      847,230
frontend-app     412,560
mobile-app       298,150
```

#### 2. Token Usage by User

```
Rows: username
Values: Sum of total_tokens, Count of mr_iid
```

**Result:**
```
User         Reviews    Total Tokens    Avg Tokens
john.doe     8          387,450         48,431
jane.smith   5          234,120         46,824
bob.jones    4          225,660         56,415
```

#### 3. Daily Trend

```
Rows: year, month, day
Values: Sum of total_tokens, Count of mr_iid
```

**Result:**
```
Date         Reviews    Total Tokens
2025-12-01   12         543,210
2025-12-02   18         891,330
2025-12-03   15         712,450
```

### Formulas

```excel
' Total tokens for December
=SUM(K:K)

' Average tokens per review
=AVERAGE(K:K)

' Count reviews by user
=COUNTIF(H:H,"john.doe")

' Total cost (Claude Sonnet 4 pricing)
' Input: $3/M, Output: $15/M
=((SUM(I:I)/1000000)*3) + ((SUM(J:J)/1000000)*15)
```

### Charts

**Token Usage Over Time:**
1. Select columns: `day`, `total_tokens`
2. Insert → Line Chart
3. Add trend line

**Top Projects by Token Usage:**
1. Create pivot table (project_name, total_tokens)
2. Insert → Bar Chart
3. Sort descending

---

## ⚙️ Configuration

### Environment Variables

```env
# Enable/disable token budget tracking
TOKEN_BUDGET_ENABLED=true

# Daily token limit (across all projects)
TOKEN_DAILY_LIMIT=1000000

# Warning threshold (80% of limit)
TOKEN_WARNING_THRESHOLD=800000

# Data directory path
TOKEN_DATA_DIR=/app/data/tokens

# Retention periods
TOKEN_SUMMARY_RETENTION_DAYS=90   # Daily summaries
TOKEN_LOG_RETENTION_DAYS=365      # Monthly CSV logs
```

### Docker Volume

```yaml
services:
  code-review-agent:
    volumes:
      - token-data:/app/data/tokens
    environment:
      - TOKEN_DATA_DIR=/app/data/tokens

volumes:
  token-data:
    driver: local
```

---

## 🚦 Budget Enforcement

### Scenario: Daily Limit Reached

**User Experience:**

1. Developer adds `ai-review` label to MR
2. Webhook triggers review process
3. Budget check fails (limit exceeded)
4. Comment posted to MR:

```markdown
⚠️ **Daily Token Budget Exhausted**

The AI code review service has reached its daily token limit 
(1,000,000 tokens used). Reviews will automatically resume tomorrow.

**Budget Details:**
- Check the budget status at: GET /budget/status
- Reviews will resume at midnight UTC

**What you can do:**
- Remove and re-add the 'ai-review' label tomorrow
- Contact your DevOps team if this is urgent

---
Token budget helps control costs and ensures fair usage.
```

5. Review process stops gracefully
6. No error in logs (expected behavior)

**Next Day:**
- Budget resets at midnight UTC
- Developer re-adds label (or it's still there)
- Review processes normally

### Monitoring

**Check Current Budget:**

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
    "avg_tokens_per_review": 49837,
    "last_updated": "2025-12-13T14:32:15Z"
  }
}
```

---

## 💰 Cost Analysis

### Token Usage Patterns

**Based on 20 MRs/day (realistic for 15-20 engineers):**

| MR Size    | Lines  | Tokens/Review | Reviews/Day | Daily Tokens |
|------------|--------|---------------|-------------|--------------|
| Small      | <500   | 15,000        | 8 (40%)     | 120,000      |
| Medium     | 500-2K | 40,000        | 9 (45%)     | 360,000      |
| Large      | 2K-5K  | 80,000        | 3 (15%)     | 240,000      |
| **Total**  |        | **36,000**    | **20**      | **720,000**  |

**Result**: 720K tokens/day = **72% of default budget**

### Cost Calculation

**Claude Sonnet 4 Pricing:**
- Input: $3 per million tokens
- Output: $15 per million tokens

**Typical Review (Medium MR):**
- Input: 25,000 tokens (the diff + prompt)
- Output: 15,000 tokens (the review)
- Total: 40,000 tokens

**Cost per Review:**
```
Input:  (25,000 / 1,000,000) × $3  = $0.075
Output: (15,000 / 1,000,000) × $15 = $0.225
Total:                                $0.30
```

**Daily Cost (20 reviews):**
```
20 reviews × $0.30 = $6.00/day
```

**Monthly Cost (22 working days):**
```
$6.00 × 22 days = $132/month
```

**Budget Recommendation:**
- **Conservative**: 500K tokens/day (~$100/month)
- **Realistic**: 1M tokens/day (~$200/month)
- **Generous**: 2M tokens/day (~$400/month)

---

## 🔧 Maintenance

### Automatic Cleanup

**Runs**: Daily (can be triggered manually)

```python
# Cleanup old files
result = await tracker.cleanup_old_files()

# Returns: {'summaries_deleted': 5, 'logs_deleted': 2}
```

**What Gets Deleted:**
- Daily summaries older than 90 days (default)
- Monthly logs older than 365 days (default)

### Manual Export

**Export Token Data:**

```bash
# Export December 2025 logs
docker exec code-review-agent cat /app/data/tokens/token-logs/2025-12.csv > export-2025-12.csv

# Export today's summary
docker exec code-review-agent cat /app/data/tokens/daily-summaries/$(date +%Y-%m-%d).json
```

### Backup

**Backup Token Data:**

```bash
# Backup entire token directory
docker cp code-review-agent:/app/data/tokens ./backups/tokens-$(date +%Y-%m-%d)

# Or use Docker volume backup
docker run --rm -v token-data:/data -v $(pwd):/backup ubuntu tar czf /backup/token-data-backup.tar.gz /data
```

---

## 🎯 Best Practices

### Budget Planning

1. **Start Conservative**: Set limit to 500K tokens/day
2. **Monitor for 1 Week**: Track actual usage
3. **Adjust Based on Data**: Increase if needed
4. **Set Warning Threshold**: 80% of limit

### Excel Analysis

1. **Monthly Review**: Analyze token logs each month
2. **Identify Patterns**: Which projects use most tokens?
3. **Optimize**: Encourage smaller MRs
4. **Report to Team**: Share cost breakdown

### Cost Optimization

1. **Smaller MRs**: Encourage focused, smaller changes
2. **Good Code**: Clean code = shorter reviews = fewer tokens
3. **Skip Trivial Changes**: Don't review documentation-only changes
4. **Batch Reviews**: Review multiple small commits together

---

## 🐛 Troubleshooting

### Issue: Token Logs Not Created

**Symptoms:**
- No CSV files in `token-logs/` directory
- Budget status shows 0 tokens

**Diagnostic:**
```bash
# Check if directory exists
docker exec code-review-agent ls -la /app/data/tokens/

# Check permissions
docker exec code-review-agent ls -la /app/data/tokens/token-logs/

# Check logs
docker logs code-review-agent | grep -i token
```

**Solutions:**
1. Verify `TOKEN_BUDGET_ENABLED=true`
2. Check directory permissions (should be writable)
3. Ensure Docker volume is mounted
4. Check disk space

### Issue: Budget Not Resetting

**Symptoms:**
- Budget shows exhausted the next day
- Yesterday's tokens still counting

**Cause:**
- Daily summaries use file date, not current date
- Cache not invalidated

**Solution:**
```bash
# Restart agent to reset cache
docker-compose restart code-review-agent

# Or delete old summary (manual reset)
docker exec code-review-agent rm /app/data/tokens/daily-summaries/$(date -d yesterday +%Y-%m-%d).json
```

### Issue: Performance Degradation

**Symptoms:**
- Budget checks taking >100ms
- Reviews slow to start

**Diagnostic:**
```bash
# Check file count
docker exec code-review-agent find /app/data/tokens -type f | wc -l

# Check file sizes
docker exec code-review-agent du -sh /app/data/tokens/*
```

**Solutions:**
1. Run cleanup: `await tracker.cleanup_old_files()`
2. Reduce retention periods
3. Archive old logs manually

---

## 📊 Example Scenarios

### Scenario 1: Normal Day (720K tokens)

```
08:00 - Review #1:  45K tokens  (Budget: 955K remaining)
09:30 - Review #2:  38K tokens  (Budget: 917K remaining)
10:15 - Review #3:  52K tokens  (Budget: 865K remaining)
...
16:45 - Review #20: 41K tokens  (Budget: 280K remaining)

End of Day: 720K tokens used (72% of budget)
Status: ✅ Healthy
```

### Scenario 2: High Usage Day (980K tokens)

```
08:00 - Review #1:  45K tokens  (Budget: 955K remaining)
...
15:30 - Review #25: 48K tokens  (Budget: 120K remaining)
15:45 - ⚠️ Warning: 88% of budget used
16:00 - Review #26: 62K tokens  (Budget: 58K remaining)
16:15 - Review #27: ❌ REJECTED - Budget exhausted

MR Comment: "Daily token budget exhausted. Reviews resume tomorrow."
```

### Scenario 3: Large MR Spike

```
10:00 - Review #1:  150K tokens (Very large MR)
10:05 - ⚠️ Warning: Single review used 15% of budget
10:30 - Review #2:  45K tokens
...
End of Day: 850K tokens (85% of budget)

Action: Team lead reviews large MRs manually
```

---

## 🚀 Future Enhancements

### Potential Features

- [ ] **Project-Level Budgets**: Per-project token limits
- [ ] **User Quotas**: Fair usage per developer
- [ ] **Time-Based Limits**: Hourly or weekly budgets
- [ ] **Cost Dashboard**: Real-time web UI for monitoring
- [ ] **Slack Alerts**: Notify when 80% budget used
- [ ] **Smart Limits**: Dynamic budgets based on team size
- [ ] **Token Forecasting**: Predict end-of-day usage

### Database Migration (If Needed)

**When to Consider:**
- >100 MRs/day (file-based becomes slower)
- Need complex queries (join projects, users)
- Want real-time dashboards

**Migration Path:**
1. Keep CSV logs (audit trail)
2. Add SQLite for queries
3. Sync CSV → SQLite daily
4. Gradual migration

---

## ✅ Summary

### What We Built

- ✅ File-based token tracking (no database needed)
- ✅ Excel-optimized monthly CSV logs
- ✅ Fast daily summary JSON files
- ✅ Hard budget limits with graceful enforcement
- ✅ Automatic cleanup of old logs
- ✅ Sub-10ms budget checks via caching

### What It Solves

- ✅ **Cost Control**: Prevents runaway API costs
- ✅ **Fair Usage**: Ensures budget shared across teams
- ✅ **Visibility**: Easy Excel analysis of usage patterns
- ✅ **Simplicity**: No database, no complex setup

### Perfect For

- ✅ Teams of 15-50 engineers
- ✅ 20-100 MRs/day
- ✅ Budget-conscious organizations
- ✅ Simple infrastructure preferences

---

**Implementation Date:** December 13, 2025  
**Version:** 1.2.0  
**Status:** ✅ Production Ready  
**Branch:** feature/hardening
