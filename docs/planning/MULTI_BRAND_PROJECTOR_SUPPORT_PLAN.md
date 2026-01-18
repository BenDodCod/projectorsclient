# Plan: Multi-Brand Projector Support Expansion

---

## ROADMAP & PROGRESS TRACKER

> **IMPORTANT:** Anyone working on this plan MUST update this section after completing tasks.
> Update the status, add dates, and log any changes or deviations in the Change Log below.

### Current Status: NOT STARTED
**Last Updated:** 2026-01-18
**Updated By:** Claude (initial creation)

### Phase Progress

| Phase | Description | Status | Started | Completed | Owner |
|-------|-------------|--------|---------|-----------|-------|
| 1 | Protocol Abstraction Layer | NOT STARTED | - | - | - |
| 2 | Hitachi Protocol Implementation | NOT STARTED | - | - | - |
| 3 | Database & UI Updates | NOT STARTED | - | - | - |
| 4 | Controller Abstraction | NOT STARTED | - | - | - |
| 5 | Additional Protocol Stubs | NOT STARTED | - | - | - |

**Status Values:** `NOT STARTED` | `IN PROGRESS` | `BLOCKED` | `COMPLETED` | `SKIPPED`

### Task Checklist

#### Phase 1: Protocol Abstraction Layer
- [ ] 1.1 Create `src/network/base_protocol.py` - Base protocol interface
- [ ] 1.2 Create `src/network/protocol_factory.py` - Factory pattern
- [ ] 1.3 Refactor PJLink to `src/network/protocols/pjlink.py`
- [ ] 1.4 Unit tests for base protocol
- [ ] 1.5 Verify backward compatibility

#### Phase 2: Hitachi Protocol Implementation
- [ ] 2.1 Create `src/network/protocols/hitachi.py` - Protocol module
- [ ] 2.2 Create `src/core/controllers/hitachi_controller.py` - Controller
- [ ] 2.3 Implement TCP Port 23 communication
- [ ] 2.4 Implement TCP Port 9715 with framing
- [ ] 2.5 Implement MD5 authentication
- [ ] 2.6 Implement full command set (power, input, mute, freeze, blank, image)
- [ ] 2.7 Unit tests for Hitachi protocol
- [ ] 2.8 Test with physical Hitachi projector

#### Phase 3: Database & UI Updates
- [ ] 3.1 Create migration `v3_multi_protocol.py`
- [ ] 3.2 Add `proj_type` enum values
- [ ] 3.3 Add `protocol_settings` JSON field
- [ ] 3.4 Update `projector_dialog.py` - brand dropdown
- [ ] 3.5 Add protocol auto-detection UI
- [ ] 3.6 Migration tests

#### Phase 4: Controller Abstraction
- [ ] 4.1 Create `src/core/controller_factory.py`
- [ ] 4.2 Update `resilient_controller.py` for multi-protocol
- [ ] 4.3 Integration tests

#### Phase 5: Additional Protocol Stubs
- [ ] 5.1 Create `src/network/protocols/sony.py` stub
- [ ] 5.2 Create `src/network/protocols/benq.py` stub
- [ ] 5.3 Create `src/network/protocols/nec.py` stub
- [ ] 5.4 Create `src/network/protocols/jvc.py` stub

### Change Log

| Date | Author | Change Description |
|------|--------|-------------------|
| 2026-01-18 | Claude | Initial plan created |
| | | |
| | | |

### Blockers & Issues

| ID | Description | Status | Raised | Resolved |
|----|-------------|--------|--------|----------|
| - | None yet | - | - | - |

### Notes & Decisions

- **2026-01-18:** Physical Hitachi projector available for testing
- **2026-01-18:** Network-only implementation (no RS-232 serial)
- **2026-01-18:** Full feature set required (freeze, blank, image adjustments)

---

## Executive Summary

Expand the Projector Control Application to support multiple projector brands beyond Epson, starting with Hitachi and preparing architecture for Sony, BenQ, NEC, JVC, Panasonic, and others.

## User Requirements (Confirmed)
- **Testing:** Physical Hitachi projector available for testing
- **Connectivity:** Network-only (TCP ports 23/9715 + PJLink)
- **Scope:** Hitachi first, with stubs prepared for other brands
- **Features:** Full feature set (power, input, mute, freeze, blank, image adjustments, status monitoring)

## Current Architecture Analysis

**Good News:** The current architecture is well-designed for extension:
- `proj_type` field exists in database (currently only `'pjlink'`)
- PJLink protocol already supports many brands (including Hitachi basic control)
- Clear separation: Protocol layer → Controller layer → Resilient layer
- STRUCTURE.md documents the extension pattern

**Key Files:**
- `src/network/pjlink_protocol.py` (704 lines) - PJLink protocol
- `src/core/projector_controller.py` (978 lines) - Core controller
- `src/controllers/resilient_controller.py` (698 lines) - Fault-tolerant wrapper
- `src/database/connection.py` - Projector schema
- `src/ui/dialogs/projector_dialog.py` - Projector configuration UI

## Research Findings

### Hitachi Projectors (Network-Only Implementation)
| Protocol | Port | Description |
|----------|------|-------------|
| **PJLink** | TCP 4352 | Standard protocol (ALREADY SUPPORTED) |
| TCP Port 23 | TCP 23 | RS-232C commands over network (primary) |
| TCP Port 9715 | TCP 9715 | RS-232C with framing + MD5 auth |

**Hitachi Command Structure (Binary):**
- Header: `BE EF 03 06 00` (5 bytes fixed)
- Action codes: SET(01 00), GET(02 00), INCREMENT(04 00), DECREMENT(05 00), EXECUTE(06 00)
- Checksum: CRC-based validation
- Auth: MD5 hash of (8-byte challenge + password)
- Timing: 40ms minimum between commands

**Full Feature Set Commands:**
| Feature | Command Type | Notes |
|---------|-------------|-------|
| Power On/Off | EXECUTE | 20-30s warm-up/cooling |
| Input Select | SET | HDMI, RGB, Component, Video |
| Mute (Video/Audio) | SET/GET | Separate audio/video mute |
| Freeze | EXECUTE | Hold current frame |
| Blank | EXECUTE | Black screen |
| Brightness | SET/GET/INC/DEC | Image adjustment |
| Contrast | SET/GET/INC/DEC | Image adjustment |
| Color | SET/GET/INC/DEC | Image adjustment |
| Lamp Hours | GET | Maintenance monitoring |
| Filter Hours | GET | Maintenance monitoring |
| Temperature | GET | Status monitoring |
| Error Status | GET | Diagnostic info |

### Other Major Brands (Protocol Summary)

| Brand | PJLink Support | Proprietary Protocol |
|-------|----------------|---------------------|
| **Epson** | Yes | ESC/VP21 (RS-232) |
| **Sony** | Yes | ADCP (TCP 53595) |
| **BenQ** | Yes | Text-based (`<CR>*cmd=val#<CR>`) |
| **NEC** | Yes | Binary (TCP 7142) |
| **JVC** | No | D-ILA Binary (TCP 20554) |
| **Panasonic** | Yes | Smart Projector Control |
| **Christie** | Yes | ASCII text commands |
| **Optoma** | Yes | AMX compatible |
| **ViewSonic** | Yes | RS-232 text protocol |
| **Barco** | Yes | Multiple integrations |

**Key Insight:** PJLink is widely supported, making the current implementation compatible with many brands for basic operations.

---

## Implementation Plan

### Phase 1: Protocol Abstraction Layer (Foundation)

**Goal:** Create a protocol-agnostic abstraction that allows multiple protocol implementations.

#### 1.1 Create Base Protocol Interface
```
src/network/base_protocol.py (NEW)
```
- Abstract base class `ProjectorProtocol`
- Define standard methods: `power_on()`, `power_off()`, `get_power_state()`, etc.
- Define standard response types and error handling
- Support for protocol detection/auto-discovery

#### 1.2 Create Protocol Factory
```
src/network/protocol_factory.py (NEW)
```
- Factory pattern to instantiate appropriate protocol
- Protocol registration system
- Auto-detection capability

#### 1.3 Refactor PJLink as Protocol Implementation
```
src/network/protocols/pjlink.py (REFACTOR from pjlink_protocol.py)
```
- Implement `ProjectorProtocol` interface
- Maintain backward compatibility

### Phase 2: Hitachi Protocol Implementation

**Goal:** Full native Hitachi support via proprietary protocol.

#### 2.1 Hitachi Protocol Module
```
src/network/protocols/hitachi.py (NEW)
```
- TCP Port 23 implementation (RS-232C over network)
- TCP Port 9715 implementation (with framing + checksum)
- Binary command builder (BE EF header format)
- MD5 authentication support
- CRC checksum calculation
- Full command set:
  - Power: on, off, status query
  - Input: select, query, list available
  - Mute: video mute, audio mute, combined mute
  - Freeze: on, off, query
  - Blank: on, off, query
  - Image: brightness, contrast, color (set/get/increment/decrement)
  - Status: lamp hours, filter hours, temperature, errors

#### 2.2 Hitachi Controller
```
src/core/controllers/hitachi_controller.py (NEW)
```
- Hitachi-specific state machine
- Warm-up/cooling cycle handling (20-30 seconds)
- Command timing enforcement (40ms minimum)
- Full feature methods:
  - `power_on()`, `power_off()`, `get_power_state()`
  - `set_input()`, `get_current_input()`, `get_available_inputs()`
  - `video_mute()`, `audio_mute()`, `mute_on()`, `mute_off()`
  - `freeze_on()`, `freeze_off()`, `get_freeze_state()`
  - `blank_on()`, `blank_off()`, `get_blank_state()`
  - `set_brightness()`, `get_brightness()`, `adjust_brightness()`
  - `set_contrast()`, `get_contrast()`, `adjust_contrast()`
  - `set_color()`, `get_color()`, `adjust_color()`
  - `get_lamp_hours()`, `get_filter_hours()`
  - `get_temperature()`, `get_error_status()`
- Extended ProjectorInfo with Hitachi-specific data

### Phase 3: Database & UI Updates

#### 3.1 Database Schema Update
```
src/database/migrations/v3_multi_protocol.py (NEW)
```
- Add new `proj_type` values: 'hitachi', 'sony', 'benq', etc.
- Add `protocol_settings` JSON field for protocol-specific config
- Migration from v2 → v3

#### 3.2 UI: Protocol Selection
```
src/ui/dialogs/projector_dialog.py (MODIFY)
```
- Add projector type/brand dropdown
- Protocol auto-detection button
- Protocol-specific settings panel
- Dynamic input discovery per protocol

### Phase 4: Controller Abstraction

#### 4.1 Multi-Protocol Controller Factory
```
src/core/controller_factory.py (NEW)
```
- Create appropriate controller based on `proj_type`
- Unified interface for ResilientController

#### 4.2 Update Resilient Controller
```
src/controllers/resilient_controller.py (MODIFY)
```
- Support multiple protocol controllers
- Protocol-agnostic resilience patterns

### Phase 5: Additional Protocols (Future-Ready)

Prepare stubs for future implementation:

#### 5.1 Protocol Stubs
```
src/network/protocols/sony.py      # ADCP protocol
src/network/protocols/benq.py      # BenQ text protocol
src/network/protocols/nec.py       # NEC binary protocol
src/network/protocols/jvc.py       # JVC D-ILA protocol
```

Each stub will include:
- Protocol specification documentation
- Command reference
- Implementation TODO markers

---

## File Structure After Implementation

```
src/
├── network/
│   ├── __init__.py (MODIFY - export new modules)
│   ├── base_protocol.py (NEW)
│   ├── protocol_factory.py (NEW)
│   ├── protocols/
│   │   ├── __init__.py (NEW)
│   │   ├── pjlink.py (REFACTOR)
│   │   ├── hitachi.py (NEW)
│   │   ├── sony.py (NEW - stub)
│   │   ├── benq.py (NEW - stub)
│   │   ├── nec.py (NEW - stub)
│   │   └── jvc.py (NEW - stub)
│   ├── circuit_breaker.py (unchanged)
│   └── connection_pool.py (unchanged)
├── core/
│   ├── __init__.py (MODIFY)
│   ├── projector_controller.py (MODIFY - base class)
│   ├── controller_factory.py (NEW)
│   └── controllers/
│       ├── __init__.py (NEW)
│       ├── pjlink_controller.py (REFACTOR)
│       └── hitachi_controller.py (NEW)
├── controllers/
│   └── resilient_controller.py (MODIFY)
├── database/
│   ├── connection.py (MODIFY - new proj_types)
│   └── migrations/
│       └── v3_multi_protocol.py (NEW)
└── ui/
    └── dialogs/
        └── projector_dialog.py (MODIFY)
```

---

## Testing Strategy

### Unit Tests
- `tests/unit/network/test_base_protocol.py`
- `tests/unit/network/protocols/test_hitachi.py`
- `tests/unit/core/test_controller_factory.py`

### Integration Tests
- `tests/integration/test_multi_protocol_control.py`
- `tests/integration/test_hitachi_controller.py`

### Mock Projector Tests
- Create mock Hitachi projector server for testing
- Protocol compliance tests

---

## Verification Plan

### Unit Testing
1. **Protocol Compliance:** Verify Hitachi binary commands match specification
2. **Command Builder:** Test BE EF header construction and CRC calculation
3. **Authentication:** Test MD5 challenge-response flow
4. **Response Parsing:** Test all response types and error codes

### Integration Testing
1. **Backward Compatibility:** Ensure existing PJLink projectors work unchanged
2. **Protocol Factory:** Verify correct protocol selection based on proj_type
3. **Controller Factory:** Verify correct controller instantiation

### Manual Testing with Physical Hitachi Projector
1. **Connection:** TCP Port 23 and Port 9715 connectivity
2. **Authentication:** If projector has auth enabled
3. **Power Control:** On/off with warm-up/cooling wait
4. **Input Switching:** All available inputs
5. **Mute Functions:** Video, audio, combined
6. **Freeze/Blank:** Visual verification
7. **Image Adjustments:** Brightness, contrast, color
8. **Status Queries:** Lamp hours, filter hours, temperature

### UI Testing
1. **Projector Dialog:** Protocol type selection and settings
2. **Main Window:** All controls work with Hitachi projector
3. **Status Display:** Hitachi-specific status information

---

## Estimated Scope

| Phase | Files | Complexity |
|-------|-------|------------|
| Phase 1: Abstraction | 3 new, 1 refactor | Medium |
| Phase 2: Hitachi | 2 new | Medium-High |
| Phase 3: DB & UI | 2 modify, 1 new | Medium |
| Phase 4: Controller | 2 new, 1 modify | Medium |
| Phase 5: Stubs | 4 new | Low |

**Total:** ~12 files, maintaining test coverage target of 85%+

---

## Implementation Order (Recommended)

1. **Phase 1** - Protocol abstraction (foundation for everything else)
2. **Phase 4** - Controller factory (enables multi-protocol support)
3. **Phase 3** - Database & UI (add projector type selection)
4. **Phase 2** - Hitachi implementation (with real projector testing)
5. **Phase 5** - Protocol stubs (documentation for future brands)

This order allows incremental testing and validation at each step.

---

## Summary

This plan creates a scalable multi-brand projector control system by:
1. Abstracting the protocol layer with factory pattern
2. Implementing full Hitachi native protocol support (network-only)
3. Maintaining backward compatibility with existing PJLink projectors
4. Preparing architecture for easy addition of Sony, BenQ, NEC, JVC, and other brands

The full feature set (power, input, mute, freeze, blank, image adjustments, status monitoring) will be available for Hitachi projectors through their native protocol, providing capabilities beyond what PJLink offers.