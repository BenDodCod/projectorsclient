"""
Configuration management.

Handles application settings, persistence, and configuration validation.

Modules:
    validators: Input validation framework for security
"""

__all__ = [
    "validate_ip_address",
    "validate_port",
    "validate_password",
    "validate_admin_password",
    "validate_projector_name",
    "validate_file_path",
    "validate_import_file",
    "sanitize_sql_identifier",
    "safe_path",
]


def __getattr__(name):
    """Lazy import of submodules."""
    if name in __all__:
        from . import validators
        return getattr(validators, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
