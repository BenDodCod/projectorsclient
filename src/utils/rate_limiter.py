"""
Rate limiting and account lockout implementation.

Provides thread-safe rate limiting for authentication attempts with
configurable lockout duration and attempt limits. Supports persistence
to survive application restarts.

Addresses threats from threat model:
- T-015: Brute force attacks on admin password

Author: Backend Infrastructure Developer
Version: 1.0.0
"""

import json
import logging
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from threading import Lock
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class LockoutConfig:
    """Configuration for account lockout behavior.

    Attributes:
        max_attempts: Maximum failed attempts before lockout.
        lockout_duration_minutes: Duration of lockout in minutes.
        sliding_window_minutes: Time window for counting attempts.
        persist_to_database: Whether to persist lockout state to database.
    """
    max_attempts: int = 5
    lockout_duration_minutes: int = 15
    sliding_window_minutes: int = 15
    persist_to_database: bool = True


@dataclass
class AttemptRecord:
    """Record of an authentication attempt.

    Attributes:
        timestamp: Unix timestamp of the attempt.
        success: Whether the attempt was successful.
        ip_address: Optional IP address (for network services).
    """
    timestamp: float
    success: bool
    ip_address: Optional[str] = None


@dataclass
class LockoutState:
    """Current lockout state for an identifier.

    Attributes:
        is_locked: Whether the identifier is currently locked out.
        remaining_seconds: Seconds remaining in lockout (0 if not locked).
        failed_attempts: Number of failed attempts in current window.
        last_attempt: Timestamp of last attempt.
    """
    is_locked: bool
    remaining_seconds: int
    failed_attempts: int
    last_attempt: Optional[float]


class AccountLockout:
    """Thread-safe account lockout implementation.

    Tracks authentication attempts and enforces lockout after exceeding
    the maximum allowed failed attempts within the sliding window.

    Addresses threat: T-015 (brute force attacks)

    Example:
        >>> lockout = AccountLockout(config=LockoutConfig(max_attempts=3))
        >>> lockout.record_attempt("admin", success=False)  # Attempt 1
        >>> lockout.record_attempt("admin", success=False)  # Attempt 2
        >>> lockout.record_attempt("admin", success=False)  # Attempt 3
        >>> state = lockout.get_state("admin")
        >>> assert state.is_locked  # Now locked out
    """

    def __init__(
        self,
        config: Optional[LockoutConfig] = None,
        db_path: Optional[str] = None
    ):
        """Initialize the account lockout manager.

        Args:
            config: Lockout configuration (uses defaults if not provided).
            db_path: Path to SQLite database for persistence (optional).
        """
        self._config = config or LockoutConfig()
        self._db_path = db_path
        self._attempts: Dict[str, List[AttemptRecord]] = {}
        self._lock = Lock()

        # Initialize database if persistence enabled
        if self._config.persist_to_database and self._db_path:
            self._init_database()
            self._load_from_database()

    def _init_database(self) -> None:
        """Initialize the lockout tracking table in database."""
        if not self._db_path:
            return

        try:
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS lockout_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    identifier TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    success INTEGER NOT NULL,
                    ip_address TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_lockout_identifier_timestamp
                ON lockout_attempts (identifier, timestamp)
            """)

            conn.commit()
            conn.close()

            logger.debug("Lockout database table initialized")

        except sqlite3.Error as e:
            logger.error("Failed to initialize lockout database: %s", e)

    def _load_from_database(self) -> None:
        """Load recent attempts from database."""
        if not self._db_path:
            return

        try:
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()

            # Load attempts within the sliding window
            cutoff = time.time() - (self._config.sliding_window_minutes * 60)

            cursor.execute("""
                SELECT identifier, timestamp, success, ip_address
                FROM lockout_attempts
                WHERE timestamp > ?
                ORDER BY timestamp
            """, (cutoff,))

            for row in cursor.fetchall():
                identifier, timestamp, success, ip_address = row
                record = AttemptRecord(
                    timestamp=timestamp,
                    success=bool(success),
                    ip_address=ip_address
                )

                if identifier not in self._attempts:
                    self._attempts[identifier] = []
                self._attempts[identifier].append(record)

            conn.close()

            logger.debug(
                "Loaded lockout state for %d identifiers",
                len(self._attempts)
            )

        except sqlite3.Error as e:
            logger.error("Failed to load lockout state: %s", e)

    def _persist_attempt(self, identifier: str, record: AttemptRecord) -> None:
        """Persist an attempt to database."""
        if not self._config.persist_to_database or not self._db_path:
            return

        try:
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO lockout_attempts (identifier, timestamp, success, ip_address)
                VALUES (?, ?, ?, ?)
            """, (identifier, record.timestamp, int(record.success), record.ip_address))

            conn.commit()
            conn.close()

        except sqlite3.Error as e:
            logger.error("Failed to persist lockout attempt: %s", e)

    def _cleanup_old_attempts(self, identifier: str) -> None:
        """Remove attempts outside the sliding window."""
        cutoff = time.time() - (self._config.sliding_window_minutes * 60)

        if identifier in self._attempts:
            self._attempts[identifier] = [
                a for a in self._attempts[identifier]
                if a.timestamp > cutoff
            ]

    def _cleanup_database(self) -> None:
        """Clean up old attempts from database."""
        if not self._config.persist_to_database or not self._db_path:
            return

        try:
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()

            # Keep attempts for 24 hours for audit purposes
            cutoff = time.time() - (24 * 60 * 60)

            cursor.execute("""
                DELETE FROM lockout_attempts WHERE timestamp < ?
            """, (cutoff,))

            deleted = cursor.rowcount
            conn.commit()
            conn.close()

            if deleted > 0:
                logger.debug("Cleaned up %d old lockout records", deleted)

        except sqlite3.Error as e:
            logger.error("Failed to cleanup lockout database: %s", e)

    def record_attempt(
        self,
        identifier: str,
        success: bool,
        ip_address: Optional[str] = None
    ) -> LockoutState:
        """Record an authentication attempt.

        Args:
            identifier: User identifier (username, IP, etc.).
            success: Whether the attempt was successful.
            ip_address: Optional IP address for logging.

        Returns:
            Current lockout state after recording the attempt.
        """
        with self._lock:
            now = time.time()

            # Clean up old attempts first
            self._cleanup_old_attempts(identifier)

            # Check if currently locked out
            state = self._get_state_unlocked(identifier)
            if state.is_locked:
                # Record the attempt anyway for audit
                record = AttemptRecord(
                    timestamp=now,
                    success=False,  # Can't succeed while locked
                    ip_address=ip_address
                )
                self._persist_attempt(identifier, record)

                logger.warning(
                    "Authentication attempt for locked account: %s",
                    identifier
                )
                return state

            # Initialize attempts list if needed
            if identifier not in self._attempts:
                self._attempts[identifier] = []

            # Record the attempt
            record = AttemptRecord(
                timestamp=now,
                success=success,
                ip_address=ip_address
            )
            self._attempts[identifier].append(record)
            self._persist_attempt(identifier, record)

            if success:
                # Clear failed attempts on success
                self._attempts[identifier] = [
                    a for a in self._attempts[identifier] if a.success
                ]
                logger.info(
                    "Successful authentication for: %s",
                    identifier
                )
            else:
                logger.warning(
                    "Failed authentication attempt for: %s (attempt %d/%d)",
                    identifier,
                    len([a for a in self._attempts[identifier] if not a.success]),
                    self._config.max_attempts
                )

            # Return updated state
            return self._get_state_unlocked(identifier)

    def _get_state_unlocked(self, identifier: str) -> LockoutState:
        """Get lockout state without acquiring lock.

        Must be called while holding self._lock.
        """
        now = time.time()
        self._cleanup_old_attempts(identifier)

        attempts = self._attempts.get(identifier, [])
        failed_attempts = [a for a in attempts if not a.success]
        failed_count = len(failed_attempts)

        last_attempt = attempts[-1].timestamp if attempts else None

        if failed_count >= self._config.max_attempts:
            # Calculate lockout expiry from first failure in window
            oldest_failure = min(a.timestamp for a in failed_attempts)
            lockout_end = oldest_failure + (self._config.lockout_duration_minutes * 60)
            remaining = int(lockout_end - now)

            if remaining > 0:
                return LockoutState(
                    is_locked=True,
                    remaining_seconds=remaining,
                    failed_attempts=failed_count,
                    last_attempt=last_attempt
                )

        return LockoutState(
            is_locked=False,
            remaining_seconds=0,
            failed_attempts=failed_count,
            last_attempt=last_attempt
        )

    def get_state(self, identifier: str) -> LockoutState:
        """Get current lockout state for an identifier.

        Args:
            identifier: User identifier to check.

        Returns:
            Current lockout state.
        """
        with self._lock:
            return self._get_state_unlocked(identifier)

    def is_locked_out(self, identifier: str) -> Tuple[bool, int]:
        """Check if an identifier is currently locked out.

        Args:
            identifier: User identifier to check.

        Returns:
            Tuple of (is_locked, remaining_seconds).
        """
        state = self.get_state(identifier)
        return (state.is_locked, state.remaining_seconds)

    def reset_attempts(self, identifier: str) -> None:
        """Reset failed attempts counter for an identifier.

        Use this for administrative password reset or recovery.

        Args:
            identifier: User identifier to reset.
        """
        with self._lock:
            if identifier in self._attempts:
                self._attempts[identifier] = []

            # Update database
            if self._config.persist_to_database and self._db_path:
                try:
                    conn = sqlite3.connect(self._db_path)
                    cursor = conn.cursor()
                    cursor.execute("""
                        DELETE FROM lockout_attempts WHERE identifier = ?
                    """, (identifier,))
                    conn.commit()
                    conn.close()
                except sqlite3.Error as e:
                    logger.error("Failed to reset lockout in database: %s", e)

            logger.info("Reset lockout attempts for: %s", identifier)

    def get_lockout_message(self, identifier: str) -> str:
        """Get a user-friendly lockout message.

        Args:
            identifier: User identifier to check.

        Returns:
            Human-readable message about lockout status.
        """
        state = self.get_state(identifier)

        if state.is_locked:
            minutes = state.remaining_seconds // 60
            seconds = state.remaining_seconds % 60

            if minutes > 0:
                return (
                    f"Account is locked due to too many failed attempts. "
                    f"Please try again in {minutes} minute(s) and {seconds} second(s)."
                )
            else:
                return (
                    f"Account is locked. Please try again in {seconds} second(s)."
                )

        elif state.failed_attempts > 0:
            remaining = self._config.max_attempts - state.failed_attempts
            return (
                f"Warning: {remaining} attempt(s) remaining before lockout."
            )

        return ""

    def get_audit_log(
        self,
        identifier: Optional[str] = None,
        since_hours: int = 24
    ) -> List[dict]:
        """Get audit log of authentication attempts.

        Args:
            identifier: Optional filter by identifier.
            since_hours: Hours of history to return.

        Returns:
            List of attempt records as dictionaries.
        """
        if not self._config.persist_to_database or not self._db_path:
            # Return from memory
            with self._lock:
                result = []
                for ident, attempts in self._attempts.items():
                    if identifier and ident != identifier:
                        continue
                    for attempt in attempts:
                        result.append({
                            'identifier': ident,
                            'timestamp': datetime.fromtimestamp(attempt.timestamp).isoformat(),
                            'success': attempt.success,
                            'ip_address': attempt.ip_address
                        })
                return result

        try:
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()

            cutoff = time.time() - (since_hours * 60 * 60)

            if identifier:
                cursor.execute("""
                    SELECT identifier, timestamp, success, ip_address
                    FROM lockout_attempts
                    WHERE identifier = ? AND timestamp > ?
                    ORDER BY timestamp DESC
                """, (identifier, cutoff))
            else:
                cursor.execute("""
                    SELECT identifier, timestamp, success, ip_address
                    FROM lockout_attempts
                    WHERE timestamp > ?
                    ORDER BY timestamp DESC
                """, (cutoff,))

            result = []
            for row in cursor.fetchall():
                result.append({
                    'identifier': row[0],
                    'timestamp': datetime.fromtimestamp(row[1]).isoformat(),
                    'success': bool(row[2]),
                    'ip_address': row[3]
                })

            conn.close()
            return result

        except sqlite3.Error as e:
            logger.error("Failed to get audit log: %s", e)
            return []


class IPRateLimiter:
    """Rate limiter for IP-based requests.

    Provides simple rate limiting for network operations like
    PJLink connections or diagnostic requests.
    """

    def __init__(
        self,
        max_requests: int = 10,
        window_seconds: int = 60
    ):
        """Initialize the IP rate limiter.

        Args:
            max_requests: Maximum requests per window.
            window_seconds: Time window in seconds.
        """
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._requests: Dict[str, List[float]] = {}
        self._lock = Lock()

    def is_allowed(self, ip_address: str) -> Tuple[bool, int]:
        """Check if a request from an IP is allowed.

        Args:
            ip_address: IP address making the request.

        Returns:
            Tuple of (allowed, retry_after_seconds).
        """
        with self._lock:
            now = time.time()
            cutoff = now - self._window_seconds

            # Clean up old requests
            if ip_address in self._requests:
                self._requests[ip_address] = [
                    t for t in self._requests[ip_address]
                    if t > cutoff
                ]
            else:
                self._requests[ip_address] = []

            current_count = len(self._requests[ip_address])

            if current_count >= self._max_requests:
                # Calculate when the oldest request will expire
                oldest = min(self._requests[ip_address])
                retry_after = int((oldest + self._window_seconds) - now)
                return (False, max(1, retry_after))

            # Record this request
            self._requests[ip_address].append(now)
            return (True, 0)

    def reset(self, ip_address: str) -> None:
        """Reset rate limit for an IP address."""
        with self._lock:
            if ip_address in self._requests:
                del self._requests[ip_address]


# Default singleton instance
_default_lockout: Optional[AccountLockout] = None


def get_account_lockout(
    config: Optional[LockoutConfig] = None,
    db_path: Optional[str] = None
) -> AccountLockout:
    """Get or create the default account lockout manager.

    Args:
        config: Lockout configuration (only used on first call).
        db_path: Database path for persistence (only used on first call).

    Returns:
        Singleton AccountLockout instance.
    """
    global _default_lockout

    if _default_lockout is None:
        _default_lockout = AccountLockout(config=config, db_path=db_path)

    return _default_lockout


def _reset_singleton() -> None:
    """Reset singleton instance. For testing only."""
    global _default_lockout
    _default_lockout = None
