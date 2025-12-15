# -*- coding: utf-8 -*-
"""
Token usage tracking and budget enforcement
Excel-friendly CSV logging with monthly rotation
"""
import csv
import json
import asyncio
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass
import logging

from src.config import settings

logger = logging.getLogger(__name__)


@dataclass
class TokenUsage:
    """Token usage for a single successful review request"""
    project_id: int
    project_name: str
    mr_iid: int
    username: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    model: str
    duration_ms: int


class TokenTracker:
    """
    Track and enforce daily token budgets with Excel-friendly logging
    
    Features:
    - Fast daily budget checks (<10ms)
    - Excel-friendly monthly CSV logs
    - Hard limit enforcement
    - Automatic cleanup of old files
    - Only logs successful Claude API responses
    """
    
    def __init__(self):
        # Directory structure
        self.data_dir = Path(settings.token_data_dir)
        self.daily_summaries_dir = self.data_dir / "daily-summaries"
        self.token_logs_dir = self.data_dir / "token-logs"
        
        # Create directories
        self.daily_summaries_dir.mkdir(parents=True, exist_ok=True)
        self.token_logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Budget settings
        self.daily_limit = settings.token_daily_limit
        self.warning_threshold = settings.token_warning_threshold
        self.summary_retention_days = settings.token_summary_retention_days
        self.log_retention_days = settings.token_log_retention_days
        
        # In-memory cache for fast budget checks
        self._today_total = None
        self._last_check = None
        self._cache_ttl_seconds = 60  # Cache for 1 minute
        self._lock = asyncio.Lock()
        
        logger.info(f"TokenTracker initialized: limit={self.daily_limit:,} tokens/day")
    
    async def check_budget(self) -> tuple[bool, int, str]:
        """
        Check if we're within daily budget (FAST - cached)
        
        Returns:
            (allowed, tokens_used_today, message)
        """
        if not settings.token_budget_enabled:
            return (True, 0, "Budget tracking disabled")
        
        tokens_used = await self._get_today_total()
        remaining = self.daily_limit - tokens_used
        
        # Hard limit - reject if exhausted
        if tokens_used >= self.daily_limit:
            return (
                False, 
                tokens_used,
                f"❌ Daily token budget exhausted ({tokens_used:,}/{self.daily_limit:,} tokens used). "
                f"AI code reviews will resume tomorrow."
            )
        
        # Warning threshold
        if tokens_used >= self.warning_threshold:
            pct_used = (tokens_used / self.daily_limit) * 100
            return (
                True,
                tokens_used,
                f"⚠️ Warning: {pct_used:.1f}% of daily budget used "
                f"({tokens_used:,}/{self.daily_limit:,} tokens). "
                f"{remaining:,} tokens remaining."
            )
        
        return (True, tokens_used, f"✅ Budget OK ({remaining:,} tokens remaining)")
    
    async def record_usage(self, usage: TokenUsage) -> None:
        """
        Record token usage from a SUCCESSFUL Claude API response
        
        This is called AFTER successful review completion, not for errors.
        
        Args:
            usage: Token usage details from Claude API response
        """
        if not settings.token_budget_enabled:
            return
        
        async with self._lock:
            try:
                # Get current timestamp
                now = datetime.utcnow()
                
                # 1. Append to monthly CSV log
                await self._append_to_monthly_csv(usage, now)
                
                # 2. Update daily summary JSON
                await self._update_daily_summary(usage, now)
                
                # 3. Invalidate cache
                self._today_total = None
                
                logger.info(
                    f"Recorded token usage: MR {usage.mr_iid} in project {usage.project_id} "
                    f"({usage.total_tokens:,} tokens)"
                )
                
            except Exception as e:
                logger.error(f"Failed to record token usage: {e}", exc_info=True)
                # Don't fail the review if logging fails
    
    async def _get_today_total(self) -> int:
        """
        Get today's token total with 1-minute caching
        
        Returns:
            Total tokens used today
        """
        now = datetime.utcnow()
        
        # Cache hit (within 1 minute)
        if self._today_total is not None and self._last_check is not None:
            if (now - self._last_check).total_seconds() < self._cache_ttl_seconds:
                return self._today_total
        
        # Cache miss - read from file
        async with self._lock:
            summary = await self._read_daily_summary()
            self._today_total = summary.get("total_tokens", 0)
            self._last_check = now
            return self._today_total
    
    async def _append_to_monthly_csv(self, usage: TokenUsage, timestamp: datetime) -> None:
        """
        Append usage to monthly CSV log (Excel-friendly format)
        
        File format: token-logs/YYYY-MM.csv
        Columns: year,month,day,time,project_id,project_name,mr_iid,username,
                 input_tokens,output_tokens,total_tokens,model,duration_ms
        """
        csv_path = self._get_monthly_csv_path(timestamp)
        
        # Create with headers if doesn't exist
        if not csv_path.exists():
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'year', 'month', 'day', 'time',
                    'project_id', 'project_name', 'mr_iid', 'username',
                    'input_tokens', 'output_tokens', 'total_tokens',
                    'model', 'duration_ms'
                ])
            logger.info(f"Created new monthly log: {csv_path.name}")
        
        # Append usage (Excel-friendly format)
        with open(csv_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp.year,
                timestamp.month,
                timestamp.day,
                timestamp.strftime('%H:%M:%S'),  # Time only (HH:MM:SS)
                usage.project_id,
                usage.project_name,
                usage.mr_iid,
                usage.username,
                usage.input_tokens,
                usage.output_tokens,
                usage.total_tokens,
                usage.model,
                usage.duration_ms
            ])
    
    async def _update_daily_summary(self, usage: TokenUsage, timestamp: datetime) -> None:
        """
        Update daily summary JSON (atomic write)
        
        File format: daily-summaries/YYYY-MM-DD.json
        """
        summary_path = self._get_daily_summary_path(timestamp)
        
        # Read current summary
        summary = await self._read_daily_summary(timestamp)
        
        # Update totals
        summary["total_tokens"] += usage.total_tokens
        summary["input_tokens"] += usage.input_tokens
        summary["output_tokens"] += usage.output_tokens
        summary["request_count"] += 1
        summary["last_updated"] = timestamp.isoformat() + "Z"
        summary["budget_remaining"] = self.daily_limit - summary["total_tokens"]
        summary["budget_exhausted"] = summary["total_tokens"] >= self.daily_limit
        
        # Atomic write (temp file + rename)
        temp_path = summary_path.with_suffix('.tmp')
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        try:
            temp_path.replace(summary_path)
        except Exception as e:
            logger.error(f"Failed to atomically replace {summary_path} with {temp_path}: {e}", exc_info=True)
            # Optionally, try to clean up the temp file
            try:
                if temp_path.exists():
                    temp_path.unlink()
            except Exception as cleanup_exc:
                logger.error(f"Failed to clean up temp file {temp_path}: {cleanup_exc}", exc_info=True)
    async def _read_daily_summary(self, timestamp: Optional[datetime] = None) -> Dict:
        """
        Read daily summary JSON
        
        Args:
            timestamp: Date to read (defaults to today)
            
        Returns:
            Daily summary dict
        """
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        summary_path = self._get_daily_summary_path(timestamp)
        
        if not summary_path.exists():
            return {
                "date": timestamp.date().isoformat(),
                "total_tokens": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "request_count": 0,
                "last_updated": timestamp.isoformat() + "Z",
                "budget_limit": self.daily_limit,
                "budget_remaining": self.daily_limit,
                "budget_exhausted": False
            }
        
        with open(summary_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _get_monthly_csv_path(self, timestamp: datetime) -> Path:
        """Get path to monthly CSV file (YYYY-MM.csv)"""
        month_str = timestamp.strftime('%Y-%m')
        return self.token_logs_dir / f"{month_str}.csv"
    
    def _get_daily_summary_path(self, timestamp: datetime) -> Path:
        """Get path to daily summary JSON (YYYY-MM-DD.json)"""
        date_str = timestamp.date().isoformat()
        return self.daily_summaries_dir / f"{date_str}.json"
    
    async def get_daily_stats(self, target_date: Optional[date] = None) -> Dict:
        """
        Get statistics for a specific day
        
        Args:
            target_date: Date to query (defaults to today)
            
        Returns:
            Daily statistics dict
        """
        if target_date is None:
            target_date = date.today()
        
        timestamp = datetime.combine(target_date, datetime.min.time())
        summary = await self._read_daily_summary(timestamp)
        
        return {
            "date": summary["date"],
            "total_tokens": summary["total_tokens"],
            "input_tokens": summary["input_tokens"],
            "output_tokens": summary["output_tokens"],
            "request_count": summary["request_count"],
            "budget_limit": self.daily_limit,
            "budget_used_percent": (
                (summary["total_tokens"] / self.daily_limit) * 100
                if self.daily_limit > 0 else 0
            ),
            "budget_remaining": summary["budget_remaining"],
            "budget_exhausted": summary["budget_exhausted"],
            "avg_tokens_per_review": (
                summary["total_tokens"] / summary["request_count"] 
                if summary["request_count"] > 0 else 0
            ),
            "last_updated": summary["last_updated"]
        }
    
    async def cleanup_old_files(self) -> Dict[str, int]:
        """
        Delete files older than retention period
        
        Returns:
            {'summaries_deleted': N, 'logs_deleted': M}
        """
        summaries_deleted = 0
        logs_deleted = 0
        
        try:
            # Cleanup daily summaries (90 days default)
            summary_cutoff = date.today() - timedelta(days=self.summary_retention_days)
            for file in self.daily_summaries_dir.glob("*.json"):
                try:
                    # Extract date from filename (YYYY-MM-DD.json)
                    file_date_str = file.stem
                    file_date = date.fromisoformat(file_date_str)
                    
                    if file_date < summary_cutoff:
                        file.unlink()
                        summaries_deleted += 1
                        logger.debug(f"Deleted old summary: {file.name}")
                except (ValueError, OSError) as e:
                    logger.warning(f"Failed to process summary file {file.name}: {e}")
            
            # Cleanup monthly logs (90 days or 1 year default)
            log_cutoff = date.today() - timedelta(days=self.log_retention_days)
            for file in self.token_logs_dir.glob("*.csv"):
                try:
                    # Extract date from filename (YYYY-MM.csv)
                    # Use last day of that month for comparison
                    year_month_str = file.stem
                    year, month = map(int, year_month_str.split('-'))
                    
                    # Last day of the month
                    if month == 12:
                        file_date = date(year, month, 31)
                    else:
                        file_date = date(year, month + 1, 1) - timedelta(days=1)
                    
                    if file_date < log_cutoff:
                        file.unlink()
                        logs_deleted += 1
                        logger.debug(f"Deleted old log: {file.name}")
                except (ValueError, OSError) as e:
                    logger.warning(f"Failed to process log file {file.name}: {e}")
            
            if summaries_deleted > 0 or logs_deleted > 0:
                logger.info(
                    f"Cleanup completed: {summaries_deleted} summaries, "
                    f"{logs_deleted} logs deleted"
                )
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}", exc_info=True)
        
        return {
            "summaries_deleted": summaries_deleted,
            "logs_deleted": logs_deleted
        }


# Global tracker instance
tracker = TokenTracker()
