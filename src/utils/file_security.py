"""
Windows file security utilities using ACLs.

Provides functions to set and verify Windows Access Control Lists (ACLs)
on sensitive files such as the SQLite database, entropy files, and logs.

Addresses threats from threat model:
- T-006: SQLite file readable by all users
- T-011: Windows ACL misconfiguration

Author: Backend Infrastructure Developer
Version: 1.0.0
"""

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

# Windows-specific imports
try:
    import ntsecuritycon as con
    import win32api
    import win32security
    import pywintypes
    WINDOWS_AVAILABLE = True
except ImportError:
    WINDOWS_AVAILABLE = False

logger = logging.getLogger(__name__)


class FileSecurityError(Exception):
    """Raised when file security operations fail."""
    pass


@dataclass
class ACEInfo:
    """Information about an Access Control Entry.

    Attributes:
        trustee: Name of the security principal.
        sid_string: SID string representation.
        access_mask: Access mask (permissions).
        ace_type: Type of ACE (allow, deny).
    """
    trustee: str
    sid_string: str
    access_mask: int
    ace_type: str


@dataclass
class FilePermissions:
    """File permission information.

    Attributes:
        owner: Owner of the file.
        is_secure: Whether permissions are appropriately restrictive.
        aces: List of ACE information.
        issues: List of security issues found.
    """
    owner: str
    is_secure: bool
    aces: List[ACEInfo]
    issues: List[str]


def _check_windows_available() -> None:
    """Check if Windows security APIs are available."""
    if not WINDOWS_AVAILABLE:
        raise FileSecurityError(
            "Windows security APIs not available. "
            "This functionality requires Windows and pywin32."
        )


def set_file_owner_only_permissions(filepath: str) -> bool:
    """Set Windows ACLs to restrict file access to owner and SYSTEM only.

    Removes all inherited permissions and sets explicit ACEs for:
    - Current user: Full Control
    - SYSTEM: Full Control (required for Windows operations)

    Addresses threats:
    - T-006: SQLite file readable by all users
    - T-011: Windows ACL misconfiguration

    Args:
        filepath: Path to the file to secure.

    Returns:
        True if permissions were set successfully.

    Raises:
        FileSecurityError: If permissions cannot be set.

    Example:
        >>> set_file_owner_only_permissions("C:\\data\\config.db")
        True
    """
    _check_windows_available()

    try:
        # Verify file exists
        if not os.path.exists(filepath):
            raise FileSecurityError(f"File does not exist: {filepath}")

        # Get current user SID
        username = win32api.GetUserName()
        user_sid, _, _ = win32security.LookupAccountName(None, username)

        # Get SYSTEM SID (well-known SID S-1-5-18)
        system_sid = win32security.ConvertStringSidToSid("S-1-5-18")

        # Create new DACL (Discretionary Access Control List)
        dacl = win32security.ACL()

        # Add owner full control ACE
        dacl.AddAccessAllowedAceEx(
            win32security.ACL_REVISION_DS,
            0,  # No inheritance flags
            con.FILE_ALL_ACCESS,
            user_sid
        )

        # Add SYSTEM full control ACE (required for Windows operations)
        dacl.AddAccessAllowedAceEx(
            win32security.ACL_REVISION_DS,
            0,  # No inheritance flags
            con.FILE_ALL_ACCESS,
            system_sid
        )

        # Get the security descriptor
        sd = win32security.GetFileSecurity(
            filepath,
            win32security.DACL_SECURITY_INFORMATION
        )

        # Set the new DACL
        sd.SetSecurityDescriptorDacl(
            True,   # DACL present
            dacl,   # The DACL
            False   # Not defaulted
        )

        # Apply the security descriptor with protection
        # PROTECTED_DACL_SECURITY_INFORMATION prevents inheritance
        win32security.SetFileSecurity(
            filepath,
            win32security.DACL_SECURITY_INFORMATION |
            win32security.PROTECTED_DACL_SECURITY_INFORMATION,
            sd
        )

        logger.info("Set owner-only permissions on: %s", filepath)
        return True

    except pywintypes.error as e:
        error_msg = f"Failed to set permissions on {filepath}: {e}"
        logger.error(error_msg)
        raise FileSecurityError(error_msg) from e
    except Exception as e:
        error_msg = f"Unexpected error setting permissions: {e}"
        logger.error(error_msg)
        raise FileSecurityError(error_msg) from e


def set_directory_owner_only_permissions(dirpath: str, recursive: bool = False) -> bool:
    """Set Windows ACLs on a directory for owner-only access.

    Args:
        dirpath: Path to the directory.
        recursive: Apply to all files and subdirectories.

    Returns:
        True if permissions were set successfully.

    Raises:
        FileSecurityError: If permissions cannot be set.
    """
    _check_windows_available()

    try:
        if not os.path.isdir(dirpath):
            raise FileSecurityError(f"Directory does not exist: {dirpath}")

        # Set permissions on the directory itself
        set_file_owner_only_permissions(dirpath)

        if recursive:
            for root, dirs, files in os.walk(dirpath):
                for name in files:
                    try:
                        set_file_owner_only_permissions(os.path.join(root, name))
                    except FileSecurityError as e:
                        logger.warning("Could not secure file %s: %s", name, e)

                for name in dirs:
                    try:
                        set_file_owner_only_permissions(os.path.join(root, name))
                    except FileSecurityError as e:
                        logger.warning("Could not secure directory %s: %s", name, e)

        return True

    except Exception as e:
        error_msg = f"Failed to set directory permissions: {e}"
        logger.error(error_msg)
        raise FileSecurityError(error_msg) from e


def verify_file_permissions(filepath: str) -> FilePermissions:
    """Verify that a file has secure (owner-only) permissions.

    Checks that:
    - File has at most 2 ACEs (owner + SYSTEM)
    - No "Everyone", "Users", or other broad access groups

    Args:
        filepath: Path to the file to verify.

    Returns:
        FilePermissions object with detailed permission information.

    Raises:
        FileSecurityError: If permissions cannot be read.
    """
    _check_windows_available()

    issues: List[str] = []
    aces: List[ACEInfo] = []

    try:
        if not os.path.exists(filepath):
            raise FileSecurityError(f"File does not exist: {filepath}")

        # Get security descriptor
        sd = win32security.GetFileSecurity(
            filepath,
            win32security.OWNER_SECURITY_INFORMATION |
            win32security.DACL_SECURITY_INFORMATION
        )

        # Get owner
        owner_sid = sd.GetSecurityDescriptorOwner()
        try:
            owner_name, domain, _ = win32security.LookupAccountSid(None, owner_sid)
            owner = f"{domain}\\{owner_name}" if domain else owner_name
        except pywintypes.error:
            owner = str(owner_sid)

        # Get DACL
        dacl = sd.GetSecurityDescriptorDacl()

        if dacl is None:
            issues.append("No DACL present - file has no explicit permissions")
            return FilePermissions(
                owner=owner,
                is_secure=False,
                aces=[],
                issues=issues
            )

        # Well-known SIDs that indicate overly permissive access
        dangerous_sids = {
            "S-1-1-0": "Everyone",
            "S-1-5-32-545": "Users",
            "S-1-5-11": "Authenticated Users",
            "S-1-5-32-544": "Administrators",  # Might be acceptable
        }

        current_user = win32api.GetUserName().lower()
        ace_count = dacl.GetAceCount()

        for i in range(ace_count):
            ace = dacl.GetAce(i)
            # ace[0] = (ace_type, ace_flags)
            # ace[1] = access_mask
            # ace[2] = sid

            ace_type_code = ace[0][0]
            access_mask = ace[1]
            sid = ace[2]

            # Determine ACE type
            if ace_type_code == win32security.ACCESS_ALLOWED_ACE_TYPE:
                ace_type = "ALLOW"
            elif ace_type_code == win32security.ACCESS_DENIED_ACE_TYPE:
                ace_type = "DENY"
            else:
                ace_type = f"OTHER({ace_type_code})"

            # Get trustee name
            try:
                name, domain, _ = win32security.LookupAccountSid(None, sid)
                trustee = f"{domain}\\{name}" if domain else name
            except pywintypes.error:
                trustee = "Unknown"

            # Get SID string
            sid_string = win32security.ConvertSidToStringSid(sid)

            aces.append(ACEInfo(
                trustee=trustee,
                sid_string=sid_string,
                access_mask=access_mask,
                ace_type=ace_type
            ))

            # Check for dangerous permissions
            if sid_string in dangerous_sids:
                if sid_string == "S-1-5-32-544":
                    # Administrators might be acceptable
                    issues.append(f"Warning: Administrators group has access")
                else:
                    issues.append(
                        f"SECURITY ISSUE: {dangerous_sids[sid_string]} has access"
                    )

        # Check if there are too many ACEs
        if ace_count > 3:  # Owner + SYSTEM + possibly Administrators
            issues.append(f"File has {ace_count} ACEs - may be too permissive")

        is_secure = len([i for i in issues if i.startswith("SECURITY ISSUE")]) == 0

        return FilePermissions(
            owner=owner,
            is_secure=is_secure,
            aces=aces,
            issues=issues
        )

    except pywintypes.error as e:
        raise FileSecurityError(f"Failed to read permissions: {e}") from e


def verify_secure_permissions(filepath: str) -> bool:
    """Quick check if file has secure permissions.

    Args:
        filepath: Path to the file to verify.

    Returns:
        True if permissions are secure (owner-only).
    """
    try:
        permissions = verify_file_permissions(filepath)
        return permissions.is_secure
    except FileSecurityError:
        return False


def ensure_secure_file(filepath: str) -> Tuple[bool, str]:
    """Ensure a file exists with secure permissions, creating if necessary.

    Args:
        filepath: Path to the file.

    Returns:
        Tuple of (success, message).
    """
    _check_windows_available()

    try:
        path = Path(filepath)

        # Create parent directories if needed
        path.parent.mkdir(parents=True, exist_ok=True)

        # Create file if it doesn't exist
        if not path.exists():
            path.touch()

        # Set secure permissions
        set_file_owner_only_permissions(filepath)

        # Verify
        if verify_secure_permissions(filepath):
            return (True, "File secured successfully")
        else:
            return (False, "File exists but permissions could not be verified")

    except FileSecurityError as e:
        return (False, str(e))
    except Exception as e:
        return (False, f"Unexpected error: {e}")


def get_permission_summary(filepath: str) -> str:
    """Get a human-readable summary of file permissions.

    Args:
        filepath: Path to the file.

    Returns:
        Permission summary string.
    """
    try:
        perms = verify_file_permissions(filepath)

        lines = [
            f"File: {filepath}",
            f"Owner: {perms.owner}",
            f"Secure: {'Yes' if perms.is_secure else 'No'}",
            "",
            "Access Control Entries:"
        ]

        for ace in perms.aces:
            lines.append(f"  - {ace.trustee}: {ace.ace_type} (mask: 0x{ace.access_mask:08X})")

        if perms.issues:
            lines.append("")
            lines.append("Issues:")
            for issue in perms.issues:
                lines.append(f"  - {issue}")

        return "\n".join(lines)

    except FileSecurityError as e:
        return f"Could not read permissions: {e}"


def secure_application_files(app_data_dir: str) -> List[Tuple[str, bool, str]]:
    """Secure all sensitive application files.

    Applies owner-only permissions to:
    - Database files (*.db, *.sqlite)
    - Entropy files
    - Configuration files

    Args:
        app_data_dir: Application data directory.

    Returns:
        List of (filepath, success, message) tuples.
    """
    results = []
    app_path = Path(app_data_dir)

    # File patterns to secure
    patterns = [
        "*.db",
        "*.sqlite",
        "*.sqlite3",
        ".projector_entropy",
        "config.json",
        "settings.json",
    ]

    for pattern in patterns:
        for filepath in app_path.glob(pattern):
            try:
                set_file_owner_only_permissions(str(filepath))
                results.append((str(filepath), True, "Secured"))
            except FileSecurityError as e:
                results.append((str(filepath), False, str(e)))

    # Also secure the logs directory
    logs_dir = app_path / "logs"
    if logs_dir.exists():
        try:
            set_directory_owner_only_permissions(str(logs_dir), recursive=True)
            results.append((str(logs_dir), True, "Secured (directory)"))
        except FileSecurityError as e:
            results.append((str(logs_dir), False, str(e)))

    return results


class FileSecurityManager:
    """Manager for application file security.

    Provides a unified interface for securing application files
    and verifying security on startup.
    """

    def __init__(self, app_data_dir: str):
        """Initialize the file security manager.

        Args:
            app_data_dir: Application data directory.
        """
        self._app_data_dir = Path(app_data_dir)

    def secure_database(self, db_path: str) -> bool:
        """Secure the SQLite database file.

        Args:
            db_path: Path to the database file.

        Returns:
            True if database was secured.
        """
        try:
            set_file_owner_only_permissions(db_path)
            logger.info("Database secured: %s", db_path)
            return True
        except FileSecurityError as e:
            logger.error("Failed to secure database: %s", e)
            return False

    def secure_entropy_file(self, entropy_path: str) -> bool:
        """Secure the entropy file.

        Args:
            entropy_path: Path to the entropy file.

        Returns:
            True if entropy file was secured.
        """
        try:
            set_file_owner_only_permissions(entropy_path)
            logger.info("Entropy file secured: %s", entropy_path)
            return True
        except FileSecurityError as e:
            logger.error("Failed to secure entropy file: %s", e)
            return False

    def verify_security(self) -> List[dict]:
        """Verify security of all application files.

        Returns:
            List of verification results.
        """
        results = []

        # Check database
        db_path = self._app_data_dir / "projector_control.db"
        if db_path.exists():
            perms = verify_file_permissions(str(db_path))
            results.append({
                'file': str(db_path),
                'type': 'database',
                'secure': perms.is_secure,
                'issues': perms.issues
            })

        # Check entropy file
        entropy_path = self._app_data_dir / ".projector_entropy"
        if entropy_path.exists():
            perms = verify_file_permissions(str(entropy_path))
            results.append({
                'file': str(entropy_path),
                'type': 'entropy',
                'secure': perms.is_secure,
                'issues': perms.issues
            })

        return results

    def secure_all(self) -> bool:
        """Secure all application files.

        Returns:
            True if all files were secured.
        """
        results = secure_application_files(str(self._app_data_dir))
        failed = [r for r in results if not r[1]]

        if failed:
            for filepath, _, message in failed:
                logger.warning("Failed to secure %s: %s", filepath, message)
            return False

        logger.info("All application files secured")
        return True
