# Optoma Projector Protocol

RS-232 and network control protocol for Optoma projectors.

## Overview

| Property | Value |
|----------|-------|
| Protocol Type | ASCII text |
| Network Port | TCP (via RS-232 adapter) |
| RS-232 Settings | 9600 baud, 8-N-1 |
| Authentication | None |
| PJLink Support | Yes (most models) |

## Connection Settings

### RS-232
```
Baud Rate: 9600
Data Bits: 8
Parity: None
Stop Bits: 1
Flow Control: None
D-Sub 9 Pin: Pins 2, 3, 5
```

### Network
Network control typically via RS-232-to-IP adapter or built-in LAN port (model dependent).

## Command Format

### Structure
```
~XX[command] [parameter]\r
```

- `~` - Command prefix
- `XX` - Projector ID (00 = all projectors)
- `[command]` - 2-digit command code
- `[parameter]` - Optional value
- `\r` - Carriage return (0x0D)

### Example
```
~XX00 1\r     # Power on (command 00, param 1)
```

## Command Reference

### Power Control

| Command | Description |
|---------|-------------|
| `~XX00 1` | Power ON |
| `~XX00 2` | Power OFF |
| `~XX00 ?` | Query power state |

### Input Selection

| Command | Input |
|---------|-------|
| `~XX12 1` | VGA 1 |
| `~XX12 5` | VGA 2 |
| `~XX12 6` | BNC |
| `~XX12 7` | Video (Composite) |
| `~XX12 8` | S-Video |
| `~XX12 10` | Component |
| `~XX12 15` | HDMI 1 |
| `~XX12 16` | HDMI 2 |
| `~XX12 18` | 3G-SDI |
| `~XX12 19` | DisplayPort |
| `~XX12 ?` | Query current input |

### Resync

| Command | Description |
|---------|-------------|
| `~XX01 1` | Resync |

### Mute Control

| Command | Description |
|---------|-------------|
| `~XX02 1` | AV Mute ON |
| `~XX02 2` | AV Mute OFF |
| `~XX02 ?` | Query mute state |

### Brightness Control

| Command | Description |
|---------|-------------|
| `~XX06 0-100` | Set brightness (0-100) |
| `~XX06 +` | Increase brightness |
| `~XX06 -` | Decrease brightness |
| `~XX06 ?` | Query brightness |

### Contrast Control

| Command | Description |
|---------|-------------|
| `~XX07 0-100` | Set contrast (0-100) |
| `~XX07 +` | Increase contrast |
| `~XX07 -` | Decrease contrast |
| `~XX07 ?` | Query contrast |

### Sharpness

| Command | Description |
|---------|-------------|
| `~XX08 0-10` | Set sharpness (0-10) |
| `~XX08 ?` | Query sharpness |

### Display Mode

| Command | Mode |
|---------|------|
| `~XX20 1` | Presentation |
| `~XX20 2` | Bright |
| `~XX20 3` | Cinema |
| `~XX20 4` | sRGB |
| `~XX20 5` | DICOM |
| `~XX20 6` | User 1 |
| `~XX20 7` | User 2 |

### Aspect Ratio

| Command | Ratio |
|---------|-------|
| `~XX60 1` | 4:3 |
| `~XX60 2` | 16:9 |
| `~XX60 3` | 16:10 |
| `~XX60 4` | LBX |
| `~XX60 5` | Native |
| `~XX60 6` | Auto |

### Freeze

| Command | Description |
|---------|-------------|
| `~XX03 1` | Freeze ON |
| `~XX03 2` | Freeze OFF |

### Volume Control

| Command | Description |
|---------|-------------|
| `~XX81 0-10` | Set volume (0-10) |
| `~XX81 +` | Volume up |
| `~XX81 -` | Volume down |

### Status Queries

| Command | Returns |
|---------|---------|
| `~XX15 ?` | Lamp hours |
| `~XX50 ?` | Model name |

## Response Format

| Response | Meaning |
|----------|---------|
| `P` | OK / Success |
| `F` | Fail / Error |
| `[value]` | Query result |

## Complete Example

```python
import socket

def optoma_command(host, command, port=9999):
    """Send command to Optoma projector (via IP adapter)."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    sock.connect((host, port))

    # Send command with CR
    full_command = f"{command}\r"
    sock.send(full_command.encode())

    # Read response
    response = sock.recv(1024).decode().strip()
    sock.close()

    return response

# For direct RS-232
import serial

def optoma_rs232(port, command):
    """Send command via RS-232."""
    ser = serial.Serial(
        port=port,
        baudrate=9600,
        bytesize=8,
        parity='N',
        stopbits=1,
        timeout=2
    )

    full_command = f"{command}\r"
    ser.write(full_command.encode())
    response = ser.read(100).decode().strip()
    ser.close()

    return response

# Examples
print(optoma_rs232("COM3", "~XX00 1"))     # Power on
print(optoma_rs232("COM3", "~XX12 15"))    # HDMI 1
print(optoma_rs232("COM3", "~XX15 ?"))     # Lamp hours
```

## AMX Integration

Optoma projectors are AMX compatible. For AMX control systems:

```netlinx
DEFINE_DEVICE
dvProj = 5001:1:0

// Set baud rate
SEND_COMMAND dvProj,'SET BAUD 9600,N,8,1'

// Send commands
SEND_STRING dvProj,"'~XX00 1',$0D"  // Power on
SEND_STRING dvProj,"'~XX12 15',$0D" // HDMI 1
```

## Projector ID

The `XX` in commands is the projector ID:
- `00` = All projectors (broadcast)
- `01-99` = Individual projector address

Set projector ID in the menu for multi-projector setups.

## Cable Notes

The RS-232 cable included with Optoma projectors:
- Uses pins 2, 3, and 5 only
- May be for firmware updates only
- Custom 3-pin cable may work better

## Timing Considerations

- Power on: ~20 seconds warm-up
- Power off: ~30 seconds cooling
- Command interval: 100ms minimum
- Some commands unavailable during transitions

## PJLink Alternative

Most Optoma projectors support PJLink on port 4352:
```
%1POWR 1\r     # Power on
%1INPT 31\r    # HDMI 1
```

PJLink provides standardized control.

## Model Variations

### Business/Education
- Full command set
- Network port available

### Home Cinema
- May have reduced commands
- RS-232 primary interface

### Portable
- Basic commands only
- No network port

## Official Documentation

- [Optoma RS232 Protocol Function List](https://www.optomausa.com/ContentStorage/Documents/471bc1d6-63f6-4825-aeef-2414e9cc5f99.pdf)
- [Optoma RS232 Command Table](https://www.optoma.de/uploads/rs232/ds309-rs232-en.pdf)
- [Optoma Europe Documentation](https://www.optomaeurope.com/ContentStorage/Documents/17f005d3-0d27-4822-b9f6-20f04085dbaf.pdf)
