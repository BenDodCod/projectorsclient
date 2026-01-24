# PJLink Testing Guide for Hitachi CP-EX301N/CP-EX302N

**Projector IP:** 192.168.19.207
**Current Status:** Authentication required, password unknown

---

## Current Situation

The projector has PJLink authentication **enabled**, but we're getting `PJLINK ERRA` (authentication error) with the tested password "12345678".

**Symptoms:**
```
Received: 'PJLINK 1 3067e208\r'  ← Authentication required (salt: 3067e208)
RX: 'PJLINK ERRA\r'                ← Authentication failed
```

**Root Cause:** The password "12345678" is likely for the **web interface** (Administrator login), not for **PJLink protocol** specifically.

---

## Two Paths Forward

### Path A: Find Correct PJLink Password (Recommended)

**Steps:**

1. **Access Projector Menu:**
   - Press MENU button on projector remote
   - Navigate to: OPTION → SECURITY → NETWORK CONTROL
   - Look for "Authentication Password" or "PJLink Password"

2. **Check Web Interface:**
   - Open browser: `http://192.168.19.207`
   - Login with Administrator/12345678
   - Navigate to Security Settings or Network Settings
   - Look for "PJLink Authentication Password" (may be different from web password)

3. **Try Common Default Passwords:**
   ```bash
   # Empty password (no authentication despite being enabled)
   python tools\test_hitachi_pjlink.py --host 192.168.19.207 --password ""

   # Common defaults
   python tools\test_hitachi_pjlink.py --host 192.168.19.207 --password admin
   python tools\test_hitachi_pjlink.py --host 192.168.19.207 --password password
   python tools\test_hitachi_pjlink.py --host 192.168.19.207 --password pjlink
   python tools\test_hitachi_pjlink.py --host 192.168.19.207 --password 0000
   ```

4. **Test with Correct Password:**
   ```bash
   python tools\test_hitachi_pjlink.py --host 192.168.19.207 --password YOUR_PASSWORD
   ```

---

### Path B: Disable Authentication Temporarily (Quick Test)

**Purpose:** Verify PJLink protocol works without authentication complexity.

**Steps:**

1. **Access Projector Web Interface:**
   - Browser: `http://192.168.19.207`
   - Login: Administrator / 12345678

2. **Disable PJLink Authentication:**
   - Navigate to: Port Settings → PJLink Port (Port:4352)
   - **Uncheck** "Authentication" checkbox
   - Click "Apply" or "Save"
   - May need to restart network or projector

3. **Test Without Authentication:**
   ```bash
   python tools\test_hitachi_pjlink.py --host 192.168.19.207 --password ""
   ```

4. **Expected Result (if working):**
   ```
   [1/3] Connecting to 192.168.19.207:4352...
         Received: 'PJLINK 0\r'
         ✓ No authentication required

   [2/3] Testing PJLink Commands

   [CMD] Query Power Status
         TX: '%1POWR ?\r'
         RX: '%1POWR=0\r'  or  '%1POWR=1\r'
         ✓ Success: %1POWR=0
   ```

5. **Re-enable Authentication After Testing:**
   - Go back to Port Settings
   - Check "Authentication" checkbox
   - Set a known password
   - Save settings

---

## Expected Test Output (Success)

When PJLink is working correctly, you should see:

```
======================================================================
Hitachi PJLink Verification Test
======================================================================
Target: 192.168.19.207:4352
Protocol: PJLink Class 1
======================================================================

[1/3] Connecting to 192.168.19.207:4352...
      Received: 'PJLINK 0\r'
      ✓ No authentication required

[2/3] Testing PJLink Commands
----------------------------------------------------------------------

[CMD] Query Power Status
      TX: '%1POWR ?\r'
      RX: '%1POWR=0\r'
      ✓ Success: %1POWR=0

[CMD] Query Input Source
      TX: '%1INPT ?\r'
      RX: '%1INPT=31\r'
      ✓ Success: %1INPT=31

[CMD] Query Audio/Video Mute
      TX: '%1AVMT ?\r'
      RX: '%1AVMT=30\r'
      ✓ Success: %1AVMT=30

...

[3/3] Connection closed

======================================================================
TEST SUMMARY
======================================================================
Total Tests: 10
Passed: 10 (100.0%)
Failed: 0 (0.0%)

✓ ALL TESTS PASSED - PJLink protocol fully functional

RECOMMENDATION: Use PJLink as primary protocol for Hitachi projectors
```

---

## Troubleshooting

### Issue: Still Getting ERRA with Empty Password

**Possible Causes:**
1. Authentication truly required (projector enforces password)
2. Need to disable auth in projector settings first

**Solution:**
- Use Path B to disable authentication in projector settings
- Verify "Authentication" checkbox is unchecked

---

### Issue: Connection Timeout

```
✗ Connection timeout
```

**Possible Causes:**
1. Wrong IP address
2. Projector network settings changed
3. Firewall blocking connection

**Solutions:**
1. Verify IP: `ping 192.168.19.207`
2. Check projector network menu: OPTION → NETWORK → TCP/IP
3. Verify PJLink port is 4352 in projector settings

---

### Issue: Connection Refused

```
[Errno 10061] No connection could be made
```

**Possible Causes:**
1. PJLink service disabled
2. Wrong port number
3. Projector off or in standby

**Solutions:**
1. Check projector Port Settings → PJLink Port is enabled
2. Verify port is 4352
3. Ensure projector is powered on (standby mode usually still responds)

---

## Next Steps After Successful Test

Once PJLink is confirmed working:

1. **Update Controller Factory:**
   - File: `src/core/controller_factory.py`
   - Add automatic PJLink fallback for Hitachi brand

2. **Update UI:**
   - File: `src/ui/dialogs/projector_dialog.py`
   - Add tooltip recommending PJLink for Hitachi

3. **Create Integration Tests:**
   - File: `tests/integration/test_hitachi_pjlink_fallback.py`
   - Use real PJLink responses from successful test

4. **Document Solution:**
   - Update `ROADMAP.md` with findings
   - Update `docs/protocols/HITACHI.md` with PJLink recommendation

---

## Quick Reference

| Scenario | Command |
|----------|---------|
| Test with password | `python tools\test_hitachi_pjlink.py --host 192.168.19.207 --password YOUR_PASSWORD` |
| Test without auth | `python tools\test_hitachi_pjlink.py --host 192.168.19.207 --password ""` |
| Test default values | `python tools\test_hitachi_pjlink.py` (uses 192.168.19.207, empty password) |

---

**Questions?** Refer to `tools/README_HITACHI_DIAGNOSTIC.md` for full diagnostic toolkit documentation.
