# -*- coding: utf-8 -*-
"""
Claude-based code reviewer using Anthropic API
"""
import httpx
import logging
from typing import Dict

from config import settings

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
    
    async def review_code(self, diff: str, mr_title: str, mr_description: str) -> str:
        """
        Review code changes using Claude
        
        Args:
            diff: Formatted code diff
            mr_title: Merge request title
            mr_description: Merge request description
            
        Returns:
            AI-generated code review
        """
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
        
        logger.info(f"Sending review request to Claude ({self.model})")
        
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
                return review_text
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Anthropic API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error calling Anthropic API: {str(e)}")
            raise
    
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
- List specific issues with severity (?? Critical, ?? Warning, ?? Info)
- Provide actionable recommendations
- Be constructive and helpful

Keep the review concise but thorough."""


# Global reviewer instance
reviewer = ClaudeReviewer()
