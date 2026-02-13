# Enhanced Projector Control Application - User Guide

**Version:** 1.0
**Last Updated:** February 12, 2026
**Application Version:** 2.0.0-rc2

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [First-Time Setup](#2-first-time-setup)
3. [Understanding the Interface](#3-understanding-the-interface)
4. [Daily Use](#4-daily-use)
5. [Advanced Features](#5-advanced-features)
6. [Settings](#6-settings)
7. [Tips and Best Practices](#7-tips-and-best-practices)
8. [Keyboard Shortcuts](#8-keyboard-shortcuts)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. Introduction

### What is the Enhanced Projector Control Application?

The Enhanced Projector Control Application is a professional tool designed to make controlling network projectors quick and easy. Instead of using a physical remote control or walking to the projector, you can control it directly from your computer over the network.

**What you can do:**
- Turn projectors on and off
- Switch between input sources (HDMI, VGA, etc.)
- Blank the screen during presentations
- Freeze the display
- View a history of all operations

**Who should use this guide:**
- Teachers and presenters who control projectors daily
- Office workers who use projectors for meetings
- Anyone who wants to learn how to use the application

### Getting Help

If you need assistance:
- **This User Guide** - Step-by-step instructions for common tasks
- **[FAQ](../FAQ.md)** - Quick answers to common questions
- **[README](../../README.md)** - Technical specifications and system requirements
- **Your IT Administrator** - For network issues, installation, or advanced configuration

---

## 2. First-Time Setup

When you launch the application for the first time, you'll go through a quick setup wizard that takes about 5 minutes to complete.

### Step 1: Language Selection

The first page lets you choose your preferred language.

[Screenshot: First-run wizard - Step 1 Language Selection. Shows the title "Welcome to Projector Control" at the top. Two large radio buttons are displayed vertically: "English" (with flag icon) and "עברית - Hebrew" (with flag icon). The English option is selected by default with a blue radio button. At the bottom right corner, there is a blue "Next" button. The wizard shows "Step 1 of 6" at the bottom left.]

**What to do:**
1. Select your preferred language:
   - **English** - Use the application in English
   - **עברית (Hebrew)** - Use the application in Hebrew with right-to-left layout
2. Click **Next** to continue

> **Tip:** You can change the language later in Settings if needed.

---

### Step 2: Admin Password Setup

This step creates a master password to protect your application settings.

[Screenshot: First-run wizard - Step 2 Admin Password Setup. Title "Create Admin Password" at top. Description text: "Create a password to protect application settings and projector credentials." Two password input fields stacked vertically: "Password" and "Confirm Password", both with eye icons to show/hide password. Below the fields, a password strength indicator bar shows segments in gray/yellow/green with text "Password Strength: Medium". Requirements checklist below: ✓ At least 8 characters, ✓ Contains uppercase letter, ✗ Contains number, ✗ Contains special character. Next button at bottom right, Back button at bottom left. Shows "Step 2 of 6".]

**What to do:**
1. Enter a password in the **Password** field
2. Enter the same password again in the **Confirm Password** field
3. Make sure the password meets these requirements:
   - At least 8 characters long
   - Contains at least one uppercase letter (A-Z)
   - Contains at least one number (0-9)
   - Contains at least one special character (!@#$%^&*)
4. Watch the password strength indicator:
   - **Weak** (Red) - Add more characters or complexity
   - **Medium** (Yellow) - Acceptable, but consider strengthening
   - **Strong** (Green) - Excellent password!
5. Click **Next** to continue

> **Warning:** Write down this password and store it in a safe place! If you forget it, there is no recovery option. You'll need to reinstall the application and reconfigure everything.

---

### Step 3: Database Mode Selection

Choose how your settings and projector configurations will be stored.

[Screenshot: First-run wizard - Step 3 Database Mode Selection. Title "Choose Database Mode" at top. Two large option cards displayed vertically with icons. First card (selected with blue border): "Standalone (SQLite)" with database icon. Description: "Store settings on this computer only. Best for single-user installations." Below shows "Data location: %APPDATA%\ProjectorControl". Second card: "Enterprise (SQL Server)" with server icon. Description: "Connect to central SQL Server database. Best for organizations with multiple computers." Shows "Requires: SQL Server connection details". Next button at bottom right, Back button at bottom left. Shows "Step 3 of 6".]

**What to do:**

Choose one of these options:

**Option 1: Standalone (SQLite)** - Recommended for most users
- Your settings stay on your computer only
- No network database required
- Perfect for individual users
- Data stored at: `%APPDATA%\ProjectorControl\`

**Option 2: Enterprise (SQL Server)** - For organizations
- Settings stored on a central server
- Multiple computers can share the same configuration
- Requires SQL Server setup by your IT administrator
- You'll need connection details from IT

> **Tip:** If you're not sure which to choose, select **Standalone (SQLite)**. You can always migrate to Enterprise mode later if needed.

For most users:
1. Select **Standalone (SQLite)**
2. Click **Next** to continue

---

### Step 4: Projector Configuration

Add your first projector to the application.

[Screenshot: First-run wizard - Step 4 Projector Configuration. Title "Configure Your Projector" at top. Form with labeled fields in vertical layout: 1) "Projector Name" text field showing "Conference Room A", 2) "IP Address" text field showing "192.168.1.100", 3) "Port" text field showing "4352" (with info icon and tooltip "PJLink default port"), 4) "Brand" dropdown menu showing "EPSON" selected (dropdown shows EPSON, Hitachi, Sony, BenQ, NEC, Panasonic, Christie, Other - PJLink Generic), 5) Optional "Password" field (empty) with info text "Leave blank if projector has no password". At the bottom, "Test Connection" button (gray) and "Skip for now" link. Next button at bottom right (disabled/gray), Back button at bottom left. Shows "Step 4 of 6".]

**What to do:**

Fill in the following information about your projector:

1. **Projector Name** - A friendly name you'll recognize
   - Example: "Conference Room A" or "Main Classroom"

2. **IP Address** - The network address of your projector
   - Example: `192.168.1.100`
   - Ask your IT administrator if you don't know this

3. **Port** - Usually `4352` for PJLink projectors
   - Default is correct for most projectors
   - Only change if your IT administrator instructs you to

4. **Brand** - Select your projector manufacturer
   - Choose from: EPSON, Hitachi, Sony, BenQ, NEC, Panasonic, Christie
   - If your brand isn't listed, select "Other - PJLink Generic"

5. **Password** (Optional)
   - Only enter if your projector requires authentication
   - Leave blank for projectors without passwords
   - Contact IT if you're unsure

6. Click **Test Connection** to verify
   - Wait a few seconds while the application connects
   - You should see "Connection successful!" message
   - If it fails, double-check the IP address and port

7. Click **Next** to continue

> **Tip:** You can add more projectors later from the Settings menu.

> **Note:** If you want to configure projectors later, click "Skip for now" to continue without adding a projector now.

---

### Step 5: UI Customization (Optional)

Customize which control buttons appear in the main window.

[Screenshot: First-run wizard - Step 5 UI Customization. Title "Customize Control Buttons" at top. Description text: "Select which controls you want visible in the main window. You can change this later in Settings." Grid layout of checkboxes with button previews, arranged in 3 columns: Row 1: ☑ Power On/Off (button preview shown), ☑ Input Source (dropdown preview), ☑ Blank Screen (button preview). Row 2: ☑ Freeze Display (button preview), ☐ Volume Control (slider preview grayed out), ☐ Mute Audio (button preview grayed out). Row 3: ☐ Picture Mode (dropdown preview grayed out), ☐ Aspect Ratio (dropdown preview grayed out). Below grid: "Recommended defaults are pre-selected" in italic gray text. Next button at bottom right, Back button at bottom left. Shows "Step 5 of 6".]

**What to do:**

1. Review the recommended default selections:
   - ✓ Power On/Off
   - ✓ Input Source
   - ✓ Blank Screen
   - ✓ Freeze Display

2. Optionally add more controls:
   - **Volume Control** - Adjust projector volume
   - **Mute Audio** - Quickly mute/unmute sound
   - **Picture Mode** - Switch between presentation modes
   - **Aspect Ratio** - Change screen aspect ratio

3. Click **Next** to continue

> **Tip:** Keep it simple! The recommended defaults cover most daily needs. You can always add more buttons later in Settings > UI Buttons.

---

### Step 6: Setup Complete

You're all set! The wizard is complete.

[Screenshot: First-run wizard - Step 6 Completion. Title "Setup Complete!" at top with green checkmark icon. Summary panel showing configured settings: "Language: English", "Database Mode: Standalone (SQLite)", "Projectors Configured: 1" (with "Conference Room A - 192.168.1.100" shown below). Green success message box: "✓ Your projector control application is ready to use!" Below: "What's next?" bulleted list: • Control your projector from the main window, • View operation history in the History panel, • Customize settings anytime from the Settings menu. Large green "Finish" button at bottom right, "Back" button at bottom left (grayed out). Shows "Step 6 of 6".]

**What you see:**
- A summary of your configuration
- Confirmation that setup is complete
- What to do next

**What to do:**
1. Review the configuration summary
2. Click **Finish** to open the main window

> **Congratulations!** You're ready to start controlling your projector!

---

## 3. Understanding the Interface

After completing setup, you'll see the main application window. Let's take a tour of each section.

### Main Window Overview

[Screenshot: Main window - Full annotated view. Use numbered blue callouts pointing to each area: 1=Top toolbar (left side: Settings gear icon, Language toggle "EN|HE", Help "?" icon; right side: Minimize, Maximize, Close buttons), 2=Status Panel (left section showing: "Conference Room A" as title, green circle "Connected", "Power: On", "Input: HDMI1", "Last Update: 2 seconds ago"), 3=Control Buttons Section (center area with 4 buttons in 2x2 grid: "Power On" (green), "Power Off" (red), "Input Source" (blue dropdown showing "HDMI1 ▼"), "Blank Screen" (yellow)), 4=History Panel (right section showing scrollable list with 5 entries, each showing timestamp, icon, and operation: "14:32:15 - Power On - Success ✓", "14:28:03 - Input Changed to HDMI1 - Success ✓", etc.), 5=Status Bar (bottom showing: left side "Connection: Stable ●", center "Operations: 127 today", right "App Version: 2.0.0-rc2"). Window title shows "Enhanced Projector Control".]

The main window has 5 key areas:

1. **Top Toolbar** - Access settings and help
2. **Status Panel** - See current projector state
3. **Control Buttons** - Control your projector
4. **History Panel** - View recent operations
5. **Status Bar** - Connection and app info

Let's explore each area in detail.

---

### 1. Top Toolbar

[Screenshot: Top toolbar close-up. Shows horizontal toolbar with light gray background. Left section: Settings gear icon (with tooltip "Settings (Ctrl+,)" showing on hover), Language toggle button showing "EN|HE" (with tooltip "Switch Language"), Help "?" icon (with tooltip "Help (F1)"). Right section standard Windows controls: Minimize "_", Maximize "□", Close "×". All icons are approximately 24x24 pixels with 8px spacing.]

**Settings Gear Icon** ⚙️
- Click to open the Settings dialog
- Keyboard shortcut: `Ctrl+,`

**Language Toggle** 🌐
- Switch between English and Hebrew
- Current language is highlighted

**Help Icon** ❓
- Access help documentation
- Keyboard shortcut: `F1`

**Window Controls**
- Minimize, Maximize/Restore, Close buttons
- Standard Windows behavior

---

### 2. Status Panel

[Screenshot: Status Panel detailed view. Panel has white background with light border. Top: Large bold text "Conference Room A" (projector name). Below in stacked rows: Row 1: Green filled circle (●) followed by "Connected" in green text. Row 2: Icon of power symbol followed by "Power: On" in bold. Row 3: Icon of input cable followed by "Input: HDMI1" in bold. Row 4: Icon of clock followed by "Last Update: 2 seconds ago" in gray italics. Panel has subtle drop shadow.]

The Status Panel shows real-time information about your projector:

**Projector Name**
- The friendly name you assigned during setup
- Example: "Conference Room A"

**Connection Status**
- 🟢 **Connected** - Communication is working
- 🔴 **Disconnected** - Cannot reach projector
- 🟡 **Connecting** - Attempting to connect

**Power State**
- **On** - Projector is powered on
- **Off** - Projector is powered off
- **Warming Up** - Projector is turning on
- **Cooling Down** - Projector is turning off

**Current Input Source**
- Shows which input is active (HDMI1, HDMI2, VGA, etc.)

**Last Update**
- Time since last status refresh
- Updates automatically every 5 seconds

> **Tip:** If "Last Update" shows a time longer than 10 seconds, there may be a connection issue.

---

### 3. Control Buttons

[Screenshot: Control Buttons section detailed view. Shows 2x2 grid of large buttons with 8px spacing. Each button is approximately 120x60 pixels. Top row: "Power On" button (green background, white text, power icon), "Power Off" button (red background, white text, power icon). Bottom row: "Input Source" button (blue background, white text, dropdown arrow, shows "HDMI1 ▼"), "Blank Screen" button (yellow background, black text, screen icon). All buttons have slight rounded corners and subtle shadows. Buttons are clearly labeled and visually distinct.]

The Control Buttons let you perform common operations:

**Power On** (Green)
- Turns the projector on
- May take 30-60 seconds for projector to warm up

**Power Off** (Red)
- Turns the projector off
- Projector will cool down (typically 60-90 seconds)

**Input Source** (Blue dropdown)
- Click to see available inputs
- Select to switch input sources
- Available options depend on your projector model

**Blank Screen** (Yellow)
- Temporarily blanks the projected image
- Click again to restore the image
- Useful for hiding content momentarily

> **Note:** The buttons shown depend on your UI Customization settings. See [Section 6](#6-settings) to add or remove buttons.

---

### 4. History Panel

[Screenshot: History Panel detailed view. Panel titled "Operation History" at top in bold. Scrollable list showing 8 entries. Each entry has: timestamp on left (gray, format "HH:MM:SS"), operation icon in middle (power/input/blank icons), operation description and status on right. Example entries: "14:35:42 🔌 Power On → Success ✓ (green checkmark)", "14:32:18 📺 Input Changed to HDMI2 → Success ✓", "14:28:55 ⚪ Screen Blanked → Success ✓", "14:15:03 🔌 Power Off → Success ✓", "13:58:12 📺 Input Changed to VGA → Failed ✗ (red X with error message 'Input not available')", etc. Vertical scrollbar on right side. Bottom of panel shows "Showing 8 of 127 operations today" in small gray text.]

The History Panel shows a log of all operations:

**Each Entry Shows:**
- **Time** - When the operation was performed (HH:MM:SS)
- **Icon** - Visual indicator of operation type
- **Operation** - What action was taken
- **Status** - Success ✓ or Failed ✗

**Entry Types:**
- 🔌 Power operations (On/Off)
- 📺 Input source changes
- ⚪ Screen blank/unblank
- 🧊 Freeze/unfreeze display
- 🔊 Volume/mute changes

**Using the History Panel:**
- Scroll to see older entries
- Failed operations shown in red with error details
- Hover over an entry to see additional details
- Right-click for options (copy details, clear history)

> **Tip:** If you see frequent failures for a specific operation, there may be a compatibility issue with your projector model. Check the [FAQ](../FAQ.md) or contact your IT administrator.

---

### 5. Status Bar

[Screenshot: Status Bar detailed view. Horizontal bar at bottom of window with light gray background. Three sections separated by subtle dividers: Left section shows green dot (●) followed by "Connection: Stable" in small text. Center section shows "Operations: 127 today" with small graph icon. Right section shows "App Version: 2.0.0-rc2" in gray text. Each section is approximately equal width.]

The Status Bar provides quick reference information:

**Connection Status** (Left)
- 🟢 **Stable** - Connection is healthy
- 🟡 **Unstable** - Intermittent connectivity
- 🔴 **Failed** - Connection lost

**Operations Count** (Center)
- Total number of operations performed today
- Resets at midnight

**Application Version** (Right)
- Current version number
- Useful when reporting issues

---

### System Tray Icon

[Screenshot: System tray area (bottom-right corner of Windows taskbar). Shows Windows system tray with multiple icons (sound, network, etc.). Highlight the projector control application icon (small projector icon) among them. Show a tooltip appearing on hover: "Projector Control - Conference Room A: On (HDMI1)". Arrow pointing to the icon with annotation "Double-click to open main window, Right-click for quick actions".]

When you minimize the application, it continues running in the system tray.

**Accessing the System Tray:**
- Look for the projector icon 📽️ in the Windows taskbar notification area (bottom-right)
- If you don't see it, click the "Show hidden icons" arrow ˄

**System Tray Actions:**
- **Double-click** - Opens the main window
- **Right-click** - Opens quick action menu (see below)

[Screenshot: System tray right-click context menu. Small popup menu with white background showing: "Conference Room A" (projector name in bold at top, gray background), horizontal separator line, "Power On" (with green circle icon), "Power Off" (with red circle icon), "Blank Screen" (with screen icon), horizontal separator line, "Show Main Window" (with window icon), "Settings" (with gear icon), horizontal separator line, "Exit" (with X icon). Menu has subtle drop shadow.]

**Quick Action Menu:**
- **Projector Name** - Header showing active projector
- **Power On** - Quickly turn on projector
- **Power Off** - Quickly turn off projector
- **Blank Screen** - Toggle blank screen
- **Show Main Window** - Restore the main window
- **Settings** - Open settings dialog
- **Exit** - Close the application completely

> **Tip:** Use the system tray for quick power control without opening the main window!

---

## 4. Daily Use

Now that you understand the interface, let's walk through common daily tasks.

### Turning the Projector On

[Screenshot: Main window with cursor hovering over green "Power On" button. Button has subtle glow effect to indicate hover state. Status Panel shows "Power: Off" and "Connection: Connected".]

**Steps:**
1. Make sure the Status Panel shows **Connected**
2. Click the green **Power On** button
3. Wait for the projector to warm up (30-60 seconds)
4. The Status Panel will update to show **Power: Warming Up**, then **Power: On**

[Screenshot: Status Panel during warm-up. Shows "Power: Warming Up" with animated ellipsis "..." and small circular progress indicator. Text below says "Estimated time: 45 seconds".]

**What happens:**
- The application sends a power-on command
- The projector lamp begins warming up
- Status updates automatically as the projector starts
- History Panel shows "Power On → Success ✓"

> **Tip:** Don't click the button multiple times! The command was received the first time. Wait for the status to update.

---

### Turning the Projector Off

[Screenshot: Main window with cursor hovering over red "Power Off" button. Button has subtle glow effect. Status Panel shows "Power: On".]

**Steps:**
1. Click the red **Power Off** button
2. If prompted, confirm you want to turn off the projector
3. Wait for the projector to cool down (60-90 seconds)
4. The Status Panel will update to show **Power: Cooling Down**, then **Power: Off**

[Screenshot: Confirmation dialog. Modal window with title "Confirm Power Off". Message: "Are you sure you want to turn off the projector?" Icon showing projector with power symbol. Two buttons: "Yes, Turn Off" (red, focused) and "Cancel" (gray). Checkbox at bottom: "☐ Don't ask me again".]

**What happens:**
- Confirmation dialog appears (optional, can be disabled)
- The application sends a power-off command
- The projector fan runs to cool the lamp
- Status updates automatically as the projector shuts down
- History Panel shows "Power Off → Success ✓"

> **Warning:** Never unplug a projector immediately after turning it off! Always let it cool down completely to protect the lamp.

---

### Switching Input Sources

[Screenshot: Main window with "Input Source" dropdown button expanded. Dropdown menu shows list of 5 options: "HDMI1" (with green checkmark indicating current selection), "HDMI2", "VGA", "Component", "Network". Each option has an appropriate icon. Dropdown has white background with subtle shadow.]

**Steps:**
1. Click the **Input Source** dropdown button
2. Select your desired input from the list:
   - HDMI1, HDMI2 - Digital HDMI inputs
   - VGA - Analog VGA input
   - Component - Component video input
   - Network - Network display
3. Wait a few seconds for the projector to switch
4. The Status Panel will update to show the new input

**What happens:**
- The application sends an input change command
- The projector switches to the selected input
- Status Panel updates to show "Input: [Source Name]"
- History Panel shows "Input Changed to [Source] → Success ✓"

> **Tip:** Available inputs depend on your specific projector model. If an input is missing, it may not be supported by your projector.

---

### Blanking the Screen

[Screenshot: Two side-by-side views. Left: Main window showing yellow "Blank Screen" button in normal state with text "Blank Screen". Right: Same button after being clicked, now showing "Unblank Screen" with slightly different icon and button is pressed/highlighted.]

**Steps:**
1. Click the **Blank Screen** button
2. The projected image immediately blanks to black
3. The button changes to **Unblank Screen**
4. Click again to restore the image

**When to use:**
- Hide sensitive content temporarily during a presentation
- Pause between presentation sections
- Keep audience focused during discussions

**What happens:**
- The projector immediately displays a black screen
- The projector lamp stays on (not the same as power off)
- Audio continues if enabled
- History Panel shows "Screen Blanked → Success ✓"

> **Tip:** Blank Screen is faster than turning the projector off and back on. Use it for brief pauses.

---

### Viewing Operation History

[Screenshot: History Panel with one entry highlighted (blue background selection). Entry shows "14:32:18 📺 Input Changed to HDMI2 → Success ✓". Context menu is open (right-click menu) showing options: "Copy Details", "View Full Message", "Clear This Entry", horizontal separator, "Clear All History", "Export History...". Menu has white background with subtle shadow.]

**Steps:**
1. Look at the **History Panel** on the right side
2. Scroll through the list to see past operations
3. Hover over an entry to see additional details
4. Right-click an entry for more options:
   - **Copy Details** - Copy operation info to clipboard
   - **View Full Message** - See complete error details (for failed operations)
   - **Clear This Entry** - Remove from history
   - **Clear All History** - Clear entire history
   - **Export History** - Save history to a file

**Understanding History Entries:**

✓ **Success (Green checkmark)**
- Operation completed successfully
- Projector responded as expected

✗ **Failed (Red X)**
- Operation failed
- Click to see error details
- Common causes: network timeout, unsupported command, projector in wrong state

**Filtering History:**
- Use the search box (if enabled in Settings) to find specific operations
- Filter by date range or operation type

> **Tip:** If you see patterns of failures (e.g., "Input Changed" always fails), this indicates a compatibility issue with your projector. Check the [FAQ](../FAQ.md) for troubleshooting.

---

### Using the System Tray

[Screenshot: Windows desktop with main application window minimized. Focus on system tray area showing projector icon. Small notification bubble appears from system tray: "Projector Control minimized - Running in background. Double-click the icon to restore." Notification fades after 3 seconds.]

**Minimizing to System Tray:**
1. Click the **Minimize** button on the main window
2. The window disappears and the icon moves to the system tray
3. A notification confirms it's still running

**Quick Power Control from System Tray:**
1. Right-click the system tray icon 📽️
2. Select **Power On** or **Power Off** from the menu
3. The operation executes in the background
4. A notification appears confirming success

[Screenshot: System tray notification balloon. Shows small popup with projector icon at top, message "Power On → Success ✓", subtitle "Conference Room A is now warming up", and timestamp "14:35:42". Notification has white background with subtle border and drop shadow. Auto-dismisses after 5 seconds.]

**Viewing Status from System Tray:**
1. Hover your mouse over the system tray icon
2. A tooltip appears showing current status:
   - Projector name
   - Power state
   - Current input

> **Tip:** Keep the application running in the system tray for instant access throughout the day!

---

### Changing the Active Projector

If you have multiple projectors configured, you can switch between them.

[Screenshot: Main window toolbar with projector selector dropdown added to left side (next to Settings icon). Dropdown shows current selection "Conference Room A ▼". When clicked, dropdown menu shows 3 projectors: "Conference Room A" (current, checkmark), "Training Room B", "Auditorium Main". Each has icon and current status shown in gray text below name: "Connected, On (HDMI1)" or "Disconnected".]

**Steps:**
1. Click the **Projector Selector** dropdown in the toolbar (if multiple projectors configured)
2. Select the projector you want to control
3. The interface updates to show the selected projector's status
4. All control buttons now affect the selected projector

> **Note:** If you only have one projector configured, the selector dropdown is hidden automatically.

---

## 5. Advanced Features

Beyond basic power and input control, the application offers advanced features for presentations and specialized scenarios.

### Freezing the Display

[Screenshot: Main window showing "Freeze Display" button (light blue color) in the control buttons section. Icon shows a snowflake or pause symbol. Below the button, small text says "Freezes projected image while source continues".]

**What it does:**
- Freezes the current projected image in place
- Your computer screen continues to update normally
- The projector shows a static "snapshot" of what was on screen

**When to use:**
- Pause a video while you explain a concept
- Keep a slide visible while you navigate to other content
- Hide your desktop while opening files or applications

**Steps:**
1. Click the **Freeze Display** button
2. The projected image freezes immediately
3. The button changes to **Unfreeze Display**
4. Continue working on your computer (audience won't see changes)
5. Click **Unfreeze Display** to resume normal projection

> **Warning:** While frozen, the audience cannot see what you're doing on your computer. This includes mouse movements, new windows, or content changes.

---

### Volume Control

[Screenshot: Main window showing "Volume" slider control (horizontal slider, range 0-100, current position at 50). Left end has speaker-with-X icon (mute), right end has speaker-with-waves icon (loud). Below slider shows "50%" in gray text. Small "Mute" checkbox to the right of slider.]

**If enabled in Settings:**

**Adjusting Volume:**
1. Locate the **Volume** slider in the control section
2. Drag the slider left (quieter) or right (louder)
3. The projector volume adjusts in real-time
4. Current volume percentage shown below slider

**Muting Audio:**
1. Click the **Mute** checkbox (or speaker-X icon)
2. Audio mutes immediately
3. Uncheck to restore audio

> **Note:** Not all projector models support volume control via network. If the slider is disabled (grayed out), your projector does not support this feature.

---

### Picture Modes

[Screenshot: Main window showing "Picture Mode" dropdown button. Dropdown expanded showing 5 options with icons: "Presentation" (current, checkmark), "Cinema", "sRGB", "Dynamic", "Custom". Each option has a small preview icon showing brightness/contrast representation.]

**If enabled in Settings:**

**Switching Picture Modes:**
1. Click the **Picture Mode** dropdown
2. Select from available modes:
   - **Presentation** - Bright, high contrast for lit rooms
   - **Cinema** - Balanced for movies
   - **sRGB** - Color-accurate for photos
   - **Dynamic** - Maximum brightness
   - **Custom** - User-defined settings
3. The projector switches modes immediately

**When to use:**
- **Presentation** - Daytime meetings or classes
- **Cinema** - Movie playback
- **sRGB** - Photo or design work
- **Dynamic** - Very bright rooms

> **Note:** Available modes vary by projector model. Some may have fewer options.

---

### Aspect Ratio Selection

[Screenshot: Main window showing "Aspect Ratio" dropdown button. Dropdown shows 4 options: "16:9 Widescreen" (current), "4:3 Standard", "16:10 Computer", "Auto". Each has small visual representation of the ratio.]

**If enabled in Settings:**

**Changing Aspect Ratio:**
1. Click the **Aspect Ratio** dropdown
2. Select your desired ratio:
   - **16:9** - Modern widescreen (most common)
   - **4:3** - Classic standard format
   - **16:10** - Computer displays
   - **Auto** - Detect from source
3. The projected image adjusts to fill the selected ratio

**Choosing the right ratio:**
- **16:9** - For modern laptops, videos, presentations
- **4:3** - For older content or classic format
- **Auto** - Let the projector decide (recommended)

---

### Testing Connection

You can manually test the connection to your projector at any time.

[Screenshot: Settings dialog open, "Connection" tab selected. Mid-section shows a card labeled "Connection Test" with text "Verify network connectivity to projector". Button labeled "Test Connection Now" (blue). Below button is a status message area (empty initially, showing "Click test to verify connection" in gray).]

**Steps:**
1. Open **Settings** (Gear icon or `Ctrl+,`)
2. Go to the **Connection** tab
3. Click **Test Connection Now**
4. Wait a few seconds for results

[Screenshot: Same Connection Test card, but status area now shows results. Green box with checkmark icon and text: "✓ Connection successful! Ping: 12ms, Projector Model: EPSON EB-2250U, Firmware: 1.23". Below shows "Last tested: Just now".]

**Successful Test Shows:**
- ✓ Connection status
- Response time (ping)
- Projector model name
- Firmware version
- Last test timestamp

**Failed Test Shows:**
- ✗ Connection error
- Error message (timeout, refused, etc.)
- Diagnostic suggestions
- Troubleshooting link

> **Tip:** Run a connection test if you notice slow response times or frequent failures in the History Panel.

---

## 6. Settings

The Settings dialog provides extensive customization options. Access it by clicking the gear icon ⚙️ or pressing `Ctrl+,`.

[Screenshot: Settings dialog window. Window title "Settings". Left sidebar shows 6 tab icons vertically: General (house icon, selected with blue highlight), Connection (plug icon), UI Buttons (grid icon), Security (lock icon), Advanced (wrench icon), Diagnostics (magnifying glass icon). Main content area on right shows "General Settings" content. Bottom of window has "Save", "Apply", "Cancel" buttons. Window is approximately 800x600 pixels with white background.]

The Settings dialog has 6 tabs:

1. **General** - Language, startup, display preferences
2. **Connection** - Network settings, timeouts, retry behavior
3. **UI Buttons** - Customize visible control buttons
4. **Security** - Password management, credential security
5. **Advanced** - Database mode, logging, performance tuning
6. **Diagnostics** - Logs, connection tests, troubleshooting tools

Let's explore each tab.

---

### General Settings

[Screenshot: Settings dialog, General tab selected. Content area shows several setting groups: 1) "Language Preferences" group with radio buttons "English" (selected) and "עברית Hebrew", 2) "Startup Behavior" group with checkboxes "☑ Launch on Windows startup" and "☑ Start minimized to system tray", 3) "User Interface" group with checkbox "☑ Show notification balloons" and "☑ Confirm before power off", 4) "Updates" group with checkbox "☐ Check for updates automatically" and button "Check Now". Each group has subtle border and padding.]

**Language Preferences:**
- **English / עברית (Hebrew)** - Select your preferred language
- Changes take effect immediately
- Switches entire interface including menus, dialogs, and messages

**Startup Behavior:**
- ☑ **Launch on Windows startup** - Auto-start when you log in to Windows
- ☑ **Start minimized to system tray** - Launch hidden in background
- Recommended for daily users

**User Interface:**
- ☑ **Show notification balloons** - Display operation results as notifications
- ☑ **Confirm before power off** - Ask before turning projector off
- Uncheck to skip confirmation dialogs

**Updates:**
- ☑ **Check for updates automatically** - Weekly check for new versions
- **Check Now** - Manually check for updates

> **Tip:** Enable "Launch on Windows startup" if you use the projector daily. The app will be ready in the system tray when you need it.

---

### Connection Settings

[Screenshot: Settings dialog, Connection tab selected. Content area shows: 1) "Active Projector" section showing current projector card "Conference Room A - 192.168.1.100:4352 - EPSON" with "Edit" and "Test" buttons, 2) "Network Timeouts" section with three labeled sliders: "Connection Timeout: 5 seconds" (range 3-30s), "Command Timeout: 10 seconds" (range 5-60s), "Status Update Interval: 5 seconds" (range 3-30s), 3) "Reliability" section with checkbox "☑ Enable automatic reconnection" and text field "Retry attempts: 3" (range 1-10), 4) "Add New Projector" button at bottom (blue).]

**Active Projector:**
- Shows currently selected projector details
- **Edit** - Modify projector configuration
- **Test** - Run connection test

**Network Timeouts:**
- **Connection Timeout** (3-30 seconds) - How long to wait when connecting
  - Increase for slow networks
  - Default: 5 seconds

- **Command Timeout** (5-60 seconds) - How long to wait for command response
  - Increase for unresponsive projectors
  - Default: 10 seconds

- **Status Update Interval** (3-30 seconds) - How often to refresh status
  - Lower = more frequent updates, more network traffic
  - Default: 5 seconds

**Reliability:**
- ☑ **Enable automatic reconnection** - Retry if connection drops
- **Retry attempts** - How many times to retry failed operations
  - Default: 3 attempts

**Managing Projectors:**
- **Add New Projector** - Configure additional projectors
- **Edit** - Modify existing projector settings
- **Remove** - Delete projector configuration

> **Tip:** If you experience frequent timeouts, increase the Connection Timeout to 10-15 seconds.

---

### UI Buttons Settings

[Screenshot: Settings dialog, UI Buttons tab selected. Content area shows grid of button toggles: "Available Control Buttons" heading, then 3 columns of checkboxes with button previews: Column 1: "☑ Power On/Off" (green/red buttons shown), "☑ Input Source" (blue dropdown shown), "☑ Blank Screen" (yellow button shown). Column 2: "☑ Freeze Display" (light blue button shown), "☐ Volume Control" (slider shown grayed), "☐ Mute Audio" (button shown grayed). Column 3: "☐ Picture Mode" (dropdown shown grayed), "☐ Aspect Ratio" (dropdown shown grayed), "☐ Info/Status" (button shown grayed). Below grid: "Preview" section showing miniature main window with only checked buttons visible. Note at bottom: "Unchecking a button hides it from the main window. You can still access all features from the system tray."]

**Customizing Control Buttons:**

1. Check the boxes for buttons you want visible
2. Uncheck boxes to hide buttons you don't use
3. See preview of main window layout below
4. Click **Apply** to update the main window

**Recommended Minimum:**
- Power On/Off
- Input Source

**Common Combinations:**

**Basic User:**
- Power On/Off
- Input Source

**Presenter:**
- Power On/Off
- Input Source
- Blank Screen
- Freeze Display

**Advanced User:**
- All buttons enabled

> **Tip:** Keep your interface clean by hiding buttons you rarely use. You can always enable them later if needed.

---

### Security Settings

[Screenshot: Settings dialog, Security tab selected. Content area shows: 1) "Admin Password" section with button "Change Admin Password..." and text "Last changed: 14 days ago", 2) "Projector Credentials" section with text "Stored projector passwords are encrypted using Windows DPAPI" and red warning box "⚠ Warning: Entropy file backup required for password recovery. See Security documentation.", 3) "Backup Encryption" section with dropdown "Encryption Strength: AES-256-GCM (Recommended)" and checkbox "☑ Require password for backup restore", 4) "Session Security" section with checkbox "☐ Automatically lock after 30 minutes of inactivity" and text field for minutes.]

**Admin Password:**
- **Change Admin Password** - Update your master password
- Shows when password was last changed
- Required to access this Settings dialog

**Projector Credentials:**
- All projector passwords are encrypted using Windows DPAPI
- Entropy file (`.projector_entropy`) must be backed up
- Without entropy file, encrypted passwords cannot be recovered

**Backup Encryption:**
- **Encryption Strength** - Choose encryption level for backups
  - AES-256-GCM (Recommended) - Strongest security
  - AES-128-GCM - Faster, still secure
- ☑ **Require password for backup restore** - Password protect backup files

**Session Security:**
- ☐ **Automatically lock after inactivity** - Lock settings after idle time
- Protects settings if you walk away from your computer

> **Warning:** The entropy file is CRITICAL! If you lose it and need to reinstall Windows or move to a new computer, you will lose all saved projector passwords. See [Backup and Disaster Recovery](../deployment/DEPLOYMENT_GUIDE.md#10-backup-and-disaster-recovery) for backup procedures.

---

### Advanced Settings

[Screenshot: Settings dialog, Advanced tab selected. Content area shows: 1) "Database Mode" section (grayed out/read-only) showing "Current Mode: Standalone (SQLite)" with info icon and tooltip "Database mode cannot be changed after initial setup", 2) "Performance" section with checkbox "☑ Enable connection pooling" and "☑ Cache projector status (reduces network calls)", 3) "Logging" section with dropdown "Log Level: Info" (options: Debug, Info, Warning, Error) and button "Open Log Folder", 4) "Developer Options" section with checkbox "☐ Enable debug mode" and red warning text "Debug mode generates large log files. Only enable when troubleshooting."]

**Database Mode:**
- Shows current database mode (Standalone or Enterprise)
- Cannot be changed after initial setup
- Contact IT administrator to migrate between modes

**Performance:**
- ☑ **Enable connection pooling** - Reuse network connections for better performance
- ☑ **Cache projector status** - Reduce network traffic by caching status
- Both recommended for normal use

**Logging:**
- **Log Level** - Control detail level in log files
  - **Debug** - Maximum detail (large files)
  - **Info** - Normal operational logs (recommended)
  - **Warning** - Only warnings and errors
  - **Error** - Only errors
- **Open Log Folder** - View log files for troubleshooting

**Developer Options:**
- ☐ **Enable debug mode** - Extra diagnostic information
- Only enable when requested by support
- Generates very large log files

> **Tip:** If experiencing issues, set Log Level to "Debug", reproduce the problem, then send the log files to your IT administrator or support.

---

### Diagnostics Settings

[Screenshot: Settings dialog, Diagnostics tab selected. Content area shows: 1) "Connection Diagnostics" section with button "Run Network Test" and empty results area, 2) "System Information" section showing read-only fields: "Application Version: 2.0.0-rc2", "Database Mode: Standalone (SQLite)", "Platform: Windows 11 Pro", "Python Version: 3.11.5", button "Copy System Info", 3) "Troubleshooting Tools" section with three buttons vertically: "Reset Window Position", "Clear History Cache", "Export Diagnostic Report", 4) "Support" section with text "Need help?" and button "View Documentation".]

**Connection Diagnostics:**
- **Run Network Test** - Comprehensive network connectivity test
- Tests: DNS resolution, ping, port connectivity, PJLink protocol
- Results show specific failure point for troubleshooting

**System Information:**
- Read-only display of system details
- Useful when reporting issues
- **Copy System Info** - Copy all details to clipboard

**Troubleshooting Tools:**
- **Reset Window Position** - Fix window stuck off-screen
- **Clear History Cache** - Clear operation history database
- **Export Diagnostic Report** - Create comprehensive diagnostic file for support

**Support:**
- **View Documentation** - Open user guide (this document)
- Links to FAQ, README, and other resources

> **Tip:** Use "Export Diagnostic Report" when contacting support. It includes all relevant system info, logs, and configuration in a single file.

---

## 7. Tips and Best Practices

### Daily Use Tips

**Tip 1: Start the app at login**
- Enable **Settings > General > Launch on Windows startup**
- App loads in system tray, ready when you need it
- No manual launching before each presentation

**Tip 2: Use keyboard shortcuts**
- `Ctrl+P` - Quick power toggle
- `Ctrl+I` - Open input selector
- `Ctrl+B` - Toggle blank screen
- See [Section 8](#8-keyboard-shortcuts) for full list

**Tip 3: Check status before presentations**
- Verify Status Panel shows **Connected**
- Test power on/off 5 minutes before your meeting
- Allows time to troubleshoot if needed

**Tip 4: Monitor the History Panel**
- Glance at recent operations for red ✗ failed entries
- Patterns of failures indicate network or compatibility issues
- Contact IT if you see recurring problems

**Tip 5: Keep the app minimized**
- Minimize to system tray instead of closing
- Right-click system tray icon for instant power control
- Faster than opening the full window

---

### Presentation Workflow

**Before Your Presentation:**

1. **15 minutes before:**
   - Open the application (double-click system tray icon if minimized)
   - Verify Status Panel shows **Connected**
   - Run **Settings > Diagnostics > Run Network Test** if unsure

2. **10 minutes before:**
   - Click **Power On** and wait for warm-up
   - Select correct input source (HDMI1, HDMI2, etc.)
   - Verify your laptop screen appears on projector

3. **5 minutes before:**
   - Test **Blank Screen** button to confirm it works
   - Test **Freeze Display** if you plan to use it
   - Close the application window (leave running in system tray)

**During Your Presentation:**

- Use **Blank Screen** during breaks or transitions
- Use **Freeze Display** to pause video while explaining
- Access controls via system tray right-click menu (no need to open main window)

**After Your Presentation:**

1. Click **Power Off** (or right-click system tray and select Power Off)
2. Wait for cooling phase to complete (Status Panel shows "Cooling Down")
3. Once Status Panel shows "Off", you can disconnect your laptop

---

### Troubleshooting Quick Tips

**Problem: "Connection: Failed" in Status Panel**
- **Quick fix:** Check network cable or Wi-Fi connection
- **Verify:** Can you ping the projector IP address?
- **Try:** Settings > Connection > Test Connection Now
- **If persistent:** Contact IT administrator

**Problem: Commands are slow (>10 seconds)**
- **Quick fix:** Increase timeout in Settings > Connection > Command Timeout
- **Check:** Is your network congested? Try at off-peak time
- **Long-term:** Consider wired Ethernet instead of Wi-Fi

**Problem: "Authentication failed" error**
- **Quick fix:** Re-enter projector password in Settings > Connection > Edit
- **Verify:** Confirm password with IT administrator
- **Check:** Entropy file exists (see Security documentation)

**Problem: Input Source button shows limited options**
- **Quick fix:** This is normal - only shows inputs your projector supports
- **Not a bug:** Projectors vary in available inputs
- **Verify:** Check projector manual for supported inputs

**Problem: Window is off-screen after monitor change**
- **Quick fix:** Settings > Diagnostics > Reset Window Position
- **Alternative:** Alt+Space, M (Move), use arrow keys, press Enter

> **For more troubleshooting, see [Section 9](#9-troubleshooting) below.**

---

## 8. Keyboard Shortcuts

Save time with keyboard shortcuts for common operations.

### Global Shortcuts

| Shortcut | Action | Description |
|----------|--------|-------------|
| `Ctrl+,` | Open Settings | Open the Settings dialog |
| `Ctrl+Q` | Quit Application | Close the application completely |
| `F1` | Help | Open this user guide |
| `Alt+F4` | Close Window | Close main window (app stays in system tray) |

### Control Shortcuts

| Shortcut | Action | Description |
|----------|--------|-------------|
| `Ctrl+P` | Power Toggle | Toggle power on/off |
| `Ctrl+I` | Input Source | Open input source selector |
| `Ctrl+B` | Blank Screen | Toggle blank screen on/off |
| `Ctrl+F` | Freeze Display | Toggle freeze on/off |
| `Ctrl+M` | Mute Audio | Toggle audio mute (if enabled) |

### Navigation Shortcuts

| Shortcut | Action | Description |
|----------|--------|-------------|
| `Ctrl+H` | History Panel | Focus the History Panel |
| `Ctrl+S` | Status Panel | Focus the Status Panel |
| `Ctrl+1` through `Ctrl+9` | Quick Projector Switch | Switch to projector 1-9 (if multiple configured) |

### Window Management

| Shortcut | Action | Description |
|----------|--------|-------------|
| `Ctrl+N` | Minimize to Tray | Minimize to system tray |
| `Ctrl+R` | Restore Window | Restore from system tray (when focused on tray icon) |

> **Tip:** Press `F1` at any time to view this help guide!

> **Note:** Some shortcuts may be disabled if the corresponding feature is hidden in UI Buttons settings.

---

## 9. Troubleshooting

### Connection Problems

#### Symptom: "Cannot connect to projector" error

[Screenshot: Error dialog with red X icon. Title "Connection Error". Message: "Cannot connect to projector at 192.168.1.100:4352. Error: Connection timed out (110)." Three buttons: "Retry", "Test Network", "Cancel". Background slightly dimmed showing main window behind.]

**Step-by-step diagnostics:**

1. **Verify Network Connectivity**
   ```
   Open Command Prompt (Win+R, type "cmd", press Enter)
   Type: ping 192.168.1.100
   Press Enter
   ```
   - **Success:** "Reply from 192.168.1.100..." → Network is working, skip to step 3
   - **Failed:** "Request timed out" → Network issue, continue to step 2

2. **Check Network Connection**
   - Is your computer connected to the network? (Check Wi-Fi or Ethernet indicator)
   - Is the projector turned on? (Check physically)
   - Are you on the same network as the projector? (VPN can cause issues)
   - Try connecting to the network again

3. **Verify Projector IP Address**
   - Confirm IP address with IT administrator
   - Check if IP address changed (DHCP lease expired)
   - Try the projector's physical menu to verify network settings

4. **Check Firewall Rules**
   - Windows Firewall may be blocking TCP port 4352
   - Temporarily disable firewall to test (re-enable after testing!)
   - Contact IT to add firewall exception for port 4352

5. **Test PJLink Protocol**
   - Open Settings > Connection > Test Connection Now
   - If test fails, check error message for specific failure reason
   - Common errors:
     - "Connection refused" → Projector not accepting connections, check port
     - "Authentication failed" → Wrong password, check Settings > Connection > Edit
     - "Timeout" → Network issue, see steps 1-4 above

#### Symptom: "Connection: Unstable" shown frequently

**Causes:**
- Poor Wi-Fi signal strength
- Network congestion
- Firewall interfering with packets
- Projector's network card issues

**Solutions:**
- **Prefer wired Ethernet** over Wi-Fi for projector connection
- Increase timeout: Settings > Connection > Command Timeout to 15-20 seconds
- Enable automatic reconnection: Settings > Connection > Reliability > Enable automatic reconnection
- Contact IT to investigate network quality

#### Symptom: Connection works but commands fail

[Screenshot: History Panel showing multiple failed operations. Entries like "14:42:15 🔌 Power On → Failed ✗ Error: Command not supported", "14:40:33 📺 Input Changed to Component → Failed ✗ Error: Invalid input", "14:38:20 🔊 Volume Control → Failed ✗ Error: Feature not available".]

**Diagnosis:**
- Connection is successful (Status Panel shows "Connected")
- But specific commands fail with errors

**Causes:**
- **Incompatible projector model** - Not all projectors support all PJLink commands
- **Projector firmware outdated** - Update firmware (contact IT)
- **Wrong protocol type** - Using PJLink but projector expects native protocol

**Solutions:**
1. Verify projector model is compatible: Check [README.md](../../README.md) compatibility list
2. Try generic PJLink: Settings > Connection > Edit > Brand > "Other - PJLink Generic"
3. Update projector firmware: Contact IT administrator
4. Report compatibility issue: See [FAQ](../FAQ.md) for how to report issues

---

### Performance Issues

#### Symptom: Application takes >5 seconds to start

**Diagnosis:**
- Measure actual startup time using stopwatch
- Compare to target: <2 seconds

**Common causes:**
- Startup time includes network connection time
- Slow network DNS resolution
- Database file fragmentation (SQLite mode)
- Antivirus scanning executable on every launch

**Solutions:**
- **Disable network check on startup:** Settings > Connection > Uncheck "Connect to projectors on startup"
- **Exclude from antivirus:** Add `ProjectorControl.exe` to antivirus exclusion list (ask IT)
- **Use wired network:** Wi-Fi DNS lookups can be slow
- **Compact database:** Settings > Advanced > Maintenance > Compact Database (if available)

#### Symptom: Commands take >10 seconds to execute

**Diagnosis:**
- Check History Panel timestamps: note time between click and success/failure
- Compare to target: <5 seconds

**Common causes:**
- Network latency (Wi-Fi, VPN, congestion)
- Projector slow to respond (old firmware)
- Timeout set too high (waiting full timeout period before retrying)

**Solutions:**
- Increase command timeout: Settings > Connection > Command Timeout to 15 seconds (gives projector more time)
- Reduce retry attempts: Settings > Connection > Retry attempts to 1 (fail faster instead of retrying)
- Test network latency: Settings > Diagnostics > Run Network Test (check ping time)
- Use wired Ethernet: Eliminates Wi-Fi latency

#### Symptom: Application uses excessive memory (>200 MB)

**Diagnosis:**
- Open Task Manager (Ctrl+Shift+Esc)
- Find "ProjectorControl.exe" in Processes tab
- Check memory usage (target: <150 MB)

**Common causes:**
- Large operation history (thousands of entries)
- Memory leak (rare, contact support)
- Debug mode enabled (generates large logs)

**Solutions:**
- Clear history: Settings > Diagnostics > Clear History Cache
- Disable debug mode: Settings > Advanced > Developer Options > Uncheck "Enable debug mode"
- Restart application: Close and reopen to free memory
- If persistent: Export diagnostic report and contact support

---

### Password and Security Issues

#### Symptom: "Authentication failed" when connecting to projector

**Diagnosis:**
- Error message: "Authentication failed" or "Invalid password"
- Connection otherwise successful (ping works, port reachable)

**Causes:**
- Wrong password entered in Settings
- Password changed on projector but not updated in app
- Entropy file missing (cannot decrypt stored password)

**Solutions:**
1. **Re-enter password:**
   - Settings > Connection > Edit (projector)
   - Enter password in "Password" field
   - Click Test Connection to verify
   - Click Save

2. **Verify password with IT:**
   - Confirm correct password with administrator
   - Projector password may have been changed

3. **Check entropy file exists:**
   - Entropy file location: `%APPDATA%\ProjectorControl\.projector_entropy`
   - If missing: Password cannot be decrypted, must re-enter all projector passwords
   - See [Backup and Disaster Recovery](../deployment/DEPLOYMENT_GUIDE.md#10-backup-and-disaster-recovery)

#### Symptom: Forgot admin password

**Unfortunately, there is NO recovery option.**

**What this means:**
- You cannot open Settings
- You cannot change any configuration
- You cannot add/edit/remove projectors

**Your options:**
1. **If you remember the password:** Try typing it carefully (check Caps Lock)
2. **If you have a backup:** Restore from backup (includes admin password)
3. **If no backup:** You must reinstall:
   - Close application
   - Delete application data: `%APPDATA%\ProjectorControl`
   - Delete entropy file: `%APPDATA%\ProjectorControl\.projector_entropy`
   - Launch application - first-run wizard starts
   - Reconfigure everything from scratch

> **Prevention:** Write down your admin password and store it securely! Consider using a password manager.

---

### Display and UI Issues

#### Symptom: Window is off-screen or partially visible

**Common after:**
- Disconnecting external monitor
- Changing display resolution
- Switching from docking station to laptop screen

**Quick fix:**
1. Settings > Diagnostics > Reset Window Position
2. OR use keyboard:
   - Click application in taskbar to select it
   - Press `Alt+Space`
   - Press `M` (Move)
   - Use arrow keys to move window
   - Press `Enter` when visible

#### Symptom: Text is too small or too large (DPI scaling)

**Diagnosis:**
- Text appears blurry
- UI elements are abnormally large or small
- Buttons are cut off

**Causes:**
- Windows DPI scaling (125%, 150%, 200%)
- Application not DPI-aware

**Solutions:**
- **Restart application:** Close completely and reopen (DPI detected on startup)
- **Check Windows DPI settings:**
  - Right-click desktop > Display settings
  - Check "Scale and layout" setting
  - Application supports 100%-400% DPI
- **If blurry:** Right-click `ProjectorControl.exe` > Properties > Compatibility > Change high DPI settings > Override high DPI scaling behavior

#### Symptom: Hebrew text displays incorrectly (RTL issues)

[Screenshot: Main window in Hebrew with RTL layout issue. Shows some text aligned left instead of right, or mixed text direction. Example: buttons showing English text on right side and Hebrew text on left side, instead of properly mirrored layout.]

**Diagnosis:**
- Hebrew text appears but layout is incorrect
- Text aligned wrong direction
- Icons not mirrored

**Causes:**
- Windows regional settings not set to Hebrew
- Font rendering issue

**Solutions:**
- **Check language selection:** Settings > General > Language > Select "עברית Hebrew"
- **Restart application:** Close and reopen to re-apply RTL layout
- **Verify Windows language pack:** Windows Settings > Time & Language > Language > Add Hebrew if missing
- If persistent: Report bug with screenshot (see [FAQ](../FAQ.md))

---

### Getting Help

If you've tried the troubleshooting steps above and still have issues:

**1. Check the FAQ**
- Read [FAQ.md](../FAQ.md) for quick answers
- Search for your specific error message

**2. Collect diagnostic information**
- Settings > Diagnostics > Export Diagnostic Report
- Saves a file with all system info, logs, and configuration
- Email this file to your IT administrator or support contact

**3. Check application logs**
- Settings > Advanced > Logging > Open Log Folder
- Look at most recent `.log` file
- Search for "ERROR" or "FAIL" entries

**4. Contact IT Administrator**
- Provide diagnostic report (from step 2)
- Describe what you were doing when problem occurred
- Include screenshots if applicable

**5. Report a bug**
- See [FAQ](../FAQ.md) "How do I report a bug?"
- Include diagnostic report, screenshots, steps to reproduce

---

## Appendix A: Glossary

**PJLink**
- Industry-standard network protocol for controlling projectors
- Uses TCP port 4352
- Supported by most major projector brands

**System Tray**
- Windows notification area (bottom-right corner of taskbar)
- Shows background applications
- Access via small arrow icon if hidden

**DPAPI (Data Protection API)**
- Windows built-in encryption system
- Used to encrypt projector passwords
- Requires entropy file for decryption

**Entropy File**
- Special file (`.projector_entropy`) used for encryption
- Located at `%APPDATA%\ProjectorControl\.projector_entropy`
- Must be backed up or encrypted passwords are lost

**SQLite**
- Standalone database mode
- Stores data in a single file on your computer
- No network database required

**SQL Server**
- Enterprise database mode
- Stores data on central server
- Multiple computers share configuration

**RTL (Right-to-Left)**
- Text direction for Hebrew and other languages
- UI layout mirrors (menus on right side instead of left)

**DPI (Dots Per Inch)**
- Screen resolution scaling
- Higher DPI = smaller pixels, sharper display
- Windows scaling: 100% (96 DPI), 125%, 150%, 200%, etc.

---

## Appendix B: File Locations

**Application Data:**
- `%APPDATA%\ProjectorControl\` - Main data folder
- `%APPDATA%\ProjectorControl\projector_control.db` - Database file (SQLite mode)
- `%APPDATA%\ProjectorControl\.projector_entropy` - Encryption entropy file
- `%APPDATA%\ProjectorControl\backups\` - Backup files

**Log Files:**
- `%APPDATA%\ProjectorControl\logs\` - Application logs
- `app.log` - Current session log
- `app.log.1`, `app.log.2`, etc. - Rotated older logs

**Configuration:**
- `%APPDATA%\ProjectorControl\config.ini` - User preferences

**Windows Startup:**
- `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\ProjectorControl.lnk` - Startup shortcut (if enabled)

> **Note:** `%APPDATA%` typically expands to `C:\Users\YourUsername\AppData\Roaming\`

---

## Appendix C: System Requirements

For complete system requirements, see [README.md](../../README.md#system-requirements).

**Minimum:**
- Windows 10 (64-bit)
- 4 GB RAM
- 100 MB disk space
- Network connectivity to projector

**Recommended:**
- Windows 11 (64-bit)
- 8 GB RAM
- Wired Ethernet connection to projector network

**Supported Projector Brands:**
- Verified: EPSON, Hitachi
- Expected Compatible: Panasonic, Sony, BenQ, NEC, JVC, Christie, InFocus
- Requirement: PJLink Class 1 or Class 2 support

---

## Appendix D: Version History

**Version 1.0** (Current)
- Corresponds to application version 2.0.0-rc2
- First complete user guide
- Covers all core features

**Future Updates:**
- This guide will be updated as new application features are added
- Check [README.md](../../README.md) for latest application version

---

**End of User Guide**

For additional resources:
- **[FAQ](../FAQ.md)** - Quick answers to common questions
- **[Deployment Guide](../deployment/DEPLOYMENT_GUIDE.md)** - For IT administrators
- **[README](../../README.md)** - Technical specifications
- **[Security Documentation](../../SECURITY.md)** - Security architecture

*User Guide Version 1.0*
*Last Updated: February 12, 2026*
*Compatible with Enhanced Projector Control Application v2.0.0-rc2 and later*
