# Copilot Instructions for GitAIPOC

## Project Overview

GitLab Code Review Agent - AI-powered code reviews using Claude Sonnet 4 for GitLab merge requests.

**Repository**: https://github.com/mgravi7/GitAIPOC  
**Current Version**: 1.2.0  
**Team Size**: 15-20 engineers  
**Expected Load**: ~20 MRs/day  

---

## Code Generation Guidelines

### 1. Documentation Philosophy

**⚠️ CRITICAL: Minimize Documentation**

- **Default**: Update existing docs (`README.md`, `CHANGELOG.md`) ONLY
- **Never** create separate documentation files without explicit request
- **Ask first**: "Should I create documentation for this feature?"
- **Restraint**: Developers are frightened by documentation volume
- **Be concise but thorough**: Explain clearly, briefly

**Anti-patterns to avoid:**
- ❌ Creating multiple docs for one feature (e.g., IMPLEMENTATION.md, SUMMARY.md, QUICK_REF.md)
- ❌ Documenting obvious patterns (retry logic, token budgeting)
- ❌ Creating docs before asking

**Approved approach:**
- ✅ One comprehensive document maximum (if separate doc is needed)
- ✅ Integrate into existing README when possible
- ✅ Show documentation plan upfront for approval

### 2. Architecture Documentation

**End of Project**: Create architecture diagrams using Mermaid for:
- System architecture (developers and DevOps audience)
- Data flow diagrams
- Component interactions
- Deployment architecture

**Not before project completion** - focus on working code first.

### 3. Code Style

- **Simplicity first**: No unnecessary complexity
- **File-based solutions**: Prefer files over databases for small scale (<100 ops/day)
- **Pragmatic design**: Right-sized for team (15-20 engineers)
- **Excel-friendly**: If logging, optimize for Excel analysis
- **Graceful degradation**: Features should fail gracefully

### 4. Feature Implementation

**Before implementing:**
1. Propose design with file list
2. Get approval
3. Implement code
4. Update CHANGELOG.md
5. Update README.md (existing sections)
6. **Ask** before creating new documentation

**Show plan upfront:**
```
## Proposed Changes
- Files to create: X, Y
- Files to modify: A, B
- Documentation: Update README.md section Z
- New docs: [ONLY IF ESSENTIAL - ask first]
```

### 5. Technology Stack

- **Backend**: FastAPI (Python 3.11)
- **AI**: Anthropic Claude Sonnet 4
- **Data**: File-based (JSON, CSV) - no database needed
- **Deployment**: Docker Compose
- **GitLab**: Self-hosted CE

### 6. Key Design Principles

1. **Scale appropriately**: 20 MRs/day, not 20,000
2. **Cost conscious**: Token budgets, rate limiting
3. **Developer-friendly**: Clear error messages, helpful comments in MRs
4. **Ops-friendly**: Simple deployment, easy monitoring
5. **Excel-ready**: Logs should open directly in Excel (separate date columns)

### 7. Testing Requirements

- Verify code compiles (use `get_errors` tool)
- Update CHANGELOG.md with version bump
- Include upgrade guide if breaking changes
- Test with realistic data (20 MRs/day scenario)

---

## Feature-Specific Guidance

### Token Budget

- File-based tracking (no database)
- Excel-optimized CSV: separate year/month/day/time columns
- Monthly log files (~600 KB each)
- Daily summary JSON for fast checks (<10ms)
- Hard limits, no Slack alerts (use MR comments)

### Retry Logic

- 3 attempts max
- Exponential backoff (1s → 2s → 4s)
- Retry on 5xx and network errors only
- No retry on 4xx errors
- Detailed logging with attempt numbers

### Rate Limiting

- Simple in-memory rate limiter
- Per-hour limits
- No complex quota systems needed

---

## Communication Style

- **Concise**: Get to the point
- **Practical**: Focus on what matters for 20 MRs/day
- **Honest**: Admit when simpler approaches work
- **Restrained**: Don't over-engineer or over-document

---

## Common Requests

### "Add retry logic"
→ Implement in code, update README config table, update CHANGELOG. **No separate retry doc.**

### "Add token budgeting"
→ Implement, update README, update CHANGELOG. **Ask before creating separate doc.**

### "Improve documentation"
→ **Ask first**: "Which section of README should I improve?" Not: "Create 3 new docs."

---

## Reminders

1. **Ask about documentation** before creating files
2. **One doc maximum** for any feature (if separate doc is essential)
3. **Mermaid diagrams** only at end of project
4. **Developers value conciseness** over comprehensive docs
5. **Show your plan** before implementing

---

**Last Updated**: December 13, 2025  
**Branch**: feature/hardening  
**Notes**: Documentation restraint added per user feedback
