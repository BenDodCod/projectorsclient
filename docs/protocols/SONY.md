# Sony Projector Protocol (ADCP)

Advanced Display Control Protocol for Sony professional projectors.

## Overview

| Property | Value |
|----------|-------|
| Protocol Name | ADCP (Advanced Display Control Protocol) |
| Port | TCP 53595 |
| Type | Text-based ASCII |
| Authentication | SHA-256 (optional) |
| PJLink Support | Yes |

## Connection Settings

```
Port: 53595 (TCP)
Encoding: ASCII
Terminator: CR+LF (\r\n)
Timeout: 30 seconds recommended
```

## Authentication

### No Authentication
Server sends: `NOKEY\r\n`
Client can send commands immediately.

### With Authentication
Server sends: `[random_string]\r\n`
- Random string is 8+ characters

Client must:
1. Concatenate: `random + password`
2. Calculate SHA-256 hash
3. Send 64-char hex hash + CR+LF

### Example

```python
import hashlib

random = "1a2b3c4d"
password = "password1234"
combined = random + password
sha256_hash = hashlib.sha256(combined.encode()).hexdigest()
# Result: 64-character hex string
# Send: hash + "\r\n"
```

### Authentication Response
- Success: `OK\r\n`
- Failure: `err_auth\r\n` (connection closed)

## Command Format

### Structure
```
[command] [parameter]\r\n
```

- Commands are lowercase ASCII
- Terminated with CR+LF
- Get commands use `?` as parameter

### Response Format
- Success: `ok\r\n`
- Data: `[value]\r\n`
- Error: `ERR[code]\r\n`

## Command Reference

### Power Control

| Command | Description |
|---------|-------------|
| `power on` | Power on |
| `power off` | Power off |
| `power_status ?` | Query power state |

**Power Status Values:**
- `standby` - Power off
- `startup` - Powering on
- `on` - Power on
- `cooling1`, `cooling2` - Cooling phases

### Input Selection

| Command | Input |
|---------|-------|
| `input_terminal rgb1` | RGB terminal 1 |
| `input_terminal dvi1` | DVI terminal 1 |
| `input_terminal hdmi1` | HDMI terminal 1 |
| `input_terminal hdmi2` | HDMI terminal 2 |
| `input_terminal hdmi3` | HDMI terminal 3 |
| `input_terminal hdmi4` | HDMI terminal 4 |
| `input_terminal svideo1` | S-Video terminal 1 |
| `input_terminal usb` | USB input |
| `input_terminal network` | Network input |
| `input_terminal ?` | Query current input |

### Mute Control

| Command | Description |
|---------|-------------|
| `picture_muting on` | Video mute on |
| `picture_muting off` | Video mute off |
| `picture_muting ?` | Query state |

### Image Adjustments

| Command | Description |
|---------|-------------|
| `brightness [value]` | Set brightness |
| `brightness ?` | Query brightness |
| `contrast [value]` | Set contrast |
| `contrast ?` | Query contrast |
| `color [value]` | Set color |
| `color ?` | Query color |
| `sharpness [value]` | Set sharpness |
| `sharpness ?` | Query sharpness |

### Menu Navigation

| Command | Description |
|---------|-------------|
| `menu up` | Navigate up |
| `menu down` | Navigate down |
| `menu left` | Navigate left |
| `menu right` | Navigate right |
| `menu enter` | Select/confirm |
| `menu exit` | Exit menu |

### Remote Control Emulation

| Command | Description |
|---------|-------------|
| `send_remote_code [hex]` | Send remote key code |

## Error Codes

| Code | Meaning |
|------|---------|
| ERR1 | Undefined command |
| ERR2 | Invalid parameter |
| ERR3 | Unavailable time (projector busy) |
| ERR4 | Projector failure |
| err_auth | Authentication failed |

## Complete Example

```python
import socket
import hashlib

def sony_adcp(host, command, password=None):
    """Send ADCP command to Sony projector."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    sock.connect((host, 53595))

    # Read authentication challenge
    challenge = sock.recv(1024).decode().strip()

    if challenge != "NOKEY":
        # Authentication required
        combined = challenge + password
        sha256_hash = hashlib.sha256(combined.encode()).hexdigest()
        sock.send(f"{sha256_hash}\r\n".encode())

        # Check auth response
        auth_response = sock.recv(1024).decode().strip()
        if auth_response != "OK":
            sock.close()
            raise Exception(f"Auth failed: {auth_response}")

    # Send command
    sock.send(f"{command}\r\n".encode())
    response = sock.recv(1024).decode().strip()

    sock.close()
    return response

# Usage examples
print(sony_adcp("192.168.1.100", "power_status ?", "mypassword"))
print(sony_adcp("192.168.1.100", "power on", "mypassword"))
print(sony_adcp("192.168.1.100", "input_terminal hdmi1", "mypassword"))
```

## Web Interface

Sony projectors also provide a web interface for configuration:
- URL: `http://[projector_ip]/`
- Allows disabling authentication if needed

## Timing Considerations

- Allow 20-30 seconds for power on warm-up
- Allow 30-60 seconds for cooling after power off
- Some commands return ERR3 during transitions

## PJLink Alternative

Sony projectors support PJLink on port 4352:
```
%1POWR 1\r     # Power on
%1INPT 31\r    # HDMI 1
```

PJLink may be simpler for basic operations.

## Official Documentation

- [Sony Protocol Manual](https://pro.sony/s3/2018/07/05125823/Sony_Protocol-Manual_1st-Edition.pdf)
- [Sony Command List](https://pro.sony/s3/2018/07/05140342/Sony_Protocol-Manual_Supported-Command-List_1st-Edition.pdf)
