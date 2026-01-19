# Hitachi Projector Protocol

Binary network control protocol for Hitachi projectors with dual-port architecture.

## Overview

| Property | Value |
|----------|-------|
| Protocol Type | Binary with BE EF header |
| Ports | TCP 23 (raw), TCP 9715 (framed + auth) |
| Authentication | MD5 challenge-response (port 9715) |
| Checksum | CRC-16-CCITT |
| PJLink Support | Yes (port 4352) |

## Connection Options

### TCP Port 23 (Raw Mode)
- Direct RS-232C command mapping
- No authentication by default
- Simple binary commands

### TCP Port 9715 (Framed Mode)
- Enhanced protocol with framing
- MD5 authentication
- Connection tracking via ID
- 30-second inactivity timeout

## Command Structure

### Port 23 Format (13 bytes)

```
Bytes 0-4:   BE EF 03 06 00    (Header - fixed)
Bytes 5-6:   [CRC_lo] [CRC_hi] (CRC-16, little-endian)
Bytes 7-8:   [Action_lo] [Action_hi] (Action code)
Bytes 9-10:  [Type_lo] [Type_hi] (Command type)
Bytes 11-12: [Set_lo] [Set_hi] (Setting value)
```

### Port 9715 Format (16 bytes)

```
Byte 0:      02              (Header)
Byte 1:      0D              (Data length = 13)
Bytes 2-14:  [13-byte RS-232C command]
Byte 15:     [Checksum]      (Sum mod 256)
Byte 16:     [Connection ID] (0-255)
```

## Action Codes

| Action | Code (hex) | Description |
|--------|------------|-------------|
| SET | 01 00 | Write value |
| GET | 02 00 | Read value |
| INCREMENT | 04 00 | Increase value |
| DECREMENT | 05 00 | Decrease value |
| EXECUTE | 06 00 | Execute action |

## Command Reference

### Power Control

| Command | Type Code | Setting | Full Bytes (after header+CRC) |
|---------|-----------|---------|-------------------------------|
| Power On | 00 60 | 00 00 | `01 00 00 60 00 00` |
| Power Off | 00 60 | 01 00 | `01 00 00 60 01 00` |
| Power Query | 02 30 | 00 00 | `02 00 02 30 00 00` |

**Complete Power On Command:**
```
BE EF 03 06 00 2A D3 01 00 00 60 00 00
```

### Input Selection

| Input | Type Code | Setting | Full Bytes |
|-------|-----------|---------|------------|
| Computer 1 | 00 20 | 00 00 | `01 00 00 20 00 00` |
| Computer 2 | 00 20 | 01 00 | `01 00 00 20 01 00` |
| Video | 00 20 | 04 00 | `01 00 00 20 04 00` |
| S-Video | 00 20 | 10 00 | `01 00 00 20 10 00` |
| HDMI 1 | 00 20 | 20 00 | `01 00 00 20 20 00` |
| HDMI 2 | 00 20 | 21 00 | `01 00 00 20 21 00` |
| Component | 00 20 | 02 00 | `01 00 00 20 02 00` |

### Mute Control

| Command | Action | Type | Setting |
|---------|--------|------|---------|
| Video Mute On | SET | TBD | TBD |
| Video Mute Off | SET | TBD | TBD |
| Audio Mute On | SET | TBD | TBD |
| Audio Mute Off | SET | TBD | TBD |

### Image Adjustments

| Function | Type Code | Range |
|----------|-----------|-------|
| Brightness | A4 D2 | 0-100 |
| Contrast | A4 D2 | 0-100 |
| Color Temp | BC F4 | varies |

## Response Codes

### Port 23 Responses

| Code | Meaning |
|------|---------|
| `06` | ACK - Success |
| `15` | NAK - Command not understood |
| `1C 00 00` | Error - Cannot execute |
| `1D [data]` | Data reply (for GET) |

### Port 9715 Responses

| Code | Meaning |
|------|---------|
| `06 [id]` | ACK + Connection ID |
| `15 [id]` | NAK + Connection ID |
| `1C 00 00 [id]` | Error + Connection ID |
| `1D [data] [id]` | Data + Connection ID |
| `1F 04 00 [id]` | Authentication error |

## CRC-16 Calculation

### Algorithm
- Polynomial: CRC-16-CCITT (0x1021)
- Initial value: 0x0000 or 0xFFFF
- Byte order: Little-endian

### Python Implementation

```python
def crc16_ccitt(data):
    """Calculate CRC-16-CCITT checksum."""
    crc = 0x0000
    poly = 0x1021

    for byte in data:
        crc ^= (byte << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ poly
            else:
                crc <<= 1
            crc &= 0xFFFF

    return crc

# Example: Power On command
action_type_setting = bytes([0x01, 0x00, 0x00, 0x60, 0x00, 0x00])
crc = crc16_ccitt(action_type_setting)
# crc = 0xD32A -> bytes: [0x2A, 0xD3] (little-endian)
```

## MD5 Authentication (Port 9715)

### Flow

1. Connect to TCP 9715
2. Receive 8-byte random challenge
3. Concatenate: `challenge + password`
4. Calculate MD5 hash
5. Prepend 32-char hex hash to first command

### Example

```python
import hashlib

challenge = "a572f60c"  # 8-byte hex from projector
password = "password"
combined = challenge + password
md5_hash = hashlib.md5(combined.encode()).hexdigest()
# Result: e3d97429adffa11bce1f7275813d4bde

# Prepend to command for first message
# Subsequent commands on same connection don't need hash
```

## Timing Requirements

| Requirement | Value |
|-------------|-------|
| Min delay between commands | 40ms |
| Inactivity timeout (port 9715) | 30 seconds |
| Warm-up period | 30-60 seconds |
| Cooling period | ~30 seconds |

**Important:** Commands are NOT accepted during warm-up!

## Complete Implementation Example

```python
import socket
import struct

HEADER = bytes([0xBE, 0xEF, 0x03, 0x06, 0x00])

def build_hitachi_command(action, type_code, setting):
    """Build 13-byte Hitachi command."""
    # Build command data (6 bytes)
    cmd_data = struct.pack('<HHH', action, type_code, setting)

    # Calculate CRC
    crc = crc16_ccitt(cmd_data)
    crc_bytes = struct.pack('<H', crc)

    # Assemble: header + crc + data
    return HEADER + crc_bytes + cmd_data

def power_on():
    return build_hitachi_command(0x0001, 0x6000, 0x0000)

def power_off():
    return build_hitachi_command(0x0001, 0x6000, 0x0001)

def select_hdmi1():
    return build_hitachi_command(0x0001, 0x2000, 0x0020)

# Send command
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(("192.168.1.100", 23))
sock.send(power_on())
response = sock.recv(1024)
sock.close()
```

## Troubleshooting

### BLK-001: Commands Timeout

**Symptoms:**
- TCP connection succeeds
- Commands don't get responses
- Timeout on all ports (23, 9715)

**Common Causes:**

1. **Wrong command codes** (most common!)
   - Verify type/setting codes match your projector model
   - Different Hitachi series may use different codes

2. **Authentication required**
   - Port 9715 may need MD5 auth
   - Check web interface settings

3. **Projector in warm-up/cooling**
   - Wait 60 seconds after power on
   - Commands rejected during transition

4. **30-second timeout exceeded**
   - Port 9715 auto-disconnects
   - Send keep-alive queries periodically

5. **Incorrect CRC**
   - Verify CRC-16 calculation
   - Check byte order (little-endian)

**Recommended Workaround:**
Use PJLink protocol on port 4352 instead! Most Hitachi projectors support PJLink, which provides basic functionality (power, input, status) with simpler implementation.

## PJLink Fallback

If native protocol fails, use PJLink:

```python
# PJLink is simpler and widely supported
sock.connect(("192.168.1.100", 4352))
sock.send(b"%1POWR 1\r")  # Power on
response = sock.recv(1024)
```

## Model Variations

Different Hitachi series may have variations:
- CP-X series (Collegiate)
- WU-series (High brightness)
- LP-series (Maxell/Hitachi)

Always verify command codes against your specific model's documentation.

## Official Documentation

- [CP-X4021N Tech Specs](https://www.hitachi.com/content/dam/hitachi/au/en_au/product-support/large-venue-projectors/CPX4021N_tech_specs.pdf)
- [Network Guide](https://olligmu.org/olliav/hitachi-cp-wu8461-network-guide.pdf)
- [Projector Management Software](https://proj-support.maxell.co.jp/en/projector/download/software/pdf/PJ_Man_Manual_v7.23_Eng.pdf)
