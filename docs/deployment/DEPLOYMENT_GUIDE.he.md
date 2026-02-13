# מדריך פריסה - Enhanced Projector Control Application

**גרסה:** 1.0
**עודכן לאחרונה:** 12 בפברואר 2026
**גרסת יישום:** 2.0.0-rc2
**קהל יעד:** מנהלי IT, מנהלי מערכת, מהנדסי DevOps

---

## תוכן עניינים

1. [סקירת פריסה](#1-סקירת-פריסה)
2. [ארכיטקטורה ומצבים](#2-ארכיטקטורה-ומצבים)
3. [תכנון קדם-פריסה](#3-תכנון-קדם-פריסה)
4. [הגדרת תשתית רשת](#4-הגדרת-תשתית-רשת)
5. [הכנת SQL Server](#5-הכנת-sql-server)
6. [פריסת מצב Standalone](#6-פריסת-מצב-standalone)
7. [פריסת מצב Enterprise](#7-פריסת-מצב-enterprise)
8. [תצורה ראשונית](#8-תצורה-ראשונית)
9. [הקשחת אבטחה](#9-הקשחת-אבטחה)
10. [גיבוי ושחזור אסון](#10-גיבוי-ושחזור-אסון)
11. [ניטור ותחזוקה](#11-ניטור-ותחזוקה)
12. [פתרון בעיות](#12-פתרון-בעיות)
13. [נספח: סקריפטים ותבניות](#13-נספח-סקריפטים-ותבניות)

---

## 1. סקירת פריסה

### תיאור כללי

Enhanced Projector Control Application הוא יישום Windows מקצועי המאפשר שליטה במקרנים ברשת באמצעות פרוטוקול PJLink. מסמך זה מספק הנחיות מקיפות למנהלי IT לפריסת היישום בסביבות ארגוניות.

**תכונות מרכזיות:**
- קובץ הפעלה יחיד (portable) - אין installer נדרש
- מצבי פריסה כפולים: Standalone (SQLite) ו-Enterprise (SQL Server)
- תמיכה בעברית מלאה עם פריסת RTL
- הצפנת DPAPI לאישורים
- פרוטוקול PJLink Class 1 & 2
- Windows 10/11 (64-bit) בלבד

---

### תרחישי פריסה

**תרחיש 1: משתמש בודד / התקנה קטנה**
- **מצב:** Standalone (SQLite)
- **סוג:** 1-10 משתמשים
- **מקרה שימוש:** מורים בודדים, חדרי כנסים בודדים
- **מורכבות:** נמוכה
- **זמן פריסה:** 30 דקות

**תרחיש 2: מחלקה או בניין**
- **מצב:** Standalone או Enterprise
- **סוג:** 10-50 משתמשים
- **מקרה שימוש:** בית ספר, בניין משרדים
- **מורכבות:** בינונית
- **זמן פריסה:** 2-4 שעות

**תרחיש 3: ארגון גדול / קמפוס**
- **מצב:** Enterprise (SQL Server)
- **סוג:** 50-500+ משתמשים
- **מקרה שימוש:** אוניברסיטה, חברה גדולה, בתי ספר מרובים
- **מורכבות:** גבוהה
- **זמן פריסה:** 1-2 שבועות (כולל בדיקות)

---

### יתרונות לפי מצב

**מצב Standalone - יתרונות:**
✅ פריסה פשוטה - אין צורך ב-SQL Server
✅ אין תלויות - כל מחשב עצמאי
✅ מתאים לסביבות מבודדות (ללא חיבור רשת)
✅ גיבויים פשוטים (קובץ SQLite + entropy file)
✅ עלות אפס (אין רישוי SQL Server)

**מצב Enterprise - יתרונות:**
✅ ניהול מרכזי - תצורה משותפת
✅ גיבויים אוטומטיים (SQL Server backups)
✅ ניתן להרחבה - מאות משתמשים
✅ ביקורת - מעקב מרכזי אחר כל הפעולות
✅ עקביות - כולם משתמשים באותן הגדרות מקרנים

---

## 2. ארכיטקטורה ומצבים

### ארכיטכטורת מערכת

```
┌─────────────────────────────────────────────────────────────────┐
│                      Windows Workstation                         │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │            ProjectorControl.exe (PyQt6 App)               │  │
│  │  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐  │  │
│  │  │  UI Layer   │  │ Controller   │  │ Database Layer  │  │  │
│  │  │  (PyQt6)    │◄─┤   Layer      │◄─┤   (SQLite or    │  │  │
│  │  │             │  │  (PJLink)    │  │   SQL Server)   │  │  │
│  │  └─────────────┘  └──────────────┘  └─────────────────┘  │  │
│  └────────────────────────┬──────────────────────────────────┘  │
│                           │                                      │
│  ┌────────────────────────┴──────────────────────────────────┐  │
│  │              Local Storage (%APPDATA%)                    │  │
│  │  • projector_control.db (Standalone mode)                 │  │
│  │  • .projector_entropy (Encryption key - CRITICAL!)        │  │
│  │  • config.ini (UI preferences)                            │  │
│  │  • logs/ (Application logs)                               │  │
│  └───────────────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────────────┘
                       │
          ┌────────────┴────────────┐
          │                         │
    ┌─────▼─────┐         ┌─────────▼────────┐
    │ Projector │         │   SQL Server     │
    │  Network  │         │    (Optional     │
    │ PJLink    │         │  Enterprise mode)│
    │ TCP 4352  │         │   TCP 1433       │
    └───────────┘         └──────────────────┘
```

---

### מצב Standalone - אחסון נתונים

**מיקום נתונים:**
```
%APPDATA%\ProjectorControl\
├── projector_control.db      ← מסד נתונים SQLite
├── .projector_entropy         ← מפתח הצפנה (חייב גיבוי!)
├── config.ini                 ← העדפות UI
├── logs\
│   ├── app.log               ← לוג נוכחי
│   ├── app.log.1             ← לוג אתמול
│   └── ...                   ← לוגים מסובבים (7 ימים)
└── backups\
    └── manual\               ← גיבויים ידניים
```

**גודל אחסון צפוי:**
- התקנה ריקה: ~50 KB
- עם 10 מקרנים: ~500 KB
- אחרי שנה (50 פעולות/יום): ~3.5 MB
- לוגים (7 ימים): ~10-35 MB

**דרישות גיבוי:**
- גבה את `projector_control.db` + `.projector_entropy` **ביחד**
- ללא קובץ entropy, סיסמאות מוצפנות **אינן ניתנות לפענוח**

---

### מצב Enterprise - אחסון נתונים

**ארכיטקטורת SQL Server:**
```
┌──────────────────────────────────────────────────────────────┐
│                    SQL Server Database                       │
│                   "ProjectorControl"                         │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Tables:                                               │  │
│  │  • projector_config (Projector configurations)         │  │
│  │  • operation_history (All operations, all users)       │  │
│  │  • schema_version (Migration tracking)                 │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
                           ▲
                           │ TCP 1433
          ┌────────────────┴────────────────┐
          │                                  │
    ┌─────┴──────┐                  ┌────────┴─────┐
    │ Workstation│                  │ Workstation  │
    │      1     │                  │      2       │
    │  (Shared   │                  │  (Shared     │
    │  config)   │                  │  config)     │
    └────────────┘                  └──────────────┘
```

**אחסון מקומי (עדיין נדרש):**
```
%APPDATA%\ProjectorControl\
├── .projector_entropy         ← מפתח הצפנה (מקומי!)
├── config.ini                 ← העדפות UI (מקומי)
└── logs\                      ← לוגים (מקומיים)
```

**חשוב:** גם במצב Enterprise, קובץ `.projector_entropy` נדרש על **כל workstation**.

---

### אבטחה ומודל איומים

**איום 1: חשיפת סיסמאות מקרן**
- **הגנה:** הצפנת DPAPI + קובץ entropy
- **הפחתה:** הרשאות קבצים, BitLocker, גיבוי entropy מאובטח

**איום 2: גישה לא מורשית לרשת**
- **הגנה:** בידוד VLAN, חוקי firewall, סיסמאות PJLink
- **הפחתה:** ניטור רשת, MAC filtering

**איום 3: SQL Injection (Enterprise mode)**
- **הגנה:** 100% שאילתות פרמטריות, אין f-strings
- **הפחתה:** ביקורת קוד, בדיקות אוטומטיות

**איום 4: אובדן נתונים**
- **הגנה:** גיבויים אוטומטיים, SQL Server backups
- **הפחתה:** אסטרטגיית 3-2-1 backup

---

## 3. תכנון קדם-פריסה

### רשימת דרישות

**דרישות חומרה:**

| רכיב | מינימום | מומלץ |
|------|---------|-------|
| **OS** | Windows 10 (64-bit) | Windows 11 Pro (64-bit) |
| **CPU** | Intel/AMD 2+ cores | Intel i5/AMD Ryzen 5+ |
| **RAM** | 4 GB | 8 GB |
| **Disk** | 100 MB פנויים | 500 MB (עם לוגים) |
| **רשת** | 100 Mbps Ethernet/Wi-Fi | 1 Gbps Ethernet |
| **תצוגה** | 1280x720 | 1920x1080+ |

**דרישות SQL Server (Enterprise mode):**

| רכיב | מינימום | מומלץ |
|------|---------|-------|
| **גרסה** | SQL Server 2016 Express | SQL Server 2019 Standard+ |
| **RAM** | 2 GB | 8 GB+ |
| **Disk** | 10 GB | 50 GB (עם backups) |
| **רשת** | חיבור יציב ל-workstations | Gigabit Ethernet |
| **רישוי** | Express (חינם, מוגבל) | Standard/Enterprise |

---

### תכנון רשת

**VLAN Architecture (מומלץ):**

```
┌─────────────────────────────────────────────────────────────┐
│                  Corporate Network                          │
│                                                             │
│  ┌──────────────┐        ┌──────────────┐                  │
│  │ VLAN 10      │        │ VLAN 50      │                  │
│  │ Users        │        │ Projectors   │                  │
│  │ 10.0.10.0/24 │◄──────►│ 10.0.50.0/24 │                  │
│  │              │ Firewall│              │                  │
│  │ Workstations │  Rules │   Projectors │                  │
│  └──────────────┘        └──────────────┘                  │
│         │                                                   │
│         │                                                   │
│  ┌──────┴───────┐                                          │
│  │ VLAN 20      │                                          │
│  │ Servers      │                                          │
│  │ 10.0.20.0/24 │                                          │
│  │              │                                          │
│  │  SQL Server  │                                          │
│  └──────────────┘                                          │
└─────────────────────────────────────────────────────────────┘
```

**חוקי Firewall:**

| מקור | יעד | פורט | פרוטוקול | פעולה | תיאור |
|------|-----|------|----------|-------|--------|
| VLAN 10 (Users) | VLAN 50 (Projectors) | 4352 | TCP | Allow | PJLink control |
| VLAN 10 (Users) | VLAN 20 (SQL) | 1433 | TCP | Allow | SQL Server (Enterprise) |
| VLAN 50 (Projectors) | VLAN 10 (Users) | Any | Any | Deny | Prevent reverse connections |
| VLAN 50 (Projectors) | Internet | Any | Any | Deny | Isolate projectors |

---

### תכנון זמן פריסה

**מצב Standalone (לכל workstation):**
- הורדת EXE: 2 דקות
- העתקה למחשבים: 10 דקות
- תצורה ראשונית: 10 דקות
- בדיקה: 5 דקות
- **סה"כ לכל מחשב:** ~30 דקות

**פריסה מרובה (10 workstations):**
- יצירת סקריפט פריסה: 30 דקות (חד-פעמי)
- הפעלת סקריפט: 15 דקות (parallel)
- תצורה + בדיקה: 1 שעה
- **סה"כ:** ~2 שעות

**מצב Enterprise:**
- הכנת SQL Server: 2 שעות
- תצורת VLAN ופריסת רשת: 4 שעות
- פריסת workstation: 1 שעה
- בדיקת אינטגרציה: 2 שעות
- **סה"כ:** ~9 שעות (יום עבודה אחד)

---

## 4. הגדרת תשתית רשת

### תצורת מקרנים

**מציאת כתובות IP של מקרנים:**

**אפשרות 1: תפריט OSD פיזי**
1. הפעל את המקרן
2. לחץ על Menu ב-שלט
3. נווט ל-Network Settings > Wired LAN
4. כתוב את כתובת ה-IP

**אפשרות 2: DHCP Lease scan**
```powershell
# סרוק DHCP leases עבור מקרנים
Get-DhcpServerv4Scope -ComputerName "dhcp-server" |
    Get-DhcpServerv4Lease |
    Where-Object {$_.HostName -like "*projector*" -or $_.HostName -like "*epson*"} |
    Select-Object IPAddress, HostName, AddressState
```

**אפשרות 3: סריקת רשת**
```powershell
# סרוק רשת עבור פורט PJLink פתוח (4352)
$subnet = "10.0.50"
1..254 | ForEach-Object -Parallel {
    $ip = "$using:subnet.$_"
    if (Test-NetConnection -ComputerName $ip -Port 4352 -InformationLevel Quiet -WarningAction SilentlyContinue) {
        Write-Output $ip
    }
} -ThrottleLimit 50
```

---

### IP סטטי עבור מקרנים (מומלץ)

**מדוע סטטי עדיף על DHCP:**
- IP consistency - לא משתנה אחרי הפעלה מחדש
- תצורה פשוטה יותר - אין צורך בעדכון בלקוחות
- אמינות - לא תלוי בשרת DHCP

**הגדרה:**

1. **הקצה IP סטטי במקרן:**
   - גש ל-Network Settings דרך OSD
   - בחר Manual IP (לא DHCP)
   - הזן:
     - IP Address: `10.0.50.10`
     - Subnet Mask: `255.255.255.0`
     - Gateway: `10.0.50.1`
     - DNS: `10.0.20.10` (DNS server שלך)

2. **תעד בטבלה:**

| מיקום | שם מקרן | מותג | IP Address | Port | Password |
|-------|----------|------|------------|------|----------|
| Conference Room A | conf-a-proj | EPSON EB-2250U | 10.0.50.10 | 4352 | (encryption) |
| Training Room B | train-b-proj | Hitachi CP-EX302N | 10.0.50.11 | 4352 | None |
| Auditorium Main | audit-main | EPSON EB-2265U | 10.0.50.12 | 4352 | (encrypted) |

---

### הגדרת VLAN ו-Firewall

**Windows Firewall (על workstations):**

```powershell
# אפשר Outbound ל-PJLink port 4352
New-NetFirewallRule -DisplayName "Projector Control - PJLink" `
    -Direction Outbound `
    -Protocol TCP `
    -LocalPort Any `
    -RemotePort 4352 `
    -Action Allow `
    -Profile Domain,Private

# אפשר Outbound ל-SQL Server port 1433 (Enterprise mode)
New-NetFirewallRule -DisplayName "Projector Control - SQL Server" `
    -Direction Outbound `
    -Protocol TCP `
    -LocalPort Any `
    -RemotePort 1433 `
    -Action Allow `
    -Profile Domain
```

**Network Switch VLAN (Cisco IOS example):**

```cisco
! צור VLANs
vlan 10
  name Users-VLAN
vlan 50
  name Projectors-VLAN
vlan 20
  name Servers-VLAN

! הקצה פורטים ל-VLANs
interface range GigabitEthernet1/0/1-24
  description User Workstations
  switchport mode access
  switchport access vlan 10

interface range GigabitEthernet1/0/25-40
  description Projectors
  switchport mode access
  switchport access vlan 50

interface GigabitEthernet1/0/48
  description Trunk to Core Router
  switchport mode trunk
  switchport trunk allowed vlan 10,20,50
```

**Firewall ACLs (example):**

```cisco
! ACL עבור גישת Users ל-Projectors
ip access-list extended USERS_TO_PROJECTORS
  permit tcp 10.0.10.0 0.0.0.255 10.0.50.0 0.0.0.255 eq 4352
  deny ip any any log

! ACL עבור גישת Users ל-SQL Server
ip access-list extended USERS_TO_SQL
  permit tcp 10.0.10.0 0.0.0.255 host 10.0.20.10 eq 1433
  deny ip any any log

! החל ACLs על interfaces
interface Vlan10
  ip access-group USERS_TO_PROJECTORS out

interface Vlan20
  ip access-group USERS_TO_SQL out
```

---

### בדיקת קישוריות רשת

**בדיקה 1: Ping למקרן**
```powershell
Test-NetConnection -ComputerName 10.0.50.10 -InformationLevel Detailed
```
**תוצאה צפויה:**
```
PingSucceeded    : True
PingReplyDetails (RTT): 2 ms
```

**בדיקה 2: Test TCP Port 4352**
```powershell
Test-NetConnection -ComputerName 10.0.50.10 -Port 4352
```
**תוצאה צפויה:**
```
TcpTestSucceeded : True
```

**בדיקה 3: בדיקת PJLink ידנית**
```powershell
# התחבר ל-PJLink ידנית (דורש telnet client)
$socket = New-Object System.Net.Sockets.TcpClient("10.0.50.10", 4352)
$stream = $socket.GetStream()
$reader = New-Object System.IO.StreamReader($stream)
$writer = New-Object System.IO.StreamWriter($stream)

# קרא banner
$banner = $reader.ReadLine()
Write-Host "Banner: $banner"  # Should be "PJLINK 0" or "PJLINK 1 <random>"

# שלח פקודת status
$writer.WriteLine("%1POWR ?`r")
$writer.Flush()
$response = $reader.ReadLine()
Write-Host "Response: $response"  # "OK=1" (On) or "OK=0" (Off)

$socket.Close()
```

---

## 5. הכנת SQL Server

### הכנת שרת SQL

**דרישות גרסה:**
- SQL Server 2016 Express (מינימום)
- SQL Server 2019 Standard (מומלץ)
- SQL Server 2022 Enterprise (ארגונים גדולים)

**התקנת SQL Server Express (חינם):**

```powershell
# הורד SQL Server Express 2022
$url = "https://go.microsoft.com/fwlink/?linkid=2216019"
$installer = "$env:TEMP\SQLServer2022-SSEI-Expr.exe"
Invoke-WebRequest -Uri $url -OutFile $installer

# הפעל התקנה שקטה
& $installer /ACTION=Install /FEATURES=SQLEngine /INSTANCENAME=SQLEXPRESS /SECURITYMODE=SQL /SAPWD="YourStrongPassword!" /IACCEPTSQLSERVERLICENSETERMS /QUIET

# הפעל SQL Server service
Start-Service -Name "MSSQL`$SQLEXPRESS"
Set-Service -Name "MSSQL`$SQLEXPRESS" -StartupType Automatic

# הפעל SQL Browser (עבור גילוי רשת)
Start-Service -Name "SQLBrowser"
Set-Service -Name "SQLBrowser" -StartupType Automatic

Write-Host "SQL Server Express installed and started."
```

---

### יצירת מסד נתונים

**שלב 1: התחבר ל-SQL Server**
```powershell
# השתמש ב-sqlcmd או SSMS
sqlcmd -S localhost\SQLEXPRESS -U sa -P "YourStrongPassword!"
```

**שלב 2: צור מסד נתונים**
```sql
-- צור מסד נתונים עם collation נכון
CREATE DATABASE ProjectorControl
    COLLATE SQL_Latin1_General_CP1_CI_AS
    ON PRIMARY (
        NAME = ProjectorControl_Data,
        FILENAME = 'C:\SQLData\ProjectorControl.mdf',
        SIZE = 100 MB,
        FILEGROWTH = 50 MB
    )
    LOG ON (
        NAME = ProjectorControl_Log,
        FILENAME = 'C:\SQLData\ProjectorControl.ldf',
        SIZE = 50 MB,
        FILEGROWTH = 25 MB
    );
GO

-- בדוק שמסד הנתונים נוצר
SELECT name, database_id, create_date, collation_name
FROM sys.databases
WHERE name = 'ProjectorControl';
GO
```

**תוצאה צפויה:**
```
name                database_id  create_date              collation_name
ProjectorControl    5            2026-02-12 14:30:00      SQL_Latin1_General_CP1_CI_AS
```

---

### יצירת משתמש יישום

**אפשרות 1: SQL Server Authentication (פשוט)**

```sql
-- צור login ברמת שרת
CREATE LOGIN projector_app_user
    WITH PASSWORD = 'P@ssw0rd_Secure_2026!',
         DEFAULT_DATABASE = ProjectorControl,
         CHECK_POLICY = ON,      -- אכוף מדיניות סיסמאות
         CHECK_EXPIRATION = ON;  -- אכוף פקיעת סיסמה
GO

-- עבור למסד הנתונים
USE ProjectorControl;
GO

-- צור משתמש
CREATE USER projector_app_user FOR LOGIN projector_app_user;
GO

-- הענק הרשאות
ALTER ROLE db_datareader ADD MEMBER projector_app_user;  -- קריאה
ALTER ROLE db_datawriter ADD MEMBER projector_app_user;  -- כתיבה
ALTER ROLE db_ddladmin ADD MEMBER projector_app_user;    -- DDL (עבור migrations)
GO

-- אמת הרשאות
SELECT
    dp.name AS UserName,
    dp.type_desc AS UserType,
    r.name AS RoleName
FROM sys.database_principals dp
LEFT JOIN sys.database_role_members drm ON dp.principal_id = drm.member_principal_id
LEFT JOIN sys.database_principals r ON drm.role_principal_id = r.principal_id
WHERE dp.name = 'projector_app_user';
GO
```

**תוצאה צפויה:**
```
UserName              UserType          RoleName
projector_app_user    SQL_USER          db_datareader
projector_app_user    SQL_USER          db_datawriter
projector_app_user    SQL_USER          db_ddladmin
```

---

**אפשרות 2: Windows Authentication (מומלץ)**

```sql
-- צור login עבור קבוצת Windows
-- (תחילה צור קבוצה ב-Active Directory: "DOMAIN\ProjectorControlUsers")
CREATE LOGIN [DOMAIN\ProjectorControlUsers] FROM WINDOWS;
GO

USE ProjectorControl;
GO

-- צור משתמש
CREATE USER [DOMAIN\ProjectorControlUsers]
    FOR LOGIN [DOMAIN\ProjectorControlUsers];
GO

-- הענק הרשאות
ALTER ROLE db_datareader ADD MEMBER [DOMAIN\ProjectorControlUsers];
ALTER ROLE db_datawriter ADD MEMBER [DOMAIN\ProjectorControlUsers];
ALTER ROLE db_ddladmin ADD MEMBER [DOMAIN\ProjectorControlUsers];
GO

-- אמת
SELECT
    dp.name AS UserName,
    dp.type_desc AS UserType
FROM sys.database_principals dp
WHERE dp.name = 'DOMAIN\ProjectorControlUsers';
GO
```

**יתרונות Windows Authentication:**
- אין צורך לאחסן סיסמאות ביישום
- Single Sign-On (SSO)
- ניהול מרכזי דרך Active Directory
- Kerberos authentication (מאובטח יותר)

---

### הצפנת חיבור SQL

**הפעל TLS/SSL עבור חיבורי SQL Server:**

**שלב 1: התקן תעודה SSL**
```powershell
# צור self-signed certificate (dev/test בלבד)
$cert = New-SelfSignedCertificate -DnsName "sqlserver.domain.local" `
    -CertStoreLocation "Cert:\LocalMachine\My" `
    -KeyExportPolicy Exportable `
    -KeySpec KeyExchange

# ייצא thumbprint
$thumbprint = $cert.Thumbprint
Write-Host "Certificate Thumbprint: $thumbprint"

# הענק הרשאות קריאה לחשבון שירות SQL Server
$servicAccount = "NT Service\MSSQL`$SQLEXPRESS"
$privateKey = [System.Security.Cryptography.X509Certificates.RSACertificateExtensions]::GetRSAPrivateKey($cert)
$keyPath = $privateKey.Key.UniqueName
$keyFullPath = "$env:ProgramData\Microsoft\Crypto\RSA\MachineKeys\$keyPath"
icacls $keyFullPath /grant "${serviceAccount}:R"
```

**שלב 2: הגדר SQL Server להשתמש בתעודה**
```sql
-- הפעל Force Encryption
USE master;
GO

EXEC sp_configure 'show advanced options', 1;
RECONFIGURE;
GO

-- הערה: הגדרת תעודה דורשת SQL Server Configuration Manager
-- אי אפשר לעשות דרך T-SQL
-- עקוב אחר: SQL Server Configuration Manager >
--   SQL Server Network Configuration > Protocols for [Instance] >
--   Properties > Certificate tab > select certificate
```

**שלב 3: אמת חיבור מוצפן**
```powershell
# בדוק שחיבור משתמש ב-TLS
$connString = "Server=sqlserver.domain.local;Database=ProjectorControl;User Id=projector_app_user;Password=P@ssw0rd;Encrypt=True;TrustServerCertificate=False;"
$conn = New-Object System.Data.SqlClient.SqlConnection($connString)
try {
    $conn.Open()
    Write-Host "Connection successful with encryption!"
    $conn.Close()
} catch {
    Write-Host "Connection failed: $_"
}
```

---

### Firewall SQL Server

**פתח פורט 1433 ב-Windows Firewall:**

```powershell
# אפשר Inbound עבור SQL Server
New-NetFirewallRule -DisplayName "SQL Server (TCP-In)" `
    -Direction Inbound `
    -Protocol TCP `
    -LocalPort 1433 `
    -Action Allow `
    -Profile Domain,Private

# אפשר SQL Browser (UDP 1434) לגילוי instances
New-NetFirewallRule -DisplayName "SQL Browser (UDP-In)" `
    -Direction Inbound `
    -Protocol UDP `
    -LocalPort 1434 `
    -Action Allow `
    -Profile Domain,Private

# בדוק שחוקים נוצרו
Get-NetFirewallRule -DisplayName "SQL Server*" | Select-Object DisplayName, Enabled, Direction, Action
```

**בדיקת קישוריות מ-workstation:**
```powershell
# בדוק חיבור ל-SQL Server
Test-NetConnection -ComputerName sqlserver.domain.local -Port 1433

# נסה חיבור SQL בפועל
sqlcmd -S sqlserver.domain.local -U projector_app_user -P "P@ssw0rd_Secure_2026!" -Q "SELECT @@VERSION"
```

---

## 6. פריסת מצב Standalone

### פריסה ידנית (workstation בודדת)

**שלב 1: הורד והעתק EXE**
```powershell
# הורד מ-network share או מקור מהימן
$source = "\\fileserver\software\ProjectorControl\ProjectorControl.exe"
$destination = "$env:USERPROFILE\Desktop\ProjectorControl.exe"

Copy-Item -Path $source -Destination $destination -Force
Write-Host "Copied to: $destination"
```

**שלב 2: הפעל בפעם הראשונה**
1. לחיצה כפולה על `ProjectorControl.exe`
2. אשר אזהרת אבטחה של Windows (אם מופיעה)
3. אשף התקנה ראשון מתחיל אוטומטית

**שלב 3: השלם אשף התקנה ראשון**
- **שלב 1/6:** בחר שפה (English או עברית)
- **שלב 2/6:** צור סיסמת מנהל (לפחות 8 תווים, מורכבת)
- **שלב 3/6:** בחר **Standalone (SQLite)**
- **שלב 4/6:** הגדר מקרן ראשון (או דלג)
- **שלב 5/6:** התאמה אישית של UI (השאר ברירות מחדל)
- **שלב 6/6:** סקור ולחץ Finish

**שלב 4: אמת**
```powershell
# בדוק שקובץ מסד נתונים נוצר
Test-Path "$env:APPDATA\ProjectorControl\projector_control.db"  # Should return True

# בדוק שקובץ entropy נוצר
Test-Path "$env:APPDATA\ProjectorControl\.projector_entropy"     # Should return True

# רשום מידע למעקב
Get-ChildItem "$env:APPDATA\ProjectorControl" -Recurse |
    Select-Object FullName, Length, LastWriteTime |
    Format-Table -AutoSize
```

---

### פריסה אוטומטית (workstations מרובות)

**סקריפט פריסה: `Deploy-ProjectorControl.ps1`**

```powershell
<#
.SYNOPSIS
    Deploy ProjectorControl.exe to remote computers

.DESCRIPTION
    Copies ProjectorControl.exe to multiple computers and creates startup shortcuts

.PARAMETER ComputerList
    Path to text file with computer names (one per line)

.PARAMETER SourceExe
    Path to ProjectorControl.exe

.PARAMETER CreateStartupShortcut
    If true, creates startup shortcut

.EXAMPLE
    .\Deploy-ProjectorControl.ps1 -ComputerList .\computers.txt -SourceExe \\fileserver\software\ProjectorControl.exe -CreateStartupShortcut
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$ComputerList,

    [Parameter(Mandatory=$true)]
    [string]$SourceExe,

    [switch]$CreateStartupShortcut
)

# קרא רשימת מחשבים
$computers = Get-Content $ComputerList

# פרוס לכל מחשב
foreach ($computer in $computers) {
    Write-Host "Deploying to $computer..." -ForegroundColor Cyan

    try {
        # בדוק אם המחשב online
        if (-not (Test-Connection -ComputerName $computer -Count 1 -Quiet)) {
            Write-Host "  [SKIP] $computer is offline" -ForegroundColor Yellow
            continue
        }

        # צור PS session
        $session = New-PSSession -ComputerName $computer -ErrorAction Stop

        # יעד: Program Files (requires admin)
        $destPath = "C:\Program Files\ProjectorControl\ProjectorControl.exe"

        # צור תיקייה
        Invoke-Command -Session $session -ScriptBlock {
            param($destPath)
            $destDir = Split-Path $destPath -Parent
            if (-not (Test-Path $destDir)) {
                New-Item -ItemType Directory -Path $destDir -Force | Out-Null
            }
        } -ArgumentList $destPath

        # העתק EXE
        Copy-Item -Path $SourceExe -Destination $destPath -ToSession $session -Force
        Write-Host "  [OK] Copied EXE" -ForegroundColor Green

        # צור startup shortcut (אם נדרש)
        if ($CreateStartupShortcut) {
            Invoke-Command -Session $session -ScriptBlock {
                param($destPath)
                $startupPath = "C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Startup\ProjectorControl.lnk"
                $WshShell = New-Object -ComObject WScript.Shell
                $Shortcut = $WshShell.CreateShortcut($startupPath)
                $Shortcut.TargetPath = $destPath
                $Shortcut.WorkingDirectory = Split-Path $destPath -Parent
                $Shortcut.Description = "Enhanced Projector Control"
                $Shortcut.Save()
            } -ArgumentList $destPath
            Write-Host "  [OK] Created startup shortcut" -ForegroundColor Green
        }

        # סגור session
        Remove-PSSession $session

        Write-Host "  [SUCCESS] Deployment complete on $computer" -ForegroundColor Green

    } catch {
        Write-Host "  [ERROR] Failed to deploy to $computer : $_" -ForegroundColor Red
    }
}

Write-Host "`nDeployment finished." -ForegroundColor Cyan
Write-Host "Total computers: $($computers.Count)" -ForegroundColor Cyan
```

**שימוש:**
```powershell
# צור קובץ computers.txt
$computers = @"
WORKSTATION-01
WORKSTATION-02
WORKSTATION-03
TEACHER-PC-101
TEACHER-PC-102
"@ | Out-File -FilePath .\computers.txt -Encoding UTF8

# הפעל פריסה
.\Deploy-ProjectorControl.ps1 `
    -ComputerList .\computers.txt `
    -SourceExe "\\fileserver\software\ProjectorControl\ProjectorControl.exe" `
    -CreateStartupShortcut
```

---

### Group Policy Deployment (GPO)

**שלב 1: הכן network share**
```powershell
# צור shared folder
$sharePath = "\\FILESERVER\Software\ProjectorControl"
New-Item -ItemType Directory -Path "C:\Shares\Software\ProjectorControl" -Force
New-SmbShare -Name "ProjectorControl$" -Path "C:\Shares\Software\ProjectorControl" -FullAccess "Domain Computers"

# העתק EXE
Copy-Item "ProjectorControl.exe" -Destination "C:\Shares\Software\ProjectorControl\"
```

**שלב 2: צור GPO**
1. פתח **Group Policy Management Console** (gpmc.msc)
2. לחץ ימין על OU עם workstations > **Create a GPO in this domain**
3. שם: "Deploy Projector Control Application"
4. לחץ ימין על GPO > **Edit**

**שלב 3: הגדר Computer Startup Script**
1. נווט ל-**Computer Configuration > Policies > Windows Settings > Scripts (Startup/Shutdown)**
2. לחיצה כפולה על **Startup** > **PowerShell Scripts** tab
3. לחץ **Add** > **Browse**
4. צור סקריפט `InstallProjectorControl.ps1`:

```powershell
# InstallProjectorControl.ps1 - GPO Startup Script
$source = "\\FILESERVER\Software\ProjectorControl$\ProjectorControl.exe"
$dest = "C:\Program Files\ProjectorControl\ProjectorControl.exe"

# צור תיקייה
$destDir = Split-Path $dest -Parent
if (-not (Test-Path $destDir)) {
    New-Item -ItemType Directory -Path $destDir -Force | Out-Null
}

# העתק אם לא קיים או גרסה ישנה
if (-not (Test-Path $dest) -or ((Get-Item $source).LastWriteTime -gt (Get-Item $dest).LastWriteTime)) {
    Copy-Item -Path $source -Destination $dest -Force

    # צור קיצור דרך startup עבור כל המשתמשים
    $startupPath = "C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Startup\ProjectorControl.lnk"
    $WshShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut($startupPath)
    $Shortcut.TargetPath = $dest
    $Shortcut.Save()
}
```

5. שמור GPO
6. קשר GPO ל-OU עם workstations

**שלב 4: אכוף GPO**
```powershell
# על workstation, אכוף GPO מיד
gpupdate /force

# בדוק שסקריפט הורץ
Get-EventLog -LogName "Application" -Source "GroupPolicy" -Newest 10
```

---

### גיבוי והפצת תצורה מוגדרת מראש

**שימוש: התקן 50 workstations עם אותן הגדרות מקרן**

**שלב 1: הגדר "Master" workstation**
1. התקן `ProjectorControl.exe`
2. השלם אשף התקנה ראשון
3. הגדר את **כל** המקרנים (Settings > Connection > Add New Projector)
4. בדוק שהכל עובד

**שלב 2: צור Backup**
1. Settings > Backup > Create Backup
2. שמור ל-`master-config.enc`
3. העתק גם את `%APPDATA%\ProjectorControl\.projector_entropy`

**שלב 3: הפץ למחשבים אחרים**

```powershell
# סקריפט: Distribute-MasterConfig.ps1
param(
    [string]$ComputerList = ".\computers.txt",
    [string]$MasterBackup = ".\master-config.enc",
    [string]$MasterEntropy = ".\.projector_entropy",
    [string]$AdminPassword = "Admin123!"  # סיסמת מנהל שכל המשתמשים ישתמשו בה
)

$computers = Get-Content $ComputerList

foreach ($computer in $computers) {
    Write-Host "Configuring $computer..." -ForegroundColor Cyan

    try {
        $session = New-PSSession -ComputerName $computer

        # העתק backup + entropy
        $appData = Invoke-Command -Session $session -ScriptBlock { $env:APPDATA }
        $destDir = "$appData\ProjectorControl"

        # צור תיקייה
        Invoke-Command -Session $session -ScriptBlock {
            param($dir)
            if (-not (Test-Path $dir)) {
                New-Item -ItemType Directory -Path $dir -Force | Out-Null
            }
        } -ArgumentList $destDir

        # העתק entropy file (CRITICAL!)
        Copy-Item -Path $MasterEntropy -Destination "$destDir\.projector_entropy" -ToSession $session -Force

        # העתק backup file
        Copy-Item -Path $MasterBackup -Destination "$destDir\master-config.enc" -ToSession $session -Force

        Write-Host "  [OK] Copied config files to $computer" -ForegroundColor Green

        Remove-PSSession $session

    } catch {
        Write-Host "  [ERROR] Failed on $computer : $_" -ForegroundColor Red
    }
}

Write-Host "`nDistribution complete."
Write-Host "NEXT STEP: Users must run ProjectorControl.exe and restore from 'master-config.enc'"
Write-Host "Admin password for all workstations: $AdminPassword"
```

**שלב 4: משתמשים משחזרים תצורה**
```
פעמיים לחיצה על ProjectorControl.exe
→ אשף התקנה ראשון מתחיל
→ שלב 2: הזן סיסמת מנהל: "Admin123!" (סיסמה משותפת)
→ שלב 3: בחר Standalone
→ השלם אשף
→ Settings > Backup > Restore from Backup
→ בחר "master-config.enc"
→ הזן סיסמת מנהל "Admin123!"
→ כל המקרנים נטענים אוטומטית!
```

---

## 7. פריסת מצב Enterprise

### תהליך פריסה

**גבוה-רמה:**
1. הכן SQL Server (ראה [סעיף 5](#5-הכנת-sql-server))
2. פרוס `ProjectorControl.exe` ל-workstations
3. הגדר workstation ראשון עם תצורות מקרן
4. workstations נוספות יורשות תצורה אוטומטית מ-SQL

---

### הגדרת Workstation ראשון (Master)

**שלב 1: התקן ביישום**
```powershell
# העתק EXE
Copy-Item "\\fileserver\software\ProjectorControl.exe" "C:\Program Files\ProjectorControl\ProjectorControl.exe"
```

**שלב 2: הפעל אשף התקנה ראשון**
1. לחיצה כפולה `ProjectorControl.exe`
2. **שלב 1/6:** בחר שפה
3. **שלב 2/6:** צור סיסמת מנהל (ייחודית לworkstation זה - לא משותפת!)
4. **שלב 3/6:** בחר **Enterprise (SQL Server)**
5. הזן פרטי חיבור SQL:
   - **שרת:** `sqlserver.domain.local` או `10.0.20.10`
   - **מסד נתונים:** `ProjectorControl`
   - **אימות:** SQL Server או Windows
     - **SQL Auth:** שם משתמש: `projector_app_user`, סיסמה: `P@ssw0rd_Secure_2026!`
     - **Windows Auth:** השאר ריק (משתמש אישורי Windows הנוכחיים)
6. לחץ **Test Connection** - צריך להראות "Success"
7. **שלב 4/6:** הגדר מקרן ראשון
8. **שלב 5-6:** השלם אשף

**שלב 3: אמת SQL Connection**
```powershell
# בדוק ש-workstation מחובר ל-SQL Server
# הפעל על workstation:
sqlcmd -S sqlserver.domain.local -d ProjectorControl -U projector_app_user -P "P@ssw0rd_Secure_2026!" -Q "SELECT name FROM sys.tables"
```

**תוצאה צפויה:**
```
name
projector_config
operation_history
schema_version
```

**שלב 4: הוסף כל המקרנים**
1. Settings > Connection > Add New Projector
2. הגדר את כל המקרנים בארגון
3. לחץ Test Connection לכל אחד
4. שמור

---

### הגדרת Workstations נוספות

**הפליטה: כל workstation נוסף יורש תצורת מקרן אוטומטית מ-SQL Server!**

**שלב 1: פרוס EXE (זהה למצב Standalone)**
```powershell
# השתמש באותו סקריפט Deploy-ProjectorControl.ps1
.\Deploy-ProjectorControl.ps1 `
    -ComputerList .\computers.txt `
    -SourceExe "\\fileserver\software\ProjectorControl\ProjectorControl.exe" `
    -CreateStartupShortcut
```

**שלב 2: הפעל אשף התקנה ראשון (על כל workstation)**
1. המשתמש פותח `ProjectorControl.exe` בפעם הראשונה
2. **שלב 1-2:** בחר שפה + צור סיסמת מנהל (ייחודית לכל משתמש)
3. **שלב 3:** בחר **Enterprise (SQL Server)**
4. הזן **אותם** פרטי חיבור SQL כמו workstation ראשון:
   - שרת: `sqlserver.domain.local`
   - מסד נתונים: `ProjectorControl`
   - אימות: SQL Server Authentication
   - שם משתמש: `projector_app_user`
   - סיסמה: `P@ssw0rd_Secure_2026!`
5. לחץ **Test Connection**
6. **שלב 4:** דלג על הגדרת מקרן (כבר מוגדר ב-SQL!)
7. השלם אשף

**שלב 3: אמת**
- פתח את היישום
- בורר המקרנים (toolbar) צריך להציג **כל** המקרנים שהוגדרו ב-workstation הראשון
- לא צריך תצורה נוספת!

---

### Automation עם Unattended Setup (Advanced)

**יצירת קובץ תצורה מוגדר מראש**

**קובץ: `enterprise-config.ini`**
```ini
[Database]
Mode=enterprise
ServerAddress=sqlserver.domain.local
DatabaseName=ProjectorControl
AuthType=sql
Username=projector_app_user
Password=P@ssw0rd_Secure_2026!

[Application]
Language=en
CreateStartupShortcut=true
AdminPasswordHash=$2b$14$...  # bcrypt hash של "Admin123!"
```

**שינוי אשף התקנה ראשון לקרוא config:**
```python
# הערה: זה דורש שינוי קוד מקור - לא זמין out-of-the-box
# דוגמה קונספטואלית בלבד

# In first_run_wizard.py:
def load_unattended_config():
    config_path = os.path.join(os.path.dirname(__file__), "enterprise-config.ini")
    if os.path.exists(config_path):
        config = configparser.ConfigParser()
        config.read(config_path)
        return config
    return None

# In wizard initialization:
unattended = load_unattended_config()
if unattended:
    # Pre-populate wizard fields
    self.db_mode = unattended['Database']['Mode']
    self.server_address = unattended['Database']['ServerAddress']
    # ... etc
    # Skip wizard entirely if all fields valid
    if self.validate_config():
        self.finish_setup_silently()
```

**פריסה:**
```powershell
# העתק config + EXE ביחד
$destDir = "C:\Program Files\ProjectorControl"
Copy-Item "ProjectorControl.exe" -Destination "$destDir\"
Copy-Item "enterprise-config.ini" -Destination "$destDir\"

# הפעל EXE - יקרא config ויגדיר אוטומטית
Start-Process "$destDir\ProjectorControl.exe" -ArgumentList "--unattended"
```

**הערה:** תכונת Unattended setup אינה מיושמת כרגע ב-v2.0. זה דורש פיתוח עתידי.

---

## 8. תצורה ראשונית

### שיטות עבודה מומלצות לסיסמת מנהל

**דרישות סיסמה:**
- לפחות 8 תווים
- אות גדולה אחת לפחות (A-Z)
- מספר אחד לפחות (0-9)
- תו מיוחד אחד לפחות (!@#$%^&*)

**דוגמאות לסיסמאות חזקות:**
- `ProjectorAdmin2026!`
- `P@ssw0rd_Secure`
- `Admin#Projector99`

**אל תעשה:**
❌ `password` - פשוט מדי
❌ `admin` - שכיח מדי
❌ `123456` - מספרים בלבד
❌ `qwerty` - דפוס מקלדת

**שיטות עבודה מומלצות:**
✅ **תעד בצורה מאובטחת** - שמור במנהל סיסמאות IT
✅ **ייחודי לכל workstation** (מצב Standalone) - למנוע פשרה מקבילה
✅ **משותף בארגון** (מצב Enterprise) - או השתמש ב-Windows Auth
✅ **סובב מדי 90 ימים** - שקול מדיניות פקיעה

---

### רשימת בדיקה של אימות התקנה

**בדיקה 1: הקובץ הוא קוב"ץ הפעלה תקין**
```powershell
# בדוק שקובץ EXE קיים וגודל סביר
$exe = "C:\Program Files\ProjectorControl\ProjectorControl.exe"
if (Test-Path $exe) {
    $size = (Get-Item $exe).Length / 1MB
    Write-Host "[OK] EXE exists. Size: $([math]::Round($size, 2)) MB"
    if ($size -lt 30 -or $size -gt 100) {
        Write-Host "[WARNING] Size unexpected (should be 40-55 MB)" -ForegroundColor Yellow
    }
} else {
    Write-Host "[FAIL] EXE not found at $exe" -ForegroundColor Red
}
```

**בדיקה 2: יישום מתחיל ללא שגיאות**
```powershell
# הפעל ובדוק שלא קורס
Start-Process $exe -PassThru | Wait-Process -Timeout 10
if ($?) {
    Write-Host "[OK] Application started without crash" -ForegroundColor Green
} else {
    Write-Host "[FAIL] Application crashed on startup" -ForegroundColor Red
}
```

**בדיקה 3: מסד נתונים נוצר (Standalone)**
```powershell
$db = "$env:APPDATA\ProjectorControl\projector_control.db"
if (Test-Path $db) {
    Write-Host "[OK] Database file created" -ForegroundColor Green
} else {
    Write-Host "[FAIL] Database file missing" -ForegroundColor Red
}
```

**בדיקה 4: קובץ Entropy נוצר**
```powershell
$entropy = "$env:APPDATA\ProjectorControl\.projector_entropy"
if (Test-Path $entropy) {
    $size = (Get-Item $entropy).Length
    Write-Host "[OK] Entropy file created ($size bytes)" -ForegroundColor Green
    if ($size -ne 256) {
        Write-Host "[WARNING] Entropy file size unexpected (should be 256 bytes)" -ForegroundColor Yellow
    }
} else {
    Write-Host "[FAIL] Entropy file missing" -ForegroundColor Red
}
```

**בדיקה 5: חיבור SQL Server (Enterprise)**
```powershell
# בדוק חיבור SQL
$connString = "Server=sqlserver.domain.local;Database=ProjectorControl;User Id=projector_app_user;Password=P@ssw0rd_Secure_2026!;Encrypt=True;TrustServerCertificate=True;"
$conn = New-Object System.Data.SqlClient.SqlConnection($connString)
try {
    $conn.Open()
    Write-Host "[OK] SQL Server connection successful" -ForegroundColor Green

    # בדוק שטבלאות קיימות
    $cmd = $conn.CreateCommand()
    $cmd.CommandText = "SELECT COUNT(*) FROM sys.tables WHERE name IN ('projector_config', 'operation_history')"
    $count = $cmd.ExecuteScalar()
    if ($count -eq 2) {
        Write-Host "[OK] Required tables exist" -ForegroundColor Green
    } else {
        Write-Host "[FAIL] Required tables missing ($count/2 found)" -ForegroundColor Red
    }

    $conn.Close()
} catch {
    Write-Host "[FAIL] SQL Server connection failed: $_" -ForegroundColor Red
}
```

**בדיקה 6: חיבור למקרן**
```powershell
# בדוק חיבור PJLink
Test-NetConnection -ComputerName 10.0.50.10 -Port 4352 -InformationLevel Detailed
```

**רשימת בדיקה מלאה:**
```
□ קובץ EXE קיים וגודל תקין (40-55 MB)
□ יישום מתחיל ללא קריסות
□ קובץ מסד נתונים נוצר (%APPDATA%\ProjectorControl\projector_control.db)
□ קובץ entropy נוצר (%APPDATA%\ProjectorControl\.projector_entropy, 256 bytes)
□ (Enterprise) חיבור SQL Server מוצלח
□ (Enterprise) טבלאות מסד נתונים קיימות
□ חיבור PJLink למקרן מוצלח (ping + port 4352)
□ פקודות Power On/Off עובדות
□ History panel מציג פעולות
□ System tray icon מופיע וזמין
```

---

## 9. הקשחת אבטחה

### הרשאות מערכת קבצים

**הגבל גישה לתיקיית %APPDATA%:**

```powershell
# תיקיית ProjectorControl
$appData = "$env:APPDATA\ProjectorControl"

# הסר הרשאות inherited
$acl = Get-Acl $appData
$acl.SetAccessRuleProtection($true, $false)  # Disable inheritance, don't copy existing

# הענק גישה רק למשתמש נוכחי + SYSTEM
$user = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$systemAccount = "NT AUTHORITY\SYSTEM"

$userRule = New-Object System.Security.AccessControl.FileSystemAccessRule(
    $user, "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow"
)
$systemRule = New-Object System.Security.AccessControl.FileSystemAccessRule(
    $systemAccount, "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow"
)

$acl.SetAccessRule($userRule)
$acl.SetAccessRule($systemRule)
Set-Acl -Path $appData -AclObject $acl

Write-Host "Permissions hardened on $appData"
```

**הגן על קובץ entropy:**

```powershell
# קובץ .projector_entropy הוא CRITICAL - הצפנה נוספת
$entropy = "$env:APPDATA\ProjectorControl\.projector_entropy"

# הסתר קובץ
$file = Get-Item $entropy -Force
$file.Attributes = $file.Attributes -bor [System.IO.FileAttributes]::Hidden

# הגבל הרשאות (רק משתמש נוכחי + SYSTEM)
$acl = Get-Acl $entropy
$acl.SetAccessRuleProtection($true, $false)

$user = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$userRule = New-Object System.Security.AccessControl.FileSystemAccessRule(
    $user, "Read", "Allow"
)
$systemRule = New-Object System.Security.AccessControl.FileSystemAccessRule(
    "NT AUTHORITY\SYSTEM", "FullControl", "Allow"
)

$acl.SetAccessRule($userRule)
$acl.SetAccessRule($systemRule)
Set-Acl -Path $entropy -AclObject $acl

Write-Host "Entropy file secured and hidden"
```

---

### הצפנת דיסק קשיח (BitLocker)

**הפעל BitLocker על כל workstations:**

```powershell
# בדוק אם BitLocker כבר מופעל
$volume = Get-BitLockerVolume -MountPoint "C:"
if ($volume.ProtectionStatus -eq "On") {
    Write-Host "BitLocker already enabled on C:" -ForegroundColor Green
} else {
    # הפעל BitLocker (דורש TPM או password)
    Enable-BitLocker -MountPoint "C:" -EncryptionMethod XtsAes256 -UsedSpaceOnly -RecoveryPasswordProtector

    # שמור recovery key במיקום מאובטח
    $recoveryKey = (Get-BitLockerVolume -MountPoint "C:").KeyProtector | Where-Object {$_.KeyProtectorType -eq 'RecoveryPassword'}
    $recoveryKey.RecoveryPassword | Out-File "\\fileserver\BitLockerKeys\$env:COMPUTERNAME.txt"

    Write-Host "BitLocker enabled. Recovery key saved to file server."
}
```

**מדוע BitLocker חשוב:**
- מגן על `%APPDATA%\ProjectorControl\` אם מחשב נגנב
- מגן על קובץ entropy ומסד נתונים מגישה פיזית
- תקן תאימות רגולטורית (GDPR, HIPAA)

---

### אבטחת רשת

**VLAN Isolation (מומלץ ביותר):**
- **VLAN 10** - משתמשים
- **VLAN 50** - מקרנים (מבודדים מאינטרנט)
- **VLAN 20** - שרתים (SQL Server)

**Firewall Rules (ראה [סעיף 4](#4-הגדרת-תשתית-רשת))**

**אבטחת פרוטוקול PJLink:**

**1. הגדר סיסמת PJLink על מקרנים:**
- גש לתפריט OSD של המקרן > Network > PJLink Settings
- הפעל "PJLink Authentication"
- הגדר סיסמה (לדוגמה: `PJLink2026!`)
- שמור

**2. הגדר סיסמה ביישום:**
- Settings > Connection > Edit (projector)
- הזן סיסמה בשדה "Password"
- Test Connection כדי לאמת
- שמור

**3. בדוק שגישה לא מאומתת נחסמת:**
```powershell
# נסה להתחבר ללא סיסמה (צריך להיכשל)
$socket = New-Object System.Net.Sockets.TcpClient("10.0.50.10", 4352)
$stream = $socket.GetStream()
$reader = New-Object System.IO.StreamReader($stream)
$writer = New-Object System.IO.StreamWriter($stream)

$banner = $reader.ReadLine()
Write-Host "Banner: $banner"  # Should be "PJLINK 1 <random-challenge>"

# נסה פקודה ללא אימות
$writer.WriteLine("%1POWR ?`r")
$writer.Flush()
$response = $reader.ReadLine()
Write-Host "Response: $response"  # Should be "PJLINK ERRA" (authentication required)

$socket.Close()
```

---

### ביקורת SQL Server (Enterprise mode)

**הפעל SQL Server Audit:**

```sql
-- צור server audit
USE master;
GO

CREATE SERVER AUDIT ProjectorControl_Audit
TO FILE (
    FILEPATH = 'C:\SQLAudit\',
    MAXSIZE = 100 MB,
    MAX_ROLLOVER_FILES = 10,
    RESERVE_DISK_SPACE = OFF
)
WITH (
    QUEUE_DELAY = 1000,
    ON_FAILURE = CONTINUE
);
GO

ALTER SERVER AUDIT ProjectorControl_Audit WITH (STATE = ON);
GO

-- צור database audit specification
USE ProjectorControl;
GO

CREATE DATABASE AUDIT SPECIFICATION ProjectorControl_DB_Audit
FOR SERVER AUDIT ProjectorControl_Audit
ADD (SELECT, INSERT, UPDATE, DELETE ON DATABASE::ProjectorControl BY [public]),
ADD (EXECUTE ON DATABASE::ProjectorControl BY [public])
WITH (STATE = ON);
GO

-- אמת שaudit פועל
SELECT
    audit_id,
    name,
    type_desc,
    on_failure_desc,
    is_state_enabled
FROM sys.server_audits
WHERE name = 'ProjectorControl_Audit';
GO
```

**צפה בלוגי Audit:**
```sql
-- הצג 100 הפעולות האחרונות
SELECT TOP 100
    event_time,
    action_id,
    succeeded,
    session_server_principal_name AS [User],
    database_name,
    schema_name,
    object_name,
    statement
FROM fn_get_audit_file('C:\SQLAudit\*.sqlaudit', DEFAULT, DEFAULT)
ORDER BY event_time DESC;
GO
```

---

## 10. גיבוי ושחזור אסון

### אסטרטגיית גיבוי

**עקרון 3-2-1:**
- **3** עותקים של הנתונים
- **2** סוגי מדיה שונים
- **1** עותק off-site

**חל על ProjectorControl:**
- **עותק 1:** מסד נתונים מקורי + entropy file
- **עותק 2:** גיבוי יומי ל-network share
- **עותק 3:** גיבוי שבועי ל-cloud storage או off-site

---

### גיבוי Standalone Mode

**סקריפט גיבוי אוטומטי:**

**קובץ: `Backup-ProjectorControl.ps1`**

```powershell
<#
.SYNOPSIS
    Automated backup for ProjectorControl (Standalone mode)

.DESCRIPTION
    Backs up SQLite database and entropy file to network share
    Retains last 30 days of backups
    Logs all operations

.PARAMETER BackupDestination
    UNC path to network share

.EXAMPLE
    .\Backup-ProjectorControl.ps1 -BackupDestination "\\fileserver\backups\ProjectorControl\$env:COMPUTERNAME"
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$BackupDestination
)

# הגדרת לוגינג
$logFile = "$env:TEMP\ProjectorControl_Backup.log"
function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp - $Message" | Tee-Object -FilePath $logFile -Append
}

Write-Log "=== Backup Started ==="

# נתיבי מקור
$sourceDir = "$env:APPDATA\ProjectorControl"
$sourceDB = "$sourceDir\projector_control.db"
$sourceEntropy = "$sourceDir\.projector_entropy"
$sourceConfig = "$sourceDir\config.ini"

# בדוק שקבצים קיימים
if (-not (Test-Path $sourceDB)) {
    Write-Log "ERROR: Database file not found at $sourceDB"
    exit 1
}
if (-not (Test-Path $sourceEntropy)) {
    Write-Log "ERROR: Entropy file not found at $sourceEntropy"
    exit 1
}

# צור תיקיית יעד
try {
    if (-not (Test-Path $BackupDestination)) {
        New-Item -ItemType Directory -Path $BackupDestination -Force | Out-Null
        Write-Log "Created backup destination: $BackupDestination"
    }
} catch {
    Write-Log "ERROR: Failed to create backup destination: $_"
    exit 1
}

# שם גיבוי עם חותמת זמן
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupSuffix = "_$timestamp"

# גבה קבצים
try {
    # Database
    $destDB = "$BackupDestination\projector_control$backupSuffix.db"
    Copy-Item -Path $sourceDB -Destination $destDB -Force
    Write-Log "Backed up database to $destDB"

    # Entropy file (CRITICAL - גבה בנפרד)
    $destEntropy = "$BackupDestination\.projector_entropy$backupSuffix"
    Copy-Item -Path $sourceEntropy -Destination $destEntropy -Force
    Write-Log "Backed up entropy file to $destEntropy"

    # Config (אופציונלי)
    if (Test-Path $sourceConfig) {
        $destConfig = "$BackupDestination\config$backupSuffix.ini"
        Copy-Item -Path $sourceConfig -Destination $destConfig -Force
        Write-Log "Backed up config to $destConfig"
    }

} catch {
    Write-Log "ERROR: Backup failed: $_"
    exit 1
}

# ניקוי גיבויים ישנים (שמור 30 ימים אחרונים)
try {
    $cutoffDate = (Get-Date).AddDays(-30)
    $oldBackups = Get-ChildItem $BackupDestination -File | Where-Object { $_.LastWriteTime -lt $cutoffDate }

    if ($oldBackups.Count -gt 0) {
        $oldBackups | Remove-Item -Force
        Write-Log "Deleted $($oldBackups.Count) old backups (older than 30 days)"
    }

} catch {
    Write-Log "WARNING: Failed to clean old backups: $_"
}

Write-Log "=== Backup Completed Successfully ==="
exit 0
```

**התזמן עם Task Scheduler:**

```powershell
# צור scheduled task (רץ כמשתמש נוכחי)
$taskName = "ProjectorControl Daily Backup"
$scriptPath = "C:\Scripts\Backup-ProjectorControl.ps1"
$backupDest = "\\fileserver\backups\ProjectorControl\$env:COMPUTERNAME"

$action = New-ScheduledTaskAction -Execute "PowerShell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`" -BackupDestination `"$backupDest`""

$trigger = New-ScheduledTaskTrigger -Daily -At 2AM

$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -RunOnlyIfNetworkAvailable

# רץ כמשתמש נוכחי (נדרש לגישה ל-%APPDATA%)
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType S4U

Register-ScheduledTask -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description "Daily backup of ProjectorControl database and entropy file"

Write-Host "Scheduled task created: $taskName"
Write-Host "Runs daily at 2:00 AM as $env:USERNAME"
```

---

### גיבוי Enterprise Mode

**SQL Server Backups:**

```sql
-- גיבוי מלא יומי
USE master;
GO

-- צור maintenance plan או השתמש ב-T-SQL job
BACKUP DATABASE [ProjectorControl]
TO DISK = N'D:\SQLBackups\ProjectorControl_Full.bak'
WITH
    FORMAT,
    INIT,
    NAME = N'ProjectorControl-Full Database Backup',
    COMPRESSION,
    STATS = 10;
GO

-- גיבוי differentialהתפלט כל 6 שעות
BACKUP DATABASE [ProjectorControl]
TO DISK = N'D:\SQLBackups\ProjectorControl_Diff.bak'
WITH
    DIFFERENTIAL,
    FORMAT,
    INIT,
    NAME = N'ProjectorControl-Differential Database Backup',
    COMPRESSION,
    STATS = 10;
GO

-- גיבוי transaction log כל שעה (אם Full/Bulk-Logged recovery model)
BACKUP LOG [ProjectorControl]
TO DISK = N'D:\SQLBackups\ProjectorControl_Log.trn'
WITH
    FORMAT,
    INIT,
    NAME = N'ProjectorControl-Transaction Log Backup',
    COMPRESSION,
    STATS = 10;
GO
```

**אוטומציה עם SQL Server Agent:**

```sql
-- צור SQL Agent Job לגיבוי מלא יומי
USE msdb;
GO

EXEC sp_add_job
    @job_name = N'ProjectorControl - Daily Full Backup',
    @enabled = 1,
    @description = N'Daily full backup of ProjectorControl database';
GO

EXEC sp_add_jobstep
    @job_name = N'ProjectorControl - Daily Full Backup',
    @step_name = N'Backup Database',
    @subsystem = N'TSQL',
    @command = N'BACKUP DATABASE [ProjectorControl] TO DISK = N''D:\SQLBackups\ProjectorControl_Full.bak'' WITH FORMAT, INIT, COMPRESSION;',
    @on_success_action = 1;  -- Quit with success
GO

EXEC sp_add_schedule
    @schedule_name = N'Daily at 2AM',
    @freq_type = 4,  -- Daily
    @freq_interval = 1,
    @active_start_time = 020000;  -- 2:00 AM
GO

EXEC sp_attach_schedule
    @job_name = N'ProjectorControl - Daily Full Backup',
    @schedule_name = N'Daily at 2AM';
GO

EXEC sp_add_jobserver
    @job_name = N'ProjectorControl - Daily Full Backup',
    @server_name = N'(local)';
GO
```

**גבה גם entropy files מ-workstations!**

```powershell
# סקריפט מרכזי לגיבוי entropy files מכל workstations
param(
    [string]$ComputerList = ".\computers.txt",
    [string]$BackupDestination = "\\fileserver\backups\EntropyFiles"
)

$computers = Get-Content $ComputerList

foreach ($computer in $computers) {
    Write-Host "Backing up entropy from $computer..." -ForegroundColor Cyan

    try {
        # התחבר remote
        $session = New-PSSession -ComputerName $computer -ErrorAction Stop

        # מצא entropy file
        $entropy = Invoke-Command -Session $session -ScriptBlock {
            Get-ChildItem "$env:APPDATA\ProjectorControl\.projector_entropy" -Force -ErrorAction Stop
        }

        if ($entropy) {
            # העתק מ-remote ל-central backup
            $dest = "$BackupDestination\$computer-entropy-$(Get-Date -Format 'yyyyMMdd').bin"
            Copy-Item -FromSession $session -Path $entropy.FullName -Destination $dest -Force
            Write-Host "  [OK] Backed up entropy from $computer" -ForegroundColor Green
        } else {
            Write-Host "  [WARNING] Entropy file not found on $computer" -ForegroundColor Yellow
        }

        Remove-PSSession $session

    } catch {
        Write-Host "  [ERROR] Failed to backup from $computer : $_" -ForegroundColor Red
    }
}
```

---

### תרחישי שחזור

**תרחיש 1: אובדן workstation בודדת (Standalone)**

**בעיה:** המחשב קרס, דיסק קשיח נכשל, או Windows הותקן מחדש.

**שחזור:**
1. התקן מחדש Windows
2. העתק `ProjectorControl.exe` למחשב חדש
3. הפעל ב first time
4. השלם אשף setup עד לסיום
5. העתק קבצי גיבוי:
   ```powershell
   # העתק גיבוי אחרון
   $backupDir = "\\fileserver\backups\ProjectorControl\OLD-COMPUTER-NAME"
   $latestDB = Get-ChildItem "$backupDir\projector_control_*.db" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
   $latestEntropy = Get-ChildItem "$backupDir\.projector_entropy_*" | Sort-Object LastWriteTime -Descending | Select-Object -First 1

   Copy-Item $latestDB.FullName -Destination "$env:APPDATA\ProjectorControl\projector_control.db" -Force
   Copy-Item $latestEntropy.FullName -Destination "$env:APPDATA\ProjectorControl\.projector_entropy" -Force
   ```
6. הפעל מחדש את היישום - כל התצורות שוחזרו!

---

**תרחיש 2: אובדן workstation (Enterprise)**

**בעיה:** מחשב קרס אך SQL Server תקין.

**שחזור:**
1. התקן Windows חדש
2. התקן `ProjectorControl.exe`
3. הפעל אשף setup ראשון
4. בחר **Enterprise**, הזן פרטי חיבור SQL
5. **רק צריך לשחזר entropy file:**
   ```powershell
   # העתק entropy מגיבוי מרכזי
   $entropyBackup = "\\fileserver\backups\EntropyFiles\OLD-COMPUTER-entropy-*.bin" | Sort-Object -Descending | Select-Object -First 1
   Copy-Item $entropyBackup -Destination "$env:APPDATA\ProjectorControl\.projector_entropy" -Force
   ```
6. הפעל את היישום - כל תצורות המקרנים נטענות מ-SQL!

---

**תרחיש 3: אובדן SQL Server (Enterprise)**

**בעיה:** SQL Server קרס, מסד נתונים נמחק.

**שחזור:**
1. שחזר SQL Server מגיבוי (ראה למעלה)
   ```sql
   USE master;
   GO

   RESTORE DATABASE [ProjectorControl]
   FROM DISK = N'D:\SQLBackups\ProjectorControl_Full.bak'
   WITH REPLACE, RECOVERY;
   GO
   ```
2. אמת שחזור:
   ```sql
   USE ProjectorControl;
   SELECT COUNT(*) FROM projector_config;  -- Should return number of configured projectors
   SELECT COUNT(*) FROM operation_history; -- Should return historical operations
   ```
3. בדוק חיבור מ-workstation
4. הכל צריך לעבוד כרגיל

---

**תרחיש 4: אובדן entropy file (קריטי!)**

**בעיה:** קובץ `.projector_entropy` נמחק או אבד. מסד נתונים קיים אך סיסמאות מוצפנות.

**שחזור:**

**אפשרות 1: שחזר מגיבוי (אידיאלי)**
```powershell
$entropyBackup = "\\fileserver\backups\EntropyFiles\$env:COMPUTERNAME-entropy-*.bin" | Sort-Object -Descending | Select-Object -First 1
Copy-Item $entropyBackup -Destination "$env:APPDATA\ProjectorControl\.projector_entropy" -Force
```

**אפשרות 2: אם אין גיבוי (אובדן נתונים!)**
- לא ניתן לפענח סיסמאות מקרן מוצפנות
- חייב להזין מחדש **כל** סיסמאות המקרנים:
  1. Settings > Connection
  2. לכל מקרן: Edit > הזן מחדש סיסמה > Test > Save
  3. קובץ entropy חדש נוצר אוטומטית
  4. צור גיבוי מיד!

> **זו הסיבה שגיבוי entropy קריטי!!!**

---

## 11. ניטור ותחזוקה

### בדיקות בריאות

**סקריפט בדיקה יומי:**

**קובץ: `HealthCheck-ProjectorControl.ps1`**

```powershell
<#
.SYNOPSIS
    Health check for ProjectorControl deployment

.DESCRIPTION
    Checks application status, database integrity, network connectivity, disk space
    Sends email alert if issues detected

.EXAMPLE
    .\HealthCheck-ProjectorControl.ps1
#>

# הגדרות
$smtpServer = "smtp.domain.local"
$emailFrom = "it-monitoring@domain.local"
$emailTo = "admin@domain.local"
$alertSubject = "[ALERT] ProjectorControl Health Check Failed"

# בדיקות
$checks = @()

# בדיקה 1: קובץ EXE קיים
$exePath = "C:\Program Files\ProjectorControl\ProjectorControl.exe"
if (Test-Path $exePath) {
    $checks += @{Name="EXE exists"; Status="PASS"; Details="Found at $exePath"}
} else {
    $checks += @{Name="EXE exists"; Status="FAIL"; Details="Not found at $exePath"}
}

# בדיקה 2: מסד נתונים קיים (Standalone)
$dbPath = "$env:APPDATA\ProjectorControl\projector_control.db"
if (Test-Path $dbPath) {
    $dbSize = (Get-Item $dbPath).Length / 1KB
    $checks += @{Name="Database exists"; Status="PASS"; Details="Size: $([math]::Round($dbSize, 2)) KB"}
} else {
    $checks += @{Name="Database exists"; Status="FAIL"; Details="Not found"}
}

# בדיקה 3: Entropy file קיים
$entropyPath = "$env:APPDATA\ProjectorControl\.projector_entropy"
if (Test-Path $entropyPath) {
    $entropySize = (Get-Item $entropyPath -Force).Length
    if ($entropySize -eq 256) {
        $checks += @{Name="Entropy file"; Status="PASS"; Details="256 bytes"}
    } else {
        $checks += @{Name="Entropy file"; Status="WARN"; Details="Size $entropySize (expected 256)"}
    }
} else {
    $checks += @{Name="Entropy file"; Status="FAIL"; Details="Not found"}
}

# בדיקה 4: גיבוי אחרון (בדוק שגיבוי התקבל ב-24 שעות אחרונות)
$backupDir = "\\fileserver\backups\ProjectorControl\$env:COMPUTERNAME"
if (Test-Path $backupDir) {
    $latestBackup = Get-ChildItem "$backupDir\projector_control_*.db" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($latestBackup) {
        $age = (Get-Date) - $latestBackup.LastWriteTime
        if ($age.TotalHours -lt 24) {
            $checks += @{Name="Recent backup"; Status="PASS"; Details="Last backup: $($latestBackup.LastWriteTime)"}
        } else {
            $checks += @{Name="Recent backup"; Status="WARN"; Details="Last backup $([math]::Round($age.TotalHours, 1)) hours ago"}
        }
    } else {
        $checks += @{Name="Recent backup"; Status="FAIL"; Details="No backups found"}
    }
} else {
    $checks += @{Name="Recent backup"; Status="FAIL"; Details="Backup directory not found"}
}

# בדיקה 5: קישוריות למקרן
$projectorIP = "10.0.50.10"  # שנה לIP של המקרן שלך
$projectorTest = Test-NetConnection -ComputerName $projectorIP -Port 4352 -InformationLevel Quiet -WarningAction SilentlyContinue
if ($projectorTest) {
    $checks += @{Name="Projector connectivity"; Status="PASS"; Details="$projectorIP:4352 reachable"}
} else {
    $checks += @{Name="Projector connectivity"; Status="FAIL"; Details="Cannot reach $projectorIP:4352"}
}

# בדיקה 6: מקום דיסק
$freeSpace = (Get-PSDrive C).Free / 1GB
if ($freeSpace -gt 5) {
    $checks += @{Name="Disk space"; Status="PASS"; Details="$([math]::Round($freeSpace, 2)) GB free"}
} else {
    $checks += @{Name="Disk space"; Status="WARN"; Details="Only $([math]::Round($freeSpace, 2)) GB free"}
}

# סיכום
$failed = $checks | Where-Object { $_.Status -eq "FAIL" }
$warnings = $checks | Where-Object { $_.Status -eq "WARN" }

Write-Host "`n=== ProjectorControl Health Check ===" -ForegroundColor Cyan
foreach ($check in $checks) {
    $color = switch ($check.Status) {
        "PASS" { "Green" }
        "WARN" { "Yellow" }
        "FAIL" { "Red" }
    }
    Write-Host "[$($check.Status)] $($check.Name): $($check.Details)" -ForegroundColor $color
}

# שלח התראה אם יש כישלונות
if ($failed.Count -gt 0) {
    $body = "ProjectorControl health check failed on $env:COMPUTERNAME`n`n"
    $body += "Failed checks:`n"
    foreach ($check in $failed) {
        $body += "  - $($check.Name): $($check.Details)`n"
    }

    Send-MailMessage -SmtpServer $smtpServer `
        -From $emailFrom `
        -To $emailTo `
        -Subject $alertSubject `
        -Body $body

    Write-Host "`n[ALERT] Email sent to $emailTo" -ForegroundColor Red
}

exit $failed.Count  # Exit code = number of failures
```

**התזמן עם Task Scheduler:**
```powershell
# רץ כל יום ב-8:00 AM
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-File C:\Scripts\HealthCheck-ProjectorControl.ps1"
$trigger = New-ScheduledTaskTrigger -Daily -At 8AM
Register-ScheduledTask -TaskName "ProjectorControl Health Check" -Action $action -Trigger $trigger
```

---

### ניטור SQL Server (Enterprise mode)

**שאילתות ניטור:**

```sql
-- בדוק גודל מסד נתונים
USE ProjectorControl;
GO

SELECT
    DB_NAME() AS DatabaseName,
    SUM(size * 8.0 / 1024) AS SizeMB
FROM sys.database_files;
GO

-- ספירת פעולות לפי יום (7 ימים אחרונים)
SELECT
    CAST(timestamp AS DATE) AS Date,
    COUNT(*) AS Operations,
    SUM(CASE WHEN status = 'Success' THEN 1 ELSE 0 END) AS Successful,
    SUM(CASE WHEN status = 'Failed' THEN 1 ELSE 0 END) AS Failed
FROM operation_history
WHERE timestamp >= DATEADD(day, -7, GETDATE())
GROUP BY CAST(timestamp AS DATE)
ORDER BY Date DESC;
GO

-- מקרנים עם כישלונות תכופים (>10% failure rate ב-7 ימים)
SELECT
    pc.projector_name,
    COUNT(*) AS TotalOperations,
    SUM(CASE WHEN oh.status = 'Success' THEN 1 ELSE 0 END) AS Successful,
    SUM(CASE WHEN oh.status = 'Failed' THEN 1 ELSE 0 END) AS Failed,
    CAST(SUM(CASE WHEN oh.status = 'Failed' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS DECIMAL(5,2)) AS FailureRate
FROM operation_history oh
INNER JOIN projector_config pc ON oh.projector_id = pc.id
WHERE oh.timestamp >= DATEADD(day, -7, GETDATE())
GROUP BY pc.projector_name
HAVING SUM(CASE WHEN oh.status = 'Failed' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) > 10
ORDER BY FailureRate DESC;
GO

-- חיבורים פעילים (real-time)
SELECT
    session_id,
    login_name,
    host_name,
    program_name,
    status,
    last_request_start_time
FROM sys.dm_exec_sessions
WHERE database_id = DB_ID('ProjectorControl')
ORDER BY last_request_start_time DESC;
GO
```

---

### משימות תחזוקה

**שבועי:**
- [ ] בדוק לוגי יישום לשגיאות (`%APPDATA%\ProjectorControl\logs\`)
- [ ] אמת שגיבויים פועלים (בדוק חותמות זמן)
- [ ] סקור כישלונות ב-operation history panel
- [ ] בדוק חיבורים למקרנים (Test Connection)

**חודשי:**
- [ ] עדכן קושחת מקרנים (אם זמינה)
- [ ] סובב סיסמאות מקרן (שיטה מומלצת אבטחתית)
- [ ] דחוס מסד נתונים SQLite (Standalone mode)
  ```sql
  VACUUM;  -- In SQLite CLI
  ```
- [ ] בדוק דוחות SQL Server Audit (Enterprise mode)
- [ ] אמת שגיבויים ניתנים לשחזור (בדוק באמצעות שחזור לסביבת בדיקה)

**רבעוני:**
- [ ] סקור מדיניות גישה (הרשאות קבצים, SQL permissions)
- [ ] בדוק עדכוני אבטחה של Windows
- [ ] בדוק עדכוני SQL Server (patches)
- [ ] אימן משתמשים על תכונות חדשות
- [ ] סקור תיעוד (האם עדכני?)

**שנתי:**
- [ ] תכנן שדרוג עבור גרסה גדולה חדשה
- [ ] בצע ביקורת אבטחה מלאה
- [ ] סקור אסטרטגיית גיבוי/שחזור
- [ ] עדכן תיעוד פריסה

---

## 12. פתרון בעיות

### אבחון בעיות פריסה

**בעיה 1: "Cannot connect to SQL Server" בעת setup**

**אבחון:**
```powershell
# בדוק חיבור רשת ל-SQL Server
Test-NetConnection -ComputerName sqlserver.domain.local -Port 1433

# נסה חיבור SQL עם sqlcmd
sqlcmd -S sqlserver.domain.local -U projector_app_user -P "P@ssw0rd" -Q "SELECT @@VERSION"

# בדוק חוקי firewall
Get-NetFirewallRule -DisplayName "SQL*" | Select-Object DisplayName, Enabled, Direction, Action
```

**פתרונות:**
- אם `Test-NetConnection` נכשל → בעיית רשת (firewall, routing)
- אם `sqlcmd` נכשל → אימות שגוי (בדוק שם משתמש/סיסמה)
- אם SQL Server לא מאזין על 1433 → הפעל TCP/IP ב-SQL Server Configuration Manager

---

**בעיה 2: "Application crashes on startup"**

**אבחון:**
```powershell
# בדוק Event Viewer
Get-EventLog -LogName Application -Source "Application Error" -Newest 10 |
    Where-Object { $_.Message -like "*ProjectorControl*" } |
    Format-List TimeGenerated, Message

# בדוק לוגי יישום
Get-Content "$env:APPDATA\ProjectorControl\logs\app.log" -Tail 50
```

**פתרונות:**
- אם שגיאה עם "DLL not found" → דורש Visual C++ Redistributable
  ```powershell
  # התקן VC++ Redist
  $vcRedist = "https://aka.ms/vs/17/release/vc_redist.x64.exe"
  Invoke-WebRequest -Uri $vcRedist -OutFile "$env:TEMP\vc_redist.x64.exe"
  Start-Process "$env:TEMP\vc_redist.x64.exe" -ArgumentList "/install /quiet /norestart" -Wait
  ```
- אם שגיאה עם "Database locked" → תהליך אחר משתמש במסד נתונים
  ```powershell
  # סגור כל instances של ProjectorControl
  Get-Process | Where-Object {$_.ProcessName -eq "ProjectorControl"} | Stop-Process -Force
  ```

---

**בעיה 3: "Authentication failed" למקרן**

**אבחון:**
```powershell
# בדוק אם PJLink authentication מופעל במקרן
# התחבר ידנית:
$socket = New-Object System.Net.Sockets.TcpClient("10.0.50.10", 4352)
$stream = $socket.GetStream()
$reader = New-Object System.IO.StreamReader($stream)

$banner = $reader.ReadLine()
Write-Host "Banner: $banner"
# אם "PJLINK 0" → אין authentication
# אם "PJLINK 1 <random>" → דורש authentication

$socket.Close()
```

**פתרונות:**
- אם המקרן דורש authentication:
  1. Settings > Connection > Edit (projector)
  2. הזן סיסמת PJLink הנכונה
  3. Test Connection
  4. Save
- אם סיסמה לא ידועה → בדוק תפריט OSD של המקרן או שאל IT

---

**בעיה 4: "Entropy file missing" אחרי שחזור**

**אבחון:**
```powershell
# בדוק אם entropy file קיים
Test-Path "$env:APPDATA\ProjectorControl\.projector_entropy"
```

**פתרונות:**
- **אם יש גיבוי:**
  ```powershell
  # שחזר מגיבוי
  Copy-Item "\\fileserver\backups\EntropyFiles\$env:COMPUTERNAME-entropy-*.bin" `
      -Destination "$env:APPDATA\ProjectorControl\.projector_entropy" -Force
  ```
- **אם אין גיבוי (אובדן נתונים!):**
  - סיסמאות מקרן מוצפנות **אינן ניתנות לפענוח**
  - חייב להזין מחדש כל סיסמאות המקרנים
  - Settings > Connection > Edit (כל מקרן) > הזן מחדש סיסמה > Save
  - קובץ entropy חדש נוצר אוטומטית
  - **צור גיבוי מיד!**

---

### בדיקת רשת

**כלי אבחון PowerShell מלא:**

```powershell
# סקריפט: Test-ProjectorNetwork.ps1
param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectorIP,

    [int]$ProjectorPort = 4352
)

Write-Host "`n=== Projector Network Diagnostics ===" -ForegroundColor Cyan
Write-Host "Target: $ProjectorIP:$ProjectorPort`n"

# בדיקה 1: Ping
Write-Host "[1/5] Testing ICMP ping..." -ForegroundColor Yellow
$ping = Test-Connection -ComputerName $ProjectorIP -Count 4 -Quiet
if ($ping) {
    $pingStats = Test-Connection -ComputerName $ProjectorIP -Count 4
    $avgRTT = ($pingStats | Measure-Object -Property ResponseTime -Average).Average
    Write-Host "  [PASS] Ping successful. Average RTT: $([math]::Round($avgRTT, 2)) ms" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] Ping failed. Check network connectivity." -ForegroundColor Red
    exit 1
}

# בדיקה 2: DNS Resolution
Write-Host "[2/5] Testing DNS resolution..." -ForegroundColor Yellow
try {
    $dns = [System.Net.Dns]::GetHostEntry($ProjectorIP)
    Write-Host "  [PASS] DNS resolved: $($dns.HostName)" -ForegroundColor Green
} catch {
    Write-Host "  [INFO] No DNS entry (using IP directly - OK)" -ForegroundColor Cyan
}

# בדיקה 3: TCP Port 4352
Write-Host "[3/5] Testing TCP port $ProjectorPort..." -ForegroundColor Yellow
$tcpTest = Test-NetConnection -ComputerName $ProjectorIP -Port $ProjectorPort -InformationLevel Detailed
if ($tcpTest.TcpTestSucceeded) {
    Write-Host "  [PASS] Port $ProjectorPort is open. RTT: $($tcpTest.PingReplyDetails.RoundtripTime) ms" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] Port $ProjectorPort is closed or filtered." -ForegroundColor Red
    Write-Host "  Check: Firewall rules, Projector network settings" -ForegroundColor Yellow
    exit 1
}

# בדיקה 4: PJLink Protocol
Write-Host "[4/5] Testing PJLink protocol..." -ForegroundColor Yellow
try {
    $socket = New-Object System.Net.Sockets.TcpClient($ProjectorIP, $ProjectorPort)
    $stream = $socket.GetStream()
    $stream.ReadTimeout = 5000
    $reader = New-Object System.IO.StreamReader($stream)
    $writer = New-Object System.IO.StreamWriter($stream)

    # קרא banner
    $banner = $reader.ReadLine()
    Write-Host "  [INFO] PJLink banner: $banner" -ForegroundColor Cyan

    if ($banner -match "PJLINK 0") {
        Write-Host "  [PASS] PJLink Class 1, No authentication required" -ForegroundColor Green
    } elseif ($banner -match "PJLINK 1") {
        Write-Host "  [PASS] PJLink Class 1, Authentication required" -ForegroundColor Green
    } else {
        Write-Host "  [WARN] Unexpected banner format" -ForegroundColor Yellow
    }

    # בדיקת פקודה פשוטה (status query)
    $writer.WriteLine("%1POWR ?`r")
    $writer.Flush()
    $response = $reader.ReadLine()
    Write-Host "  [INFO] Power status response: $response" -ForegroundColor Cyan

    if ($response -match "PJLINK ERRA") {
        Write-Host "  [INFO] Authentication required for commands" -ForegroundColor Cyan
    } elseif ($response -match "%1POWR=") {
        Write-Host "  [PASS] Command executed successfully" -ForegroundColor Green
    }

    $socket.Close()

} catch {
    Write-Host "  [FAIL] PJLink protocol error: $_" -ForegroundColor Red
}

# בדיקה 5: Firewall Rules
Write-Host "[5/5] Checking Windows Firewall..." -ForegroundColor Yellow
$firewallRule = Get-NetFirewallRule -DisplayName "*Projector*" -ErrorAction SilentlyContinue
if ($firewallRule) {
    Write-Host "  [PASS] Firewall rule found: $($firewallRule.DisplayName)" -ForegroundColor Green
} else {
    Write-Host "  [WARN] No specific firewall rule found. Outbound may be blocked." -ForegroundColor Yellow
    Write-Host "  Recommend: Create firewall rule for TCP $ProjectorPort outbound" -ForegroundColor Yellow
}

Write-Host "`n=== Diagnostics Complete ===" -ForegroundColor Cyan
```

**שימוש:**
```powershell
.\Test-ProjectorNetwork.ps1 -ProjectorIP 10.0.50.10
```

---

## 13. נספח: סקריפטים ותבניות

### סקריפט פריסה מלא

ראה [סעיף 6.2](#פריסה-אוטומטית-workstations-מרובות) לסקריפט `Deploy-ProjectorControl.ps1`

---

### סקריפט הגדרת SQL Server

ראה [סעיף 5](#5-הכנת-sql-server) לכל פקודות SQL

---

### סקריפט אוטומציית גיבוי

ראה [סעיף 10.2](#גיבוי-standalone-mode) לסקריפט `Backup-ProjectorControl.ps1`

---

### סקריפט בדיקת בריאות

ראה [סעיף 11.1](#בדיקות-בריאות) לסקריפט `HealthCheck-ProjectorControl.ps1`

---

### תבנית תיעוד רשת

**קובץ: `Network-Documentation.xlsx`**

| שם מקרן | מיקום | מותג | דגם | IP Address | Port | MAC Address | VLAN | סיסמת PJLink | הערות |
|---------|--------|------|-----|------------|------|-------------|------|--------------|-------|
| conf-a-proj | Conference Room A | EPSON | EB-2250U | 10.0.50.10 | 4352 | 00:11:22:33:44:55 | 50 | (encrypted) | Main projector |
| train-b-proj | Training Room B | Hitachi | CP-EX302N | 10.0.50.11 | 4352 | AA:BB:CC:DD:EE:FF | 50 | None | No password |
| audit-main | Auditorium | EPSON | EB-2265U | 10.0.50.12 | 4352 | 11:22:33:44:55:66 | 50 | (encrypted) | 4K capable |

---

### תבנית רשימת בדיקה של פריסה

**קובץ: `Deployment-Checklist.docx`**

```
ProjectorControl Deployment Checklist
Computer Name: _________________
Date: _________________
Technician: _________________

□ Pre-Deployment
  □ Network connectivity verified
  □ Projector IPs documented
  □ SQL Server prepared (Enterprise mode only)
  □ Backup destination configured

□ Installation
  □ ProjectorControl.exe copied to: C:\Program Files\ProjectorControl\
  □ Startup shortcut created (if required)
  □ First-run wizard completed
    □ Language: English / Hebrew
    □ Admin password set (documented in password manager)
    □ Database mode: Standalone / Enterprise
    □ Projector(s) configured
  □ Application launches without errors

□ Validation
  □ Database file created (%APPDATA%\ProjectorControl\projector_control.db)
  □ Entropy file created (%APPDATA%\ProjectorControl\.projector_entropy)
  □ Power On command successful
  □ Power Off command successful
  □ History panel shows operations

□ Configuration
  □ File permissions hardened
  □ Backup scheduled (Task Scheduler)
  □ Health check scheduled (if applicable)

□ Documentation
  □ Workstation added to inventory
  □ Projector IPs documented
  □ Backup location recorded
  □ User trained on basic operation

Signature: _________________
Date: _________________
```

---

**סיום מדריך פריסה**

לתיעוד נוסף:
- **[FAQ](../FAQ.he.md)** - שאלות נפוצות
- **[מדריך משתמש](../user-guide/USER_GUIDE.he.md)** - שימוש יומיומי
- **[README](../../README.md)** - מפרט טכני
- **[תיעוד אבטחה](../../SECURITY.md)** - ארכיטקטורת אבטחה

*מדריך פריסה גרסה 1.0*
*עודכן לאחרונה: 12 בפברואר 2026*
*תואם ל-Enhanced Projector Control Application v2.0.0-rc2 ואילך*
