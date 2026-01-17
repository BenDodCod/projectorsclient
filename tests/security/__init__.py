"""
Security test suite for Projector Control Application.

This module provides comprehensive security testing covering:
- Authentication mechanisms (bcrypt, lockout, rate limiting)
- Data protection (DPAPI encryption, file permissions)
- Input validation (IP, port, SQL injection, path traversal)
- Network protocol security (PJLink)

Addresses SEC-05: External penetration test completed with 0 critical/high issues.

Author: Security Test Engineer
Version: 1.0.0
"""

# Test parameters
BCRYPT_MIN_COST = 12
BCRYPT_DEFAULT_COST = 14
BCRYPT_MAX_COST = 16

# Timing test thresholds
HASH_TIME_MIN_MS = 50  # bcrypt with cost 12+ should take at least 50ms
TIMING_VARIANCE_MAX_MS = 10  # Timing-safe comparison variance threshold

# Lockout configuration defaults
DEFAULT_MAX_ATTEMPTS = 5
DEFAULT_LOCKOUT_DURATION_MINUTES = 15

# Rate limiting defaults
DEFAULT_RATE_LIMIT_REQUESTS = 10
DEFAULT_RATE_LIMIT_WINDOW_SECONDS = 60
