# -*- coding: utf-8 -*-
"""
GitLab API client for fetching merge requests and posting comments
"""
import httpx
import logging
from typing import Dict, List, Optional

from config import settings

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
        Fetch merge request details
        
        Args:
            project_id: GitLab project ID
            mr_iid: Merge request IID (internal ID)
            
        Returns:
            Merge request details
        """
        url = f"{self.base_url}/api/v4/projects/{project_id}/merge_requests/{mr_iid}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
    
    async def get_merge_request_changes(self, project_id: int, mr_iid: int) -> Dict:
        """
        Fetch merge request diff/changes
        
        Args:
            project_id: GitLab project ID
            mr_iid: Merge request IID
            
        Returns:
            MR changes including diffs
        """
        url = f"{self.base_url}/api/v4/projects/{project_id}/merge_requests/{mr_iid}/changes"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
    
    async def post_merge_request_comment(
        self, 
        project_id: int, 
        mr_iid: int, 
        comment: str
    ) -> Dict:
        """
        Post a comment on a merge request
        
        Args:
            project_id: GitLab project ID
            mr_iid: Merge request IID
            comment: Comment text (markdown supported)
            
        Returns:
            Created comment details
        """
        url = f"{self.base_url}/api/v4/projects/{project_id}/merge_requests/{mr_iid}/notes"
        
        data = {"body": comment}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url, 
                headers=self.headers, 
                json=data,
                timeout=30.0
            )
            response.raise_for_status()
            logger.info(f"Posted comment to MR {mr_iid} in project {project_id}")
            return response.json()
    
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
