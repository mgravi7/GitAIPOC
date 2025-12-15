# -*- coding: utf-8 -*-
"""
Custom exceptions for the Code Review Agent
"""


class TokenBudgetExceeded(Exception):
    """Raised when daily token budget is exhausted"""
    pass


class ReviewError(Exception):
    """Base exception for review-related errors"""
    pass
