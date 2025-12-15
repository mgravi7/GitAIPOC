# Changelog

All notable changes to the GitLab Code Review Agent will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2025-12-13

### Added
- **Token Budget Tracking**: Comprehensive token usage tracking and budget enforcement
  - Daily token limit with hard stop (default: 1M tokens/day)
  - Warning threshold at 80% of daily limit
  - Excel-friendly monthly CSV logs with separate year/month/day columns
  - Fast daily summary JSON files for sub-10ms budget checks
  - In-memory caching for performance
  - Automatic file cleanup (90 days for summaries, 365 days for logs)
- **Docker Volume Persistence**: Token data now persists across container restarts
- **New API Endpoint**: `GET /budget/status` to check current token usage
- **Budget Enforcement**: Automatic rejection of reviews when daily limit is reached
  - Clear error messages posted to MR comments
  - Automatic resume next day
  - No manual intervention needed
- **Excel-Optimized Logging**:
  - Separate columns for year, month, day, time
  - Monthly CSV files for manageable file sizes
  - Ready for pivot tables and analysis
  - Includes project, user, MR, and token details
- **UTC Timestamp Documentation**: Clear explanation of UTC usage and time zone conversion
- **Rate Limiting Documentation**: Comprehensive explanation of in-memory rate limiter
- **New Configuration Options**:
  - `TOKEN_BUDGET_ENABLED`: Enable/disable token tracking (default: true)
  - `TOKEN_DAILY_LIMIT`: Daily token limit (default: 1,000,000)
  - `TOKEN_WARNING_THRESHOLD`: Warning threshold (default: 800,000)
  - `TOKEN_DATA_DIR`: Data directory path (default: /app/data/tokens)
  - `TOKEN_SUMMARY_RETENTION_DAYS`: Summary retention (default: 90)
  - `TOKEN_LOG_RETENTION_DAYS`: Log retention (default: 365)

### Changed
- **Enhanced Review Flow**: Now includes budget check before API calls
- **Improved Error Handling**: Specific handling for budget exhaustion
- **Better Logging**: Includes token counts and budget status in log messages
- **Version Bump**: Application version updated to 1.2.0
- **Documentation**: Consolidated all token budget docs into README.md (removed 3 separate files)

### Fixed
- Token tracking only logs successful Claude API responses (not errors)
- Graceful degradation if token tracking fails
- Docker volumes now properly configured for data persistence

### Production Readiness
- ✅ **Tested**: All features tested with Claude Sonnet 4 and 4.5
- ✅ **Cost Controls**: Token budget + rate limiting (dual protection)
- ✅ **Reliability**: Retry logic with exponential backoff
- ✅ **Monitoring**: Budget status endpoint + detailed CSV logs
- ✅ **Documentation**: Comprehensive README with all features explained
- ✅ **Persistence**: Docker volumes configured for stateful data
- ✅ **Ready for Corporate GitLab**: Tested with self-hosted GitLab CE

## [1.1.0] - 2025-12-13

### Added
- **Automatic Retry Logic**: Added retry mechanism with exponential backoff for both GitLab and Anthropic API calls
  - Maximum of 3 retry attempts by default (configurable)
  - Smart retry on server errors (5xx) and network issues
  - No retry on client errors (4xx) to avoid unnecessary API calls
  - Exponential backoff with configurable delays (1s → 2s → 4s by default)
  - Maximum delay cap to prevent excessive waiting
- **New Configuration Options**:
  - `MAX_RETRIES`: Maximum retry attempts (default: 3)
  - `RETRY_INITIAL_DELAY`: Initial retry delay in seconds (default: 1.0)
  - `RETRY_BACKOFF_FACTOR`: Exponential backoff multiplier (default: 2.0)
  - `RETRY_MAX_DELAY`: Maximum retry delay cap (default: 10.0)

### Changed
- **Enhanced Error Logging**: Now includes attempt numbers and retry delays in log messages
- **Improved Reliability**: All API calls now automatically recover from transient failures
- **GitLab Client Refactoring**: Centralized retry logic in `_request_with_retry()` method
- **Updated Documentation**: Added comprehensive retry logic documentation in README.md

### Fixed
- Improved resilience against transient network issues
- Better handling of temporary service outages
- Reduced false failure notifications

## [1.0.0] - 2025-12-11

### Added
- Initial release of GitLab Code Review Agent
- Claude Sonnet 4 integration for AI-powered code reviews
- GitLab webhook support for automated review triggering
- Label-based review triggering (`ai-review` label)
- Rate limiting to control API usage
- Health check endpoint
- Docker-based deployment
- Environment-based configuration
- Comprehensive documentation

### Features
- Automatic code review on merge requests
- Security issue detection
- Performance optimization suggestions
- Best practices recommendations
- Bug detection and edge case analysis
- Maintainability improvements

### Security
- Webhook secret validation
- Bearer token authentication support
- Secure API key management via environment variables

---

## Version History

- **v1.2.0** - Token Budget & Cost Control (Current)
- **v1.1.0** - Retry Logic & Security Hardening
- **v1.0.0** - Initial Release

## Upgrade Guide

### From 1.1.0 to 1.2.0

1. **Pull Latest Code:**
   ```bash
   git pull origin feature/hardening
   ```

2. **Optional Configuration (uses defaults if not set):**
   ```env
   # Add to .env file (optional - has sensible defaults)
   TOKEN_BUDGET_ENABLED=true
   TOKEN_DAILY_LIMIT=1000000
   TOKEN_WARNING_THRESHOLD=800000
   TOKEN_DATA_DIR=/app/data/tokens
   TOKEN_SUMMARY_RETENTION_DAYS=90
   TOKEN_LOG_RETENTION_DAYS=365
   ```

3. **Update Docker Compose (if using volumes):**
   ```yaml
   services:
     code-review-agent:
       volumes:
         - token-data:/app/data/tokens
   
   volumes:
     token-data:
   ```

4. **Restart Service:**
   ```bash
   docker-compose up -d --force-recreate code-review-agent
   ```

5. **Verify:**
   ```bash
   # Check budget status
   curl http://localhost:8000/budget/status
   
   # Check logs
   docker-compose logs -f code-review-agent
   ```

**Note:** This is a backward-compatible update. All token budget settings have sensible defaults and work without any configuration changes.

### From 1.0.0 to 1.1.0

1. **Pull Latest Code:**
   ```bash
   git pull origin feature/hardening
   ```

2. **Optional Configuration (uses defaults if not set):**
   ```env
   # Add to .env file (optional)
   MAX_RETRIES=3
   RETRY_INITIAL_DELAY=1.0
   RETRY_BACKOFF_FACTOR=2.0
   RETRY_MAX_DELAY=10.0
   ```

3. **Restart Service:**
   ```bash
   docker-compose up -d --force-recreate code-review-agent
   ```

4. **Verify:**
   ```bash
   docker-compose logs -f code-review-agent
   ```

**Note:** This is a backward-compatible update. All retry settings have sensible defaults and work without any configuration changes.
