# T-002: Test Projector Connection - Flow Diagram

## User Interaction Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    Settings Dialog                          │
│                   Connection Tab                            │
│                                                             │
│  ┌───────────────────────────────────────────────────┐     │
│  │         Projector Configuration Table             │     │
│  │  ┌────────┬──────────────┬──────┬─────────┐      │     │
│  │  │  Name  │  IP Address  │ Port │  Type   │      │     │
│  │  ├────────┼──────────────┼──────┼─────────┤      │     │
│  │  │ Proj1  │ 192.168.1.10 │ 4352 │ pjlink  │ ◄─── Selected
│  │  │ Proj2  │ 192.168.1.11 │ 4352 │ pjlink  │      │     │
│  │  └────────┴──────────────┴──────┴─────────┘      │     │
│  └───────────────────────────────────────────────────┘     │
│                                                             │
│  [ Add ] [ Edit ] [ Remove ]     [ Test Connection ]       │
│                                         ▲                   │
└─────────────────────────────────────────┼───────────────────┘
                                          │
                                    User clicks
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────┐
│              _test_projector_connection()                   │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
        ┌─────────────────────────────┐
        │  Is projector selected?     │
        └─────────────────────────────┘
                │               │
                │ No            │ Yes
                ▼               ▼
        ┌──────────────┐   ┌──────────────────────┐
        │ Show Warning │   │ Extract table data:  │
        │   "Select    │   │  - Name              │
        │  projector   │   │  - IP                │
        │   first"     │   │  - Port              │
        └──────────────┘   └──────────────────────┘
                                      │
                                      ▼
                          ┌────────────────────────┐
                          │ Query database for     │
                          │ encrypted password     │
                          └────────────────────────┘
                                      │
                                      ▼
                          ┌────────────────────────┐
                          │ Decrypt password       │
                          │ using CredentialManager│
                          └────────────────────────┘
                                      │
                                      ▼
                          ┌────────────────────────┐
                          │ Disable button         │
                          │ Set text: "Testing..." │
                          └────────────────────────┘
                                      │
                                      ▼
                          ┌────────────────────────┐
                          │ Create                 │
                          │ ProjectorController    │
                          │  - host: IP            │
                          │  - port: Port          │
                          │  - password: Decrypted │
                          │  - timeout: 5 sec      │
                          └────────────────────────┘
                                      │
                                      ▼
                          ┌────────────────────────┐
                          │ Call connect()         │
                          └────────────────────────┘
                          │                    │
                Success   │                    │ Failure
                          ▼                    ▼
            ┌──────────────────────┐  ┌──────────────────────┐
            │ Show SUCCESS dialog  │  │ Show FAILURE dialog  │
            │                      │  │                      │
            │ "Successfully        │  │ "Failed to connect"  │
            │  connected to X"     │  │                      │
            │                      │  │ Error: {last_error}  │
            │ IP: xxx.xxx.xxx.xxx  │  │                      │
            │ Port: xxxx           │  │ Troubleshooting:     │
            │                      │  │  - Check IP          │
            │                      │  │  - Check power       │
            │                      │  │  - Check password    │
            │                      │  │  - Check firewall    │
            └──────────────────────┘  └──────────────────────┘
                          │                    │
                          ▼                    ▼
                    ┌──────────────────────────────┐
                    │ Call disconnect()            │
                    └──────────────────────────────┘
                                      │
                                      ▼
                          ┌────────────────────────┐
                          │ FINALLY:               │
                          │  - Re-enable button    │
                          │  - Reset button text   │
                          └────────────────────────┘
```

## Data Flow Diagram

```
┌──────────────┐        ┌──────────────┐        ┌──────────────────┐
│ UI Table     │───────▶│  Method      │───────▶│ Database         │
│              │        │              │        │                  │
│ Projector    │        │ Extract:     │        │ Query:           │
│ selected     │        │  - Name      │        │  proj_name       │
│              │        │  - IP        │        │  proj_user       │
│              │        │  - Port      │        │  proj_pass_enc   │
└──────────────┘        └──────────────┘        └──────────────────┘
                                                          │
                                                          ▼
                                                ┌──────────────────┐
                                                │ CredentialManager│
                                                │                  │
                                                │ Decrypt password │
                                                │ using DPAPI      │
                                                └──────────────────┘
                                                          │
                                                          ▼
                                                ┌──────────────────┐
                                                │ ProjectorController
                                                │                  │
                                                │ connect(         │
                                                │   ip,            │
                                                │   port,          │
                                                │   password       │
                                                │ )                │
                                                └──────────────────┘
                                                          │
                                                          ▼
                                                ┌──────────────────┐
                                                │ Network          │
                                                │ PJLink Protocol  │
                                                │                  │
                                                │ TCP Socket       │
                                                │ 192.168.x.x:4352 │
                                                └──────────────────┘
                                                          │
                                                          ▼
                                                ┌──────────────────┐
                                                │ Physical         │
                                                │ Projector        │
                                                │                  │
                                                │ [Device]         │
                                                └──────────────────┘
```

## Error Handling Flow

```
┌────────────────────────────────────────────────────────────┐
│                    Try Block                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Query database for password                         │  │
│  │    └──► Exception? ──► Log warning, password = None  │  │
│  │                                                       │  │
│  │  Create ProjectorController                          │  │
│  │    └──► ValueError? ──► Caught by outer except       │  │
│  │                                                       │  │
│  │  Call connect()                                      │  │
│  │    └──► Timeout? ──► Returns False, handled          │  │
│  │    └──► Socket error? ──► Returns False, handled     │  │
│  │    └──► Auth error? ──► Returns False, handled       │  │
│  │                                                       │  │
│  │  Show dialog (success or failure)                    │  │
│  │                                                       │  │
│  │  Call disconnect()                                   │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
                          │
                Exception │
                          ▼
┌────────────────────────────────────────────────────────────┐
│                  Except Block                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Log error                                           │  │
│  │  Show critical dialog with error message            │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────────┐
│                  Finally Block                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Re-enable button (ALWAYS executed)                  │  │
│  │  Reset button text to "Test Connection"             │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

## Security Flow

```
┌─────────────────────────────────────────────────────────┐
│                    Password Security                     │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────────┐
        │ Database: proj_pass_encrypted       │
        │                                     │
        │ Stored as:                          │
        │  Base64(DPAPI(plaintext))           │
        │                                     │
        │ Protected by:                       │
        │  - Windows DPAPI                    │
        │  - User account credentials         │
        │  - Machine-specific entropy         │
        │  - App-specific entropy file        │
        └─────────────────────────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────────┐
        │ CredentialManager                   │
        │                                     │
        │ decrypt_credential():               │
        │  1. Base64 decode                   │
        │  2. Load app entropy                │
        │  3. Call CryptUnprotectData()       │
        │  4. Return plaintext password       │
        └─────────────────────────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────────┐
        │ ProjectorController                 │
        │                                     │
        │ Stored as: self._password (private) │
        │                                     │
        │ Never logged                        │
        │ Never displayed                     │
        │ Used only for PJLink auth           │
        └─────────────────────────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────────┐
        │ Network Transmission                │
        │                                     │
        │ PJLink authentication:              │
        │  - Challenge-response (MD5 hash)    │
        │  - Password never sent in clear     │
        │  - Hash = MD5(random + password)    │
        └─────────────────────────────────────┘
```

## Timeout Behavior

```
Time →
0s         1s         2s         3s         4s         5s
│          │          │          │          │          │
▼          │          │          │          │          │
Button     │          │          │          │          │
clicked    │          │          │          │          │
           │          │          │          │          │
Button     │          │          │          │          │
disabled   │          │          │          │          │
           │          │          │          │          │
"Testing..."│         │          │          │          │
displayed  │          │          │          │          │
           │          │          │          │          │
TCP        │          │          │          │          │
connect    │          │          │          │          │
attempt    │          │          │          │          │
           │          │          │          │          │
           ▼          │          │          │          │
      If success:     │          │          │          │
      ┌────────┐      │          │          │          │
      │ Dialog │      │          │          │          │
      │ shown  │      │          │          │          │
      └────────┘      │          │          │          │
                      │          │          │          │
                      │          │          │          ▼
                      │          │          │     If timeout:
                      │          │          │     ┌────────┐
                      │          │          │     │ Error  │
                      │          │          │     │ dialog │
                      │          │          │     └────────┘
                      │          │          │
                      ▼          ▼          ▼
                 Maximum wait: 5 seconds
                      │
                      ▼
              Button re-enabled
              Text reset
```

---

**Implementation Date**: 2026-01-17
**Author**: Frontend UI Developer (Claude Agent)
