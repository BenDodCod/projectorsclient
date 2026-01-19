# Epson Projector Protocol (ESC/VP21)

Epson's proprietary control protocol for business and home cinema projectors.

## Overview

| Property | Value |
|----------|-------|
| Protocol Name | ESC/VP21 |
| Network Port | TCP 3629 (ESC/VP.net) |
| Serial Settings | 9600 baud, 8-N-1 |
| Type | Text-based ASCII |
| PJLink Support | Yes (most models) |

## Connection Methods

### 1. RS-232C Serial
- Direct connection via serial cable
- Settings: 9600/19200/38400 baud, 8-N-1

### 2. TCP/IP Network (ESC/VP.net)
- Port: 3629 (default, configurable)
- Requires session establishment before commands

### 3. USB
- Via USB-B port on projector

## Command Format

### Structure
```
[COMMAND] [PARAMETER]\r
```

- Commands are ASCII text
- Terminated with CR (0x0D)
- Response ends with `:` (ready for next command)

### Command Types

| Type | Format | Example |
|------|--------|---------|
| Set | `CMD param` | `PWR ON` |
| Get | `CMD ?` | `PWR ?` |
| Increment | `CMD INC` | `VOL INC` |
| Decrement | `CMD DEC` | `VOL DEC` |
| Initialize | `CMD INIT` | `BRIGHT INIT` |
| Null | `\r` only | Check connection |

## ESC/VP.net Session (TCP)

### Connection Flow
1. Connect to TCP port 3629
2. Receive `ESC/VP.net` header
3. Send authentication (if enabled)
4. Begin sending ESC/VP21 commands

### Authentication
```python
# If password required:
# 1. Receive challenge from projector
# 2. Calculate MD5(challenge + password)
# 3. Send hash to authenticate
```

## Command Reference

### Power Control

| Command | Description |
|---------|-------------|
| `PWR ON` | Power on |
| `PWR OFF` | Power off |
| `PWR ?` | Query power state |

**Response:** `PWR=01` (on), `PWR=00` (off)

### Input Selection (SOURCE)

| Command | Input |
|---------|-------|
| `SOURCE 10` | Computer 1 (RGB) |
| `SOURCE 11` | Computer 2 |
| `SOURCE 14` | BNC |
| `SOURCE 20` | Video |
| `SOURCE 21` | S-Video |
| `SOURCE 30` | USB Display |
| `SOURCE 40` | LAN |
| `SOURCE 41` | USB-A |
| `SOURCE A0` | HDMI 1 |
| `SOURCE A1` | HDMI 2 |
| `SOURCE ?` | Query current |

### Mute Control

| Command | Description |
|---------|-------------|
| `MUTE ON` | A/V Mute on |
| `MUTE OFF` | A/V Mute off |
| `MUTE ?` | Query state |

### Volume Control

| Command | Description |
|---------|-------------|
| `VOL value` | Set volume (0-255) |
| `VOL INC` | Increase |
| `VOL DEC` | Decrease |
| `VOL ?` | Query level |

### Image Adjustments

| Command | Description | Range |
|---------|-------------|-------|
| `BRIGHT value` | Brightness | 0-255 |
| `BRIGHT INC/DEC` | Adjust | - |
| `CONTRAST value` | Contrast | 0-255 |
| `CONTRAST INC/DEC` | Adjust | - |
| `CMODE mode` | Color mode | See below |

**Color Modes:**
- `00` - Dynamic
- `01` - Presentation
- `02` - Theatre
- `03` - sRGB
- `06` - Custom

### Status Queries

| Command | Returns |
|---------|---------|
| `LAMP ?` | Lamp hours |
| `ERR ?` | Error code |
| `SNO ?` | Serial number |

### Freeze & Blank

| Command | Description |
|---------|-------------|
| `FREEZE ON` | Freeze image |
| `FREEZE OFF` | Unfreeze |
| `BLANK ON` | Blank screen |
| `BLANK OFF` | Show image |

## Response Codes

| Response | Meaning |
|----------|---------|
| `:` | Ready for command |
| `ERR` | Error occurred |
| `value:` | Query result |

### Error Codes

| Code | Description |
|------|-------------|
| `ERR` | General error |
| `ERR 01` | Undefined command |
| `ERR 02` | Invalid parameter |
| `ERR 03` | Unavailable (warming/cooling) |

## Complete Example

```python
import socket

def epson_command(host, command, port=3629):
    """Send ESC/VP21 command to Epson projector."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    sock.connect((host, port))

    # Read initial response
    response = sock.recv(1024)

    # Send command with CR
    sock.send(f"{command}\r".encode())

    # Read response until ':'
    response = b""
    while True:
        data = sock.recv(1024)
        response += data
        if b":" in data:
            break

    sock.close()
    return response.decode().strip()

# Examples
print(epson_command("192.168.1.100", "PWR ?"))      # PWR=01:
print(epson_command("192.168.1.100", "PWR ON"))     # :
print(epson_command("192.168.1.100", "SOURCE A0"))  # HDMI 1
print(epson_command("192.168.1.100", "LAMP ?"))     # LAMP=1234:
```

## Model Compatibility

### Full ESC/VP21 Support
- Business projectors (EB-xxxx series)
- Education projectors
- Large venue projectors

### Limited Support
- Home Cinema projectors (may have reduced command set)
- Older models (may not support all inputs)

### PJLink Alternative
Most Epson projectors also support PJLink on port 4352, which provides:
- Standardized commands
- Wider compatibility
- Simpler authentication

## Official Documentation

- [ESC/VP21 Command User's Guide](https://files.support.epson.com/pdf/pl600p/pl600pcm.pdf)
- [ESC/VP21 Commands Reference](https://files.support.epson.com/docid/cpd6/cpd65860/EN/Monitoring/Reference/esc_vp21_command_list.html)
- [Epson Europe Documentation](https://download.epson-europe.com/pub/download/3222/epson322269eu.pdf)
- [Atlona IP Control Guide](https://support.atlona.com/hc/en-us/articles/360048888054-IP-Control-of-Epson-Projectors)
