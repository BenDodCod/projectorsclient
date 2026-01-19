# JVC D-ILA Projector Protocol

Proprietary binary protocol for JVC D-ILA projectors.

## Overview

| Property | Value |
|----------|-------|
| Protocol Type | Binary with handshake |
| Network Port | TCP 20554 |
| RS-232 Settings | 19200 baud, 8-N-1 |
| Authentication | None (handshake required) |
| PJLink Support | **NO** |

**Important:** JVC projectors do NOT support PJLink!

## Connection Settings

### Network
```
Port: 20554 (TCP)
Binary protocol
Handshake required before commands
5-second timeout between messages
```

### RS-232
```
Baud Rate: 19200
Data Bits: 8
Parity: None
Stop Bits: 1
```

## Connection Handshake

### Required Sequence

1. **Connect** to TCP 20554
2. **Receive:** `PJ_OK` from projector
3. **Send:** `PJREQ` to request control
4. **Receive:** `PJACK` to confirm

After handshake, commands can be sent.

### Timeout Rules
- Must send `PJREQ` within 5 seconds of `PJ_OK`
- Must send command within 5 seconds of `PJACK`
- Connection closes after 5 seconds of inactivity

### Handshake Example

```python
import socket

def jvc_connect(host, port=20554):
    """Connect to JVC projector with handshake."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    sock.connect((host, port))

    # Wait for PJ_OK
    response = sock.recv(1024)
    if b"PJ_OK" not in response:
        raise Exception(f"Expected PJ_OK, got: {response}")

    # Send PJREQ
    sock.send(b"PJREQ")

    # Wait for PJACK
    response = sock.recv(1024)
    if b"PJACK" not in response:
        raise Exception(f"Expected PJACK, got: {response}")

    return sock
```

## Command Format

### Structure
```
21 89 01 [CMD] [CMD] [PARAM] 0A
```

- `21` - Command header
- `89 01` - Unit ID (fixed for most models)
- `[CMD]` - 2-byte ASCII command code
- `[PARAM]` - Parameter byte
- `0A` - Line feed terminator

### Commands as Hex

| Command | Hex Bytes | Description |
|---------|-----------|-------------|
| Power On | `21 89 01 50 57 31 0A` | PW1 |
| Power Off | `21 89 01 50 57 30 0A` | PW0 |
| HDMI 1 | `21 89 01 49 50 36 0A` | IP6 |
| HDMI 2 | `21 89 01 49 50 37 0A` | IP7 |
| Component | `21 89 01 49 50 32 0A` | IP2 |

## Command Reference

### Power Control (PW)

| Command | Bytes | Description |
|---------|-------|-------------|
| Power On | `21 89 01 50 57 31 0A` | PW + '1' |
| Power Off | `21 89 01 50 57 30 0A` | PW + '0' |

### Input Selection (IP)

| Input | Bytes | Parameter |
|-------|-------|-----------|
| S-Video | `21 89 01 49 50 30 0A` | IP + '0' |
| Video | `21 89 01 49 50 31 0A` | IP + '1' |
| Component | `21 89 01 49 50 32 0A` | IP + '2' |
| PC | `21 89 01 49 50 33 0A` | IP + '3' |
| HDMI 1 | `21 89 01 49 50 36 0A` | IP + '6' |
| HDMI 2 | `21 89 01 49 50 37 0A` | IP + '7' |

### Picture Mode (PM)

| Mode | Bytes | Parameter |
|------|-------|-----------|
| Film | `21 89 01 50 4D 30 0A` | PM + '0' |
| Cinema | `21 89 01 50 4D 31 0A` | PM + '1' |
| Natural | `21 89 01 50 4D 33 0A` | PM + '3' |
| User 1 | `21 89 01 50 4D 43 0A` | PM + 'C' |

### Lens Control

| Function | Bytes |
|----------|-------|
| Lens Memory 1 | `21 89 01 49 4E 4D 4C 31 0A` |
| Lens Memory 2 | `21 89 01 49 4E 4D 4C 32 0A` |

## Response Codes

| Response | Meaning |
|----------|---------|
| `06` (ACK) | Command received and executed |
| `15` (NAK) | Command not understood |

## Complete Example

```python
import socket

class JVCProjector:
    def __init__(self, host, port=20554):
        self.host = host
        self.port = port
        self.sock = None

    def connect(self):
        """Connect with handshake."""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(5)
        self.sock.connect((self.host, self.port))

        # Handshake
        response = self.sock.recv(1024)
        if b"PJ_OK" not in response:
            raise Exception("Handshake failed: no PJ_OK")

        self.sock.send(b"PJREQ")
        response = self.sock.recv(1024)
        if b"PJACK" not in response:
            raise Exception("Handshake failed: no PJACK")

    def send_command(self, cmd_bytes):
        """Send command and get response."""
        self.sock.send(bytes(cmd_bytes))
        return self.sock.recv(1024)

    def power_on(self):
        """Power on projector."""
        return self.send_command([0x21, 0x89, 0x01, 0x50, 0x57, 0x31, 0x0A])

    def power_off(self):
        """Power off projector."""
        return self.send_command([0x21, 0x89, 0x01, 0x50, 0x57, 0x30, 0x0A])

    def select_hdmi1(self):
        """Select HDMI 1 input."""
        return self.send_command([0x21, 0x89, 0x01, 0x49, 0x50, 0x36, 0x0A])

    def select_hdmi2(self):
        """Select HDMI 2 input."""
        return self.send_command([0x21, 0x89, 0x01, 0x49, 0x50, 0x37, 0x0A])

    def disconnect(self):
        """Close connection."""
        if self.sock:
            self.sock.close()
            self.sock = None

# Usage
proj = JVCProjector("192.168.1.100")
proj.connect()
proj.power_on()
proj.select_hdmi1()
proj.disconnect()
```

## Timing Considerations

- **5-second timeout** - Connection closes if idle
- **Power on:** ~60 seconds warm-up
- **Power off:** ~90 seconds cooling
- Commands may fail during transitions

## Model Variations

### D-ILA Series
- DLA-X series
- DLA-NX series
- DLA-RS series

### Unit ID
Most models use `89 01`. Check documentation for specific model.

## No PJLink!

JVC D-ILA projectors do **NOT** support PJLink. You must use the proprietary protocol described above.

## Official Documentation

- [JVC Remote Control Guide](https://support.jvc.com/consumer/support/documents/DILAremoteControlGuide.pdf)
- [JVC External Command List](http://www.us.jvc.com/projectors/pdf/2018_ILA-FPJ_Ext_Command_List_v1.2.pdf)
