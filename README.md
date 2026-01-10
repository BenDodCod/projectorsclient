# Enhanced Projector Control Application

A robust, modern Python-based application for controlling network-connected projectors. Replaces legacy scripts with a professional PyQt6 interface, featuring dual operation modes (Standalone/SQL Server), multi-language support (English/Hebrew), and intuitive GUI-based configuration.

## Key Features

*   **Modern GUI:** A professional and intuitive user interface built with PyQt6, supporting both light and dark modes.
*   **Dual Operation Modes:**
    *   **Standalone Mode:** Uses a local SQLite database for single-room setups.
    *   **SQL Server Mode:** Connects to a central enterprise database for managing a fleet of projectors.
*   **GUI-Based Configuration:** No more editing config files. All settings are managed through a secure, password-protected admin interface. The first launch guides technicians through a simple setup wizard.
*   **Single Executable:** Deploys as a single `.exe` file created with PyInstaller. No complex installation scripts required.
*   **Multi-Brand Support:** Native support for PJLink-compatible projectors (Epson, Hitachi, etc.) with an extensible plugin architecture for future brands.
*   **Internationalization:** Full support for English and Hebrew (including RTL layouts) using Qt Linguist.
*   **Resilient Connectivity:** Features auto-retry logic with exponential backoff, connection diagnostics, and smart status polling to handle unreliable networks.
*   **System Tray Integration:** Provides quick access to essential controls and status information directly from the system tray.

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| UI Framework | PyQt6 | Modern, professional GUI with RTL support |
| Database (Standalone) | SQLite3 | Embedded database for local config |
| Database (SQL Mode) | pyodbc | SQL Server connectivity |
| Projector Protocol | pypjlink | PJLink implementation |
| Internationalization | Qt Linguist (.ts files) | English/Hebrew translations |
| Security | bcrypt, DPAPI, keyring | Password hashing and credential encryption |
| Logging | JSON structured logging | Machine-readable logs with context |
| Testing | pytest + pytest-qt | Unit and integration testing |
| Security Scanning | bandit, pip-audit, safety | Static checks and CVE audits |
| Packaging | PyInstaller | .exe compilation |


## Installation and Usage

### Installation
1.  Download the `ProjectorControl.exe` file.
2.  Run the installer or place the executable in a desired directory.
3.  Create a shortcut for easy access.

### First Run & Configuration
1.  Launch the application for the first time.
2.  You will be prompted to set an **Admin Password**. This password protects the configuration settings.
3.  A setup wizard will guide you through the initial configuration:
    *   **Connection:** Choose Standalone or SQL Server mode and enter projector details (IP, Port).
    *   **UI Customization:** Select which control buttons are visible to the end-user.
    *   **Options:** Set the application language, startup options, and status update intervals.
4.  Once saved, the application will display the main control interface, ready for use.

## Documentation

*   **[User Guide](USER_GUIDE.md):** Instructions for daily operation.
*   **[Technician Guide](TECHNICIAN_GUIDE.md):** Detailed setup and configuration instructions.
*   **[Troubleshooting Guide](TROUBLESHOOTING.md):** Solutions for common issues and diagnostics.
*   **[Security Policy](SECURITY.md):** Security architecture and reporting vulnerabilities.
*   **[Developer Guide](DEVELOPER.md):** Instructions for setting up the development environment, building, and contributing.
*   **[Implementation Plan](IMPLEMENTATION_PLAN.md):** The detailed project plan and technical specifications.

## Project Structure

The project follows a standard Python application layout:

```
projector-control-app/
├── src/                 # Main source code
│   ├── main.py          # Application entry point
│   ├── app.py           # Main application class
│   ├── config/          # Configuration and settings management
│   ├── controllers/     # Projector communication and control logic
│   ├── models/          # Data models and database interaction
│   ├── ui/              # PyQt6 windows, dialogs, and widgets
│   ├── i18n/            # Internationalization files
│   └── utils/           # Shared utilities
├── resources/           # Assets like SQL schemas and icons
├── tests/               # Unit, integration, and end-to-end tests
└── ...
```

## License

This is proprietary software intended for internal use.
