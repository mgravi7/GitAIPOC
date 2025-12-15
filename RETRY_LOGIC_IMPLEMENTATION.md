# Retry Logic Implementation - Security Hardening

## Overview

Added automatic retry logic with exponential backoff to the GitLab Code Review Agent for improved reliability and resilience against transient network issues and server errors.

## Changes Made

### 1. Configuration Updates (`src/config.py`)

Added retry configuration settings:

```python
# Retry Configuration
max_retries: int = 3
retry_initial_delay: float = 1.0
retry_backoff_factor: float = 2.0
retry_max_delay: float = 10.0
```

**Configuration Options:**
- `MAX_RETRIES`: Maximum number of retry attempts (default: 3)
- `RETRY_INITIAL_DELAY`: Initial delay between retries in seconds (default: 1.0)
- `RETRY_BACKOFF_FACTOR`: Exponential backoff multiplier (default: 2.0)
- `RETRY_MAX_DELAY`: Maximum delay cap in seconds (default: 10.0)

### 2. Claude Reviewer Updates (`src/claude_reviewer.py`)

Enhanced `review_code()` method with:
- ✅ Automatic retry loop (up to 3 attempts)
- ✅ Exponential backoff calculation
- ✅ Smart retry on 5xx errors and network issues
- ✅ No retry on 4xx client errors (authentication, not found, etc.)
- ✅ Detailed logging of retry attempts

**Retry Behavior:**
```
Attempt 1 → 503 Service Error → Wait 1.0s
Attempt 2 → Network Timeout → Wait 2.0s
Attempt 3 → Success ✓
```

**Error Types That Trigger Retry:**
- `httpx.HTTPStatusError` with status >= 500 (server errors)
- `httpx.TimeoutException` (request timeouts)
- `httpx.NetworkError` (network failures)
- `httpx.ConnectError` (connection failures)

### 3. GitLab Client Updates (`src/gitlab_client.py`)

Refactored all API methods to use a centralized `_request_with_retry()` method:
- ✅ `get_merge_request()` - Fetch MR details with retry
- ✅ `get_merge_request_changes()` - Fetch MR diff with retry
- ✅ `post_merge_request_comment()` - Post comments with retry

**Implementation:**
- Single retry method handles both GET and POST requests
- Exponential backoff calculation (same as Claude reviewer)
- Comprehensive error logging with attempt numbers
- Graceful degradation after max retries

### 4. Documentation Updates (`README.md`)

Added comprehensive documentation:
- ✅ Retry logic feature in Features section
- ✅ Retry configuration table
- ✅ Retry behavior explanation with examples
- ✅ Troubleshooting guide for retry-related issues

## Example Retry Sequence

### Successful Retry After Transient Error

```
INFO - Sending review request to Claude (claude-sonnet-4-20250514)
ERROR - Anthropic API error (attempt 1/3): 503 - Service Temporarily Unavailable
INFO - Retrying in 1.0 seconds...
ERROR - Network/timeout error (attempt 2/3): Connection timeout
INFO - Retrying in 2.0 seconds...
INFO - Received review from Claude (1247 chars)
```

### All Retries Exhausted

```
ERROR - GitLab API error (attempt 1/3): 500 - Internal Server Error
INFO - Retrying GitLab API call in 1.0 seconds...
ERROR - GitLab API error (attempt 2/3): 500 - Internal Server Error
INFO - Retrying GitLab API call in 2.0 seconds...
ERROR - GitLab API error (attempt 3/3): 500 - Internal Server Error
ERROR - Error during code review: HTTP 500 - Internal Server Error
```

## Configuration Examples

### Default Configuration (Conservative)

```env
MAX_RETRIES=3
RETRY_INITIAL_DELAY=1.0
RETRY_BACKOFF_FACTOR=2.0
RETRY_MAX_DELAY=10.0
```

**Retry delays:** 1s → 2s → 4s

### Aggressive Retries (High Latency Networks)

```env
MAX_RETRIES=5
RETRY_INITIAL_DELAY=2.0
RETRY_BACKOFF_FACTOR=2.0
RETRY_MAX_DELAY=30.0
```

**Retry delays:** 2s → 4s → 8s → 16s → 30s

### Minimal Retries (Fast Fail)

```env
MAX_RETRIES=2
RETRY_INITIAL_DELAY=0.5
RETRY_BACKOFF_FACTOR=2.0
RETRY_MAX_DELAY=5.0
```

**Retry delays:** 0.5s → 1s

## Benefits

### 1. Improved Reliability
- Automatically recovers from transient network issues
- Handles temporary service outages gracefully
- Reduces false failure notifications

### 2. Production Ready
- No manual intervention needed for transient failures
- Smart retry logic (doesn't retry on auth errors)
- Configurable for different environments

### 3. Better Observability
- Detailed logging of retry attempts
- Clear visibility into retry sequences
- Easy debugging of persistent issues

### 4. Cost Effective
- Prevents wasted reviews due to network hiccups
- Reduces manual re-triggering of reviews
- Better resource utilization

## Testing Recommendations

### Unit Testing
```python
# Test retry on 5xx error
# Test retry on network timeout
# Test no retry on 4xx error
# Test exponential backoff calculation
# Test max delay cap
```

### Integration Testing
```bash
# Test with real GitLab instance
# Test with Anthropic API
# Test under network instability
# Test timeout scenarios
```

### Load Testing
```bash
# Test concurrent retries
# Test retry behavior under rate limiting
# Verify no retry storms
```

## Monitoring

### Key Metrics to Track
- Average retry count per request
- Success rate after retries
- Time spent in retries
- Retry exhaustion rate

### Alerting Thresholds
- Alert if retry exhaustion > 5% of requests
- Alert if average retries > 1.5 per request
- Alert if retry delays exceed 10 seconds frequently

## Migration Guide

### For Existing Deployments

1. **Update Code:**
   ```bash
   git pull origin feature/hardening
   ```

2. **Update Environment (Optional):**
   ```env
   # Add to .env file
   MAX_RETRIES=3
   RETRY_INITIAL_DELAY=1.0
   RETRY_BACKOFF_FACTOR=2.0
   RETRY_MAX_DELAY=10.0
   ```

3. **Restart Service:**
   ```bash
   docker-compose up -d --force-recreate code-review-agent
   ```

4. **Monitor Logs:**
   ```bash
   docker-compose logs -f code-review-agent | grep -i retry
   ```

### Backward Compatibility

- ✅ All retry settings have sensible defaults
- ✅ No breaking changes to existing functionality
- ✅ Works with existing .env files
- ✅ No API changes

## Future Enhancements

### Potential Improvements
- [ ] Jitter in retry delays to prevent thundering herd
- [ ] Circuit breaker pattern for persistent failures
- [ ] Retry metrics endpoint for monitoring
- [ ] Per-endpoint retry configuration
- [ ] Adaptive retry delays based on error patterns

### Advanced Features
- [ ] Retry budget (max retries per hour)
- [ ] Correlation ID tracking across retries
- [ ] Retry queue for failed requests
- [ ] Dead letter queue for exhausted retries

## References

- **Exponential Backoff:** https://en.wikipedia.org/wiki/Exponential_backoff
- **HTTPX Exceptions:** https://www.python-httpx.org/exceptions/
- **GitLab API:** https://docs.gitlab.com/ee/api/
- **Anthropic API:** https://docs.anthropic.com/

---

**Implementation Date:** December 2025  
**Version:** 1.1.0  
**Status:** ✅ Complete  
**Branch:** feature/hardening
