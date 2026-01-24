# Hitachi CP-EX301N/CP-EX302N Protocol Debugging Results

**Model:** Hitachi CP-EX301N / CP-EX302N
**Projector IP:** 192.168.19.207
**Test Date:** [To be filled during testing]
**Tester:** [Name]

---

## Executive Summary

**Issue:** Hitachi native protocol commands timeout on all ports (23, 9715) despite successful TCP connection.

**Working Alternative:** PJLink protocol on port 4352 works correctly.

**Root Cause:** [To be determined during testing]

**Resolution:** [To be determined]

---

## Test Environment

- **Projector Model:** CP-EX301N / CP-EX302N
- **Projector IP:** 192.168.19.207
- **Firmware Version:** [Check during testing]
- **Network:** Direct Ethernet connection
- **Test Tools:**
  - `tools/hitachi_diagnostic.py` - Main diagnostic script
  - `tools/hitachi_crc_validator.py` - CRC validation
  - `tools/hitachi_traffic_capture.py` - Traffic capture
- **Documentation Reference:** `docs/Hitachi_CP-EX301N_CP-EX302N_Complete_Control_Documentation.md`

---

## Test Results

### Phase 1: Pre-Test Verification

#### Network Connectivity
- [ ] Ping test successful
- [ ] PJLink port 4352 confirmed working
- [ ] Port 23 TCP connection successful
- [ ] Port 9715 TCP connection successful (if testing)

#### PJLink Baseline (Control Test)
```
Command: %1POWR ?\r
Response: [Fill in]
Result: [PASS/FAIL]
Notes: [Observations]
```

---

### Phase 2: Official Commands Test (Port 23)

Run: `python hitachi_diagnostic.py --host 192.168.19.207 --port 23`

#### Results Table

| # | Command | Official Hex | Status | Response | Duration | Notes |
|---|---------|-------------|--------|----------|----------|-------|
| 1 | Power Query | `BEEF03060019D30200006000 00` | [PASS/FAIL/TIMEOUT] | [hex bytes or timeout] | [time]s | [notes] |
| 2 | Get Input | `BEEF030600CDD20200002000 00` | [PASS/FAIL/TIMEOUT] | [hex bytes or timeout] | [time]s | [notes] |
| 3 | Mute Query | `BEEF03060075D30200022000 00` | [PASS/FAIL/TIMEOUT] | [hex bytes or timeout] | [time]s | [notes] |
| 4 | Freeze Query | `BEEF030600B0D20200023000 00` | [PASS/FAIL/TIMEOUT] | [hex bytes or timeout] | [time]s | [notes] |
| 5 | Get Brightness | `BEEF030600 89D20200032000 00` | [PASS/FAIL/TIMEOUT] | [hex bytes or timeout] | [time]s | [notes] |

#### Summary
- **Total Tests:** 5
- **Successful:** [count]
- **Timeouts:** [count]
- **Errors:** [count]

#### Decision Point
- [ ] At least one command got a response → Continue to Phase 3 (fix implementation)
- [ ] All commands timeout → Continue to Phase 3 (CRC variations)

---

### Phase 3: CRC Variation Testing

**If all official commands timeout, test CRC variations:**

Run: `python hitachi_crc_validator.py`

#### CRC Algorithm Validation Results

| Algorithm | Match Rate | Notes |
|-----------|-----------|-------|
| Official (from doc) | 100% (baseline) | Pre-calculated values |
| Current Proprietary | [%] | Reverse-engineered formula |
| CRC-16-CCITT | [%] | Standard polynomial 0x1021 |
| Modbus CRC-16 | [%] | Polynomial 0xA001 |
| XMODEM CRC-16 | [%] | Alternative standard |
| Sum Checksum | [%] | Simple sum-based |

#### CRC Test with Projector

Test Power Query with different CRC algorithms:

| CRC Type | Command Hex | Response | Status |
|----------|-------------|----------|--------|
| Original (doc) | `BEEF03060019D30200006000 00` | [response] | [PASS/TIMEOUT] |
| Zero CRC | `BEEF0306000000020000600000` | [response] | [PASS/TIMEOUT] |
| Inverted CRC | `BEEF030600D31902000060 0000` | [response] | [PASS/TIMEOUT] |
| Std CRC-16 | `BEEF030600[XX XX]0200006000 00` | [response] | [PASS/TIMEOUT] |

#### Decision Point
- [ ] CRC variation got response → Identify correct algorithm
- [ ] All CRC variations timeout → Continue to Phase 4

---

### Phase 4: Byte Order Testing

Test byte order variations for Power Query command:

| Variation | Bytes Modified | Command Hex | Response | Status |
|-----------|---------------|-------------|----------|--------|
| Original | None | `BEEF03060019D30200006000 00` | [response] | [PASS/TIMEOUT] |
| Swap Action | Bytes 7-8 | `BEEF03060019D30002006000 00` | [response] | [PASS/TIMEOUT] |
| Swap Type | Bytes 9-10 | `BEEF03060019D30200600000 00` | [response] | [PASS/TIMEOUT] |
| Swap Data | Bytes 11-12 | `BEEF03060019D30200006000 00` | [response] | [PASS/TIMEOUT] |

#### Decision Point
- [ ] Byte order variation got response → Document correct byte order
- [ ] All variations timeout → Continue to Phase 5

---

### Phase 5: Port 9715 Framing Test

**Test with Network Bridge framing format:**

Run: `python hitachi_diagnostic.py --host 192.168.19.207 --port 9715 --framed`

Frame structure:
```
Byte 0:      02h (Header)
Byte 1:      0Dh (Length = 13)
Bytes 2-14:  [13-byte RS-232 command]
Byte 15:     [Checksum]
Byte 16:     [Connection ID]
```

#### Results

| Command | Framed Hex | Response | Status | Notes |
|---------|-----------|----------|--------|-------|
| Power Query | `020D[BEEF...][CS]01` | [response] | [PASS/TIMEOUT] | [notes] |
| Get Input | `020D[BEEF...][CS]01` | [response] | [PASS/TIMEOUT] | [notes] |

#### Decision Point
- [ ] Port 9715 works → Update default port to 9715
- [ ] Port 9715 also timeouts → Continue to Phase 6

---

### Phase 6: Network Traffic Analysis

Run: `python hitachi_traffic_capture.py --host 192.168.19.207 --capture both --compare`

#### Comparison Results

**PJLink (Port 4352):**
- Connection: [SUCCESS/FAIL]
- Commands tested: [count]
- Response time: [ms]
- Status: [WORKING/FAILED]

**Native Protocol (Port 23):**
- Connection: [SUCCESS/FAIL]
- Commands tested: [count]
- Response time: [TIMEOUT/ms]
- Status: [WORKING/FAILED]

#### Packet Analysis

[Insert hex dump comparison or observations]

**Differences Identified:**
1. [Observation 1]
2. [Observation 2]
3. [Observation 3]

---

## Root Cause Analysis

### Findings

**Primary Issue:** [Describe root cause]

**Evidence:**
1. [Evidence 1]
2. [Evidence 2]
3. [Evidence 3]

**Contributing Factors:**
- [Factor 1]
- [Factor 2]

---

## Resolution

### Option A: Fix Implementation (if protocol works)

**Changes Required:**
1. [Change 1 with file reference]
2. [Change 2 with file reference]
3. [Change 3 with file reference]

**Testing Plan:**
1. [Test step 1]
2. [Test step 2]
3. [Test step 3]

### Option B: Document Limitation (if protocol doesn't work)

**Limitation:** CP-EX301N/CP-EX302N native protocol [describe limitation]

**Recommended Solution:**
- Use PJLink protocol (port 4352) as primary control method
- Document in UI/manual that PJLink is recommended for this model
- Add automatic fallback logic to PJLink if native commands timeout

**Implementation:**
1. Update projector dialog to recommend PJLink for Hitachi models
2. Add tooltip explaining native protocol limitation
3. Update documentation in `docs/protocols/HITACHI.md`
4. Update ROADMAP.md to mark native protocol as "model-specific"

---

## Recommendations

### Immediate Actions

1. [Action 1]
2. [Action 2]
3. [Action 3]

### Long-term Improvements

1. [Improvement 1]
2. [Improvement 2]
3. [Improvement 3]

---

## Appendix

### Test Commands Used

```python
# Official Commands from Documentation
POWER_QUERY = "BEEF03060019D30200006000 00"
INPUT_QUERY = "BEEF030600CDD20200002000 00"
MUTE_QUERY = "BEEF03060075D30200022000 00"

# PJLink Commands
PJLINK_POWER = "%1POWR ?\r"
PJLINK_INPUT = "%1INPT ?\r"
```

### Tool Output Files

- Diagnostic Report: `tools/diagnostic_results/hitachi_diagnostic_23_[timestamp].md`
- CRC Validation: `tools/diagnostic_results/hitachi_crc_validation.md`
- Traffic Capture: `tools/diagnostic_results/traffic/`
  - PJLink session: `pjlink_session_[timestamp].txt`
  - Native session: `native_session_[timestamp].txt`
  - Comparison: `comparison_[timestamp].md`

### References

1. Official Documentation: `docs/Hitachi_CP-EX301N_CP-EX302N_Complete_Control_Documentation.md`
2. Implementation Plan: `docs/planning/MULTI_BRAND_PROJECTOR_SUPPORT_PLAN.md`
3. Current Implementation: `src/network/protocols/hitachi.py`
4. Controller: `src/core/controllers/hitachi_controller.py`

---

**Test Completed:** [Date/Time]
**Signed Off:** [Name]
**Next Steps:** [Action items]
