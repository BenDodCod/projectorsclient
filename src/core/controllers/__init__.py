"""
Controller implementations package.

This package contains protocol-specific controller implementations.
Each controller handles the high-level operations for a specific
projector brand/protocol.

Implemented Controllers:
    - HitachiController: Hitachi native binary protocol controller

Author: Backend Infrastructure Developer
Version: 1.0.0
"""

from src.core.controllers.hitachi_controller import HitachiController

__all__ = ["HitachiController"]
