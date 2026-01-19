# Projector Protocol Documentation

Technical documentation for all supported projector control protocols.

## Protocol Overview

| Brand | Protocol | Port | Authentication | PJLink Support |
|-------|----------|------|----------------|----------------|
| [PJLink](PJLINK.md) | Industry Standard | TCP 4352 | MD5/SHA256 | Yes (native) |
| [Epson](EPSON.md) | ESC/VP21 | TCP 3629 | MD5 | Yes |
| [Hitachi](HITACHI.md) | Binary | TCP 23, 9715 | MD5 | Yes |
| [Sony](SONY.md) | ADCP | TCP 53595 | SHA256 | Yes |
| [BenQ](BENQ.md) | Text | TCP 8000 | None | Yes |
| [NEC](NEC.md) | Binary | TCP 7142 | None | Yes |
| [JVC](JVC.md) | D-ILA | TCP 20554 | None | **No** |
| [Panasonic](PANASONIC.md) | Native | TCP 1024 | MD5 | Yes |
| [Optoma](OPTOMA.md) | AMX | RS-232/TCP | None | Yes |

## Quick Reference

### Protocol Types

1. **PJLink** - Industry standard, widely supported
2. **Text-based** - ASCII commands (Epson ESC/VP21, BenQ, Sony ADCP)
3. **Binary** - Hex commands with checksums (Hitachi, NEC, JVC)

### Recommended Approach

For most projectors, **use PJLink first** - it's supported by most major brands and provides:
- Power control
- Input selection
- Mute control
- Status queries
- Lamp hours

Only use proprietary protocols when:
- PJLink is not supported (JVC D-ILA)
- Advanced features needed (freeze, blank, image adjustments)
- Better reliability required

## Implementation Status

| Protocol | Status | Notes |
|----------|--------|-------|
| PJLink | Fully Implemented | Class 1 & 2 support |
| Hitachi | Implemented | BLK-001: Use PJLink fallback |
| Sony | Stub | Documentation ready |
| BenQ | Stub | Documentation ready |
| NEC | Stub | Documentation ready |
| JVC | Stub | Documentation ready |

## Related Files

- Implementation: `src/network/protocols/`
- Base Protocol: `src/network/base_protocol.py`
- Protocol Factory: `src/network/protocol_factory.py`
