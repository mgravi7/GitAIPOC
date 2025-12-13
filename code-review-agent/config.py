# -*- coding: utf-8 -*-
"""
Configuration management for Code Review Agent
Loads and validates environment variables
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application configuration from environment variables"""
    
    # ===== GitLab Configuration =====
    gitlab_url: str = Field(..., description="GitLab instance URL")
    gitlab_token: str = Field(..., description="GitLab API token")
    gitlab_webhook_secret: Optional[str] = Field(None, description="Webhook secret for validation")
    gitlab_trigger_label: str = Field(default="ai-review", description="Label to trigger reviews")
    
    # ===== Anthropic Configuration =====
    anthropic_api_key: str = Field(..., description="Anthropic API key")
    anthropic_model: str = Field(
        default="claude-sonnet-4-20250514",
        description="Claude model to use"
    )
    anthropic_max_tokens: int = Field(
        default=4096,
        description="Maximum tokens for Claude response"
    )
    anthropic_api_version: str = Field(
        default="2023-06-01",
        description="Anthropic API version"
    )
    
    # ===== Application Configuration =====
    app_host: str = Field(default="0.0.0.0", description="Application host")
    app_port: int = Field(default=8000, description="Application port")
    log_level: str = Field(default="INFO", description="Logging level")
    
    # ===== Rate Limiting =====
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
    max_reviews_per_hour: int = Field(default=50, description="Maximum reviews per hour")
    
    # ===== Review Configuration =====
    review_timeout: int = Field(default=120, description="Review timeout in seconds")
    max_diff_size: int = Field(default=10000, description="Maximum diff size in lines")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
