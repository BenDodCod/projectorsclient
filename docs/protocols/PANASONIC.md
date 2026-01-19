# Panasonic Projector Protocol

Native control protocol for Panasonic projectors and displays.

## Overview

| Property | Value |
|----------|-------|
| Protocol Type | Text-based |
| Network Port | TCP 1024 (Protocol 2) |
| RS-232 Settings | 9600 baud, 8-N-1 |
| Authentication | MD5 (optional) |
| PJLink Support | Yes |

## Connection Settings

### Network
```
Port: 1024 (TCP) - Protocol 2
Encoding: ASCII
Optional MD5 authentication
```

### RS-232
```
Baud Rate: 9600
Data Bits: 8
Parity: None
Stop Bits: 1
```

## Protocol Types

Panasonic supports multiple protocols:

1. **Panasonic Native** - Proprietary commands (Port 1024)
2. **Projector Protocol** - Shared with older models
3. **PJLink** - Industry standard (Port 4352)

## Command Format

### Structure
```
[STX][Command][Parameter][ETX]
```

Or simplified:
```
[Command][Parameter]\r
```

- Commands are uppercase ASCII
- Terminated with CR (0x0D)

## Authentication

### Disabling Authentication
1. Access web interface: `http://[projector_ip]/`
2. Set password to empty string
3. Set "Command control timeout" to non-zero value

### MD5 Authentication Flow
1. Connect and receive challenge
2. Calculate MD5(challenge + password)
3. Send 32-byte hash before commands

```python
import hashlib

challenge = "received_challenge"
password = "admin_password"
md5_hash = hashlib.md5((challenge + password).encode()).hexdigest()
```

## Command Reference

### Power Control

| Command | Description |
|---------|-------------|
| `PON` | Power on |
| `POF` | Power off |
| `QPW` | Query power state |

**Response:** `000` (off), `001` (on)

### Input Selection

| Command | Input |
|---------|-------|
| `IIS:RG1` | RGB 1 |
| `IIS:RG2` | RGB 2 |
| `IIS:VID` | Video |
| `IIS:SVD` | S-Video |
| `IIS:HD1` | HDMI 1 |
| `IIS:HD2` | HDMI 2 |
| `IIS:DVI` | DVI |
| `IIS:DP1` | DisplayPort |
| `IIS:NWP` | Network |
| `IIS:USB` | USB |
| `QIN` | Query current input |

### Mute Control

| Command | Description |
|---------|-------------|
| `OSH:1` | Shutter close (mute on) |
| `OSH:0` | Shutter open (mute off) |
| `QSH` | Query shutter state |

### Volume Control

| Command | Description |
|---------|-------------|
| `AVL:xx` | Set volume (00-63) |
| `QAV` | Query volume |

### Image Adjustments

| Command | Description | Range |
|---------|-------------|-------|
| `VBR:xxx` | Brightness | 000-100 |
| `VCN:xxx` | Contrast | 000-100 |
| `VCO:xxx` | Color | 000-100 |
| `VTN:xxx` | Tint | 000-100 |
| `VSH:xxx` | Sharpness | 000-015 |

### Status Queries

| Command | Returns |
|---------|---------|
| `Q$L` | Lamp hours |
| `Q$S` | Projector status |
| `QER` | Error status |

### Lens Control (if equipped)

| Command | Description |
|---------|-------------|
| `VXX:LMEM1` | Load lens memory 1 |
| `VXX:LMEM2` | Load lens memory 2 |

## Complete Example

```python
import socket

def panasonic_command(host, command, port=1024):
    """Send command to Panasonic projector."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    sock.connect((host, port))

    # Some models need initial handshake
    # Check if authentication required

    # Send command with CR
    sock.send(f"{command}\r".encode())

    # Read response
    response = sock.recv(1024).decode().strip()
    sock.close()

    return response

# Examples
print(panasonic_command("192.168.1.100", "QPW"))       # Query power
print(panasonic_command("192.168.1.100", "PON"))       # Power on
print(panasonic_command("192.168.1.100", "IIS:HD1"))   # HDMI 1
print(panasonic_command("192.168.1.100", "Q$L"))       # Lamp hours
```

## Web Interface

Panasonic projectors provide a web interface for configuration:
- URL: `http://[projector_ip]/`
- Configure network settings
- Enable/disable authentication
- Set command control timeout

### Important Settings
- **WEB CONTROL**: Must be ON
- **PJLink CONTROL**: Must be ON for PJLink
- **COMMAND CONTROL**: Must be ON for Protocol 2
- **Command timeout**: Set > 0 seconds

## Response Codes

| Response | Meaning |
|----------|---------|
| `000-xxx` | Success with value |
| `ER401` | Invalid command |
| `ER402` | Invalid parameter |
| `ER403` | Unavailable |

## Timing Considerations

- Power on: ~30 seconds warm-up
- Power off: ~60 seconds cooling
- Command interval: 500ms minimum
- Connection timeout varies by firmware

### Timeout Issue
Some firmware versions have default timeout of 0 seconds, which disconnects immediately. Set to higher value in web interface.

## PJLink Alternative

For simpler integration, use PJLink on port 4352:
```
%1POWR 1\r     # Power on
%1INPT 31\r    # HDMI 1
```

PJLink is recommended for basic operations.

## Model Variations

### PT-DZ/DW/DX Series
- Full command set
- Lens control available

### PT-MZ/MW Series
- Compact models
- May have reduced commands

### Professional/Venue
- Extended commands
- Multiple lamp support

## Official Documentation

- [LAN Control Protocol](https://docs.connect.panasonic.com/prodisplays/support/download/pdf/LAN_Protocol_exp.pdf)
- [PT-DZ870 Command Reference](https://na.panasonic.com/ns/35519_PT-DZ870DW830DX100_RS-232C_control_spec_-_.pdf)
- [Smart Projector Control](https://docs.connect.panasonic.com/projector/download/application/smartpj/setting/)
