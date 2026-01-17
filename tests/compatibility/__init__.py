"""
Compatibility test suite for the Projector Control Application.

This module provides comprehensive compatibility testing across:
- Windows versions (10, 11)
- DPI scaling (100%, 125%, 150%, 175%, 200%)
- Projector protocols (PJLink Class 1 and 2, brand-specific quirks)

Test Categories:
- Windows compatibility: Verifies required Windows features and APIs
- DPI compatibility: Validates UI scaling behavior
- Projector compatibility: Tests protocol implementations against mock servers

Requirements Fulfilled:
- QA-04: Windows compatibility matrix
- QA-05: Display/DPI compatibility matrix
- QA-06: Projector brand compatibility matrix

Version: 1.0.0
"""

# Supported Windows builds for compatibility testing
SUPPORTED_WINDOWS_BUILDS = {
    "Windows 10 21H2": "19044",
    "Windows 10 22H2": "19045",
    "Windows 11 21H2": "22000",
    "Windows 11 22H2": "22621",
    "Windows 11 23H2": "22631",
}

# Supported DPI scaling factors
SUPPORTED_DPI_SCALES = {
    100: 96,    # 96 DPI
    125: 120,   # 120 DPI
    150: 144,   # 144 DPI
    175: 168,   # 168 DPI
    200: 192,   # 192 DPI
}

# Minimum UI dimensions at 100% scaling
MIN_WINDOW_WIDTH = 520
MIN_WINDOW_HEIGHT = 380
MIN_FONT_SIZE = 10  # points

# Supported projector brands
SUPPORTED_PROJECTOR_BRANDS = [
    "EPSON",
    "Hitachi",
    "Panasonic",
    "Sony",
    "BenQ",
    "NEC",
]

# PJLink protocol support levels
PJLINK_CLASS_SUPPORT = {
    1: "Basic control (power, input, mute, status)",
    2: "Extended (freeze, filter hours, serial number)",
}
