"""
Core business logic module.

Contains the core application logic, constants, and business rules.

Exports:
    Controller Factory:
        - ControllerFactory: Factory for creating projector controllers
        - ProjectorControllerProtocol: Protocol interface for controllers

    Projector Controller:
        - ProjectorController: PJLink projector controller implementation
"""

from src.core.controller_factory import ControllerFactory, ProjectorControllerProtocol

__all__ = [
    "ControllerFactory",
    "ProjectorControllerProtocol",
]
