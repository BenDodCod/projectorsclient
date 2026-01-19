# BenQ Projector Protocol

Simple text-based control protocol for BenQ projectors.

## Overview

| Property | Value |
|----------|-------|
| Protocol Type | Text-based ASCII |
| Network Port | TCP 8000 |
| RS-232 Settings | 9600/115200 baud, 8-N-1 |
| Authentication | None |
| PJLink Support | Yes |

## Connection Settings

### Network
```
Port: 8000 (TCP)
Encoding: ASCII
No authentication required
```

### RS-232
```
Baud Rate: 9600 or 115200 (model dependent)
Data Bits: 8
Parity: None
Stop Bits: 1
Flow Control: None
```

## Command Format

### Structure
```
<CR>*[command]=[value]#<CR>
```

- `<CR>` = Carriage Return (0x0D)
- `*` = Command prefix
- `command` = Command name (lowercase)
- `=` = Separator
- `value` = Parameter value
- `#` = Command terminator

### Query Format
```
<CR>*[command]=?#<CR>
```

## Response Format

| Response | Meaning |
|----------|---------|
| `*[command]=[value]#` | Success with value |
| `+` | Command acknowledged |
| `-` | Command failed/error |

## Command Reference

### Power Control

| Command | Description |
|---------|-------------|
| `<CR>*pow=on#<CR>` | Power on |
| `<CR>*pow=off#<CR>` | Power off |
| `<CR>*pow=?#<CR>` | Query power state |

### Input Selection (sour)

| Command | Input |
|---------|-------|
| `*sour=hdmi#` | HDMI |
| `*sour=hdmi2#` | HDMI 2 |
| `*sour=computer#` | Computer/RGB |
| `*sour=computer2#` | Computer 2 |
| `*sour=video#` | Video |
| `*sour=svideo#` | S-Video |
| `*sour=ypbpr#` | Component |
| `*sour=usb#` | USB |
| `*sour=network#` | Network |
| `*sour=?#` | Query current |

### Mute Control

| Command | Description |
|---------|-------------|
| `*mute=on#` | Mute on |
| `*mute=off#` | Mute off |
| `*mute=?#` | Query state |

### Audio Control

| Command | Description |
|---------|-------------|
| `*vol=0-20#` | Set volume (0-20) |
| `*vol=+#` | Volume up |
| `*vol=-#` | Volume down |
| `*vol=?#` | Query volume |

### Image Adjustments

| Command | Range | Description |
|---------|-------|-------------|
| `*bright=0-100#` | 0-100 | Brightness |
| `*con=0-100#` | 0-100 | Contrast |
| `*color=0-100#` | 0-100 | Color |
| `*sharp=0-15#` | 0-15 | Sharpness |

### Picture Mode (appmod)

| Command | Mode |
|---------|------|
| `*appmod=dynamic#` | Dynamic |
| `*appmod=std#` | Standard |
| `*appmod=cine#` | Cinema |
| `*appmod=game#` | Game |
| `*appmod=user#` | User |

### Aspect Ratio (asp)

| Command | Ratio |
|---------|-------|
| `*asp=auto#` | Auto |
| `*asp=4:3#` | 4:3 |
| `*asp=16:9#` | 16:9 |
| `*asp=16:10#` | 16:10 |
| `*asp=real#` | Real/Native |

### 3D Mode

| Command | Mode |
|---------|------|
| `*3d=off#` | 3D off |
| `*3d=auto#` | Auto detect |
| `*3d=tb#` | Top-bottom |
| `*3d=fs#` | Frame sequential |
| `*3d=sbs#` | Side-by-side |

### Blank/Freeze

| Command | Description |
|---------|-------------|
| `*blank=on#` | Blank screen |
| `*blank=off#` | Show image |
| `*freeze=on#` | Freeze image |
| `*freeze=off#` | Unfreeze |

### Status Queries

| Command | Returns |
|---------|---------|
| `*ltim=?#` | Lamp hours |
| `*modelname=?#` | Model name |
| `*session=?#` | Session info |

## Complete Example

```python
import socket

def benq_command(host, command, port=8000):
    """Send command to BenQ projector."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    sock.connect((host, port))

    # Format command with CR prefix and suffix
    full_command = f"\r*{command}#\r"
    sock.send(full_command.encode())

    # Read response
    response = sock.recv(1024).decode().strip()
    sock.close()

    return response

# Examples
print(benq_command("192.168.1.100", "pow=?"))      # Query power
print(benq_command("192.168.1.100", "pow=on"))     # Power on
print(benq_command("192.168.1.100", "sour=hdmi"))  # Select HDMI
print(benq_command("192.168.1.100", "bright=75"))  # Set brightness
print(benq_command("192.168.1.100", "ltim=?"))     # Lamp hours
```

## RS-232 Example

```python
import serial

def benq_rs232(port, command):
    """Send command via RS-232."""
    ser = serial.Serial(
        port=port,
        baudrate=9600,
        bytesize=8,
        parity='N',
        stopbits=1,
        timeout=2
    )

    full_command = f"\r*{command}#\r"
    ser.write(full_command.encode())
    response = ser.read(100).decode().strip()
    ser.close()

    return response

# Example
print(benq_rs232("COM3", "pow=on"))
```

## Model Variations

### Business Projectors
- Full command set support
- Network control standard

### Home Cinema
- May have limited commands
- Check specific model documentation

### Portable/Education
- Basic commands supported
- Volume may have different range

## Timing Considerations

- Power on: ~20 seconds warm-up
- Power off: ~30 seconds cooling
- Command interval: 100ms minimum recommended

## PJLink Alternative

BenQ projectors also support PJLink on port 4352:
```
%1POWR 1\r     # Power on
%1INPT 31\r    # HDMI
```

## Official Documentation

- [BenQ RS232 Control Guide](https://esupportdownload.benq.com/esupport/Projector/Control%20Protocols/PU9530/RS232%20Control%20Guide_0_Windows7_Windows8_WinXP.pdf)
- [BenQ Network Operation Guide](https://esupportdownload.benq.com/esupport/Projector/UserManual/Projector_um_User%20Manual_20120920_123347Network-Operation-LAN1_EN.pdf)
