# -*- coding: utf-8 -*-
"""
Claude-based code reviewer using Anthropic API
"""
import httpx
import logging
import asyncio
from typing import Dict
from datetime import datetime

from src.config import settings
from src.token_tracker import tracker, TokenUsage
from src.exceptions import TokenBudgetExceeded

logger = logging.getLogger(__name__)


class ClaudeReviewer:
    """Code reviewer using Claude Sonnet 4 via Anthropic API"""
    
    def __init__(self):
        self.api_key = settings.anthropic_api_key
        self.model = settings.anthropic_model
        self.max_tokens = settings.anthropic_max_tokens
        self.api_version = settings.anthropic_api_version
        self.api_url = "https://api.anthropic.com/v1/messages"
        
        self.headers = {
            "x-api-key": self.api_key,
            "anthropic-version": self.api_version,
            "content-type": "application/json"
        }
    
    async def review_code(
        self,
        diff: str,
        mr_title: str,
        mr_description: str,
        project_id: int,
        project_name: str,
        mr_iid: int,
        username: str
    ) -> str:
        """
        Review code changes using Claude with retry logic and token tracking
        
        Args:
            diff: Formatted code diff
            mr_title: Merge request title
            mr_description: Merge request description
            project_id: GitLab project ID
            project_name: GitLab project name
            mr_iid: Merge request IID
            username: User who created the MR
            
        Returns:
            AI-generated code review
            
        Raises:
            TokenBudgetExceeded: If daily token budget is exhausted
        """
        # CHECK BUDGET BEFORE API CALL
        if settings.token_budget_enabled:
            allowed, tokens_used, message = await tracker.check_budget()
            if not allowed:
                logger.warning(f"Token budget exhausted for MR {mr_iid}: {message}")
                raise TokenBudgetExceeded(message)
            
            if tokens_used >= settings.token_warning_threshold:
                logger.warning(f"Token budget warning for MR {mr_iid}: {message}")
        
        # Record start time for duration tracking
        start_time = datetime.utcnow()
        
        prompt = self._build_review_prompt(diff, mr_title, mr_description)
        
        payload = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        logger.info(f"Sending review request to Claude ({self.model}) for MR {mr_iid}")
        
        for attempt in range(settings.max_retries):
            try:
                async with httpx.AsyncClient(timeout=settings.review_timeout) as client:
                    response = await client.post(
                        self.api_url,
                        headers=self.headers,
                        json=payload
                    )
                    response.raise_for_status()
                    
                    result = response.json()
                    review_text = result["content"][0]["text"]
                    
                    logger.info(f"Received review from Claude ({len(review_text)} chars)")
                    
                    # RECORD TOKEN USAGE (only on successful response)
                    if settings.token_budget_enabled:
                        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                        usage_data = result.get("usage", {})
                        
                        if usage_data:
                            await tracker.record_usage(TokenUsage(
                                project_id=project_id,
                                project_name=project_name,
                                mr_iid=mr_iid,
                                username=username,
                                input_tokens=usage_data.get("input_tokens", 0),
                                output_tokens=usage_data.get("output_tokens", 0),
                                total_tokens=(
                                    usage_data.get("input_tokens", 0) + 
                                    usage_data.get("output_tokens", 0)
                                ),
                                model=self.model,
                                duration_ms=duration_ms
                            ))
                    
                    return review_text
                    
            except httpx.HTTPStatusError as e:
                logger.error(f"Anthropic API error (attempt {attempt + 1}/{settings.max_retries}): {e.response.status_code} - {e.response.text}")
                if attempt < settings.max_retries - 1 and e.response.status_code >= 500:
                    delay = self._calculate_retry_delay(attempt)
                    logger.info(f"Retrying in {delay:.1f} seconds...")
                    await asyncio.sleep(delay)
                else:
                    raise
            except (httpx.TimeoutException, httpx.NetworkError, httpx.ConnectError) as e:
                logger.error(f"Network/timeout error (attempt {attempt + 1}/{settings.max_retries}): {str(e)}")
                if attempt < settings.max_retries - 1:
                    delay = self._calculate_retry_delay(attempt)
                    logger.info(f"Retrying in {delay:.1f} seconds...")
                    await asyncio.sleep(delay)
                else:
                    raise
            except Exception as e:
                logger.error(f"Error calling Anthropic API: {str(e)}")
                raise
    
    def _calculate_retry_delay(self, attempt: int) -> float:
        """
        Calculate exponential backoff delay
        
        Args:
            attempt: Current attempt number (0-based)
            
        Returns:
            Delay in seconds
        """
        delay = settings.retry_initial_delay * (settings.retry_backoff_factor ** attempt)
        return min(delay, settings.retry_max_delay)
    
    def _build_review_prompt(self, diff: str, mr_title: str, mr_description: str) -> str:
        """Build the prompt for Claude code review"""
        
        return f"""You are an expert code reviewer. Please review the following code changes from a merge request.

**Merge Request:** {mr_title}
**Description:** {mr_description or "No description provided"}

**Code Changes:**
{diff}

Please provide a thorough code review focusing on:

1. **Security Issues** - Identify vulnerabilities (SQL injection, XSS, hardcoded secrets, etc.)
2. **Performance** - Highlight inefficient code, unnecessary loops, or optimization opportunities
3. **Best Practices** - Code style, naming conventions, error handling
4. **Bugs** - Potential bugs or edge cases not handled
5. **Maintainability** - Code clarity, documentation, complexity

Format your review as:
- Start with a brief summary
- List specific issues with severity (🔴 Critical, ⚠️ Warning, ℹ️ Info)
- Provide actionable recommendations
- Be constructive and helpful

Keep the review concise but thorough."""


# Global reviewer instance
reviewer = ClaudeReviewer()
