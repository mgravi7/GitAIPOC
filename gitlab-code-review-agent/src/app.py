# -*- coding: utf-8 -*-
"""
Code Review Agent - Main Application
FastAPI webhook listener for GitLab merge request events
"""
import logging
import asyncio
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict
from datetime import datetime

from src.config import settings
from src.gitlab_client import GitLabClient
from src.claude_reviewer import reviewer
from src.token_tracker import tracker
from src.exceptions import TokenBudgetExceeded

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Code Review Agent",
    description="AI-powered code reviews for GitLab merge requests using Claude",
    version="1.1.0"
)

# Initialize GitLab client
gitlab = GitLabClient()

# Simple in-memory rate limiter
review_timestamps = []


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.1.0"
    }


@app.get("/budget/status")
async def budget_status():
    """
    Get current token budget status
    
    Returns daily statistics including tokens used, remaining, and budget percentage
    """
    if not settings.token_budget_enabled:
        return {"enabled": False, "message": "Token budget tracking is disabled"}
    
    stats = await tracker.get_daily_stats()
    return {
        "enabled": True,
        "stats": stats
    }


@app.post("/webhook/gitlab")
async def gitlab_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    GitLab webhook endpoint for merge request events
    """
    try:
        # Parse webhook payload
        payload = await request.json()
        
        # Validate webhook secret if configured
        if settings.gitlab_webhook_secret:
            token = request.headers.get("X-Gitlab-Token")
            if token != settings.gitlab_webhook_secret:
                raise HTTPException(status_code=401, detail="Invalid webhook secret")
        
        # Extract event type
        event_type = payload.get("object_kind")
        
        if event_type != "merge_request":
            return {"status": "ignored", "reason": f"Not a merge request event: {event_type}"}
        
        # Extract MR details
        mr = payload.get("object_attributes", {})
        project = payload.get("project", {})
        
        project_id = project.get("id")
        mr_iid = mr.get("iid")
        action = mr.get("action")
        
        logger.info(f"Received MR event: project={project_id}, MR={mr_iid}, action={action}")
        
        # Check if we should review (based on labels)
        labels = [label.get("title") for label in payload.get("labels", [])]
        
        if settings.gitlab_trigger_label not in labels:
            return {
                "status": "skipped",
                "reason": f"Label '{settings.gitlab_trigger_label}' not present"
            }
        
        # Process review in background
        background_tasks.add_task(process_code_review, project_id, mr_iid)
        
        return {"status": "accepted", "message": "Review queued"}
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def process_code_review(project_id: int, mr_iid: int):
    """
    Process code review for a merge request
    
    Args:
        project_id: GitLab project ID
        mr_iid: Merge request IID
    """
    try:
        logger.info(f"Starting code review for MR {mr_iid} in project {project_id}")
        
        # Check rate limit
        if settings.rate_limit_enabled:
            if not check_rate_limit():
                error_msg = "⚠️ Rate limit exceeded. Please try again later."
                await gitlab.post_merge_request_comment(project_id, mr_iid, error_msg)
                return
        
        # Fetch MR details and changes
        mr_details = await gitlab.get_merge_request(project_id, mr_iid)
        mr_changes = await gitlab.get_merge_request_changes(project_id, mr_iid)
        
        mr_title = mr_details.get("title", "")
        mr_description = mr_details.get("description", "")
        
        # Extract author information for token tracking
        author = mr_details.get("author", {})
        username = author.get("username", "unknown")
        
        # Extract project name from web_url or use project_id as fallback
        project_web_url = mr_details.get("web_url", "")
        if project_web_url:
            # Extract project path from URL (e.g., "root/python-test-app")
            project_path = project_web_url.split("/merge_requests/")[0].split("/")[-2:]
            project_name = "/".join(project_path) if len(project_path) == 2 else str(project_id)
        else:
            project_name = str(project_id)
        
        # Format diff for review
        diff = gitlab.format_diff_for_review(mr_changes)
        
        # Check diff size
        diff_lines = len(diff.split("\n"))
        if diff_lines > settings.max_diff_size:
            error_msg = f"⚠️ Diff too large ({diff_lines} lines). Maximum is {settings.max_diff_size} lines."
            await gitlab.post_merge_request_comment(project_id, mr_iid, error_msg)
            return
        
        if not diff.strip():
            await gitlab.post_merge_request_comment(
                project_id, mr_iid, 
                "ℹ️ No code changes detected to review."
            )
            return
        
        # Get AI review from Claude (with budget check and token tracking)
        logger.info(f"Requesting review from Claude for MR {mr_iid}")
        review = await reviewer.review_code(
            diff, mr_title, mr_description,
            project_id, project_name, mr_iid, username
        )
        
        # Format and post review comment
        comment = format_review_comment(review)
        await gitlab.post_merge_request_comment(project_id, mr_iid, comment)
        
        logger.info(f"✅ Successfully completed review for MR {mr_iid}")
        
    except TokenBudgetExceeded as e:
        logger.warning(f"Token budget exhausted for MR {mr_iid}: {str(e)}")
        
        # Post budget exhausted message to MR
        budget_msg = f"""⚠️ **Daily Token Budget Exhausted**

{str(e)}

The AI code review service has reached its daily token limit. Reviews will automatically resume tomorrow.

**Budget Details:**
- Check the budget status at: `GET /budget/status`
- Reviews will resume at midnight UTC

**What you can do:**
- Merge requests will be queued automatically
- Remove and re-add the `{settings.gitlab_trigger_label}` label tomorrow to trigger a review
- Contact your DevOps team if this is urgent

---
*Token budget helps control costs and ensures fair usage across all teams.*
"""
        await gitlab.post_merge_request_comment(project_id, mr_iid, budget_msg)
        
    except Exception as e:
        logger.error(f"Error during code review: {str(e)}", exc_info=True)
        
        # Post error comment to MR
        try:
            error_comment = f"""❌ **AI Code Review Failed**

An error occurred during the review process:
```
{str(e)}
```

Please check the agent logs for details or contact support."""
            
            await gitlab.post_merge_request_comment(project_id, mr_iid, error_comment)
        except:
            logger.error("Failed to post error comment to GitLab")


def check_rate_limit() -> bool:
    """Simple rate limiter check"""
    global review_timestamps
    
    now = datetime.utcnow().timestamp()
    hour_ago = now - 3600
    
    # Remove old timestamps
    review_timestamps = [ts for ts in review_timestamps if ts > hour_ago]
    
    # Check limit
    if len(review_timestamps) >= settings.max_reviews_per_hour:
        logger.warning("Rate limit exceeded")
        return False
    
    # Add current timestamp
    review_timestamps.append(now)
    return True


def format_review_comment(review: str) -> str:
    """Format the AI review into a nice GitLab comment"""
    
    return f"""## 🤖 AI Code Review (Claude Sonnet 4)

{review}

---
*Generated by Code Review Agent • Powered by Anthropic Claude*
"""


# Run the application
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host=settings.app_host,
        port=settings.app_port,
        log_level=settings.log_level.lower()
    )
