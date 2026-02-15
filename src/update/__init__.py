"""
Auto-update system for Projector Control application.

This module provides automatic update checking, downloading, and installation
for the Projector Control application using GitHub Releases.

Key Components:
- UpdateChecker: Core update logic and version comparison
- UpdateDownloader: Download manager with SHA-256 verification
- UpdateCheckWorker/UpdateDownloadWorker: QThread workers for non-blocking operations
- RolloutManager: Staged rollout decision engine
- Version: Semantic version comparison
- GitHubClient: GitHub Releases API integration

Example Usage:
    from src.update import UpdateChecker, UpdateCheckWorker

    checker = UpdateChecker(settings, "BenDodCod/projectorsclient")
    worker = UpdateCheckWorker(checker)
    worker.check_complete.connect(on_update_available)
    worker.start()
"""

from .update_checker import UpdateChecker, UpdateCheckResult
from .update_downloader import UpdateDownloader
from .update_worker import UpdateCheckWorker, UpdateDownloadWorker
from .rollout_manager import RolloutManager
from .version_utils import Version, is_newer_version
from .github_client import GitHubClient

__all__ = [
    'UpdateChecker',
    'UpdateCheckResult',
    'UpdateDownloader',
    'UpdateCheckWorker',
    'UpdateDownloadWorker',
    'RolloutManager',
    'Version',
    'is_newer_version',
    'GitHubClient',
]

__version__ = '1.0.0'
