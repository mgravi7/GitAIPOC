# -*- coding: utf-8 -*-
"""
GitLab API client for fetching merge requests and posting comments
"""
import httpx
import logging
import asyncio
from typing import Dict, List, Optional

from src.config import settings

logger = logging.getLogger(__name__)


class GitLabClient:
    """Client for GitLab API interactions"""
    
    def __init__(self):
        self.base_url = settings.gitlab_url.rstrip('/')
        self.token = settings.gitlab_token
        self.headers = {
            "PRIVATE-TOKEN": self.token,
            "Content-Type": "application/json"
        }
    
    async def get_merge_request(self, project_id: int, mr_iid: int) -> Dict:
        """
        Fetch merge request details with retry logic
        
        Args:
            project_id: GitLab project ID
            mr_iid: Merge request IID (internal ID)
            
        Returns:
            Merge request details
        """
        url = f"{self.base_url}/api/v4/projects/{project_id}/merge_requests/{mr_iid}"
        return await self._request_with_retry("GET", url)
    
    async def get_merge_request_changes(self, project_id: int, mr_iid: int) -> Dict:
        """
        Fetch merge request diff/changes with retry logic
        
        Args:
            project_id: GitLab project ID
            mr_iid: Merge request IID
            
        Returns:
            MR changes including diffs
        """
        url = f"{self.base_url}/api/v4/projects/{project_id}/merge_requests/{mr_iid}/changes"
        return await self._request_with_retry("GET", url)
    
    async def post_merge_request_comment(
        self, 
        project_id: int, 
        mr_iid: int, 
        comment: str
    ) -> Dict:
        """
        Post a comment on a merge request with retry logic
        
        Args:
            project_id: GitLab project ID
            mr_iid: Merge request IID
            comment: Comment text (markdown supported)
            
        Returns:
            Created comment details
        """
        url = f"{self.base_url}/api/v4/projects/{project_id}/merge_requests/{mr_iid}/notes"
        data = {"body": comment}
        
        result = await self._request_with_retry("POST", url, json_data=data)
        logger.info(f"Posted comment to MR {mr_iid} in project {project_id}")
        return result
    
    async def _request_with_retry(
        self, 
        method: str, 
        url: str, 
        json_data: Optional[Dict] = None
    ) -> Dict:
        """
        Make HTTP request with retry logic and exponential backoff
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            json_data: Optional JSON payload for POST requests
            
        Returns:
            Response JSON
        """
        for attempt in range(settings.max_retries):
            try:
                async with httpx.AsyncClient() as client:
                    if method == "GET":
                        response = await client.get(url, headers=self.headers, timeout=30.0)
                    elif method == "POST":
                        response = await client.post(
                            url, 
                            headers=self.headers, 
                            json=json_data,
                            timeout=30.0
                        )
                    else:
                        raise ValueError(f"Unsupported HTTP method: {method}")
                    
                    response.raise_for_status()
                    return response.json()
                    
            except httpx.HTTPStatusError as e:
                logger.error(f"GitLab API error (attempt {attempt + 1}/{settings.max_retries}): {e.response.status_code} - {e.response.text}")
                if attempt < settings.max_retries - 1 and e.response.status_code >= 500:
                    delay = self._calculate_retry_delay(attempt)
                    logger.info(f"Retrying GitLab API call in {delay:.1f} seconds...")
                    await asyncio.sleep(delay)
                else:
                    raise
            except (httpx.TimeoutException, httpx.NetworkError, httpx.ConnectError) as e:
                logger.error(f"GitLab network/timeout error (attempt {attempt + 1}/{settings.max_retries}): {str(e)}")
                if attempt < settings.max_retries - 1:
                    delay = self._calculate_retry_delay(attempt)
                    logger.info(f"Retrying GitLab API call in {delay:.1f} seconds...")
                    await asyncio.sleep(delay)
                else:
                    raise
            except Exception as e:
                logger.error(f"Unexpected error during GitLab API call: {str(e)}")
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
    
    def format_diff_for_review(self, changes: Dict) -> str:
        """
        Format MR changes into readable diff for Claude
        
        Args:
            changes: MR changes from GitLab API
            
        Returns:
            Formatted diff text
        """
        diff_parts = []
        
        for change in changes.get("changes", []):
            file_path = change.get("new_path") or change.get("old_path")
            diff = change.get("diff", "")
            
            if diff:
                diff_parts.append(f"## File: {file_path}\n```diff\n{diff}\n```\n")
        
        return "\n".join(diff_parts)
