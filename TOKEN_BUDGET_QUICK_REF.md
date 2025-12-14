# Token Budget - Quick Reference Card

## 🎯 At a Glance

**Purpose**: Control AI code review costs with daily token limits  
**Approach**: File-based tracking with Excel-friendly CSV logs  
**Performance**: <10ms budget checks  
**Default Limit**: 1,000,000 tokens/day  

---

## 📁 File Structure

```
/app/data/tokens/
├── daily-summaries/
│   └── 2025-12-13.json       # Fast budget checks
└── token-logs/
    └── 2025-12.csv            # Monthly CSV (Excel-ready)
```

---

## ⚙️ Configuration (.env)

```env
TOKEN_BUDGET_ENABLED=true      # Enable tracking
TOKEN_DAILY_LIMIT=1000000      # Daily limit (tokens)
TOKEN_WARNING_THRESHOLD=800000 # Warning at 80%
```

---

## 📊 CSV Format (Excel-Optimized)

```csv
year,month,day,time,project_id,project_name,mr_iid,username,input_tokens,output_tokens,total_tokens,model,duration_ms
2025,12,13,09:15:32,42,backend-api,123,john.doe,12450,18230,30680,claude-sonnet-4,2340
```

**Excel Tips:**
- Open directly (no import wizard)
- Pivot by: project_name, username, day
- Sum: total_tokens
- Cost formula: `=((SUM(I:I)/1000000)*3) + ((SUM(J:J)/1000000)*15)`

---

## 🔍 Check Budget

```bash
# API endpoint
curl http://localhost:8000/budget/status

# Response
{
  "total_tokens": 720000,
  "budget_used_percent": 72.0,
  "budget_remaining": 280000
}
```

---

## 💰 Cost Estimate (Your Team)

**20 MRs/day:**
- Daily: 720K tokens = $6
- Monthly: 15.8M tokens = **$132**

**Budget vs Reality:**
- Limit: 1M tokens/day
- Actual: 720K/day (72%)
- Buffer: 28% ✅

---

## ⚠️ Budget Exhausted

**MR Comment:**
```
⚠️ Daily Token Budget Exhausted

Reviews will resume tomorrow.
Remove and re-add 'ai-review' label tomorrow.
```

**Action**: Wait until next day (auto-reset at midnight UTC)

---

## 🗂️ Export Data

```bash
# Export December CSV
docker cp code-review-agent:/app/data/tokens/token-logs/2025-12.csv ./

# Open in Excel
start 2025-12.csv
```

---

## 🎯 Key Files

| File | Purpose |
|------|---------|
| `src/token_tracker.py` | Core tracking logic |
| `src/config.py` | Configuration settings |
| `src/claude_reviewer.py` | Budget check before API call |
| `src/app.py` | `/budget/status` endpoint |
| `src/exceptions.py` | `TokenBudgetExceeded` exception |

---

## ✅ Production Checklist

- [ ] Set `TOKEN_DAILY_LIMIT` based on budget
- [ ] Mount Docker volume for persistence
- [ ] Test budget exhaustion scenario
- [ ] Test budget reset next day
- [ ] Test Excel CSV import
- [ ] Monitor `/budget/status` daily

---

## 🐛 Common Issues

**Logs not created?**
→ Check `TOKEN_BUDGET_ENABLED=true`

**Budget not resetting?**
→ Restart: `docker-compose restart code-review-agent`

**Excel shows dates weird?**
→ Use separate year/month/day columns (already separated!)

---

## 📞 Support

- Docs: `TOKEN_BUDGET_IMPLEMENTATION.md`
- Changelog: `CHANGELOG.md` (v1.2.0)
- Summary: `IMPLEMENTATION_SUMMARY.md`

---

**Version**: 1.2.0  
**Date**: December 13, 2025  
**Status**: ✅ Production Ready
