# UAT Test Scenarios

This document contains 7 test scenarios for User Acceptance Testing. Testers should complete each scenario and record their results.

**Instructions:**
1. Work through each scenario in order (unless marked as optional)
2. Check off each step as you complete it
3. Record your actual results in the "Actual Result" section
4. Note any issues in the feedback form
5. Scenarios 3 (Hebrew/RTL) is only for Hebrew speakers

---

## Scenario 1: First-Run Experience

**Objective:** New user can install and configure application without assistance

**Requirements Covered:** UI-02, I18N-01

**Priority:** Critical

**Estimated Time:** 5-10 minutes

### Prerequisites
- Downloaded ProjectorControl.exe
- Windows 10/11 system
- Network access to projector (if testing with real hardware)

### Steps

1. **Launch Application**
   - Double-click `ProjectorControl.exe`
   - [ ] Application launches without errors
   - [ ] First-run wizard appears automatically

2. **Language Selection**
   - [ ] Language selection page appears
   - [ ] English option available
   - [ ] Hebrew option available
   - Select your preferred language

3. **Admin Password Setup**
   - [ ] Password setup page appears
   - [ ] Password strength indicator visible
   - Create a password (minimum 8 characters)
   - [ ] Password accepted without errors

4. **Database Mode Selection**
   - [ ] Database mode page appears
   - [ ] SQLite (Standalone) option pre-selected
   - Keep SQLite selected for testing
   - [ ] Selection accepted

5. **Projector Configuration**
   - [ ] Projector setup page appears
   - Enter projector details:
     - Name: "Test Projector"
     - IP: [your projector IP or 192.168.1.100]
     - Port: 4352 (PJLink default)
     - Brand: [select your brand or EPSON]
   - [ ] Configuration saved

6. **Wizard Completion**
   - [ ] Summary/completion page appears
   - [ ] "Finish" button works
   - [ ] Main window appears after wizard

### Expected Result
- Wizard completes in under 5 minutes
- Main window shows configured projector
- No error messages or crashes

### Actual Result
| Metric | Result |
|--------|--------|
| Wizard completed | Yes / No |
| Time to complete | _____ minutes |
| Errors encountered | None / Describe: _____ |
| Main window visible | Yes / No |

### Notes
_Write any observations here:_

---

## Scenario 2: Basic Projector Control

**Objective:** User can control projector power reliably

**Requirements Covered:** UI-01, PERF-05

**Priority:** Critical

**Estimated Time:** 5-10 minutes

### Prerequisites
- Completed Scenario 1 (application configured)
- Projector accessible on network (or using mock mode)

### Steps

1. **Launch Application**
   - Open ProjectorControl.exe (if not already open)
   - [ ] Main window appears
   - [ ] Configured projector visible

2. **Check Status Display**
   - [ ] Status panel shows projector name
   - [ ] Power status indicator visible
   - [ ] Connection status shown

3. **Power On**
   - Click "Power On" button
   - [ ] Button is clearly visible
   - [ ] Button click responds immediately
   - Start timer when clicked
   - [ ] Status updates within 5 seconds
   - Stop timer when status shows "On"
   - Time elapsed: _____ seconds

4. **Verify Projector State**
   - [ ] Projector actually powered on (if real hardware)
   - [ ] Status display shows "On" state
   - [ ] No error messages

5. **Power Off**
   - Click "Power Off" button
   - [ ] Button responds immediately
   - Start timer when clicked
   - [ ] Status updates within 5 seconds
   - Stop timer when status shows "Off"
   - Time elapsed: _____ seconds

6. **Verify Power Off**
   - [ ] Projector powered off (if real hardware)
   - [ ] Status display shows "Off" state

### Expected Result
- Commands execute within 5 seconds
- Status updates correctly after each command
- History panel shows operations

### Actual Result
| Metric | Result |
|--------|--------|
| Power On successful | Yes / No / Error |
| Power On time | _____ seconds |
| Power Off successful | Yes / No / Error |
| Power Off time | _____ seconds |
| Status display accurate | Yes / No |

### Notes
_Write any observations here:_

---

## Scenario 3: Hebrew/RTL Mode

**Objective:** Hebrew users see correct RTL layout and translations

**Requirements Covered:** I18N-03, I18N-04, I18N-05

**Priority:** High

**Estimated Time:** 5-10 minutes

**Note:** This scenario is for Hebrew speakers only. English-only testers should skip this scenario.

### Prerequisites
- Application installed and running
- Hebrew language familiarity

### Steps

1. **Access Language Settings**
   - Open Settings (gear icon or menu)
   - OR: Re-run first-run wizard
   - [ ] Settings/Language option accessible

2. **Select Hebrew**
   - Select Hebrew (עברית) language
   - [ ] Hebrew option available
   - [ ] Selection confirmed

3. **Observe Layout Change**
   - [ ] Application layout changes to RTL
   - [ ] Menu items move to right side
   - [ ] Text alignment is right-to-left

4. **Check Text Translation**
   - [ ] All button labels in Hebrew
   - [ ] All menu items in Hebrew
   - [ ] Status messages in Hebrew
   - [ ] Error messages in Hebrew (if any appear)

5. **Check Icon Mirroring**
   - [ ] Directional icons (arrows, etc.) point correct direction
   - [ ] Icons are properly aligned in RTL layout

6. **Use Application in Hebrew**
   - Perform basic operations (power on/off)
   - [ ] Operations work correctly in Hebrew mode
   - [ ] No layout glitches or overlapping text

7. **Translation Quality**
   Rate translation accuracy:
   - [ ] All text understandable
   - [ ] No English text remaining (except brand names)
   - [ ] Grammar/spelling correct

### Expected Result
- All UI text displays in Hebrew
- RTL layout applied throughout application
- No layout glitches or visual issues
- Icons mirror correctly for RTL

### Actual Result
| Metric | Result |
|--------|--------|
| Hebrew text visible | Yes / No |
| RTL layout applied | Yes / No |
| Icons mirrored correctly | Yes / No |
| Translation quality | Good / Acceptable / Poor |
| Layout issues found | None / Describe: _____ |

### Notes
_Write any observations here:_

---

## Scenario 4: Input Source Switching

**Objective:** User can change projector input source

**Requirements Covered:** UI-01

**Priority:** High

**Estimated Time:** 3-5 minutes

### Prerequisites
- Completed Scenario 2
- Projector supports multiple inputs

### Steps

1. **Access Input Control**
   - Locate "Input" button or dropdown
   - [ ] Input control is visible and accessible

2. **View Available Inputs**
   - Click/open input selector
   - [ ] List of input sources appears
   - Available inputs shown:
     - [ ] HDMI1
     - [ ] HDMI2
     - [ ] VGA
     - [ ] Other: _____

3. **Switch Input**
   - Select a different input source
   - [ ] Selection responds immediately
   - Start timer
   - [ ] Input change confirmed within 5 seconds
   - Time elapsed: _____ seconds

4. **Verify Change**
   - [ ] Status panel shows new input source
   - [ ] Projector displays new input (if real hardware)

5. **Switch Back**
   - Return to original input
   - [ ] Change successful

### Expected Result
- Input changes within 5 seconds
- Status reflects correct input source
- No errors during switching

### Actual Result
| Metric | Result |
|--------|--------|
| Input switching works | Yes / No / Partial |
| Time to switch | _____ seconds |
| Status updates correctly | Yes / No |
| Errors encountered | None / Describe: _____ |

### Notes
_Write any observations here:_

---

## Scenario 5: Operation History

**Objective:** User can view and review past operations

**Requirements Covered:** UI-01, DB-01

**Priority:** Medium

**Estimated Time:** 3-5 minutes

### Prerequisites
- Completed Scenarios 2 and 4 (operations performed)

### Steps

1. **Locate History Panel**
   - [ ] History panel/tab visible in main window
   - [ ] History is easily accessible

2. **Review Operations**
   - [ ] Recent operations listed
   - [ ] Operations show timestamps
   - [ ] Operations show success/failure status
   - Operations visible:
     - [ ] Power On
     - [ ] Power Off
     - [ ] Input Change

3. **Check Details**
   - Select an operation entry (if clickable)
   - [ ] Details viewable (if applicable)
   - [ ] Timestamps are accurate (match when you performed actions)

4. **History Scrolling**
   - If many entries, scroll through list
   - [ ] Scrolling works smoothly
   - [ ] Older entries accessible

### Expected Result
- History shows all recent operations
- Timestamps are accurate
- Success/failure clearly indicated

### Actual Result
| Metric | Result |
|--------|--------|
| History visible | Yes / No |
| Operations listed | Yes / No / Partial |
| Timestamps accurate | Yes / No |
| UI responsive | Yes / No |

### Notes
_Write any observations here:_

---

## Scenario 6: Application Startup Performance

**Objective:** Application starts quickly

**Requirements Covered:** PERF-04

**Priority:** High

**Estimated Time:** 2-3 minutes

### Prerequisites
- Application was previously configured (Scenario 1 complete)

### Steps

1. **Close Application**
   - Close the application completely
   - [ ] Application closes cleanly
   - [ ] No hanging processes (check Task Manager if unsure)

2. **Cold Start Test**
   - Have a stopwatch or timer ready
   - Double-click ProjectorControl.exe
   - Start timer immediately on click
   - Stop timer when main window is fully visible and responsive
   - Time: _____ seconds

3. **Verify State Preservation**
   - [ ] Previous settings preserved
   - [ ] Configured projector still visible
   - [ ] Language setting retained

4. **Second Start Test**
   - Close and reopen application again
   - Time: _____ seconds
   - [ ] Consistent with first test

### Expected Result
- Startup time under 2 seconds
- Previous settings preserved
- Application immediately usable

### Actual Result
| Metric | Result |
|--------|--------|
| Cold start time | _____ seconds |
| Second start time | _____ seconds |
| Target met (<2 sec) | Yes / No |
| Settings preserved | Yes / No |

### Notes
_Write any observations here:_

---

## Scenario 7: Settings Backup and Restore

**Objective:** User can backup and restore application settings

**Requirements Covered:** DB-03

**Priority:** Medium

**Estimated Time:** 5-10 minutes

### Prerequisites
- Application configured with settings worth backing up

### Steps

1. **Note Current Settings**
   - Record your current configuration:
     - Projector name: _____
     - Language: _____
     - Other settings: _____

2. **Create Backup**
   - Navigate to Settings > Backup (or similar)
   - [ ] Backup option accessible
   - Click backup/export
   - [ ] File save dialog appears
   - Save backup file
   - [ ] Backup file created
   - File location: _____

3. **Verify Backup File**
   - [ ] File exists at specified location
   - [ ] File has reasonable size (not 0 bytes)
   - [ ] File is encrypted (cannot read as plain text)

4. **Simulate Data Loss (Optional)**
   - If comfortable: Delete/rename the app data folder
   - OR: Skip to step 5 and just verify restore works

5. **Restore from Backup**
   - Navigate to Settings > Restore (or similar)
   - [ ] Restore option accessible
   - Select your backup file
   - [ ] Restore process starts
   - [ ] Restore completes successfully

6. **Verify Restored Settings**
   - [ ] Projector configuration restored
   - [ ] Language setting restored
   - [ ] Other settings restored
   - [ ] Application functions normally

### Expected Result
- Backup creates encrypted file
- Restore recovers all settings
- Application works normally after restore

### Actual Result
| Metric | Result |
|--------|--------|
| Backup created | Yes / No |
| Backup encrypted | Yes / No / Unsure |
| Restore successful | Yes / No |
| All settings recovered | Yes / No / Partial |
| Errors encountered | None / Describe: _____ |

### Notes
_Write any observations here:_

---

## Scenario Completion Summary

After completing all applicable scenarios, fill in this summary:

| Scenario | Completed | Pass/Fail | Time (min) | Issues Found |
|----------|-----------|-----------|------------|--------------|
| 1. First-Run | Yes/No | P/F | | |
| 2. Basic Control | Yes/No | P/F | | |
| 3. Hebrew/RTL | Yes/No/NA | P/F | | |
| 4. Input Switch | Yes/No | P/F | | |
| 5. History | Yes/No | P/F | | |
| 6. Startup | Yes/No | P/F | | |
| 7. Backup | Yes/No | P/F | | |

**Total Time:** _____ minutes

**Overall Assessment:**
- [ ] All scenarios passed - Ready for release
- [ ] Minor issues found - Acceptable for release with fixes
- [ ] Major issues found - Not ready for release

---

*Scenarios document created: 2026-01-17*
*For use with Projector Control v1.0 UAT*
