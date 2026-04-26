"""
Exceptions for Agent Platform SDK
"""


class PlatformException(Exception):
    """Base exception for platform errors"""
    pass


class AgentNotFoundException(PlatformException):
    """Agent not found"""
    pass


class TaskNotFoundException(PlatformException):
    """Task not found"""
    pass


class RateLimitException(PlatformException):
    """Rate limit exceeded"""
    pass


class AuthenticationException(PlatformException):
    """Authentication failed"""
    pass


class ValidationException(PlatformException):
    """Validation error"""
    pass


class ServiceUnavailableException(PlatformException):
    """Service unavailable"""
    pass
