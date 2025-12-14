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
    max_diff_size_lines: int = Field(default=10000, description="Maximum diff size in lines")
    
    # ===== Retry Configuration =====
    max_retries: int = Field(default=3, description="Maximum number of retry attempts")
    retry_initial_delay: float = Field(default=1.0, description="Initial delay between retries in seconds")
    retry_backoff_factor: float = Field(default=2.0, description="Exponential backoff multiplier")
    retry_max_delay: float = Field(default=10.0, description="Maximum delay between retries in seconds")
    
    # ===== Token Budget Configuration =====
    token_budget_enabled: bool = Field(default=True, description="Enable token budget tracking and enforcement")
    token_daily_limit: int = Field(default=1000000, description="Maximum tokens per day across all projects")
    token_warning_threshold: int = Field(default=800000, description="Warning threshold (tokens)")
    token_data_dir: str = Field(default="/app/data/tokens", description="Directory for token tracking data")
    token_summary_retention_days: int = Field(default=90, description="Daily summary retention (days)")
    token_log_retention_days: int = Field(default=365, description="Monthly log retention (days)")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
