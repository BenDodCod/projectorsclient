# PJLink Protocol Technical Specification

## Overview

PJLink is an industry-standard network protocol for controlling and monitoring projectors, developed by JBMIA (Japan Business Machine and Information System Industries Association).

### Key Characteristics

| Property | Value |
|----------|-------|
| **Protocol** | TCP/IP (commands), UDP (search/notifications) |
| **Default Port** | 4352 (TCP and UDP) |
| **Classes** | Class 1 (basic), Class 2 (extended) |
| **Character Encoding** | ASCII |
| **Authentication** | Optional MD5 (Class 1), MD5/SHA-256 (Class 2) |

### Manufacturer Support

PJLink is widely supported across manufacturers including:
- Epson
- Panasonic
- NEC
- Sony
- BenQ
- Hitachi
- Mitsubishi
- Casio
- Canon
- Sharp
- Ricoh

---

## Command Format

### Request Structure

```
<Header><Class><Command><Separator><Parameter><Terminator>
```

| Component | Description | Example |
|-----------|-------------|---------|
| **Header** | Percent symbol | `%` |
| **Class** | Protocol class (1 or 2) | `1` |
| **Command** | 4 ASCII characters | `POWR` |
| **Separator** | Space character | ` ` |
| **Parameter** | Command-specific | `1` |
| **Terminator** | Carriage return (0x0D) | `\r` |

### Example Commands

```
%1POWR 1\r      # Power on (Class 1)
%1INPT 31\r     # Select HDMI 1 input
%2FREZ 1\r      # Freeze on (Class 2)
%1POWR ?\r      # Query power status
```

---

## Response Format

### Success Response

```
<Header><Class><Command>=<Response><Terminator>
```

**Example:**
```
%1POWR=OK\r     # Power command accepted
%1POWR=1\r      # Power status: ON
```

### Error Responses

| Error Code | Description | Meaning |
|------------|-------------|---------|
| **ERR1** | Undefined command | Command not recognized |
| **ERR2** | Out of parameter | Invalid parameter value |
| **ERR3** | Unavailable time | Command cannot be executed now |
| **ERR4** | Projector failure | Hardware error detected |

**Example:**
```
%1INPT=ERR2\r   # Invalid input parameter
```

---

## Authentication

### No Authentication

**Server Response:**
```
PJLINK 0
```

Client proceeds without authentication.

### With Authentication (Class 1)

**Server Response:**
```
PJLINK 1 [8-byte hex random]
```

**Example:**
```
PJLINK 1 a1b2c3d4
```

**Client Authentication:**
1. Concatenate random + password: `a1b2c3d4mypassword`
2. Calculate MD5 hash: `5d41402abc4b2a76b9719d911017c592`
3. Prepend hash to command:
```
5d41402abc4b2a76b9719d911017c592%1POWR 1\r
```

### Class 2 Authentication

Class 2 supports both MD5 and SHA-256 authentication methods.

---

## Command Reference

### Power Commands (POWR)

| Command | Parameter | Description | Response |
|---------|-----------|-------------|----------|
| `%1POWR` | `0` | Power Off | `OK` |
| `%1POWR` | `1` | Power On | `OK` |
| `%1POWR` | `?` | Query power status | `0` (off), `1` (on), `2` (cooling), `3` (warming) |

**Examples:**
```
# Power on the projector
%1POWR 1\r
Response: %1POWR=OK\r

# Query power status
%1POWR ?\r
Response: %1POWR=1\r  # Projector is on
```

---

### Input Selection Commands (INPT)

#### Input Type Codes

| Input Type | Code Range | Description |
|------------|------------|-------------|
| **RGB** | 11-19 | Analog RGB/VGA inputs |
| **Video** | 21-29 | Composite/S-Video inputs |
| **Digital** | 31-39 | HDMI/DVI/DisplayPort inputs |
| **Storage** | 41-49 | USB/SD card inputs |
| **Network** | 51-59 | Network/streaming inputs |

**Format:** `XY` where X = type (1-5), Y = number (1-9)

#### Common Input Codes

| Code | Input |
|------|-------|
| `11` | RGB 1 (VGA 1) |
| `12` | RGB 2 (VGA 2) |
| `21` | Video 1 |
| `31` | Digital 1 (HDMI 1) |
| `32` | Digital 2 (HDMI 2) |
| `33` | Digital 3 (HDMI 3) |

**Examples:**
```
# Select HDMI 1
%1INPT 31\r
Response: %1INPT=OK\r

# Query current input
%1INPT ?\r
Response: %1INPT=31\r  # Currently on HDMI 1
```

---

### Mute Commands (AVMT)

#### Mute Parameter Codes

| Parameter | Video | Audio | Description |
|-----------|-------|-------|-------------|
| `10` | Off | - | Video mute off |
| `11` | On | - | Video mute on (blank screen) |
| `20` | - | Off | Audio mute off |
| `21` | - | On | Audio mute on |
| `30` | Off | Off | Both off |
| `31` | On | On | Both on |

**Examples:**
```
# Mute video (blank screen)
%1AVMT 11\r
Response: %1AVMT=OK\r

# Unmute both video and audio
%1AVMT 30\r
Response: %1AVMT=OK\r

# Query mute status
%1AVMT ?\r
Response: %1AVMT=31\r  # Both video and audio muted
```

---

### Error Status Query (ERST)

Returns a 6-digit status code representing different subsystems.

#### Status Code Format

```
<Fan><Lamp><Temperature><Cover><Filter><Other>
```

#### Status Values

| Value | Meaning |
|-------|---------|
| `0` | No error/warning |
| `1` | Warning |
| `2` | Error |

**Example:**
```
%1ERST ?\r
Response: %1ERST=000000\r  # All systems normal
Response: %1ERST=100020\r  # Fan warning, filter error
```

#### Status Interpretation

| Position | Subsystem | Warning Example | Error Example |
|----------|-----------|-----------------|---------------|
| 1 | Fan | Fan running slow | Fan failure |
| 2 | Lamp | Lamp hours high | Lamp failure |
| 3 | Temperature | High temperature | Overheat shutdown |
| 4 | Cover | Cover opened | Cover interlock active |
| 5 | Filter | Filter dirty | Filter clogged |
| 6 | Other | General warning | General error |

---

### Lamp Status Query (LAMP)

Returns lamp hours and on/off status.

**Format:** `<Hours> <Status>[ <Hours2> <Status2>]...`

| Status | Meaning |
|--------|---------|
| `0` | Lamp off |
| `1` | Lamp on |

**Examples:**
```
%1LAMP ?\r
Response: %1LAMP=1234 1\r  # 1234 hours, lamp on

# Dual-lamp projector
Response: %1LAMP=1500 1 2300 0\r  # Lamp1: 1500h (on), Lamp2: 2300h (off)
```

---

### Information Queries

| Command | Description | Example Response |
|---------|-------------|------------------|
| `%1NAME ?` | Projector name | `Boardroom East` |
| `%1INF1 ?` | Manufacturer name | `Epson` |
| `%1INF2 ?` | Model name | `EB-2250U` |
| `%1INFO ?` | Additional info | `Firmware 1.2.3` |
| `%1CLSS ?` | PJLink class | `1` or `2` |

**Examples:**
```
%1INF2 ?\r
Response: %1INF2=EB-2250U\r

%1CLSS ?\r
Response: %1CLSS=2\r  # Supports Class 2
```

---

## Class 2 Extended Commands

### Serial Number and Version

| Command | Description | Example Response |
|---------|-------------|------------------|
| `%2SNUM ?` | Serial number | `ABC123456789` |
| `%2SVER ?` | Software version | `1.05.002` |

### Input Information

| Command | Description | Example Response |
|---------|-------------|------------------|
| `%2INST ?` | Available inputs list | `11 21 31 32` |
| `%2INNM XX ?` | Input name for code XX | `HDMI 1` |

**Example:**
```
# Get available inputs
%2INST ?\r
Response: %2INST=11 31 32 33\r  # VGA, HDMI1, HDMI2, HDMI3

# Get name for HDMI 1
%2INNM 31 ?\r
Response: %2INNM=HDMI 1\r
```

### Resolution Information

| Command | Description | Example Response |
|---------|-------------|------------------|
| `%2IRES ?` | Current resolution | `1920x1080` |
| `%2RRES ?` | Recommended resolution | `1920x1200` |

### Maintenance Information

| Command | Description | Example Response |
|---------|-------------|------------------|
| `%2FILT ?` | Filter usage hours | `450` |
| `%2RLMP ?` | Replacement lamp model | `ELPLP95` |
| `%2RFIL ?` | Replacement filter model | `ELPAF60` |

### Freeze Command

| Command | Parameter | Description |
|---------|-----------|-------------|
| `%2FREZ` | `0` | Freeze off |
| `%2FREZ` | `1` | Freeze on (pause image) |
| `%2FREZ` | `?` | Query freeze status |

**Example:**
```
# Freeze the current image
%2FREZ 1\r
Response: %2FREZ=OK\r
```

---

## Search Protocol (Class 2, UDP)

### Discovery Process

1. Client broadcasts search command to network on UDP port 4352
2. Projectors respond within 10 seconds
3. Response includes MAC address and other identification

**Use Case:** Automatically discover all PJLink-compatible projectors on a network

---

## Status Notification (Class 2, UDP)

### Unsolicited Status Updates

Class 2 projectors can send unsolicited status notifications via UDP.

#### Trigger Events

- Power state change (warm-up, cooling)
- Input change
- Error conditions detected
- Filter/lamp warnings

**Use Case:** Monitor projector health without continuous polling

---

## Implementation Notes

### Connection Flow

```
1. Client connects to projector TCP port 4352
2. Server responds with authentication requirement:
   - "PJLINK 0" (no auth) or
   - "PJLINK 1 <random>" (auth required)
3. If auth required, client sends <MD5(random+password)><command>
4. Server executes command and responds
5. Connection can remain open for multiple commands or close after each
```

### Timing Considerations

| Operation | Recommended Timeout |
|-----------|---------------------|
| Initial connection | 5 seconds |
| Command response | 3 seconds |
| Power on completion | 60-90 seconds |
| Power off/cooling | 30-60 seconds |
| Input switching | 3-5 seconds |

### Error Handling Best Practices

1. **ERR3 (Unavailable):** Retry after delay (especially during warm-up/cooling)
2. **ERR2 (Invalid Parameter):** Check input code compatibility
3. **ERR4 (Failure):** Query ERST for detailed error status
4. **No Response:** Check network connectivity, verify port 4352 is open

### Common Gotchas

1. **Input Codes Vary:** Not all projectors support all input codes (11-59)
   - Always query `%2INST ?` (Class 2) to get available inputs

2. **Power State Delays:** Projectors require time to warm up and cool down
   - Poll `%1POWR ?` to monitor state transitions

3. **Authentication Persistence:** Some projectors require auth per command, others per session

4. **Class Support:** Always query `%1CLSS ?` to determine supported features

---

## Code Examples

### Python: Basic Connection and Power On

```python
import socket
import hashlib

def pjlink_connect(host, port=4352, password=None):
    """Connect to PJLink projector with optional authentication."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    sock.connect((host, port))

    # Read authentication challenge
    response = sock.recv(1024).decode('ascii')

    if response.startswith('PJLINK 1'):
        # Authentication required
        random = response.split()[2]
        auth_hash = hashlib.md5((random + password).encode()).hexdigest()
        return sock, auth_hash
    elif response.startswith('PJLINK 0'):
        # No authentication
        return sock, None
    else:
        raise Exception(f"Unexpected response: {response}")

def send_command(sock, command, auth_hash=None):
    """Send PJLink command and return response."""
    if auth_hash:
        command = auth_hash + command

    sock.sendall(command.encode('ascii'))
    response = sock.recv(1024).decode('ascii')
    return response.strip()

# Example usage
sock, auth = pjlink_connect('192.168.1.100', password='mypassword')
response = send_command(sock, '%1POWR 1\r', auth)
print(f"Power on response: {response}")

# Query power status
response = send_command(sock, '%1POWR ?\r', auth)
print(f"Power status: {response}")

sock.close()
```

### Python: Query Projector Information

```python
def get_projector_info(host, password=None):
    """Retrieve comprehensive projector information."""
    sock, auth = pjlink_connect(host, password=password)

    info = {}
    commands = {
        'class': '%1CLSS ?\r',
        'name': '%1NAME ?\r',
        'manufacturer': '%1INF1 ?\r',
        'model': '%1INF2 ?\r',
        'power': '%1POWR ?\r',
        'input': '%1INPT ?\r',
        'lamp_hours': '%1LAMP ?\r',
        'errors': '%1ERST ?\r'
    }

    for key, cmd in commands.items():
        response = send_command(sock, cmd, auth)
        # Parse response (format: %1XXXX=value)
        if '=' in response:
            info[key] = response.split('=')[1].strip()

    sock.close()
    return info

# Example usage
info = get_projector_info('192.168.1.100', password='admin')
print(f"Projector: {info['manufacturer']} {info['model']}")
print(f"Lamp hours: {info['lamp_hours']}")
```

---

## Official Documentation

- **PJLink Specification v5.1:** [https://pjlink.jbmia.or.jp/english/data_cl2/PJLink_5-1.pdf](https://pjlink.jbmia.or.jp/english/data_cl2/PJLink_5-1.pdf)
- **Class 2 Additions:** [https://pjlink.jbmia.or.jp/english/data_cl2/PJLink_2-1.pdf](https://pjlink.jbmia.or.jp/english/data_cl2/PJLink_2-1.pdf)
- **JBMIA Official Site:** [https://pjlink.jbmia.or.jp/english/](https://pjlink.jbmia.or.jp/english/)

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-18 | Initial documentation created |

---

**Document Path:** `docs/protocols/PJLINK.md`
**Related Files:**
- `src/network/protocols/pjlink_protocol.py` (implementation)
- `tests/unit/test_pjlink_protocol.py` (test suite)
