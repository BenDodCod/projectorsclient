# NEC Projector Protocol

Binary control protocol for NEC professional projectors.

## Overview

| Property | Value |
|----------|-------|
| Protocol Type | Binary |
| Network Port | TCP 7142 |
| RS-232 Settings | 38400 baud, 8-N-1 |
| Authentication | None |
| PJLink Support | Yes |

## Connection Settings

### Network
```
Port: 7142 (TCP)
Binary protocol
No authentication
```

### RS-232
```
Baud Rate: 38400 (some models 19200)
Data Bits: 8
Parity: None
Stop Bits: 1
```

## Command Structure

### Packet Format
```
[Header] [Model ID] [Op Code] [Parameters] [Checksum]
```

### Header Bytes
| Operation | Header |
|-----------|--------|
| Command | 02 XX |
| Response OK | 22 XX |
| Response Error | A2 XX |

### Checksum Calculation
Simple sum of all bytes modulo 256:
```python
def calculate_checksum(data):
    """Calculate NEC checksum."""
    return sum(data) & 0xFF
```

## Command Reference

### Power Control

**Power On:**
```
02 00 [model_id] [model_id] 00 00 00 02 [checksum]
```

**Power Off:**
```
02 00 [model_id] [model_id] 00 00 00 01 [checksum]
```

**Power Query:**
```
02 01 [model_id] [model_id] 00 00 [checksum]
```

### Response Format

**Success Response:**
```
22 [op_code] [model_id] [model_id] [data...] [checksum]
```

**Error Response:**
```
A2 [op_code] [model_id] [model_id] 02 [error_code] [checksum]
```

### Input Selection

| Input | Op Code | Parameter |
|-------|---------|-----------|
| RGB 1 | 02 03 | 01 |
| RGB 2 | 02 03 | 02 |
| Video | 02 03 | 03 |
| S-Video | 02 03 | 04 |
| Component | 02 03 | 05 |
| HDMI 1 | 02 03 | 0A |
| HDMI 2 | 02 03 | 0B |
| DisplayPort | 02 03 | 0D |
| LAN | 02 03 | 07 |
| USB | 02 03 | 08 |

### Mute Control

| Command | Op Code | Parameter |
|---------|---------|-----------|
| Picture Mute On | 02 10 | 01 |
| Picture Mute Off | 02 10 | 00 |
| Audio Mute On | 02 12 | 01 |
| Audio Mute Off | 02 12 | 00 |

### Image Adjustments

| Function | Op Code | Range |
|----------|---------|-------|
| Brightness | 03 10 | 0-100 |
| Contrast | 03 12 | 0-100 |
| Color | 03 14 | 0-100 |
| Sharpness | 03 16 | 0-15 |

### Status Queries

| Query | Op Code |
|-------|---------|
| Power Status | 00 BF |
| Lamp Hours | 03 94 |
| Input Status | 00 C0 |
| Error Status | 00 88 |

## Error Codes

| Code | Meaning |
|------|---------|
| 00 | OK / No error |
| 01 | Invalid command |
| 02 | Invalid parameter |
| 03 | Unavailable (busy) |
| 04 | Hardware failure |

## Complete Example

```python
import socket
import struct

def nec_command(host, command_bytes, port=7142):
    """Send binary command to NEC projector."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    sock.connect((host, port))

    # Calculate checksum
    checksum = sum(command_bytes) & 0xFF
    full_command = bytes(command_bytes) + bytes([checksum])

    sock.send(full_command)
    response = sock.recv(1024)
    sock.close()

    return response

def nec_power_on(host, model_id=0x00):
    """Power on NEC projector."""
    # Header + model + op code + parameters
    cmd = [0x02, 0x00, model_id, model_id, 0x00, 0x00, 0x00, 0x02]
    return nec_command(host, cmd)

def nec_power_off(host, model_id=0x00):
    """Power off NEC projector."""
    cmd = [0x02, 0x00, model_id, model_id, 0x00, 0x00, 0x00, 0x01]
    return nec_command(host, cmd)

def nec_select_hdmi(host, hdmi_num=1, model_id=0x00):
    """Select HDMI input."""
    input_code = 0x0A if hdmi_num == 1 else 0x0B
    cmd = [0x02, 0x03, model_id, model_id, 0x00, 0x00, input_code]
    return nec_command(host, cmd)

def nec_query_lamp_hours(host, model_id=0x00):
    """Query lamp hours."""
    cmd = [0x03, 0x94, model_id, model_id, 0x00, 0x00]
    response = nec_command(host, cmd)
    # Parse response for hours
    if response[0] == 0x23:  # Success
        hours = struct.unpack('<I', response[5:9])[0]
        return hours
    return None

# Usage
response = nec_power_on("192.168.1.100")
print(f"Response: {response.hex()}")
```

## Model ID

The model ID varies by projector. Common values:
- `00 00` - Generic/broadcast
- Check projector documentation for specific ID

## Timing Considerations

- Power on: ~30 seconds warm-up
- Power off: ~60 seconds cooling
- Command interval: 500ms minimum
- Some commands unavailable during transitions

## PJLink Alternative

NEC projectors support PJLink on port 4352:
```
%1POWR 1\r     # Power on
%1INPT 31\r    # HDMI 1
```

PJLink is simpler for basic operations.

## Official Documentation

- [NEC Control Commands](https://assets.sharpnecdisplays.us/documents/miscellaneous/pj-control-command-codes.pdf)
- [NEC External Control Manual](https://www.sharpdisplays.eu/p/download/cp/Products/Projectors/Shared/CommandLists/NEC-ExternalControlManual-english.pdf)
