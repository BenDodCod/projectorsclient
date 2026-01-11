"""
Utility modules.

Security utilities, logging configuration, singleton enforcement,
diagnostics, and other helper functions.

Modules:
    security: DPAPI credential encryption and bcrypt password hashing
    rate_limiter: Account lockout and rate limiting
    logging_config: Secure logging with credential redaction
    file_security: Windows ACL file security
"""

# Lazy imports to avoid circular dependencies and allow individual module imports
# These are available when importing from the package
__all__ = [
    # Security
    "CredentialManager",
    "DatabaseIntegrityManager",
    "PasswordHasher",
    "decrypt_credential",
    "encrypt_credential",
    "hash_password",
    "verify_password",
    # Rate limiting
    "AccountLockout",
    "LockoutConfig",
    "get_account_lockout",
    # Logging
    "SecureFormatter",
    "AuditLogger",
    "setup_secure_logging",
    "get_audit_logger",
    # File security
    "FileSecurityManager",
    "set_file_owner_only_permissions",
    "verify_file_permissions",
    "verify_secure_permissions",
]


def __getattr__(name):
    """Lazy import of submodules."""
    if name in ("CredentialManager", "DatabaseIntegrityManager", "PasswordHasher",
                "decrypt_credential", "encrypt_credential", "hash_password", "verify_password"):
        from . import security
        return getattr(security, name)
    elif name in ("AccountLockout", "LockoutConfig", "get_account_lockout"):
        from . import rate_limiter
        return getattr(rate_limiter, name)
    elif name in ("SecureFormatter", "AuditLogger", "setup_secure_logging", "get_audit_logger"):
        from . import logging_config
        return getattr(logging_config, name)
    elif name in ("FileSecurityManager", "set_file_owner_only_permissions",
                  "verify_file_permissions", "verify_secure_permissions"):
        from . import file_security
        return getattr(file_security, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
