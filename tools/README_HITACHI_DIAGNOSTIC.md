# Hitachi CP-EX301N/CP-EX302N Diagnostic Tools

Comprehensive diagnostic toolkit for testing and debugging Hitachi native protocol with physical projectors.

---

## Quick Start

### Prerequisites

- Python 3.8+
- Network access to Hitachi projector
- Projector IP address: **192.168.19.207**

### Running the Complete Diagnostic

```bash
# Navigate to project root
cd d:\projectorsclient

# Run full diagnostic on port 23 (raw mode)
python tools/hitachi_diagnostic.py --host 192.168.19.207 --port 23 --all-tests --verbose

# Run CRC validation
python tools/hitachi_crc_validator.py

# Capture and compare network traffic
python tools/hitachi_traffic_capture.py --host 192.168.19.207 --capture both --compare
```

---

## Tool Overview

### 1. `hitachi_diagnostic.py` - Main Diagnostic Script

**Purpose:** Systematically test Hitachi native protocol commands with physical projector.

**Features:**
- Send exact commands from official documentation
- Test CRC variations automatically
- Test byte order variations
- Support for both port 23 (raw) and port 9715 (framed)
- Generate comprehensive test reports

#### Usage Examples

```bash
# Test port 23 with official commands only
python tools/hitachi_diagnostic.py --host 192.168.19.207 --port 23

# Test port 9715 with framing
python tools/hitachi_diagnostic.py --host 192.168.19.207 --port 9715 --framed

# Run complete test suite (recommended)
python tools/hitachi_diagnostic.py --host 192.168.19.207 --all-tests --verbose

# Test single command
python tools/hitachi_diagnostic.py --host 192.168.19.207 --port 23 --command "Power Query"
```

#### Output

```
[2026-01-24 10:30:45] INFO: Hitachi Diagnostic Tool initialized
[2026-01-24 10:30:45] INFO: Target: 192.168.19.207:23
[2026-01-24 10:30:45] INFO: Mode: Raw
[2026-01-24 10:30:45] INFO: Timeout: 5.0s
[2026-01-24 10:30:45] INFO: Connecting to 192.168.19.207:23...
[2026-01-24 10:30:45] INFO: ✓ Connection established in 0.045s

======================================================================
TEST: Power Query
======================================================================
  TX (13 bytes): BE EF 03 06 00 19 D3 02 00 00 60 00 00
  RX: Timeout after 5.0s
Result: ✗ TIMEOUT - No response received
Duration: 5.003s

...

✓ Report generated: tools/diagnostic_results/hitachi_diagnostic_23_20260124_103050.md
```

#### Output Files

Reports saved to: `tools/diagnostic_results/`

- `hitachi_diagnostic_23_[timestamp].md` - Full test results
- Markdown format with summary statistics
- Detailed results for each test
- Recommendations based on findings

---

### 2. `hitachi_crc_validator.py` - CRC Validation Tool

**Purpose:** Validate CRC calculations against official documentation and identify correct algorithm.

**Features:**
- Compare 6 different CRC algorithms
- Test against 9 known-good commands from documentation
- Generate lookup table
- Identify which algorithm matches official values

#### Usage

```bash
# Run validation and generate report
python tools/hitachi_crc_validator.py
```

#### Output

```
================================================================================
Hitachi CRC Validation Report
================================================================================

Testing 9 known-good commands from documentation

────────────────────────────────────────────────────────────────────────────────
Algorithm: Official (from doc)
Match Rate: 9/9 (100.0%)
────────────────────────────────────────────────────────────────────────────────
✓ PERFECT MATCH - This is likely the correct algorithm!

────────────────────────────────────────────────────────────────────────────────
Algorithm: Current Proprietary
Match Rate: 7/9 (77.8%)
────────────────────────────────────────────────────────────────────────────────
⚠ PARTIAL MATCH - 7 commands match, investigate pattern

Mismatches:
  • Power ON        | Expected: 0xD2BA | Got: 0xD2BC
  • Mute ON         | Expected: 0xD2D6 | Got: 0xD2D4

...

================================================================================
RECOMMENDATION
================================================================================

✓ Use algorithm: Official (from doc)

This algorithm matches ALL 9 official commands from documentation.

✓ Report saved to: tools/diagnostic_results/hitachi_crc_validation.md
```

#### Interpretation

- **100% match:** Algorithm is correct
- **>50% match:** Algorithm close, may need tweaking
- **<50% match:** Wrong algorithm, try different approach
- **0% match:** Algorithm completely wrong

---

### 3. `hitachi_traffic_capture.py` - Network Traffic Capture

**Purpose:** Capture and compare working PJLink vs. failing native protocol traffic.

**Features:**
- Capture PJLink session (port 4352)
- Capture native protocol session (port 23)
- Generate comparison report
- Identify packet-level differences

#### Usage

```bash
# Capture both protocols and generate comparison
python tools/hitachi_traffic_capture.py --host 192.168.19.207 --capture both --compare

# Capture PJLink only
python tools/hitachi_traffic_capture.py --host 192.168.19.207 --capture pjlink

# Capture native protocol only
python tools/hitachi_traffic_capture.py --host 192.168.19.207 --capture native
```

#### Output

```
Hitachi Traffic Capture Tool
Target: 192.168.19.207
Output: tools/diagnostic_results/traffic

======================================================================
Capturing PJLink Session (Port 4352)
======================================================================

Testing: Query Power Status
Command: '%1POWR ?\r'
  Initial: 'PJLINK 0\r'
  TX (9 bytes): 25 31 50 4F 57 52 20 3F 0D
  RX (11 bytes): 25 31 50 4F 57 52 3D 30 0D
  Response: '%1POWR=0\r'
  ✓ SUCCESS

...

✓ PJLink capture saved to: tools/diagnostic_results/traffic/pjlink_session_20260124_103100.txt

======================================================================
Capturing Native Protocol Session (Port 23)
======================================================================

Testing: Power Query
Command: BEEF03060019D30200006000 00
  TX (13 bytes): BE EF 03 06 00 19 D3 02 00 00 60 00 00
  ✗ TIMEOUT (no response)

...

✓ Comparison report saved to: tools/diagnostic_results/traffic/comparison_20260124_103105.md
```

---

## Testing Workflow

### Recommended Test Sequence

```bash
# Step 1: Verify network connectivity
ping 192.168.19.207

# Step 2: Baseline test (PJLink works)
python tools/hitachi_traffic_capture.py --host 192.168.19.207 --capture pjlink

# Step 3: Run CRC validation
python tools/hitachi_crc_validator.py

# Step 4: Full diagnostic on port 23
python tools/hitachi_diagnostic.py --host 192.168.19.207 --port 23 --all-tests --verbose

# Step 5: If port 23 fails, try port 9715
python tools/hitachi_diagnostic.py --host 192.168.19.207 --port 9715 --framed --all-tests

# Step 6: Capture both protocols for comparison
python tools/hitachi_traffic_capture.py --host 192.168.19.207 --capture both --compare
```

### Interpreting Results

**Scenario A: At least one command gets a response**
- ✓ Protocol is working (partially or fully)
- Action: Identify which command format worked
- Next: Update implementation with correct CRC/byte order
- File issue as: "Implementation bug - wrong CRC algorithm"

**Scenario B: All commands timeout on port 23**
- ⚠ Port 23 may not be supported
- Action: Test port 9715 with framing
- Next: If 9715 works, update default port
- File issue as: "Port 23 unsupported on CP-EX301N"

**Scenario C: All ports timeout**
- ✗ Native protocol not supported on this model
- Action: Use PJLink as fallback
- Next: Document limitation, add automatic fallback
- File issue as: "CP-EX301N requires PJLink fallback"

---

## Troubleshooting

### "Connection refused" error

```
✗ Connection failed: [Errno 10061] No connection could be made...
```

**Causes:**
- Projector not on network
- Wrong IP address
- Firewall blocking connection
- Port not open on projector

**Solutions:**
1. Verify projector IP: Check OPTION → NETWORK → TCP/IP
2. Ping test: `ping 192.168.19.207`
3. Try PJLink port first: `--port 4352`
4. Check firewall settings

### "Connection timeout" error

```
✗ Connection timeout after 5.0s
```

**Causes:**
- Network latency
- Projector slow to respond
- Wrong subnet

**Solutions:**
1. Increase timeout: `--timeout 10.0`
2. Check network path (direct vs. switch)
3. Verify subnet mask matches

### All commands timeout but connection succeeds

```
✓ Connection established in 0.045s
...
RX: Timeout after 5.0s
```

**This is the current issue we're debugging!**

**Possible causes:**
1. Wrong CRC algorithm → Run `hitachi_crc_validator.py`
2. Wrong byte order → Check Phase 4 results
3. Port requires framing → Try `--port 9715 --framed`
4. Model doesn't support native protocol → Use PJLink fallback

---

## Output Files Reference

All diagnostic output is saved to: `tools/diagnostic_results/`

### Directory Structure

```
tools/diagnostic_results/
├── hitachi_diagnostic_23_[timestamp].md      # Port 23 test results
├── hitachi_diagnostic_9715_[timestamp].md    # Port 9715 test results (if run)
├── hitachi_crc_validation.md                 # CRC validation results
└── traffic/
    ├── pjlink_session_[timestamp].txt        # PJLink capture
    ├── native_session_[timestamp].txt        # Native protocol capture
    └── comparison_[timestamp].md             # Side-by-side comparison
```

### File Formats

All files are in Markdown format for easy viewing in:
- GitHub/GitLab
- VS Code
- Any text editor
- Markdown preview tools

---

## Expected Diagnostic Timeline

| Phase | Task | Est. Time | Tool |
|-------|------|-----------|------|
| **Phase 1** | Network verification | 5 min | ping, PJLink test |
| **Phase 2** | Official commands test | 10 min | `hitachi_diagnostic.py` |
| **Phase 3** | CRC validation | 5 min | `hitachi_crc_validator.py` |
| **Phase 4** | Byte order testing | 10 min | `hitachi_diagnostic.py --all-tests` |
| **Phase 5** | Port 9715 testing | 10 min | `hitachi_diagnostic.py --port 9715 --framed` |
| **Phase 6** | Traffic capture | 10 min | `hitachi_traffic_capture.py` |
| **Phase 7** | Analysis & reporting | 15 min | Manual review |

**Total:** ~65 minutes (1 hour systematic testing)

---

## Next Steps After Diagnosis

### If Protocol Works

1. **Update Implementation**
   - File: `src/network/protocols/hitachi.py`
   - Fix: Update CRC algorithm or byte order
   - Test: Run existing unit tests
   - Verify: Test with physical projector

2. **Add Integration Test**
   - File: `tests/integration/test_hitachi_physical.py`
   - Add: Real command/response pairs from successful test
   - Mark: `@pytest.mark.physical` (requires real projector)

3. **Update Documentation**
   - File: `docs/protocols/HITACHI.md`
   - Add: Correct CRC algorithm
   - Add: CP-EX301N/CP-EX302N specific notes

4. **Remove Blocker**
   - File: `ROADMAP.md`
   - Update: Mark BLK-001 as RESOLVED
   - Add: Test results summary

### If Protocol Doesn't Work

1. **Document Limitation**
   - File: `docs/protocols/HITACHI.md`
   - Add: Section "CP-EX301N/CP-EX302N Limitations"
   - Note: Use PJLink as primary protocol

2. **Update UI**
   - File: `src/ui/dialogs/projector_dialog.py`
   - Add: Tooltip recommending PJLink for Hitachi
   - Add: Warning if user selects native protocol

3. **Add Automatic Fallback**
   - File: `src/core/controller_factory.py`
   - Add: Timeout detection and auto-switch to PJLink
   - Log: Warning about native protocol failure

4. **Update Roadmap**
   - File: `ROADMAP.md`
   - Update: Mark BLK-001 as CLOSED (won't fix - model limitation)
   - Add: PJLink fallback as recommended solution

---

## Support & References

### Documentation

- **Official Hitachi Docs:** `docs/Hitachi_CP-EX301N_CP-EX302N_Complete_Control_Documentation.md`
- **Multi-Brand Plan:** `docs/planning/MULTI_BRAND_PROJECTOR_SUPPORT_PLAN.md`
- **Results Template:** `docs/HITACHI_CP-EX_DEBUGGING.md`

### Implementation Files

- **Protocol:** `src/network/protocols/hitachi.py` (lines 267-343 CRC)
- **Controller:** `src/core/controllers/hitachi_controller.py`
- **Tests:** `tests/unit/test_hitachi_protocol.py` (117 tests)

### Getting Help

1. **Check LESSONS_LEARNED.md** - Known issues and solutions
2. **Review test results** - Look for patterns in failures
3. **Compare with documentation** - Verify command format
4. **Ask user** - Clarify model number, firmware version

---

## Revision History

| Date | Version | Author | Changes |
|------|---------|--------|---------|
| 2026-01-24 | 1.0 | Claude | Initial diagnostic tools creation |
| | | | Created diagnostic, CRC validator, traffic capture |
| | | | Comprehensive testing workflow |

---

**Questions?** Contact project maintainer or open an issue on GitHub.

**Ready to test?** Start with: `python tools/hitachi_diagnostic.py --host 192.168.19.207 --all-tests`
