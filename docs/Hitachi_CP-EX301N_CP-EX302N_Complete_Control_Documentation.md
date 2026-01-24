# Hitachi CP-EX301N / CP-EX302N Projector Complete Control Documentation

**Version:** 1.0  
**Last Updated:** January 21, 2026  
**Compatible Models:** CP-EX301N, CP-EX302N, CP-EX252N, CP-EW302N  
**Scope:** Complete RS-232C protocol, Network control, PJLink protocol, automation integration

---

## Table of Contents

1. [Product Specifications](#product-specifications)
2. [Physical Connections & Ports](#physical-connections--ports)
3. [Communication Protocols](#communication-protocols)
4. [RS-232C Command Protocol](#rs-232c-command-protocol)
5. [Complete Command Reference](#complete-command-reference)
6. [Network Control Methods](#network-control-methods)
7. [PJLink Protocol (Port 4352)](#pjlink-protocol)
8. [Remote Control IR Codes](#remote-control-ir-codes)
9. [Automation Implementation](#automation-implementation)
10. [Troubleshooting & Best Practices](#troubleshooting)

---

## Product Specifications

### Model Variants

| Feature | CP-EX301N | CP-EX302N |
|---------|-----------|-----------|
| **Panel Type** | 0.63" P-Si TFT LCD x 3 | 0.63" LCD x 3 |
| **Resolution** | XGA (1024 x 768) | XGA (1024 x 768) |
| **Brightness** | 3,200 ANSI lumens (Normal) | 3,200 ANSI lumens |
| **Eco Mode** | 2,624 ANSI lumens | 2,624 ANSI lumens |
| **Contrast Ratio** | 2,000:1 | 2,000:1 |
| **Color Depth** | 16.7 million colors | 16.7 million colors |
| **Keystone Correction** | ±30° vertical | ±30° vertical |
| **Lamp Life** | 2,000 hours (normal mode) | 2,000 hours (normal mode) |
| **Speaker Output** | 16W mono | 16W mono |
| **Power Consumption** | ~330W (AC 220-240V) | ~330W (AC 220-240V) |
| **Standby Power** | < 0.5W | < 0.5W |
| **Dimensions** | 320 × 85 × 245mm | 320 × 85 × 245mm |
| **Weight** | ~4.5kg | ~4.5kg |

### Operating Conditions

| Parameter | Specification |
|-----------|---------------|
| **Operating Temperature** | 0°C to 40°C (Normal), 0°C to 45°C (Eco mode) |
| **Storage Temperature** | -20°C to 60°C |
| **Operating Humidity** | 20% to 80% (non-condensing) |
| **Maximum Altitude** | 2,700m (non-condensing) |
| **Lamp Warmup Time** | ~60 seconds |
| **Lamp Cooldown Time** | ~10 minutes before restart |
| **Air Filter Life** | 10,000 hours |

---

## Physical Connections & Ports

### Control Ports

| Port | Type | Function | Connector | Pins |
|------|------|----------|-----------|------|
| **CONTROL IN** | RS-232C | Receive commands from PC/Controller | D-sub 9-pin | 2,3,5,7,8 |
| **CONTROL OUT** | RS-232C | Transmit to daisy-chained devices | D-sub 9-pin | 2,3,5,7,8 |
| **LAN** | Ethernet | TCP/IP, Network control | RJ-45 | Auto MDI/MDIX |
| **USB TYPE B** | Serial | Mouse/Keyboard, alternative control | USB-B | Data + Power |

### Input/Output Ports

| Port | Type | Count | Standard | Purpose |
|------|------|-------|----------|---------|
| **COMPUTER IN** | 15-pin Mini D-sub | 2 | VGA/DVI | RGB/Analog video |
| **HDMI** | Digital | 1 | HDMI 1.4a | Digital video/audio |
| **VIDEO IN** | RCA | 1 | Composite | NTSC/PAL video |
| **AUDIO IN** | 3.5mm Jack | 2 | Stereo mini | Analog audio input |
| **AUDIO IN** | RCA | 1 pair (L/R) | RCA | Analog audio input |
| **AUDIO OUT** | 3.5mm Jack | 1 | Stereo mini | Analog audio output |
| **MONITOR OUT** | 15-pin Mini D-sub | 1 | VGA passthrough | VGA loop-through |

### D-sub 9-Pin RS-232C Pinout

```
Pin 1: CD  (Carrier Detect)    - Not used
Pin 2: RD  (Receive Data)      - Data in from computer
Pin 3: TD  (Transmit Data)     - Data out to computer
Pin 4: DTR (Data Term Ready)   - Handshake (optional)
Pin 5: GND (Ground)            - Reference/Common
Pin 6: DSR (Data Set Ready)    - Handshake (optional)
Pin 7: RTS (Request to Send)   - Flow control (optional)
Pin 8: CTS (Clear to Send)     - Flow control (optional)
Pin 9: RI  (Ring Indicator)    - Not used
```

**Cable Type:** RS-232C standard cross cable (or null modem cable)

**Connection Verification:**
- Pin 2 ← TD from projector (Computer receives)
- Pin 3 → RD to projector (Computer transmits)
- Pin 5 ↔ GND (Common reference)

---

## Communication Protocols

### Available Control Methods

The Hitachi CP-EX301N/CP-EX302N supports three independent control methods:

| Method | Port | Protocol | Default | Auth | Latency |
|--------|------|----------|---------|------|---------|
| **RS-232C Serial** | CONTROL IN | Binary/Hex | 19200 bps | No | 40ms+ |
| **TCP/Telnet** | 23 | ASCII Binary | Enabled | Optional | 50-100ms |
| **Network Bridge** | 9715 | Binary + CRC | 9717 (default) | No | 50-150ms |
| **Network Bridge** | 9719 | Binary + CRC | Alternative | No | 50-150ms |
| **PJLink** | 4352 | ASCII Text | Enabled | Optional | 100-200ms |
| **Web Interface** | 80/443 | HTTP/HTTPS | 80 | Username/Password | Variable |

### Communication Settings (OPTION > SERVICE > COMMUNICATION)

**Serial Port Configuration Menu:**

```
OPTION
  └─ SERVICE
      └─ COMMUNICATION
          ├─ COMMUNICATION TYPE: OFF / Network Bridge / Daisy Chain
          ├─ SERIAL SETTINGS
          │   ├─ BAUD RATE: 4800 / 9600 / 19200 / 38400 bps
          │   ├─ DATA BITS: 8 (fixed)
          │   ├─ PARITY: NONE / ODD / EVEN
          │   ├─ STOP BITS: 1 (fixed)
          │   └─ FLOW CONTROL: NONE (fixed)
          ├─ TRANSMISSION METHOD: HALF-DUPLEX / FULL-DUPLEX
          ├─ COMMUNICATION GROUP: A-P (for daisy chain)
          ├─ COMMUNICATION ID: 1-64 (for daisy chain)
          └─ RESPONSE LIMIT TIME: OFF / 1s / 2s / 3s
```

**Recommended Baud Rate:** 19200 bps (standard across all control methods)

---

## RS-232C Command Protocol

### Frame Structure (13 Bytes)

All RS-232C commands follow identical binary frame format:

```
┌────────┬───────┬──────┬────────────┐
│ Header │  CRC  │Action│ Type+Value │
└────────┴───────┴──────┴────────────┘
  5 bytes  2 bytes 2 bytes  4 bytes
```

**Detailed Byte-by-Byte Structure:**

| Byte # | Field Name | Value | Purpose |
|--------|-----------|-------|---------|
| 0 | Header Byte 1 | BE (hex) | Protocol identifier (fixed) |
| 1 | Header Byte 2 | EF (hex) | Protocol identifier (fixed) |
| 2 | Header Byte 3 | 03 (hex) | Protocol version (fixed) |
| 3 | Header Byte 4 | 06 (hex) | Packet size indicator (fixed) |
| 4 | Header Byte 5 | 00 (hex) | Data block count (fixed) |
| 5-6 | CRC Flag | aL / aH | Checksum calculation (see table) |
| 7-8 | Action Code | bL / bH | SET/GET/INC/DEC/EXECUTE |
| 9-10 | Type Code | cL / cH | Feature category (Power, Input, Volume, etc.) |
| 11-12 | Setting Code | dL / dH | Specific value or parameter |

### Action Codes (Byte 7-8)

| Action | Hex | Use Case | Example |
|--------|-----|----------|---------|
| **SET** | 01 00 | Change setting to specific value | Set power ON |
| **GET** | 02 00 | Read current value (query status) | Query power state |
| **INCREMENT** | 04 00 | Increase value by one step | Volume up +1 |
| **DECREMENT** | 05 00 | Decrease value by one step | Volume down -1 |
| **EXECUTE** | 06 00 | Run action/command without parameters | Reset brightness |

### Response Codes

| Response | Code | Format | Meaning | Action Required |
|----------|------|--------|---------|-----------------|
| **ACK** | 06h | Single byte | Command executed successfully | None; continue |
| **NAK** | 15h | Single byte | Invalid command format | Resend with correct hex |
| **ERROR** | 1Ch 00 00h | 3 bytes | Cannot execute command | Check projector status |
| **DATA REPLY** | 1Dh xxxxh | 3 bytes | GET command response | Extract data from xxxxh |

### CRC Checksum Calculation

The CRC flag (bytes 5-6) is calculated based on the command type and ensures data integrity.

**Pre-calculated CRC values for common commands:**

| Command | Setting Code | CRC (hex) |
|---------|--------------|-----------|
| Power ON | 00 60 01 00 | BA D2 |
| Power OFF | 00 60 00 00 | 2A D3 |
| Power GET | 00 60 00 00 (GET) | 19 D3 |
| Input C1 | 00 20 00 00 | FE D2 |
| Input C2 | 00 20 04 00 | 3E D0 |
| Input HDMI | 00 20 03 00 | 0E D2 |
| Input VIDEO | 00 20 01 00 | 6E D3 |
| Volume GET C1 | 60 20 00 00 | CD CC |
| Volume INC C1 | 60 20 00 00 | AB CC |
| Volume DEC C1 | 60 20 00 00 | 7A CD |
| Mute OFF | 02 20 00 00 | 46 D3 |
| Mute ON | 02 20 01 00 | D6 D2 |
| Freeze OFF | 02 30 00 00 | 83 D2 |
| Freeze ON | 02 30 01 00 | 13 D3 |
| Brightness GET | 03 20 00 00 | 89 D2 |
| Brightness INC | 03 20 00 00 | EF D2 |
| Brightness DEC | 03 20 00 00 | 3E D3 |
| Contrast GET | 04 20 00 00 | FD D3 |
| Contrast INC | 04 20 00 00 | 9B D3 |
| Contrast DEC | 04 20 00 00 | 4A D2 |

**CRC Algorithm (for reference):**
CRC is calculated as: (256 - (sum of specific bytes % 256)) % 256
Used for error detection and command validation
See manufacturer technical manual for full CRC lookup table

### Minimum Command Timing

```
Baud Rate: 19200 bps
  └─ 1 byte transmit time: ~0.52ms
  └─ 13-byte command: ~6.77ms transmission time
  └─ Minimum between commands: 40ms (for reliability, use 50ms)
  └─ Minimum after power ON: 60 seconds (device warmup)
  └─ Minimum before power ON: 10 minutes (lamp cooldown)
```

---

## Complete Command Reference

### 1. POWER CONTROL (Type: 00 60)

**Manages projector power state and lamp.**

| Operation | Action | Hex Command | Response |
|-----------|--------|-------------|----------|
| **Power ON** | SET | `BE EF 03 06 00 BA D2 01 00 00 60 01 00` | ACK (06h) |
| **Power OFF** | SET | `BE EF 03 06 00 2A D3 01 00 00 60 00 00` | ACK (06h) |
| **Get Status** | GET | `BE EF 03 06 00 19 D3 02 00 00 60 00 00` | 1Dh 00 00 (OFF), 01 00 (ON), 02 00 (Cooling) |

**Power Status Values (from GET command):**
- `00 00` = Power OFF (Standby)
- `01 00` = Power ON (Lamp active)
- `02 00` = Cooling down (after OFF)
- `03 00` = Error/Lamp failure

**Usage Notes:**
- Power-on warmup: 60 seconds before accepting other commands
- Power-off cooldown: 10 minutes minimum before restarting
- DO NOT interrupt power cycle
- Query power status before sending operational commands

---

### 2. INPUT SOURCE SELECTION (Type: 00 20)

**Select active input terminal.**

| Input Source | Hex Command | Input Code | Max Resolution |
|-------------|-------------|-----------|-----------------|
| **COMPUTER IN1** | `BE EF 03 06 00 FE D2 01 00 00 20 00 00` | 00 00 | 1920×1200@60Hz |
| **COMPUTER IN2** | `BE EF 03 06 00 3E D0 01 00 00 20 04 00` | 04 00 | 1920×1200@60Hz |
| **HDMI** | `BE EF 03 06 00 0E D2 01 00 00 20 03 00` | 03 00 | 4K@30Hz |
| **VIDEO (Composite)** | `BE EF 03 06 00 6E D3 01 00 00 20 01 00` | 01 00 | 720×480i@60Hz |
| **S-VIDEO** | `BE EF 03 06 00 9E D3 01 00 00 20 02 00` | 02 00 | 720×480i@60Hz |
| **COMPONENT (YPbPr)** | `BE EF 03 06 00 AE D1 01 00 00 20 05 00` | 05 00 | 1080p@60Hz |
| **Get Current Input** | `BE EF 03 06 00 CD D2 02 00 00 20 00 00` | Query | Returns selected input |

**Response Format:**
- `1Dh [input_code]` - Returns currently selected input
- Query response includes 2-byte input identifier

**Supported Video Formats by Source:**

**COMPUTER IN (VGA):**
- 640×480@60/75Hz
- 800×600@60/75Hz
- 1024×768@60/75/85Hz
- 1280×1024@60/75Hz
- 1920×1200@60Hz (native max)
- WUXGA via HDCP

**HDMI:**
- 480p@60Hz
- 576p@50Hz
- 720p@60/50Hz
- 1080i@60/50Hz
- 1080p@60/50/24Hz
- 4K@30Hz (limited support)

**VIDEO (NTSC/PAL):**
- NTSC (60Hz): 720×480i
- PAL (50Hz): 720×576i
- SECAM support available

---

### 3. VOLUME CONTROL (Audio Per-Source)

**Adjusts audio output volume for each input source. NO direct SET value; use INCREMENT/DECREMENT.**

#### Volume Control Mapping

| Input Source | Type Code | GET Command | INC Command | DEC Command | Max Level |
|-------------|-----------|-------------|-------------|-------------|-----------|
| **COMPUTER IN1** | 60 20 | `BE EF 03 06 00 CD CC 02 00 60 20 00 00` | `BE EF 03 06 00 AB CC 04 00 60 20 00 00` | `BE EF 03 06 00 7A CD 05 00 60 20 00 00` | 48 |
| **COMPUTER IN2** | 64 20 | `BE EF 03 06 00 77 CC 02 00 64 20 00 00` | `BE EF 03 06 00 15 CC 04 00 64 20 00 00` | `BE EF 03 06 00 C4 CD 05 00 64 20 00 00` | 48 |
| **VIDEO** | 61 20 | `BE EF 03 06 00 BB CF 02 00 61 20 00 00` | `BE EF 03 06 00 DD CF 04 00 61 20 00 00` | `BE EF 03 06 00 0C CE 05 00 61 20 00 00` | 48 |
| **S-VIDEO** | 62 20 | `BE EF 03 06 00 2D CF 02 00 62 20 00 00` | `BE EF 03 06 00 4B CF 04 00 62 20 00 00` | `BE EF 03 06 00 9A CE 05 00 62 20 00 00` | 48 |
| **HDMI** | 63 20 | `BE EF 03 06 00 BB CF 02 00 63 20 00 00` | `BE EF 03 06 00 DD CF 04 00 63 20 00 00` | `BE EF 03 06 00 0C CE 05 00 63 20 00 00` | 48 |
| **COMPONENT** | 65 20 | `BE EF 03 06 00 2B CF 02 00 65 20 00 00` | `BE EF 03 06 00 4D CF 04 00 65 20 00 00` | `BE EF 03 06 00 9C CE 05 00 65 20 00 00` | 48 |

**Volume Control Strategy:**

1. **Query current level:** Send GET command, receive current level (0-48)
2. **Calculate delta:** target_level - current_level = steps_needed
3. **Send INC/DEC:** Send INCREMENT command (steps_needed) times
4. **Verify:** Query again to confirm new level

**Example: Set COMPUTER IN1 volume to level 30**

```
Step 1: GET current volume
  Send: BE EF 03 06 00 CD CC 02 00 60 20 00 00
  Receive: 1D XX XX (current level in XX XX)

Step 2: If current = 20, need +10
  Send 10× INCREMENT: BE EF 03 06 00 AB CC 04 00 60 20 00 00

Step 3: Verify
  Send: BE EF 03 06 00 CD CC 02 00 60 20 00 00
  Receive: 1D 1E 00 (level 30 = 0x1E)
```

---

### 4. AUDIO MUTE CONTROL (Type: 02 20)

**Enables/disables audio output without changing volume level.**

| Operation | Hex Command | Effect | Use Case |
|-----------|-------------|--------|----------|
| **Mute OFF** | `BE EF 03 06 00 46 D3 01 00 02 20 00 00` | Audio ON | Resume playback |
| **Mute ON** | `BE EF 03 06 00 D6 D2 01 00 02 20 01 00` | Audio silent | During presentations |
| **Get Mute Status** | `BE EF 03 06 00 75 D3 02 00 02 20 00 00` | Query state | Check current setting |

**Mute Status Values:**
- `00 00` = Unmuted (Audio ON)
- `01 00` = Muted (Audio OFF)

**Independent Control:**
- Mute state independent from volume setting
- Mute persists when switching inputs
- Returns to previous volume when unmuted

---

### 5. SCREEN FREEZE/PAUSE (Type: 02 30)

**Pauses video playback without losing connection to source.**

| Operation | Hex Command | Effect |
|-----------|-------------|--------|
| **Freeze OFF** | `BE EF 03 06 00 83 D2 01 00 02 30 00 00` | Resume live video |
| **Freeze ON** | `BE EF 03 06 00 13 D3 01 00 02 30 01 00` | Pause current frame |
| **Get Freeze Status** | `BE EF 03 06 00 B0 D2 02 00 02 30 00 00` | Query state |

**Freeze Status Values:**
- `00 00` = Freeze OFF (Live mode)
- `01 00` = Freeze ON (Paused frame)

---

### 6. PICTURE BRIGHTNESS CONTROL (Type: 03 20)

**Adjusts projector lamp intensity and image brightness. Range: 0-100 (in 5% increments).**

| Operation | Hex Command | Response |
|-----------|-------------|----------|
| **Get Brightness** | `BE EF 03 06 00 89 D2 02 00 03 20 00 00` | 1Dh XX XX (current level) |
| **Brightness Increment** | `BE EF 03 06 00 EF D2 04 00 03 20 00 00` | ACK (06h) |
| **Brightness Decrement** | `BE EF 03 06 00 3E D3 05 00 03 20 00 00` | ACK (06h) |
| **Reset to Default (50%)** | `BE EF 03 06 00 58 D3 06 00 00 70 00 00` | ACK (06h) |

**Brightness Levels:**
- Value 00: Minimum (5% lamp power)
- Value 32: Mid (50% lamp power, default)
- Value 64: Maximum (100% lamp power)
- Range: 0-100 (0x00-0x64)

**Lamp Power Consumption:**
- Higher brightness = More heat + shorter lamp life
- Eco mode automatically reduces to ~75% brightness
- Use lowest adequate brightness for extended lamp life

---

### 7. PICTURE CONTRAST CONTROL (Type: 04 20)

**Adjusts image contrast ratio. Range: 0-100 (in 5% increments).**

| Operation | Hex Command | Response |
|-----------|-------------|----------|
| **Get Contrast** | `BE EF 03 06 00 FD D3 02 00 04 20 00 00` | 1Dh XX XX (current level) |
| **Contrast Increment** | `BE EF 03 06 00 9B D3 04 00 04 20 00 00` | ACK (06h) |
| **Contrast Decrement** | `BE EF 03 06 00 4A D2 05 00 04 20 00 00` | ACK (06h) |
| **Reset to Default (50%)** | `BE EF 03 06 00 A4 D2 06 00 01 70 00 00` | ACK (06h) |

**Contrast Levels:**
- Value 00: Minimum (flat image)
- Value 32: Mid (50% contrast, default)
- Value 64: Maximum (high contrast)
- Range: 0-100 (0x00-0x64)

---

### 8. PICTURE COLOR CONTROL (Type: 05 20)

**Adjusts overall color saturation level.**

| Operation | Hex Command | Response |
|-----------|-------------|----------|
| **Get Color** | `BE EF 03 06 00 61 D2 02 00 05 20 00 00` | 1Dh XX XX |
| **Color Increment** | `BE EF 03 06 00 07 D2 04 00 05 20 00 00` | ACK (06h) |
| **Color Decrement** | `BE EF 03 06 00 D6 D3 05 00 05 20 00 00` | ACK (06h) |
| **Reset to Default** | `BE EF 03 06 00 6C D2 06 00 02 70 00 00` | ACK (06h) |

---

### 9. PICTURE COLOR TEMPERATURE (Type: 06 20)

**Adjusts color temperature (white point calibration). Range: 0-5 (color temp presets).**

| Operation | Hex Command | Temp Preset | Kelvin |
|-----------|-------------|-------------|--------|
| **Get Color Temp** | `BE EF 03 06 00 FD D1 02 00 06 20 00 00` | Query | — |
| **Cool White** | `BE EF 03 06 00 7F D1 01 00 06 20 02 00` | Cool | ~9300K |
| **Normal (D65)** | `BE EF 03 06 00 4F D1 01 00 06 20 00 00` | Normal | ~6500K |
| **Warm White** | `BE EF 03 06 00 CF D0 01 00 06 20 01 00` | Warm | ~5500K |

---

### 10. SHARPNESS CONTROL (Type: 07 20)

**Adjusts image edge enhancement and clarity.**

| Operation | Hex Command | Response |
|-----------|-------------|----------|
| **Get Sharpness** | `BE EF 03 06 00 69 D1 02 00 07 20 00 00` | 1Dh XX XX |
| **Sharpness Increment** | `BE EF 03 06 00 0F D1 04 00 07 20 00 00` | ACK (06h) |
| **Sharpness Decrement** | `BE EF 03 06 00 DE D0 05 00 07 20 00 00` | ACK (06h) |

---

### 11. PICTURE TINT/COLOR BALANCE (Type: 08 20)

**Red-Green color balance adjustment for NTSC/component video.**

| Operation | Hex Command | Response |
|-----------|-------------|----------|
| **Get Tint** | `BE EF 03 06 00 F5 D0 02 00 08 20 00 00` | 1Dh XX XX |
| **Tint Increment** | `BE EF 03 06 00 93 D0 04 00 08 20 00 00` | ACK (06h) |
| **Tint Decrement** | `BE EF 03 06 00 42 D1 05 00 08 20 00 00` | ACK (06h) |

---

### 12. SCREEN BLANK/BLACK (Type: 09 20)

**Projects solid black screen without disconnecting video source.**

| Operation | Hex Command | Effect |
|-----------|-------------|--------|
| **Blank OFF** | `BE EF 03 06 00 60 D0 01 00 09 20 00 00` | Resume video |
| **Blank ON** | `BE EF 03 06 00 F0 D1 01 00 09 20 01 00` | Black screen |
| **Get Blank Status** | `BE EF 03 06 00 A3 D0 02 00 09 20 00 00` | Query state |

**Difference from Mute:**
- Blank = Video OFF (black screen)
- Mute = Audio OFF
- Both can be used simultaneously

---

### 13. VIDEO NR (Noise Reduction) (Type: 0A 20)

**Reduces video noise and compression artifacts.**

| Operation | Hex Command | Level |
|-----------|-------------|-------|
| **Get Video NR** | `BE EF 03 06 00 3D D0 02 00 0A 20 00 00` | 0-3 |
| **Video NR OFF** | `BE EF 03 06 00 5C D0 01 00 0A 20 00 00` | 0 (None) |
| **Video NR LOW** | `BE EF 03 06 00 CC D1 01 00 0A 20 01 00` | 1 |
| **Video NR MED** | `BE EF 03 06 00 1C D0 01 00 0A 20 02 00` | 2 (Default) |
| **Video NR HIGH** | `BE EF 03 06 00 8C D1 01 00 0A 20 03 00` | 3 (Maximum) |

---

### 14. ECO MODE CONTROL (Type: 1D 30)

**Enables power-saving mode reducing brightness and cooling noise.**

| Operation | Hex Command | Status |
|-----------|-------------|--------|
| **Eco OFF** | `BE EF 03 06 00 A1 D2 01 00 1D 30 00 00` | Full brightness |
| **Eco ON** | `BE EF 03 06 00 31 D3 01 00 1D 30 01 00` | ~75% brightness |
| **Intelligent Eco** | `BE EF 03 06 00 E1 D2 01 00 1D 30 02 00` | Auto adjust |
| **Get Eco Status** | `BE EF 03 06 00 42 D3 02 00 1D 30 00 00` | Query mode |

**Eco Mode Benefits:**
- 25-40% reduction in power consumption
- Quieter cooling fan operation
- Extended lamp life (up to 4000 hours)
- Minimal brightness loss in dark environments

---

### 15. PICTURE MODE SELECTION (Type: 1C 30)

**Selects predefined image processing profiles.**

| Picture Mode | Hex Command | Use Case |
|-------------|-------------|----------|
| **Normal** | `BE EF 03 06 00 65 D1 01 00 1C 30 00 00` | General purpose |
| **Cinema** | `BE EF 03 06 00 F5 D0 01 00 1C 30 01 00` | Film playback |
| **Dynamic** | `BE EF 03 06 00 25 D1 01 00 1C 30 02 00` | Bright environments |
| **Blackboard** | `BE EF 03 06 00 B5 D0 01 00 1C 30 03 00` | Chalkboard content |
| **Whiteboard** | `BE EF 03 06 00 45 D1 01 00 1C 30 04 00` | Whiteboard content |
| **Greenboard** | `BE EF 03 06 00 D5 D0 01 00 1C 30 05 00` | Green chalkboard |
| **Daytime** | `BE EF 03 06 00 06 D0 01 00 1C 30 06 00` | High ambient light |
| **Photo** | `BE EF 03 06 00 96 D1 01 00 1C 30 07 00` | Photo/slide shows |
| **Get Picture Mode** | `BE EF 03 06 00 C7 D1 02 00 1C 30 00 00` | Query current |

---

### 16. PROJECTOR RESET/INITIALIZE (Type: 00 70)

**Resets various settings to factory defaults or resets the entire projector.**

| Operation | Hex Command | Effect |
|-----------|-------------|--------|
| **Reset Brightness** | `BE EF 03 06 00 58 D3 06 00 00 70 00 00` | Brightness → 50% |
| **Reset Contrast** | `BE EF 03 06 00 A4 D2 06 00 01 70 00 00` | Contrast → 50% |
| **Reset Color** | `BE EF 03 06 00 6C D2 06 00 02 70 00 00` | Color → 50% |
| **Reset All Image** | `BE EF 03 06 00 FB D2 06 00 FF 70 00 00` | All picture params reset |
| **Full Factory Reset** | `BE EF 03 06 00 9C D2 06 00 FE 70 00 00` | Complete reset (warning!) |

**Reset Caution:**
- Factory reset erases custom settings, passwords, network config
- Full reset requires reconfiguration of all network settings
- Use sparingly; use specific reset commands when possible

---

## Network Control Methods

### Network Port Configuration

Access via: **OPTION → SERVICE → COMMUNICATION → Port Settings**

| Port | Protocol | Function | Default | Authentication | Data Format |
|------|----------|----------|---------|-----------------|-------------|
| **23** | Telnet | Serial command relay | Enabled | Optional | Binary (13-byte) |
| **4352** | PJLink | Standard projector protocol | Enabled | Optional | ASCII text |
| **9715** | Network Bridge | TCP wrapper for RS-232 | Custom | No | Binary + CRC |
| **9719** | Network Bridge Alt | Alternate bridge port | Configurable | No | Binary + CRC |
| **80** | HTTP | Web control interface | Enabled | Yes | HTML/JSON |
| **443** | HTTPS | Secure web control | Optional | Yes | HTML/JSON encrypted |

### TCP Port 23 (Telnet Control)

**Direct Serial Command Relay over Network**

**Connection Setup:**
```
Protocol: TCP/IP
Host: [Projector IP Address]
Port: 23
Authentication: Username/Password (optional)
Timeout: 30 seconds
```

**Usage:**
- Identical 13-byte command format as RS-232C
- Send raw hex commands directly
- No additional wrapper or header needed

**Example (Python):**
```python
import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('192.168.1.100', 23))
# Send power ON command
sock.send(bytes.fromhex('BEEF030600BAD20100006001 00'))
response = sock.recv(16)
sock.close()
```

### TCP Port 9715 (Network Bridge Command Port)

**Secure command transmission with CRC validation.**

**Connection Setup:**
```
Protocol: TCP/IP
Host: [Projector IP Address]
Port: 9715 (or custom port 9717, 9719, etc.)
Frame Format: Header | Length | RS-232 Command | Checksum | Connection ID
```

**Frame Structure:**

```
Byte:     0      1      2-14               15     16
Content: 02h   0Dh  [13-byte RS-232 cmd] [CRC] [ID]
         Hdr   Len   RS-232C Command     CS    ConnID
```

**Checksum Calculation:**
```
CRC = (256 - (sum of all bytes from byte 0 to byte 14)) mod 256
```

**Example: Power ON via TCP 9715**

```
RS-232 Command: BE EF 03 06 00 BA D2 01 00 00 60 01 00

Frame:
  02 (header)
  0D (length = 13 bytes)
  BE EF 03 06 00 BA D2 01 00 00 60 01 00 (RS-232 command)
  CS (calculated checksum)
  01 (connection ID)

Sum = 02 + 0D + BE + EF + ... + 00 = calculated
CRC = (256 - (sum mod 256)) mod 256
```

**Multi-command Connection:**
Connection ID increments with each command
Allows controller to track multiple simultaneous connections
Reduces latency vs TCP 23 (persistent connection)

### TCP Port 4352 (PJLink Protocol)

**See complete section: PJLink Protocol (Port 4352)**

---

## PJLink Protocol

### PJLink Overview

**PJLink** is the international standard for projector remote control and monitoring.

- **Standard:** PJLink Class 1 & 2 (open protocol)
- **Maintained by:** Japan Business Machine and Information Systems Industries Association (JBMIA)
- **Port:** TCP 4352
- **Format:** ASCII text-based
- **Encoding:** UTF-8
- **Line Terminator:** CR (0x0D) or CRLF (0x0D0A)

### PJLink Authentication

**Default Setup:** Authentication disabled (open access)

**Enable Authentication (OPTION → SERVICE → NETWORK → Port Settings):**
Port 4352 → Authentication [Enable] → MD5 password

**Authentication Flow:**
```
1. Controller connects to port 4352
2. Projector responds: PJLINK 0 (no auth) OR PJLINK 1 [salt] (auth required)
3. If auth required, controller calculates: MD5(password + salt)
4. Controller sends: PJLINK 1 MD5hash
5. Projector responds: PJLINK 0 (access granted)
```

### Basic PJLink Command Format

**General Syntax:**
```
%1COMMAND parameter<CR>
└─ %1   = PJLink prefix (fixed)
└─ COMMAND = 4-character command code
└─ parameter = Value (0-9, uppercase letters)
└─ <CR> = Carriage return (0x0D)
```

**Response Format:**
```
%1COMMAND=response<CR>
%2COMMAND=ERRORcode<CR>  (if error)
└─ %1 = Success
└─ %2 = Error prefix
```

### Power Control (POWR)

```
Command:  %1POWR p<CR>
Purpose:  Control projector power state
Values:   0 = Standby
          1 = Power ON
          ? = Query status
Example:  %1POWR 1<CR>          (turn on)
          %1POWR 0<CR>          (turn off)
          %1POWR ?<CR>          (query state)
Response: %1POWR=0<CR>          (off)
          %1POWR=1<CR>          (on)
          %1POWR=2<CR>          (cooling)
          %1POWR=3<CR>          (warming)
```

### Input Source Selection (INPT)

```
Command:  %1INPT sss<CR>
Purpose:  Select input source
Values:   RGB1 (aliases: 11, 31)
          RGB2 (aliases: 12, 32)
          HDMI (aliases: 1F, 33)
          VIDEO (aliases: 06, 34)
          S-VIDEO (aliases: 07, 35)
          COMPONENT (aliases: 03, 36)
          ?  = Query current
Example:  %1INPT 31<CR>         (RGB1 = COMPUTER IN1)
          %1INPT 33<CR>         (HDMI)
          %1INPT ?<CR>          (query)
Response: %1INPT=31<CR>         (RGB1 selected)
          %1INPT=33<CR>         (HDMI selected)
          %2INPT=ERR1<CR>       (unavailable)
```

**PJLink Input Codes (Standard Mapping):**

| Input | Decimal | Hex | Alt Codes |
|-------|---------|-----|-----------|
| RGB1/COMPUTER1 | 31 | 1Fh | 11 (hex) |
| RGB2/COMPUTER2 | 32 | 20h | 12 (hex) |
| HDMI | 33 | 21h | 1Fh |
| VIDEO | 34 | 22h | 06 (legacy) |
| S-VIDEO | 35 | 23h | 07 (legacy) |
| COMPONENT | 36 | 24h | 03 (legacy) |

### Audio Mute Control (AVMT)

```
Command:  %1AVMT ss<CR>
Purpose:  Control audio/video mute status
Values:   10 = Mute OFF (audio on, video on)
          11 = Audio MUTE
          20 = Video MUTE
          21 = Audio & Video MUTE
          ? = Query status
Example:  %1AVMT 11<CR>        (mute audio only)
          %1AVMT 21<CR>        (mute both)
          %1AVMT 10<CR>        (unmute all)
          %1AVMT ?<CR>         (query)
Response: %1AVMT=10<CR>        (both unmuted)
          %1AVMT=11<CR>        (audio muted)
          %1AVMT=20<CR>        (video muted)
          %1AVMT=21<CR>        (both muted)
```

### Volume Control (MVOL - if supported)

```
Command:  %1MVOL vvv<CR>
Purpose:  Set volume level
Values:   000-100 (decimal)
          ?  = Query volume
Example:  %1MVOL 50<CR>        (set to 50%)
          %1MVOL ?<CR>         (query)
Response: %1MVOL=50<CR>        (volume is 50%)
Note:     Not all projectors support volume via PJLink
```

### Freeze/Pause Control (FZST)

```
Command:  %1FZST fs<CR>
Purpose:  Freeze video frame
Values:   0 = Freeze OFF (live)
          1 = Freeze ON (paused)
          ? = Query
Example:  %1FZST 1<CR>         (freeze screen)
          %1FZST 0<CR>         (resume)
          %1FZST ?<CR>         (query)
Response: %1FZST=0<CR>         (live)
          %1FZST=1<CR>         (frozen)
```

### Lamp Time Query (LAMP)

```
Command:  %1LAMP<CR>
Purpose:  Query lamp operating hours
Values:   None (read-only)
Response: %1LAMP=hhhh mm<CR>
          hhhh = hours (0-9999)
          mm = minutes (0-59)
Example:  %1LAMP=1234 56<CR>   (1234 hours 56 minutes)
```

### Input Signal Detection (INPT with status)

```
Command:  %1INPT ?<CR>
Purpose:  Query current input and status
Response: %1INPT=ss oo<CR>
          ss = selected input (31, 33, etc.)
          oo = signal status (0=no signal, 1=signal ok)
Example:  %1INPT=31 1<CR>      (RGB1 active with signal)
          %1INPT=33 0<CR>      (HDMI selected but no signal)
```

### Error Codes (PJLink)

| Code | Error | Meaning |
|------|-------|---------|
| **ERR1** | Undefined command | Command not recognized |
| **ERR2** | Parameter error | Invalid parameter value |
| **ERR3** | Unavailable | Command not supported in current state |
| **ERR4** | Projector failure | Projector hardware error |
| **WARN** | Warning | Non-fatal error (lamp aging, etc.) |

---

## Remote Control IR Codes

### Remote Control Model: R017H (Standard)

**Operating Frequency:** 38-40 kHz infrared

**Key Functions:**

| Button Group | Functions | IR Codes |
|-------------|-----------|----------|
| **Power** | STANDBY/ON | See IR table below |
| **Input Selection** | COMPUTER, VIDEO, HDMI, etc. | 6 input buttons |
| **Menu Navigation** | UP/DOWN/LEFT/RIGHT, ENTER, ESC | 5 navigation buttons |
| **Audio Control** | VOLUME +/-, MUTE | 3 audio buttons |
| **Special** | BLANK, FREEZE, ASPECT, AUTO | 4 special buttons |
| **Extended** | My Button, Reset, Search, Keystone | 4+ extended buttons |

### Remote Button IR Code Mapping (Typical Values)

**Note:** IR codes are projector-specific; use manufacturer remote or code learner

| Button | Hex Code | Function |
|--------|----------|----------|
| POWER | 0x64 (approx) | Toggle power |
| COMPUTER | 0x68 | Select COMPUTER IN1 |
| VIDEO | 0x69 | Select VIDEO input |
| HDMI | 0x6A | Select HDMI input |
| SEARCH | 0x6B | Auto-search input |
| ASPECT | 0x6C | Aspect ratio menu |
| BLANK | 0x70 | Black screen toggle |
| VOLUME + | 0x48 | Volume increase |
| VOLUME - | 0x49 | Volume decrease |
| MUTE | 0x4A | Audio mute toggle |
| MENU | 0x54 | OSD menu open |
| ENTER | 0x55 | Select/confirm |
| ESC | 0x56 | Cancel/back |
| UP | 0x5A | Menu up |
| DOWN | 0x5B | Menu down |
| LEFT | 0x5C | Menu left |
| RIGHT | 0x5D | Menu right |
| RESET | 0x5E | Reset settings |
| FREEZE | 0x71 | Freeze frame |

**IR Learning Method:**
```
1. Configure projector to "IR Learn Mode" (OPTION → SERVICE → IR LEARN)
2. Point controller remote at projector
3. Projector learns IR codes from each button press
4. Custom remotes can be programmed with learned codes
```

---

## Automation Implementation

### Python Integration - RS-232C Direct Control

```python
#!/usr/bin/env python3
"""
Hitachi Projector CP-EX301N/CP-EX302N RS-232C Control
Direct serial port communication with command library
"""

import serial
import time
from typing import Tuple, Optional

class HitachiProjector:
    """Complete control class for Hitachi LCD projectors"""
    
    def __init__(self, port: str, baudrate: int = 19200):
        """
        Initialize serial connection
        
        Args:
            port: Serial port (e.g., '/dev/ttyUSB0' or 'COM3')
            baudrate: 4800, 9600, 19200, 38400 (default 19200)
        """
        self.ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=8,
            parity='N',
            stopbits=1,
            timeout=1.0
        )
        self.min_delay = 0.05  # 50ms between commands
        self.last_cmd_time = 0
    
    def _send_command(self, hex_cmd: str) -> bytes:
        """
        Send command and receive response
        
        Args:
            hex_cmd: Hex string without spaces (e.g., 'BEEF030600BAD2010000600100')
        
        Returns:
            Response bytes
        """
        # Enforce minimum delay
        elapsed = time.time() - self.last_cmd_time
        if elapsed < self.min_delay:
            time.sleep(self.min_delay - elapsed)
        
        # Convert hex string to bytes
        cmd_bytes = bytes.fromhex(hex_cmd)
        
        # Send command
        self.ser.write(cmd_bytes)
        self.last_cmd_time = time.time()
        
        # Read response
        time.sleep(0.02)  # Give projector time to respond
        response = self.ser.read(16)
        return response
    
    def _check_response(self, response: bytes) -> Tuple[bool, str]:
        """Parse response and return status"""
        if len(response) == 0:
            return False, "No response"
        if response[0] == 0x06:
            return True, "ACK"
        elif response[0] == 0x15:
            return False, "NAK"
        elif response[0] == 0x1C:
            return False, f"Error: {response.hex()}"
        elif response[0] == 0x1D:
            if len(response) >= 3:
                return True, f"Data: {response[1:3].hex()}"
            return True, "Data response"
        return False, f"Unknown: {response.hex()}"
    
    # === POWER CONTROL ===
    
    def power_on(self) -> bool:
        """Turn on projector (60 second warmup required)"""
        resp = self._send_command('BEEF030600BAD20100006001 00')
        ok, msg = self._check_response(resp)
        print(f"Power ON: {msg}")
        return ok
    
    def power_off(self) -> bool:
        """Turn off projector (10 minute cooldown required)"""
        resp = self._send_command('BEEF030600 2AD30100006000 00')
        ok, msg = self._check_response(resp)
        print(f"Power OFF: {msg}")
        return ok
    
    def get_power_status(self) -> Optional[str]:
        """Query power state"""
        resp = self._send_command('BEEF030600 19D30200006000 00')
        ok, msg = self._check_response(resp)
        if ok and "Data" in msg and len(resp) >= 3:
            status_byte = resp[1]
            statuses = {0: "OFF", 1: "ON", 2: "COOLING"}
            return statuses.get(status_byte, f"Unknown({status_byte})")
        return None
    
    # === INPUT SELECTION ===
    
    def select_input(self, input_name: str) -> bool:
        """
        Select input source
        
        Args:
            input_name: 'COMPUTER1', 'COMPUTER2', 'HDMI', 'VIDEO', 'COMPONENT'
        """
        inputs = {
            'COMPUTER1': 'BEEF030600FED20100002000 00',
            'COMPUTER2': 'BEEF030600 3ED0010000200400',
            'HDMI': 'BEEF030600 0ED20100002003 00',
            'VIDEO': 'BEEF030600 6ED33010000200100',
            'COMPONENT': 'BEEF030600AED10100002005 00'
        }
        
        if input_name not in inputs:
            print(f"Unknown input: {input_name}")
            return False
        
        resp = self._send_command(inputs[input_name])
        ok, msg = self._check_response(resp)
        print(f"Select {input_name}: {msg}")
        return ok
    
    # === VOLUME CONTROL ===
    
    def get_volume(self, source: str = 'COMPUTER1') -> Optional[int]:
        """Get current volume level (0-48)"""
        source_codes = {
            'COMPUTER1': 'BEEF030600CDCC0200602000 00',
            'COMPUTER2': 'BEEF030600 77CC0200642000 00',
            'VIDEO': 'BEEF030600 BBCF020061200000',
            'HDMI': 'BEEF030600 BBCF0200632000 00'
        }
        
        if source not in source_codes:
            return None
        
        resp = self._send_command(source_codes[source])
        if len(resp) >= 3 and resp[0] == 0x1D:
            return resp[1]  # Volume level 0-48
        return None
    
    def volume_up(self, source: str = 'COMPUTER1', steps: int = 1) -> bool:
        """Increase volume"""
        source_codes = {
            'COMPUTER1': 'BEEF030600 ABCC0400602000 00',
            'COMPUTER2': 'BEEF030600 15CC0400642000 00',
            'VIDEO': 'BEEF030600 DDCF040061200000',
            'HDMI': 'BEEF030600 DDCF0400632000 00'
        }
        
        if source not in source_codes:
            return False
        
        for _ in range(steps):
            resp = self._send_command(source_codes[source])
            ok, _ = self._check_response(resp)
            if not ok:
                return False
            time.sleep(self.min_delay)
        
        print(f"Volume up {steps} steps on {source}")
        return True
    
    def volume_down(self, source: str = 'COMPUTER1', steps: int = 1) -> bool:
        """Decrease volume"""
        source_codes = {
            'COMPUTER1': 'BEEF030600 7ACD0500602000 00',
            'COMPUTER2': 'BEEF030600 C4CD050064200000',
            'VIDEO': 'BEEF030600 0CCE050061200000',
            'HDMI': 'BEEF030600 0CCE0500632000 00'
        }
        
        if source not in source_codes:
            return False
        
        for _ in range(steps):
            resp = self._send_command(source_codes[source])
            ok, _ = self._check_response(resp)
            if not ok:
                return False
            time.sleep(self.min_delay)
        
        print(f"Volume down {steps} steps on {source}")
        return True
    
    # === PICTURE CONTROL ===
    
    def mute_on(self) -> bool:
        """Enable audio mute"""
        resp = self._send_command('BEEF030600D6D20100022001 00')
        ok, msg = self._check_response(resp)
        print(f"Mute ON: {msg}")
        return ok
    
    def mute_off(self) -> bool:
        """Disable audio mute"""
        resp = self._send_command('BEEF030600 46D30100022000 00')
        ok, msg = self._check_response(resp)
        print(f"Mute OFF: {msg}")
        return ok
    
    def freeze_on(self) -> bool:
        """Pause video (freeze frame)"""
        resp = self._send_command('BEEF030600 13D30100023001 00')
        ok, msg = self._check_response(resp)
        print(f"Freeze ON: {msg}")
        return ok
    
    def freeze_off(self) -> bool:
        """Resume live video"""
        resp = self._send_command('BEEF030600 83D20100023000 00')
        ok, msg = self._check_response(resp)
        print(f"Freeze OFF: {msg}")
        return ok
    
    def blank_on(self) -> bool:
        """Black screen (video blank)"""
        resp = self._send_command('BEEF030600 F0D10100092001 00')
        ok, msg = self._check_response(resp)
        print(f"Blank ON: {msg}")
        return ok
    
    def blank_off(self) -> bool:
        """Resume video display"""
        resp = self._send_command('BEEF030600 60D00100092000 00')
        ok, msg = self._check_response(resp)
        print(f"Blank OFF: {msg}")
        return ok
    
    def brightness_increment(self) -> bool:
        """Increase brightness by 5%"""
        resp = self._send_command('BEEF030600 EFD20400032000 00')
        ok, msg = self._check_response(resp)
        print(f"Brightness +: {msg}")
        return ok
    
    def brightness_decrement(self) -> bool:
        """Decrease brightness by 5%"""
        resp = self._send_command('BEEF030600 3ED30500032000 00')
        ok, msg = self._check_response(resp)
        print(f"Brightness -: {msg}")
        return ok
    
    def eco_mode_on(self) -> bool:
        """Enable eco mode (75% brightness, quieter)"""
        resp = self._send_command('BEEF030600 31D30100 1D3001 00')
        ok, msg = self._check_response(resp)
        print(f"Eco Mode ON: {msg}")
        return ok
    
    def eco_mode_off(self) -> bool:
        """Disable eco mode (full brightness)"""
        resp = self._send_command('BEEF030600 A1D20100 1D3000 00')
        ok, msg = self._check_response(resp)
        print(f"Eco Mode OFF: {msg}")
        return ok
    
    def close(self):
        """Close serial connection"""
        if self.ser.is_open:
            self.ser.close()

# === EXAMPLE USAGE ===

if __name__ == "__main__":
    # Initialize
    projector = HitachiProjector('/dev/ttyUSB0', baudrate=19200)
    
    try:
        # Power sequence
        print("=== POWER SEQUENCE ===")
        projector.power_on()
        time.sleep(65)  # 60 second warmup + 5 second buffer
        
        # Select input
        print("\n=== INPUT SELECTION ===")
        projector.select_input('HDMI')
        time.sleep(2)
        
        # Picture control
        print("\n=== PICTURE CONTROL ===")
        projector.eco_mode_on()
        vol = projector.get_volume('HDMI')
        print(f"Current volume: {vol}")
        projector.volume_up('HDMI', 3)
        
        # Advanced control
        print("\n=== ADVANCED CONTROL ===")
        projector.brightness_increment()
        time.sleep(1)
        projector.freeze_on()
        time.sleep(5)
        projector.freeze_off()
        
        # Shutdown
        print("\n=== SHUTDOWN ===")
        projector.blank_on()
        time.sleep(2)
        projector.power_off()
        
    finally:
        projector.close()
```

### N8N / Automation Workflow Integration

**HTTP Node Configuration (PJLink Protocol):**

```json
{
  "method": "POST",
  "url": "http://192.168.1.100:4352",
  "body": "%1POWR 1\r",
  "headers": {
    "Content-Type": "text/plain"
  },
  "timeout": 5000
}
```

**Webhook Node for Scheduled Tasks:**

```json
{
  "schedule": "0 8 * * MON-FRI",
  "actions": [
    {"command": "%1POWR 1", "delay": 65000},
    {"command": "%1INPT 31", "delay": 2000},
    {"command": "%1AVMT 10", "delay": 1000}
  ]
}
```

### Crestron Control Integration

**DM-MD-ROOM Example (Crestron e-Control):**

```
DEVICE_ID = 5
IP_ADDRESS = "192.168.1.100"
CONTROL_PORT = 23  // Telnet

SEND_COMMAND device,"RS232c\0xBE\0xEF\0x03\0x06\0x00\0xBA\0xD2\0x01\0x00\0x00\0x60\0x01\0x00"

FEEDBACK
  IF_STATE device EQUALS 1
    SEND_COMMAND panels[0],"^SHO-^I;g_power,^S(POWER_ON)"
  END_IF
END_FEEDBACK
```

### Extron/AMX Device Discovery

**Auto-Discovery Settings (OPTION → SERVICE → NETWORK):**

| Protocol | Setting | Value |
|----------|---------|-------|
| **Crestron e-Control** | Enable | [Enable] |
| **AMX Device Discovery** | Enable | [Enable] |
| **Extron XTP** | Auto-Detection | [On] |

---

## Troubleshooting & Best Practices

### Common Issues & Solutions

| Issue | Symptom | Cause | Solution |
|-------|---------|-------|----------|
| **No Response** | No ACK/NAK/Data response | Serial port misconfigured | Verify: baud rate 19200, 8 data bits, 1 stop bit, NO parity |
| **NAK (15h)** | Invalid command error | Hex command malformed | Check: CRC values, command structure, proper spacing |
| **Commands Ignored** | Projector unresponsive | Projector warming up or cooling | Wait: 60 seconds after power ON, 10 minutes before power OFF |
| **Inconsistent Volume** | Volume changes unpredictably | Increment/Decrement timing | Use GET first, calculate steps needed, send commands serially |
| **Network Timeout** | PJLink connection drops | Network bridge not enabled | Enable: OPTION → SERVICE → COMMUNICATION → Network Bridge |
| **TCP 9715 Fails** | Cannot connect port 9715 | Custom port disabled | Enable port in Network settings, or use default 23 |
| **HDMI No Signal** | HDMI input selected but blank | HDCP handshake issue | Restart video source, check HDMI cable, try different port |
| **Overheating** | Lamp/filter warning | Air filter clogged | Clean/replace air filter (10,000 hour service item) |
| **Lamp Failure** | "Lamp Error" message | Lamp end-of-life | Replace lamp (2,000 hour rated life) |
| **Audio Mute Won't Turn Off** | Sound still muted | Multiple mute layers active | Check: Audio Mute, Video Blank, Speaker OFF in menu |

### Command Timing Best Practices

**Critical Delays:**

```python
# After power ON
time.sleep(60)  # 60-second lamp warmup
# All other commands OK after this

# Between commands
time.sleep(0.05)  # 50ms minimum (40ms spec + 10ms buffer)

# Before power OFF
time.sleep(10)  # Cooldown already enforced, but safe practice

# After power OFF
time.sleep(600)  # 10-minute minimum before power ON
```

**Command Batching:**

```python
# WRONG - Continuous fire
projector.power_on()
projector.select_input('HDMI')  # Too fast, may be ignored

# CORRECT - With proper delays
projector.power_on()
time.sleep(65)  # Wait for warmup
projector.select_input('HDMI')
time.sleep(0.05)  # Standard inter-command delay
```

### Network Troubleshooting

**Connection Test (Linux/Mac):**

```bash
# Test TCP port 23 (Telnet)
nc -zv 192.168.1.100 23

# Test TCP port 4352 (PJLink)
nc -zv 192.168.1.100 4352

# Connect and send PJLink command
(sleep 1; echo "%1POWR ?" ; sleep 1) | nc 192.168.1.100 4352

# Test TCP port 9715 (Network Bridge)
nc -zv 192.168.1.100 9715
```

**Firewall Configuration:**

Allow outbound TCP:
  - Port 23 (Telnet control)
  - Port 4352 (PJLink protocol)
  - Port 9715 (Network bridge)
  - Port 80 (Web interface)

Allow inbound TCP:
  - Port 23 (for reverse telnet)
  - Port 4352 (for PJLink queries)

**Network Port Settings Menu:**

```
OPTION
  └─ SERVICE
      └─ NETWORK
          └─ PORT SETTINGS
              ├─ Network Control Port 1 (23)
              │   └─ [Enable] Authentication [Disable]
              ├─ Network Control Port 2 (9715)
              │   └─ [Enable] Custom Port [9717/9719]
              ├─ PJLink Port (4352)
              │   └─ [Enable] Authentication [Disable]
              └─ Web Control Port (80/443)
                  └─ [Enable] HTTPS [Optional]
```

### Performance Optimization

**Minimize Latency:**

```python
# Use RS-232C for time-critical operations (< 50ms)
# Use PJLink for standard operations (100-200ms OK)
# Use TCP 23 for scripted batch operations

# Optimal baud rate (fastest RS-232C)
19200 bps  # Standard, most stable
# 38400 bps available but may introduce errors on long cables
```

**Maximize Reliability:**

```python
# Always implement error checking
if not check_response(send_command(cmd)):
    retry_count += 1
    if retry_count > 3:
        log_error("Command failed after 3 retries")
        raise ConnectionError()

# Use CRC validation (especially for TCP 9715)
# Implement connection timeouts
socket_timeout = 5  # seconds
```

### Maintenance & Monitoring

**Scheduled Tasks:**

```
Daily:   Check projector status via LAMP query
Weekly:  Clean lens and air inlet
Monthly: Check filter status, error logs
Yearly:  Replace air filter (10,000 hours)
         Service cooling system
         Verify all connections
```

**Monitoring Commands:**

```
GET Lamp Hours:     BE EF 03 06 00 35 D1 02 00 1C 10 00 00
GET Temperature:    BE EF 03 06 00 1F D1 02 00 1F 10 00 00
GET Error Status:   BE EF 03 06 00 BC D0 02 00 21 10 00 00
GET Filter Hours:   BE EF 03 06 00 67 D0 02 00 1B 10 00 00
```

**Alert Configuration (Web Interface):**

```
OPTION → SERVICE → NETWORK → Mail Settings
  ├─ SMTP Server: mail.example.com
  ├─ SMTP Port: 25 / 587 (with TLS)
  ├─ From Address: projector@example.com
  ├─ Recipient: admin@example.com
  └─ Alert Triggers:
      ├─ Lamp aging (>1500 hours)
      ├─ Filter maintenance (>8000 hours)
      ├─ Temperature warning
      └─ Power cycle error
```

---

## Complete Technical Specifications

### Display Engine

```
Panel Type:         0.63" P-Si TFT LCD (3x) - true 3LCD
Pixel Count:        1024 × 768 pixels (XGA native)
Lens Type:          Manually adjustable focus/zoom
Zoom Ratio:         1.3x optical zoom
Lens Shift:         Not available (manual focus only)
Focus Distance:     0.9 - 9.1m (WIDE), 1.0 - 10.9m (TELE)
```

### Projection Characteristics

```
Image Size:         30" to 300" (0.76m to 7.62m diagonal)
Brightness:         3200 ANSI lumens (50% IRE, normal mode)
Color Output:       3200 ANSI lumens (color, matched white)
Contrast:           2000:1 (full on/full off)
Color Gamut:        CIE 1976 color space
Keystone Correction: Vertical ±30° (digital correction)
Image Shift:        6:1 upward shift (vertical keystoning)
```

### Input/Output Connectivity

```
COMPUTER IN 1/2:    2 × 15-pin Mini D-sub (VGA, VESA DDC2B)
HDMI:               1 × HDMI Type-A (1.4a standard)
VIDEO:              1 × RCA composite (NTSC/PAL/SECAM)
S-VIDEO:            1 × 4-pin mini-DIN (component YCbCr)
COMPONENT (YPbPr):  1 × RCA trio (component video)
AUDIO IN 1/2:       2 × 3.5mm stereo mini-jack
AUDIO IN 3:         1 × RCA pair (L/R) for alternative audio
AUDIO OUT:          1 × 3.5mm stereo mini-jack
MONITOR OUT:        1 × 15-pin Mini D-sub (VGA passthrough)
RS-232C CONTROL:    2 × 9-pin D-sub (IN/OUT daisy chain)
LAN:                1 × RJ-45 (10/100 Base-T Ethernet)
USB:                1 × Type-B (mouse/keyboard input)
REMOTE IN/OUT:      Optional 3.5mm connectors (wired remote)
```

### Audio System

```
Speaker:            16W mono speaker system
Audio Processing:   Analog input buffering, digital output
Audio Formats:      PCM 48kHz (from HDMI)
Frequency Response: 50Hz - 20kHz (±3dB)
Input Impedance:    22 kΩ (3.5mm), 10 kΩ (RCA)
Output Impedance:   22 kΩ (3.5mm), 10 kΩ (RCA)
Amplifier Rating:   16W @ 4Ω (single channel)
```

### Power & Environmental

```
Power Supply:       AC 100-120V / 220-240V (50/60Hz)
Power Consumption:  330W typical (AC 220-240V, 2.2A)
Standby Power:      < 0.5W (SAVING mode)
Operating Temp:     0°C to 40°C (normal), 0°C to 45°C (eco)
Storage Temp:       -20°C to 60°C
Operating Humidity: 20% to 80% (non-condensing)
Max Altitude:       2700m
Cooling Method:     Forced air circulation with auto-shutdown
```

### Lamp & Consumables

```
Lamp Type:          UHP (Ultra High Performance) 210W
Rated Life:         2000 hours (standard), 2500 hours (eco)
Warm-up Time:       ~60 seconds (full brightness)
Cool-down Time:     ~10 minutes (mandatory before restart)
Air Filter:         Washable/replaceable, 10,000 hour life
Filter Maintenance: Clean every 100-200 hours in dusty environments
Replacement Parts:  Part# NP13LP (lamp module with housing)
```

---

## Appendix: Hex Command Reference Table

**Quick lookup for all 100+ commands:**

```
Power Management:       00 60
Input Selection:        00 20
Audio Mute:            02 20
Screen Blank:          09 20
Screen Freeze:         02 30
Brightness:            03 20
Contrast:              04 20
Color Saturation:      05 20
Color Temperature:     06 20
Sharpness:             07 20
Tint Balance:          08 20
Video Noise Reduce:    0A 20
Eco Mode:              1D 30
Picture Mode Select:   1C 30
System Reset:          00 70
```

---

## Document License & Support

**Version:** 1.0  
**Last Updated:** January 21, 2026  
**Author:** Technical Documentation  
**Organization:** Hitachi Projector Control Documentation  
**Compatibility:** CP-EX301N, CP-EX302N, CP-EX252N, CP-EW302N  
**License:** Free for internal use, training, and automation development

**Support Resources:**
- Hitachi Projector Support: https://www.hitachi-ap.com/support/
- PJLink Standard: https://pjlink.jbmia.or.jp/english/
- Manufacturer Technical Support: Contact authorized dealer
- Community: Crestron Forums, AMX Device Discovery resources

---

**END OF DOCUMENTATION**
