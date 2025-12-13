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
    version="1.0.0"
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
        "version": "1.0.0"
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
        
        # Get AI review from Claude
        logger.info(f"Requesting review from Claude for MR {mr_iid}")
        review = await reviewer.review_code(diff, mr_title, mr_description)
        
        # Format and post review comment
        comment = format_review_comment(review)
        await gitlab.post_merge_request_comment(project_id, mr_iid, comment)
        
        logger.info(f"✅ Successfully completed review for MR {mr_iid}")
        
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
