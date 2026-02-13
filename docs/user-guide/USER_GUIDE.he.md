# מדריך משתמש - Enhanced Projector Control Application

**גרסה:** 1.0
**עודכן לאחרונה:** 12 בפברואר 2026
**גרסת יישום:** 2.0.0-rc2

---

## תוכן עניינים

1. [מבוא](#1-מבוא)
2. [הגדרה ראשונית](#2-הגדרה-ראשונית)
3. [הבנת הממשק](#3-הבנת-הממשק)
4. [שימוש יומיומי](#4-שימוש-יומיומי)
5. [תכונות מתקדמות](#5-תכונות-מתקדמות)
6. [הגדרות](#6-הגדרות)
7. [טיפים ושיטות עבודה מומלצות](#7-טיפים-ושיטות-עבודה-מומלצות)
8. [קיצורי מקלדת](#8-קיצורי-מקלדת)
9. [פתרון בעיות](#9-פתרון-בעיות)

---

## 1. מבוא

### מהו יישום Enhanced Projector Control?

Enhanced Projector Control Application הוא כלי מקצועי שתוכנן להפוך את השליטה במקרנים ברשת למהירה וקלה. במקום להשתמש בשלט רחוק פיזי או ללכת אל המקרן, תוכל לשלוט בו ישירות מהמחשב שלך דרך הרשת.

**מה אפשר לעשות:**
- הפעלה וכיבוי של מקרנים
- החלפה בין מקורות קלט (HDMI, VGA, וכו')
- השחרת המסך במהלך מצגות
- הקפאת התצוגה
- צפייה בהיסטוריה של כל הפעולות

**למי מיועד מדריך זה:**
- מורים ומציגים שמשתמשים במקרנים מדי יום
- עובדי משרד המשתמשים במקרנים לפגישות
- כל מי שרוצה ללמוד כיצד להשתמש ביישום

### קבלת עזרה

אם אתה זקוק לסיוע:
- **מדריך משתמש זה** - הוראות צעד אחר צעד למשימות נפוצות
- **[שאלות נפוצות](../FAQ.he.md)** - תשובות מהירות לשאלות נפוצות
- **[README](../../README.md)** - מפרט טכני ודרישות מערכת
- **מנהל ה-IT שלך** - לבעיות רשת, התקנה או תצורה מתקדמת

---

## 2. הגדרה ראשונית

כאשר אתה מפעיל את היישום בפעם הראשונה, תעבור אשף הגדרה מהיר שלוקח כ-5 דקות להשלים.

### שלב 1: בחירת שפה

העמוד הראשון מאפשר לך לבחור את השפה המועדפת עליך.

[Screenshot: First-run wizard - Step 1 Language Selection. Shows the title "Welcome to Projector Control" at the top. Two large radio buttons are displayed vertically: "English" (with flag icon) and "עברית - Hebrew" (with flag icon). The English option is selected by default with a blue radio button. At the bottom right corner, there is a blue "Next" button. The wizard shows "Step 1 of 6" at the bottom left.]

**מה לעשות:**
1. בחר את השפה המועדפת עליך:
   - **English** - השתמש ביישום באנגלית
   - **עברית (Hebrew)** - השתמש ביישום בעברית עם פריסה מימין לשמאל
2. לחץ על **Next** להמשך

> **טיפ:** תוכל לשנות את השפה מאוחר יותר בהגדרות במידת הצורך.

---

### שלב 2: הגדרת סיסמת מנהל

שלב זה יוצר סיסמת אב להגנה על הגדרות היישום שלך.

[Screenshot: First-run wizard - Step 2 Admin Password Setup. Title "Create Admin Password" at top. Description text: "Create a password to protect application settings and projector credentials." Two password input fields stacked vertically: "Password" and "Confirm Password", both with eye icons to show/hide password. Below the fields, a password strength indicator bar shows segments in gray/yellow/green with text "Password Strength: Medium". Requirements checklist below: ✓ At least 8 characters, ✓ Contains uppercase letter, ✗ Contains number, ✗ Contains special character. Next button at bottom right, Back button at bottom left. Shows "Step 2 of 6".]

**מה לעשות:**
1. הזן סיסמה בשדה **Password**
2. הזן שוב את אותה סיסמה בשדה **Confirm Password**
3. ודא שהסיסמה עומדת בדרישות אלה:
   - לפחות 8 תווים באורך
   - מכילה לפחות אות גדולה אחת (A-Z)
   - מכילה לפחות מספר אחד (0-9)
   - מכילה לפחות תו מיוחד אחד (!@#$%^&*)
4. עקוב אחר מחוון חוזק הסיסמה:
   - **Weak** (אדום) - הוסף תווים נוספים או מורכבות
   - **Medium** (צהוב) - מקובל, אך שקול חיזוק
   - **Strong** (ירוק) - סיסמה מצוינת!
5. לחץ על **Next** להמשך

> **אזהרה:** רשום סיסמה זו ושמור אותה במקום בטוח! אם תשכח אותה, אין אפשרות שחזור. תצטרך להתקין מחדש את היישום ולהגדיר הכל מחדש.

---

### שלב 3: בחירת מצב מסד נתונים

בחר כיצד ההגדרות ותצורות המקרן שלך יאוחסנו.

[Screenshot: First-run wizard - Step 3 Database Mode Selection. Title "Choose Database Mode" at top. Two large option cards displayed vertically with icons. First card (selected with blue border): "Standalone (SQLite)" with database icon. Description: "Store settings on this computer only. Best for single-user installations." Below shows "Data location: %APPDATA%\ProjectorControl". Second card: "Enterprise (SQL Server)" with server icon. Description: "Connect to central SQL Server database. Best for organizations with multiple computers." Shows "Requires: SQL Server connection details". Next button at bottom right, Back button at bottom left. Shows "Step 3 of 6".]

**מה לעשות:**

בחר באחת מהאפשרויות הבאות:

**אפשרות 1: Standalone (SQLite)** - מומלץ לרוב המשתמשים
- ההגדרות שלך נשארות במחשב שלך בלבד
- אין צורך במסד נתונים ברשת
- מושלם למשתמשים בודדים
- נתונים מאוחסנים ב: `%APPDATA%\ProjectorControl\`

**אפשרות 2: Enterprise (SQL Server)** - עבור ארגונים
- הגדרות מאוחסנות בשרת מרכזי
- מספר מחשבים יכולים לשתף את אותה תצורה
- דורש התקנת SQL Server על ידי מנהל ה-IT שלך
- תצטרך פרטי חיבור מה-IT

> **טיפ:** אם אינך בטוח איזו לבחור, בחר **Standalone (SQLite)**. תמיד תוכל לעבור למצב Enterprise מאוחר יותר במידת הצורך.

עבור רוב המשתמשים:
1. בחר **Standalone (SQLite)**
2. לחץ על **Next** להמשך

---

### שלב 4: תצורת מקרן

הוסף את המקרן הראשון שלך ליישום.

[Screenshot: First-run wizard - Step 4 Projector Configuration. Title "Configure Your Projector" at top. Form with labeled fields in vertical layout: 1) "Projector Name" text field showing "Conference Room A", 2) "IP Address" text field showing "192.168.1.100", 3) "Port" text field showing "4352" (with info icon and tooltip "PJLink default port"), 4) "Brand" dropdown menu showing "EPSON" selected (dropdown shows EPSON, Hitachi, Sony, BenQ, NEC, Panasonic, Christie, Other - PJLink Generic), 5) Optional "Password" field (empty) with info text "Leave blank if projector has no password". At the bottom, "Test Connection" button (gray) and "Skip for now" link. Next button at bottom right (disabled/gray), Back button at bottom left. Shows "Step 4 of 6".]

**מה לעשות:**

מלא את המידע הבא אודות המקרן שלך:

1. **Projector Name** - שם ידידותי שתזהה
   - דוגמה: "Conference Room A" או "Main Classroom"

2. **IP Address** - כתובת הרשת של המקרן שלך
   - דוגמה: `192.168.1.100`
   - שאל את מנהל ה-IT שלך אם אינך יודע זאת

3. **Port** - בדרך כלל `4352` למקרני PJLink
   - ברירת המחדל נכונה לרוב המקרנים
   - שנה רק אם מנהל ה-IT שלך מנחה אותך לעשות זאת

4. **Brand** - בחר את יצרן המקרן שלך
   - בחר מתוך: EPSON, Hitachi, Sony, BenQ, NEC, Panasonic, Christie
   - אם המותג שלך לא ברשימה, בחר "Other - PJLink Generic"

5. **Password** (אופציונלי)
   - הזן רק אם המקרן שלך דורש אימות
   - השאר ריק למקרנים ללא סיסמאות
   - פנה ל-IT אם אינך בטוח

6. לחץ על **Test Connection** לאימות
   - המתן מספר שניות בעוד היישום מתחבר
   - אמור להופיע הודעת "Connection successful!"
   - אם נכשל, בדוק שוב את כתובת ה-IP והפורט

7. לחץ על **Next** להמשך

> **טיפ:** תוכל להוסיף מקרנים נוספים מאוחר יותר מתפריט ההגדרות.

> **הערה:** אם ברצונך להגדיר מקרנים מאוחר יותר, לחץ על "Skip for now" להמשך ללא הוספת מקרן כעת.

---

### שלב 5: התאמת ממשק משתמש (אופציונלי)

התאם אילו כפתורי בקרה מופיעים בחלון הראשי.

[Screenshot: First-run wizard - Step 5 UI Customization. Title "Customize Control Buttons" at top. Description text: "Select which controls you want visible in the main window. You can change this later in Settings." Grid layout of checkboxes with button previews, arranged in 3 columns: Row 1: ☑ Power On/Off (button preview shown), ☑ Input Source (dropdown preview), ☑ Blank Screen (button preview). Row 2: ☑ Freeze Display (button preview), ☐ Volume Control (slider preview grayed out), ☐ Mute Audio (button preview grayed out). Row 3: ☐ Picture Mode (dropdown preview grayed out), ☐ Aspect Ratio (dropdown preview grayed out). Below grid: "Recommended defaults are pre-selected" in italic gray text. Next button at bottom right, Back button at bottom left. Shows "Step 5 of 6".]

**מה לעשות:**

1. עיין בברירות המחדל המומלצות:
   - ✓ Power On/Off (הפעלה/כיבוי)
   - ✓ Input Source (מקור קלט)
   - ✓ Blank Screen (השחרת מסך)
   - ✓ Freeze Display (הקפאת תצוגה)

2. באופן אופציונלי הוסף בקרים נוספים:
   - **Volume Control** - התאמת עוצמת קול המקרן
   - **Mute Audio** - השתקה/ביטול השתקת קול במהירות
   - **Picture Mode** - החלפה בין מצבי מצגת
   - **Aspect Ratio** - שינוי יחס גובה-רוחב המסך

3. לחץ על **Next** להמשך

> **טיפ:** שמור על פשטות! ברירות המחדל המומלצות מכסות את רוב הצרכים היומיומיים. תמיד תוכל להוסיף כפתורים נוספים מאוחר יותר בהגדרות > UI Buttons.

---

### שלב 6: השלמת ההגדרה

הכל מוכן! האשף הושלם.

[Screenshot: First-run wizard - Step 6 Completion. Title "Setup Complete!" at top with green checkmark icon. Summary panel showing configured settings: "Language: English", "Database Mode: Standalone (SQLite)", "Projectors Configured: 1" (with "Conference Room A - 192.168.1.100" shown below). Green success message box: "✓ Your projector control application is ready to use!" Below: "What's next?" bulleted list: • Control your projector from the main window, • View operation history in the History panel, • Customize settings anytime from the Settings menu. Large green "Finish" button at bottom right, "Back" button at bottom left (grayed out). Shows "Step 6 of 6".]

**מה אתה רואה:**
- סיכום התצורה שלך
- אישור שההגדרה הושלמה
- מה לעשות הלאה

**מה לעשות:**
1. עיין בסיכום התצורה
2. לחץ על **Finish** לפתיחת החלון הראשי

> **מזל טוב!** אתה מוכן להתחיל לשלוט במקרן שלך!

---

## 3. הבנת הממשק

לאחר השלמת ההגדרה, תראה את חלון היישום הראשי. בוא ניקח סיור בכל חלק.

### סקירת החלון הראשי

[Screenshot: Main window - Full annotated view. Use numbered blue callouts pointing to each area: 1=Top toolbar (left side: Settings gear icon, Language toggle "EN|HE", Help "?" icon; right side: Minimize, Maximize, Close buttons), 2=Status Panel (left section showing: "Conference Room A" as title, green circle "Connected", "Power: On", "Input: HDMI1", "Last Update: 2 seconds ago"), 3=Control Buttons Section (center area with 4 buttons in 2x2 grid: "Power On" (green), "Power Off" (red), "Input Source" (blue dropdown showing "HDMI1 ▼"), "Blank Screen" (yellow)), 4=History Panel (right section showing scrollable list with 5 entries, each showing timestamp, icon, and operation: "14:32:15 - Power On - Success ✓", "14:28:03 - Input Changed to HDMI1 - Success ✓", etc.), 5=Status Bar (bottom showing: left side "Connection: Stable ●", center "Operations: 127 today", right "App Version: 2.0.0-rc2"). Window title shows "Enhanced Projector Control".]

לחלון הראשי יש 5 אזורים מרכזיים:

1. **סרגל כלים עליון** - גישה להגדרות ועזרה
2. **לוח סטטוס** - צפייה במצב המקרן הנוכחי
3. **כפתורי בקרה** - שליטה במקרן שלך
4. **פאנל היסטוריה** - צפייה בפעולות אחרונות
5. **שורת מצב** - מידע על חיבור והיישום

בוא נחקור כל אזור בפירוט.

---

### 1. סרגל כלים עליון

[Screenshot: Top toolbar close-up. Shows horizontal toolbar with light gray background. Left section: Settings gear icon (with tooltip "Settings (Ctrl+,)" showing on hover), Language toggle button showing "EN|HE" (with tooltip "Switch Language"), Help "?" icon (with tooltip "Help (F1)"). Right section standard Windows controls: Minimize "_", Maximize "□", Close "×". All icons are approximately 24x24 pixels with 8px spacing.]

**סמל גלגל השיניים להגדרות** ⚙️
- לחץ לפתיחת תיבת הדו-שיח הגדרות
- קיצור מקלדת: `Ctrl+,`

**החלפת שפה** 🌐
- החלפה בין אנגלית לעברית
- השפה הנוכחית מסומנת

**סמל עזרה** ❓
- גישה לתיעוד עזרה
- קיצור מקלדת: `F1`

**בקרי חלון**
- כפתורי מזעור, הגדלה/שחזור, סגירה
- התנהגות Windows סטנדרטית

---

### 2. לוח סטטוס

[Screenshot: Status Panel detailed view. Panel has white background with light border. Top: Large bold text "Conference Room A" (projector name). Below in stacked rows: Row 1: Green filled circle (●) followed by "Connected" in green text. Row 2: Icon of power symbol followed by "Power: On" in bold. Row 3: Icon of input cable followed by "Input: HDMI1" in bold. Row 4: Icon of clock followed by "Last Update: 2 seconds ago" in gray italics. Panel has subtle drop shadow.]

לוח הסטטוס מציג מידע בזמן אמת אודות המקרן שלך:

**שם המקרן**
- השם הידידותי שהקצית במהלך ההגדרה
- דוגמה: "Conference Room A"

**מצב חיבור**
- 🟢 **Connected** - התקשורת פועלת
- 🔴 **Disconnected** - לא ניתן להגיע למקרן
- 🟡 **Connecting** - מנסה להתחבר

**מצב חשמל**
- **On** - המקרן מופעל
- **Off** - המקרן כבוי
- **Warming Up** - המקרן מתחמם
- **Cooling Down** - המקרן מתקרר

**מקור קלט נוכחי**
- מציג איזה קלט פעיל (HDMI1, HDMI2, VGA, וכו')

**עדכון אחרון**
- זמן מאז רענון סטטוס אחרון
- מתעדכן אוטומטית כל 5 שניות

> **טיפ:** אם "Last Update" מציג זמן ארוך יותר מ-10 שניות, ייתכן שיש בעיית חיבור.

---

### 3. כפתורי בקרה

[Screenshot: Control Buttons section detailed view. Shows 2x2 grid of large buttons with 8px spacing. Each button is approximately 120x60 pixels. Top row: "Power On" button (green background, white text, power icon), "Power Off" button (red background, white text, power icon). Bottom row: "Input Source" button (blue background, white text, dropdown arrow, shows "HDMI1 ▼"), "Blank Screen" button (yellow background, black text, screen icon). All buttons have slight rounded corners and subtle shadows. Buttons are clearly labeled and visually distinct.]

כפתורי הבקרה מאפשרים לך לבצע פעולות נפוצות:

**Power On** (ירוק)
- מפעיל את המקרן
- עשוי לקחת 30-60 שניות למקרן להתחמם

**Power Off** (אדום)
- כיבוי המקרן
- המקרן יתקרר (בדרך כלל 60-90 שניות)

**Input Source** (תפריט נפתח כחול)
- לחץ לצפייה בקלטים זמינים
- בחר להחלפת מקורות קלט
- האפשרויות הזמינות תלויות בדגם המקרן שלך

**Blank Screen** (צהוב)
- משחיר זמנית את התמונה המוקרנת
- לחץ שוב לשחזור התמונה
- שימושי להסתרת תוכן לרגע

> **הערה:** הכפתורים המוצגים תלויים בהגדרות התאמת ממשק המשתמש שלך. ראה [סעיף 6](#6-הגדרות) להוספה או הסרה של כפתורים.

---

### 4. פאנל היסטוריה

[Screenshot: History Panel detailed view. Panel titled "Operation History" at top in bold. Scrollable list showing 8 entries. Each entry has: timestamp on left (gray, format "HH:MM:SS"), operation icon in middle (power/input/blank icons), operation description and status on right. Example entries: "14:35:42 🔌 Power On → Success ✓ (green checkmark)", "14:32:18 📺 Input Changed to HDMI2 → Success ✓", "14:28:55 ⚪ Screen Blanked → Success ✓", "14:15:03 🔌 Power Off → Success ✓", "13:58:12 📺 Input Changed to VGA → Failed ✗ (red X with error message 'Input not available')", etc. Vertical scrollbar on right side. Bottom of panel shows "Showing 8 of 127 operations today" in small gray text.]

פאנל ההיסטוריה מציג לוג של כל הפעולות:

**כל ערך מציג:**
- **זמן** - מתי הפעולה בוצעה (HH:MM:SS)
- **סמל** - סימן חזותי לסוג הפעולה
- **פעולה** - איזו פעולה בוצעה
- **מצב** - הצלחה ✓ או כישלון ✗

**סוגי ערכים:**
- 🔌 פעולות חשמל (הפעלה/כיבוי)
- 📺 שינויי מקור קלט
- ⚪ השחרת/ביטול השחרת מסך
- 🧊 הקפאה/ביטול הקפאת תצוגה
- 🔊 שינויי עוצמה/השתקה

**שימוש בפאנל ההיסטוריה:**
- גלול לצפייה בערכים ישנים יותר
- פעולות שנכשלו מוצגות באדום עם פרטי שגיאה
- העבר את העכבר מעל ערך לצפייה בפרטים נוספים
- לחץ לחיצה ימנית לאפשרויות (העתקת פרטים, ניקוי היסטוריה)

> **טיפ:** אם אתה רואה כישלונות תכופים לפעולה ספציפית, ייתכן שיש בעיית תאימות עם דגם המקרן שלך. בדוק ב[שאלות נפוצות](../FAQ.he.md) או פנה למנהל ה-IT שלך.

---

### 5. שורת מצב

[Screenshot: Status Bar detailed view. Horizontal bar at bottom of window with light gray background. Three sections separated by subtle dividers: Left section shows green dot (●) followed by "Connection: Stable" in small text. Center section shows "Operations: 127 today" with small graph icon. Right section shows "App Version: 2.0.0-rc2" in gray text. Each section is approximately equal width.]

שורת המצב מספקת מידע עזר מהיר:

**מצב חיבור** (שמאל)
- 🟢 **Stable** - החיבור תקין
- 🟡 **Unstable** - קישוריות לסירוגין
- 🔴 **Failed** - החיבור אבד

**ספירת פעולות** (מרכז)
- מספר כולל של פעולות שבוצעו היום
- מתאפס בחצות

**גרסת יישום** (ימין)
- מספר גרסה נוכחי
- שימושי בעת דיווח על בעיות

---

### סמל במגש המערכת

[Screenshot: System tray area (bottom-right corner of Windows taskbar). Shows Windows system tray with multiple icons (sound, network, etc.). Highlight the projector control application icon (small projector icon) among them. Show a tooltip appearing on hover: "Projector Control - Conference Room A: On (HDMI1)". Arrow pointing to the icon with annotation "Double-click to open main window, Right-click for quick actions".]

כאשר אתה ממזער את היישום, הוא ממשיך לפעול במגש המערכת.

**גישה למגש המערכת:**
- חפש את סמל המקרן 📽️ באזור ההודעות של סרגל המשימות של Windows (פינה ימנית תחתונה)
- אם אינך רואה אותו, לחץ על החץ "הצג סמלים מוסתרים" ˄

**פעולות מגש מערכת:**
- **לחיצה כפולה** - פותח את החלון הראשי
- **לחיצה ימנית** - פותח תפריט פעולות מהירות (ראה להלן)

[Screenshot: System tray right-click context menu. Small popup menu with white background showing: "Conference Room A" (projector name in bold at top, gray background), horizontal separator line, "Power On" (with green circle icon), "Power Off" (with red circle icon), "Blank Screen" (with screen icon), horizontal separator line, "Show Main Window" (with window icon), "Settings" (with gear icon), horizontal separator line, "Exit" (with X icon). Menu has subtle drop shadow.]

**תפריט פעולות מהירות:**
- **שם המקרן** - כותרת המציגה את המקרן הפעיל
- **Power On** - הפעלה מהירה של המקרן
- **Power Off** - כיבוי מהיר של המקרן
- **Blank Screen** - החלפת מצב השחרת מסך
- **Show Main Window** - שחזור החלון הראשי
- **Settings** - פתיחת תיבת דו-שיח הגדרות
- **Exit** - סגירת היישום לחלוטין

> **טיפ:** השתמש במגש המערכת לשליטת חשמל מהירה ללא פתיחת החלון הראשי!

---

## 4. שימוש יומיומי

כעת כשאתה מבין את הממשק, בוא נעבור על משימות יומיומיות נפוצות.

### הפעלת המקרן

[Screenshot: Main window with cursor hovering over green "Power On" button. Button has subtle glow effect to indicate hover state. Status Panel shows "Power: Off" and "Connection: Connected".]

**שלבים:**
1. ודא שלוח הסטטוס מציג **Connected**
2. לחץ על כפתור **Power On** הירוק
3. המתן למקרן להתחמם (30-60 שניות)
4. לוח הסטטוס יתעדכן להציג **Power: Warming Up**, ולאחר מכן **Power: On**

[Screenshot: Status Panel during warm-up. Shows "Power: Warming Up" with animated ellipsis "..." and small circular progress indicator. Text below says "Estimated time: 45 seconds".]

**מה קורה:**
- היישום שולח פקודת הפעלה
- נורת המקרן מתחילה להתחמם
- הסטטוס מתעדכן אוטומטית כשהמקרן מתחיל
- פאנל ההיסטוריה מציג "Power On → Success ✓"

> **טיפ:** אל תלחץ על הכפתור מספר פעמים! הפקודה התקבלה בפעם הראשונה. המתן לעדכון הסטטוס.

---

### כיבוי המקרן

[Screenshot: Main window with cursor hovering over red "Power Off" button. Button has subtle glow effect. Status Panel shows "Power: On".]

**שלבים:**
1. לחץ על כפתור **Power Off** האדום
2. אם תתבקש, אשר שברצונך לכבות את המקרן
3. המתן למקרן להתקרר (60-90 שניות)
4. לוח הסטטוס יתעדכן להציג **Power: Cooling Down**, ולאחר מכן **Power: Off**

[Screenshot: Confirmation dialog. Modal window with title "Confirm Power Off". Message: "Are you sure you want to turn off the projector?" Icon showing projector with power symbol. Two buttons: "Yes, Turn Off" (red, focused) and "Cancel" (gray). Checkbox at bottom: "☐ Don't ask me again".]

**מה קורה:**
- מופיע דיאלוג אישור (אופציונלי, ניתן להשבית)
- היישום שולח פקודת כיבוי
- מאוורר המקרן פועל לקירור הנורה
- הסטטוס מתעדכן אוטומטית כשהמקרן נכבה
- פאנל ההיסטוריה מציג "Power Off → Success ✓"

> **אזהרה:** לעולם אל תנתק מקרן מהחשמל מיד לאחר כיבויו! תמיד תן לו להתקרר לחלוטין כדי להגן על הנורה.

---

### החלפת מקורות קלט

[Screenshot: Main window with "Input Source" dropdown button expanded. Dropdown menu shows list of 5 options: "HDMI1" (with green checkmark indicating current selection), "HDMI2", "VGA", "Component", "Network". Each option has an appropriate icon. Dropdown has white background with subtle shadow.]

**שלבים:**
1. לחץ על כפתור התפריט הנפתח **Input Source**
2. בחר את הקלט הרצוי מהרשימה:
   - HDMI1, HDMI2 - כניסות HDMI דיגיטליות
   - VGA - כניסת VGA אנלוגית
   - Component - כניסת וידאו רכיבים
   - Network - תצוגת רשת
3. המתן מספר שניות למקרן להחליף
4. לוח הסטטוס יתעדכן להציג את הקלט החדש

**מה קורה:**
- היישום שולח פקודת שינוי קלט
- המקרן עובר לקלט שנבחר
- לוח הסטטוס מתעדכן להציג "Input: [שם מקור]"
- פאנל ההיסטוריה מציג "Input Changed to [מקור] → Success ✓"

> **טיפ:** הקלטים הזמינים תלויים בדגם המקרן הספציפי שלך. אם קלט חסר, ייתכן שהוא לא נתמך על ידי המקרן שלך.

---

### השחרת המסך

[Screenshot: Two side-by-side views. Left: Main window showing yellow "Blank Screen" button in normal state with text "Blank Screen". Right: Same button after being clicked, now showing "Unblank Screen" with slightly different icon and button is pressed/highlighted.]

**שלבים:**
1. לחץ על כפתור **Blank Screen**
2. התמונה המוקרנת משחירה מיידית
3. הכפתור משתנה ל-**Unblank Screen**
4. לחץ שוב לשחזור התמונה

**מתי להשתמש:**
- הסתרת תוכן רגיש זמנית במהלך מצגת
- השהייה בין חלקי מצגת
- שמירת מיקוד הקהל במהלך דיונים

**מה קורה:**
- המקרן מציג מיידית מסך שחור
- נורת המקרן נשארת דלוקה (לא זהה לכיבוי)
- אודיו ממשיך אם מופעל
- פאנל ההיסטוריה מציג "Screen Blanked → Success ✓"

> **טיפ:** השחרת מסך מהירה יותר מכיבוי והפעלת המקרן. השתמש בה להפסקות קצרות.

---

### צפייה בהיסטוריית פעולות

[Screenshot: History Panel with one entry highlighted (blue background selection). Entry shows "14:32:18 📺 Input Changed to HDMI2 → Success ✓". Context menu is open (right-click menu) showing options: "Copy Details", "View Full Message", "Clear This Entry", horizontal separator, "Clear All History", "Export History...". Menu has white background with subtle shadow.]

**שלבים:**
1. הסתכל על **פאנל ההיסטוריה** בצד ימין
2. גלול דרך הרשימה לצפייה בפעולות קודמות
3. העבר את העכבר מעל ערך לצפייה בפרטים נוספים
4. לחץ לחיצה ימנית על ערך לאפשרויות נוספות:
   - **Copy Details** - העתקת מידע פעולה ללוח
   - **View Full Message** - צפייה בפרטי שגיאה מלאים (לפעולות שנכשלו)
   - **Clear This Entry** - הסרה מההיסטוריה
   - **Clear All History** - ניקוי כל ההיסטוריה
   - **Export History** - שמירת היסטוריה לקובץ

**הבנת ערכי היסטוריה:**

✓ **הצלחה (סימן וי ירוק)**
- הפעולה הושלמה בהצלחה
- המקרן הגיב כצפוי

✗ **כישלון (X אדום)**
- הפעולה נכשלה
- לחץ לצפייה בפרטי שגיאה
- סיבות נפוצות: תפוגת רשת, פקודה לא נתמכת, מקרן במצב שגוי

**סינון היסטוריה:**
- השתמש בתיבת החיפוש (אם מופעלת בהגדרות) למציאת פעולות ספציפיות
- סנן לפי טווח תאריכים או סוג פעולה

> **טיפ:** אם אתה רואה דפוסים של כישלונות (למשל, "Input Changed" תמיד נכשל), זה מצביע על בעיית תאימות עם המקרן שלך. בדוק ב[שאלות נפוצות](../FAQ.he.md) לפתרון בעיות.

---

### שימוש במגש המערכת

[Screenshot: Windows desktop with main application window minimized. Focus on system tray area showing projector icon. Small notification bubble appears from system tray: "Projector Control minimized - Running in background. Double-click the icon to restore." Notification fades after 3 seconds.]

**מזעור למגש המערכת:**
1. לחץ על כפתור **Minimize** בחלון הראשי
2. החלון נעלם והסמל עובר למגש המערכת
3. הודעה מאשרת שהוא עדיין פועל

**בקרת חשמל מהירה ממגש המערכת:**
1. לחץ לחיצה ימנית על סמל מגש המערכת 📽️
2. בחר **Power On** או **Power Off** מהתפריט
3. הפעולה מבוצעת ברקע
4. מופיעה הודעה המאשרת הצלחה

[Screenshot: System tray notification balloon. Shows small popup with projector icon at top, message "Power On → Success ✓", subtitle "Conference Room A is now warming up", and timestamp "14:35:42". Notification has white background with subtle border and drop shadow. Auto-dismisses after 5 seconds.]

**צפייה בסטטוס ממגש המערכת:**
1. העבר את העכבר מעל סמל מגש המערכת
2. מופיעה רמז כלי המציג את הסטטוס הנוכחי:
   - שם מקרן
   - מצב חשמל
   - קלט נוכחי

> **טיפ:** שמור את היישום פועל במגש המערכת לגישה מיידית לאורך היום!

---

### שינוי המקרן הפעיל

אם יש לך מספר מקרנים מוגדרים, תוכל להחליף ביניהם.

[Screenshot: Main window toolbar with projector selector dropdown added to left side (next to Settings icon). Dropdown shows current selection "Conference Room A ▼". When clicked, dropdown menu shows 3 projectors: "Conference Room A" (current, checkmark), "Training Room B", "Auditorium Main". Each has icon and current status shown in gray text below name: "Connected, On (HDMI1)" or "Disconnected".]

**שלבים:**
1. לחץ על תפריט **Projector Selector** הנפתח בסרגל הכלים (אם מוגדרים מספר מקרנים)
2. בחר את המקרן שברצונך לשלוט בו
3. הממשק מתעדכן להציג את סטטוס המקרן שנבחר
4. כל כפתורי הבקרה עכשיו משפיעים על המקרן שנבחר

> **הערה:** אם יש לך רק מקרן אחד מוגדר, תפריט הבחירה הנפתח מוסתר אוטומטית.

---

## 5. תכונות מתקדמות

מעבר לבקרת חשמל וקלט בסיסית, היישום מציע תכונות מתקדמות למצגות ותרחישים מיוחדים.

### הקפאת התצוגה

[Screenshot: Main window showing "Freeze Display" button (light blue color) in the control buttons section. Icon shows a snowflake or pause symbol. Below the button, small text says "Freezes projected image while source continues".]

**מה זה עושה:**
- מקפיא את התמונה המוקרנת הנוכחית במקומה
- מסך המחשב שלך ממשיך להתעדכן באופן רגיל
- המקרן מציג "תמונת מצב" סטטית של מה שהיה על המסך

**מתי להשתמש:**
- השהייה של סרטון בזמן שאתה מסביר מושג
- שמירת שקופית גלויה בזמן שאתה מנווט לתוכן אחר
- הסתרת שולחן העבודה שלך בזמן פתיחת קבצים או יישומים

**שלבים:**
1. לחץ על כפתור **Freeze Display**
2. התמונה המוקרנת קופאת מיידית
3. הכפתור משתנה ל-**Unfreeze Display**
4. המשך לעבוד על המחשב שלך (הקהל לא יראה שינויים)
5. לחץ על **Unfreeze Display** לחידוש הקרנה רגילה

> **אזהרה:** בזמן שהתצוגה קפואה, הקהל לא יכול לראות מה אתה עושה במחשב שלך. זה כולל תנועות עכבר, חלונות חדשים או שינויי תוכן.

---

### בקרת עוצמת קול

[Screenshot: Main window showing "Volume" slider control (horizontal slider, range 0-100, current position at 50). Left end has speaker-with-X icon (mute), right end has speaker-with-waves icon (loud). Below slider shows "50%" in gray text. Small "Mute" checkbox to the right of slider.]

**אם מופעל בהגדרות:**

**התאמת עוצמת קול:**
1. אתר את סרגל ה-**Volume** באזור הבקרה
2. גרור את הסרגל שמאלה (שקט יותר) או ימינה (חזק יותר)
3. עוצמת קול המקרן מתכווננת בזמן אמת
4. אחוז עוצמת הקול הנוכחית מוצג מתחת לסרגל

**השתקת אודיו:**
1. לחץ על תיבת הסימון **Mute** (או סמל רמקול-X)
2. האודיו מושתק מיידית
3. בטל סימון לשחזור אודיו

> **הערה:** לא כל דגמי המקרנים תומכים בבקרת עוצמת קול דרך רשת. אם הסרגל מושבת (אפור), המקרן שלך אינו תומך בתכונה זו.

---

### מצבי תמונה

[Screenshot: Main window showing "Picture Mode" dropdown button. Dropdown expanded showing 5 options with icons: "Presentation" (current, checkmark), "Cinema", "sRGB", "Dynamic", "Custom". Each option has a small preview icon showing brightness/contrast representation.]

**אם מופעל בהגדרות:**

**החלפת מצבי תמונה:**
1. לחץ על תפריט **Picture Mode** הנפתח
2. בחר מהמצבים הזמינים:
   - **Presentation** - בהיר, ניגודיות גבוהה לחדרים מוארים
   - **Cinema** - מאוזן לסרטים
   - **sRGB** - צבעים מדויקים לתמונות
   - **Dynamic** - בהירות מקסימלית
   - **Custom** - הגדרות מוגדרות משתמש
3. המקרן מחליף מצבים מיידית

**מתי להשתמש:**
- **Presentation** - פגישות או שיעורים ביום
- **Cinema** - השמעת סרטים
- **sRGB** - עבודת תמונה או עיצוב
- **Dynamic** - חדרים בהירים מאוד

> **הערה:** המצבים הזמינים משתנים לפי דגם המקרן. לחלקם עשויות להיות אפשרויות פחותות.

---

### בחירת יחס גובה-רוחב

[Screenshot: Main window showing "Aspect Ratio" dropdown button. Dropdown shows 4 options: "16:9 Widescreen" (current), "4:3 Standard", "16:10 Computer", "Auto". Each has small visual representation of the ratio.]

**אם מופעל בהגדרות:**

**שינוי יחס גובה-רוחב:**
1. לחץ על תפריט **Aspect Ratio** הנפתח
2. בחר את היחס הרצוי:
   - **16:9** - מסך רחב מודרני (הנפוץ ביותר)
   - **4:3** - פורמט סטנדרטי קלאסי
   - **16:10** - מסכי מחשב
   - **Auto** - זיהוי מהמקור
3. התמונה המוקרנת מתכווננת למלא את היחס שנבחר

**בחירת היחס הנכון:**
- **16:9** - למחשבים ניידים מודרניים, סרטונים, מצגות
- **4:3** - לתוכן ישן או פורמט קלאסי
- **Auto** - תן למקרן להחליט (מומלץ)

---

### בדיקת חיבור

אתה יכול לבדוק ידנית את החיבור למקרן שלך בכל עת.

[Screenshot: Settings dialog open, "Connection" tab selected. Mid-section shows a card labeled "Connection Test" with text "Verify network connectivity to projector". Button labeled "Test Connection Now" (blue). Below button is a status message area (empty initially, showing "Click test to verify connection" in gray).]

**שלבים:**
1. פתח **Settings** (סמל גלגל שיניים או `Ctrl+,`)
2. עבור לטאב **Connection**
3. לחץ על **Test Connection Now**
4. המתן מספר שניות לתוצאות

[Screenshot: Same Connection Test card, but status area now shows results. Green box with checkmark icon and text: "✓ Connection successful! Ping: 12ms, Projector Model: EPSON EB-2250U, Firmware: 1.23". Below shows "Last tested: Just now".]

**בדיקה מוצלחת מציגה:**
- ✓ מצב חיבור
- זמן תגובה (ping)
- שם דגם מקרן
- גרסת קושחה
- חותמת זמן בדיקה אחרונה

**בדיקה שנכשלה מציגה:**
- ✗ שגיאת חיבור
- הודעת שגיאה (timeout, refused, וכו')
- הצעות אבחון
- קישור לפתרון בעיות

> **טיפ:** הפעל בדיקת חיבור אם אתה מבחין בזמני תגובה איטיים או כישלונות תכופים בפאנל ההיסטוריה.

---

## 6. הגדרות

דיאלוג ההגדרות מספק אפשרויות התאמה אישית נרחבות. גש אליו על ידי לחיצה על סמל גלגל השיניים ⚙️ או לחיצה על `Ctrl+,`.

[Screenshot: Settings dialog window. Window title "Settings". Left sidebar shows 6 tab icons vertically: General (house icon, selected with blue highlight), Connection (plug icon), UI Buttons (grid icon), Security (lock icon), Advanced (wrench icon), Diagnostics (magnifying glass icon). Main content area on right shows "General Settings" content. Bottom of window has "Save", "Apply", "Cancel" buttons. Window is approximately 800x600 pixels with white background.]

לדיאלוג ההגדרות יש 6 טאבים:

1. **General** - שפה, הפעלה, העדפות תצוגה
2. **Connection** - הגדרות רשת, תפוגות, התנהגות ניסיון חוזר
3. **UI Buttons** - התאמת כפתורי בקרה גלויים
4. **Security** - ניהול סיסמאות, אבטחת אישורים
5. **Advanced** - מצב מסד נתונים, רישום, כוונון ביצועים
6. **Diagnostics** - לוגים, בדיקות חיבור, כלי פתרון בעיות

בוא נחקור כל טאב.

---

### הגדרות כלליות

[Screenshot: Settings dialog, General tab selected. Content area shows several setting groups: 1) "Language Preferences" group with radio buttons "English" (selected) and "עברית Hebrew", 2) "Startup Behavior" group with checkboxes "☑ Launch on Windows startup" and "☑ Start minimized to system tray", 3) "User Interface" group with checkbox "☑ Show notification balloons" and "☑ Confirm before power off", 4) "Updates" group with checkbox "☐ Check for updates automatically" and button "Check Now". Each group has subtle border and padding.]

**העדפות שפה:**
- **English / עברית (Hebrew)** - בחר את השפה המועדפת עליך
- השינויים נכנסים לתוקף מיידית
- מחליף את כל הממשק כולל תפריטים, דיאלוגים והודעות

**התנהגות הפעלה:**
- ☑ **Launch on Windows startup** - הפעלה אוטומטית כאשר אתה מתחבר ל-Windows
- ☑ **Start minimized to system tray** - השקה מוסתרת ברקע
- מומלץ למשתמשים יומיומיים

**ממשק משתמש:**
- ☑ **Show notification balloons** - הצגת תוצאות פעולה כהודעות
- ☑ **Confirm before power off** - שאל לפני כיבוי מקרן
- בטל סימון לדילוג על דיאלוגי אישור

**עדכונים:**
- ☑ **Check for updates automatically** - בדיקה שבועית לגרסאות חדשות
- **Check Now** - בדיקה ידנית לעדכונים

> **טיפ:** הפעל "Launch on Windows startup" אם אתה משתמש במקרן מדי יום. היישום יהיה מוכן במגש המערכת כשתזדקק לו.

---

### הגדרות חיבור

[Screenshot: Settings dialog, Connection tab selected. Content area shows: 1) "Active Projector" section showing current projector card "Conference Room A - 192.168.1.100:4352 - EPSON" with "Edit" and "Test" buttons, 2) "Network Timeouts" section with three labeled sliders: "Connection Timeout: 5 seconds" (range 3-30s), "Command Timeout: 10 seconds" (range 5-60s), "Status Update Interval: 5 seconds" (range 3-30s), 3) "Reliability" section with checkbox "☑ Enable automatic reconnection" and text field "Retry attempts: 3" (range 1-10), 4) "Add New Projector" button at bottom (blue).]

**מקרן פעיל:**
- מציג פרטי מקרן שנבחר כעת
- **Edit** - שינוי תצורת מקרן
- **Test** - הפעלת בדיקת חיבור

**תפוגות רשת:**
- **Connection Timeout** (3-30 שניות) - כמה זמן להמתין בעת התחברות
  - הגדל לרשתות איטיות
  - ברירת מחדל: 5 שניות

- **Command Timeout** (5-60 שניות) - כמה זמן להמתין לתגובת פקודה
  - הגדל למקרנים שאינם מגיבים
  - ברירת מחדל: 10 שניות

- **Status Update Interval** (3-30 שניות) - באיזו תדירות לרענן סטטוס
  - נמוך יותר = עדכונים תכופים יותר, תעבורת רשת רבה יותר
  - ברירת מחדל: 5 שניות

**אמינות:**
- ☑ **Enable automatic reconnection** - נסה שוב אם החיבור נופל
- **Retry attempts** - כמה פעמים לנסות שוב פעולות שנכשלו
  - ברירת מחדל: 3 ניסיונות

**ניהול מקרנים:**
- **Add New Projector** - הגדרת מקרנים נוספים
- **Edit** - שינוי הגדרות מקרן קיים
- **Remove** - מחיקת תצורת מקרן

> **טיפ:** אם אתה חווה תפוגות תכופות, הגדל את ה-Connection Timeout ל-10-15 שניות.

---

### הגדרות כפתורי ממשק משתמש

[Screenshot: Settings dialog, UI Buttons tab selected. Content area shows grid of button toggles: "Available Control Buttons" heading, then 3 columns of checkboxes with button previews: Column 1: "☑ Power On/Off" (green/red buttons shown), "☑ Input Source" (blue dropdown shown), "☑ Blank Screen" (yellow button shown). Column 2: "☑ Freeze Display" (light blue button shown), "☐ Volume Control" (slider shown grayed), "☐ Mute Audio" (button shown grayed). Column 3: "☐ Picture Mode" (dropdown shown grayed), "☐ Aspect Ratio" (dropdown shown grayed), "☐ Info/Status" (button shown grayed). Below grid: "Preview" section showing miniature main window with only checked buttons visible. Note at bottom: "Unchecking a button hides it from the main window. You can still access all features from the system tray."]

**התאמת כפתורי בקרה:**

1. סמן תיבות עבור כפתורים שאתה רוצה גלויים
2. בטל סימון תיבות להסתרת כפתורים שאינך משתמש בהם
3. ראה תצוגה מקדימה של פריסת חלון ראשי למטה
4. לחץ על **Apply** לעדכון החלון הראשי

**מינימום מומלץ:**
- Power On/Off
- Input Source

**שילובים נפוצים:**

**משתמש בסיסי:**
- Power On/Off
- Input Source

**מציג:**
- Power On/Off
- Input Source
- Blank Screen
- Freeze Display

**משתמש מתקדם:**
- כל הכפתורים מופעלים

> **טיפ:** שמור על ממשק נקי על ידי הסתרת כפתורים שאתה משתמש בהם לעתים רחוקות. תמיד תוכל להפעיל אותם מאוחר יותר במידת הצורך.

---

### הגדרות אבטחה

[Screenshot: Settings dialog, Security tab selected. Content area shows: 1) "Admin Password" section with button "Change Admin Password..." and text "Last changed: 14 days ago", 2) "Projector Credentials" section with text "Stored projector passwords are encrypted using Windows DPAPI" and red warning box "⚠ Warning: Entropy file backup required for password recovery. See Security documentation.", 3) "Backup Encryption" section with dropdown "Encryption Strength: AES-256-GCM (Recommended)" and checkbox "☑ Require password for backup restore", 4) "Session Security" section with checkbox "☐ Automatically lock after 30 minutes of inactivity" and text field for minutes.]

**סיסמת מנהל:**
- **Change Admin Password** - עדכון סיסמת אב שלך
- מציג מתי הסיסמה שונתה לאחרונה
- נדרש לגישה לדיאלוג הגדרות זה

**אישורי מקרן:**
- כל סיסמאות המקרן מוצפנות באמצעות Windows DPAPI
- יש לגבות קובץ entropy (`.projector_entropy`)
- ללא קובץ entropy, לא ניתן לשחזר סיסמאות מוצפנות

**הצפנת גיבוי:**
- **Encryption Strength** - בחר רמת הצפנה לגיבויים
  - AES-256-GCM (מומלץ) - אבטחה חזקה ביותר
  - AES-128-GCM - מהיר יותר, עדיין מאובטח
- ☑ **Require password for backup restore** - הגנת סיסמה על קבצי גיבוי

**אבטחת הפעלה:**
- ☐ **Automatically lock after inactivity** - נעילת הגדרות לאחר זמן סרק
- מגן על הגדרות אם אתה מתרחק מהמחשב שלך

> **אזהרה:** קובץ ה-entropy הוא קריטי! אם תאבד אותו ותצטרך להתקין מחדש את Windows או לעבור למחשב חדש, תאבד את כל סיסמאות המקרן השמורות. ראה [גיבוי ושחזור אסון](../deployment/DEPLOYMENT_GUIDE.he.md#10-גיבוי-ושחזור-אסון) לנהלי גיבוי.

---

### הגדרות מתקדמות

[Screenshot: Settings dialog, Advanced tab selected. Content area shows: 1) "Database Mode" section (grayed out/read-only) showing "Current Mode: Standalone (SQLite)" with info icon and tooltip "Database mode cannot be changed after initial setup", 2) "Performance" section with checkbox "☑ Enable connection pooling" and "☑ Cache projector status (reduces network calls)", 3) "Logging" section with dropdown "Log Level: Info" (options: Debug, Info, Warning, Error) and button "Open Log Folder", 4) "Developer Options" section with checkbox "☐ Enable debug mode" and red warning text "Debug mode generates large log files. Only enable when troubleshooting."]

**מצב מסד נתונים:**
- מציג מצב מסד נתונים נוכחי (Standalone או Enterprise)
- לא ניתן לשנות לאחר ההגדרה הראשונית
- פנה למנהל IT להעברה בין מצבים

**ביצועים:**
- ☑ **Enable connection pooling** - שימוש חוזר בחיבורי רשת לביצועים טובים יותר
- ☑ **Cache projector status** - הפחתת תעבורת רשת על ידי שמירת סטטוס במטמון
- שניהם מומלצים לשימוש רגיל

**רישום:**
- **Log Level** - בקרת רמת פירוט בקבצי לוג
  - **Debug** - פירוט מקסימלי (קבצים גדולים)
  - **Info** - לוגים תפעוליים רגילים (מומלץ)
  - **Warning** - רק אזהרות ושגיאות
  - **Error** - רק שגיאות
- **Open Log Folder** - צפייה בקבצי לוג לפתרון בעיות

**אפשרויות מפתח:**
- ☐ **Enable debug mode** - מידע אבחון נוסף
- הפעל רק כאשר מתבקש על ידי תמיכה
- מייצר קבצי לוג גדולים מאוד

> **טיפ:** אם אתה חווה בעיות, הגדר Log Level ל-"Debug", שחזר את הבעיה, ולאחר מכן שלח את קבצי הלוג למנהל ה-IT שלך או לתמיכה.

---

### הגדרות אבחון

[Screenshot: Settings dialog, Diagnostics tab selected. Content area shows: 1) "Connection Diagnostics" section with button "Run Network Test" and empty results area, 2) "System Information" section showing read-only fields: "Application Version: 2.0.0-rc2", "Database Mode: Standalone (SQLite)", "Platform: Windows 11 Pro", "Python Version: 3.11.5", button "Copy System Info", 3) "Troubleshooting Tools" section with three buttons vertically: "Reset Window Position", "Clear History Cache", "Export Diagnostic Report", 4) "Support" section with text "Need help?" and button "View Documentation".]

**אבחון חיבור:**
- **Run Network Test** - בדיקת קישוריות רשת מקיפה
- בדיקות: פתרון DNS, ping, קישוריות פורט, פרוטוקול PJLink
- תוצאות מציגות נקודת כישלון ספציפית לפתרון בעיות

**מידע מערכת:**
- תצוגה לקריאה בלבד של פרטי מערכת
- שימושי בעת דיווח על בעיות
- **Copy System Info** - העתקת כל הפרטים ללוח

**כלי פתרון בעיות:**
- **Reset Window Position** - תיקון חלון תקוע מחוץ למסך
- **Clear History Cache** - ניקוי מסד נתונים של היסטוריית פעולות
- **Export Diagnostic Report** - יצירת קובץ אבחון מקיף לתמיכה

**תמיכה:**
- **View Documentation** - פתיחת מדריך משתמש (מסמך זה)
- קישורים לשאלות נפוצות, README ומשאבים אחרים

> **טיפ:** השתמש ב-"Export Diagnostic Report" בעת יצירת קשר עם תמיכה. הוא כולל את כל מידע המערכת הרלוונטי, לוגים ותצורה בקובץ בודד.

---

## 7. טיפים ושיטות עבודה מומלצות

### טיפים לשימוש יומיומי

**טיפ 1: הפעל את היישום בהתחברות**
- הפעל **Settings > General > Launch on Windows startup**
- היישום נטען במגש המערכת, מוכן כשתזדקק לו
- אין צורך בהפעלה ידנית לפני כל מצגת

**טיפ 2: השתמש בקיצורי מקלדת**
- `Ctrl+P` - החלפת מצב חשמל מהירה
- `Ctrl+I` - פתיחת בורר קלט
- `Ctrl+B` - החלפת מצב השחרת מסך
- ראה [סעיף 8](#8-קיצורי-מקלדת) לרשימה מלאה

**טיפ 3: בדוק סטטוס לפני מצגות**
- אמת שלוח הסטטוס מציג **Connected**
- בדוק הפעלה/כיבוי 5 דקות לפני הפגישה שלך
- מאפשר זמן לפתור בעיות במידת הצורך

**טיפ 4: עקוב אחר פאנל ההיסטוריה**
- הצץ בפעולות אחרונות לערכי ✗ כישלון אדומים
- דפוסי כישלונות מצביעים על בעיות רשת או תאימות
- פנה ל-IT אם אתה רואה בעיות חוזרות

**טיפ 5: שמור את היישום ממוזער**
- מזער למגש מערכת במקום סגירה
- לחיצה ימנית על סמל מגש מערכת לשליטת חשמל מיידית
- מהיר יותר מפתיחת החלון המלא

---

### זרימת עבודה למצגת

**לפני המצגת שלך:**

1. **15 דקות לפני:**
   - פתח את היישום (לחיצה כפולה על סמל מגש מערכת אם ממוזער)
   - אמת שלוח הסטטוס מציג **Connected**
   - הפעל **Settings > Diagnostics > Run Network Test** אם לא בטוח

2. **10 דקות לפני:**
   - לחץ על **Power On** והמתן לחימום
   - בחר מקור קלט נכון (HDMI1, HDMI2, וכו')
   - אמת שמסך המחשב הנייד שלך מופיע על המקרן

3. **5 דקות לפני:**
   - בדוק כפתור **Blank Screen** לאישור שהוא עובד
   - בדוק **Freeze Display** אם אתה מתכנן להשתמש בו
   - סגור את חלון היישום (השאר פועל במגש מערכת)

**במהלך המצגת שלך:**

- השתמש ב-**Blank Screen** במהלך הפסקות או מעברים
- השתמש ב-**Freeze Display** להשהיית וידאו בזמן הסבר
- גש לבקרים דרך תפריט לחיצה ימנית במגש מערכת (אין צורך לפתוח חלון ראשי)

**לאחר המצגת שלך:**

1. לחץ על **Power Off** (או לחיצה ימנית על מגש מערכת ובחר Power Off)
2. המתן לשלב הקירור להסתיים (לוח הסטטוס מציג "Cooling Down")
3. ברגע שלוח הסטטוס מציג "Off", תוכל לנתק את המחשב הנייד שלך

---

### טיפים מהירים לפתרון בעיות

**בעיה: "Connection: Failed" בלוח הסטטוס**
- **תיקון מהיר:** בדוק כבל רשת או חיבור Wi-Fi
- **אימות:** האם אתה יכול לפנג את כתובת ה-IP של המקרן?
- **נסה:** Settings > Connection > Test Connection Now
- **אם מתמשך:** פנה למנהל IT

**בעיה: פקודות איטיות (>10 שניות)**
- **תיקון מהיר:** הגדל timeout ב-Settings > Connection > Command Timeout
- **בדוק:** האם הרשת שלך עמוסה? נסה בזמן מחוץ לשעות שיא
- **לטווח ארוך:** שקול Ethernet קווי במקום Wi-Fi

**בעיה: שגיאת "Authentication failed"**
- **תיקון מהיר:** הזן מחדש סיסמת מקרן ב-Settings > Connection > Edit
- **אימות:** אשר סיסמה עם מנהל IT
- **בדוק:** קובץ entropy קיים (ראה תיעוד אבטחה)

**בעיה: כפתור Input Source מציג אפשרויות מוגבלות**
- **תיקון מהיר:** זה נורמלי - מציג רק קלטים שהמקרן שלך תומך
- **לא באג:** מקרנים משתנים בקלטים זמינים
- **אימות:** בדוק מדריך מקרן לקלטים נתמכים

**בעיה: החלון מחוץ למסך לאחר שינוי מסך**
- **תיקון מהיר:** Settings > Diagnostics > Reset Window Position
- **חלופה:** Alt+Space, M (Move), השתמש במקשי חצים, לחץ Enter

> **לפתרון בעיות נוסף, ראה [סעיף 9](#9-פתרון-בעיות) להלן.**

---

## 8. קיצורי מקלדת

חסוך זמן עם קיצורי מקלדת לפעולות נפוצות.

### קיצורים גלובליים

| קיצור | פעולה | תיאור |
|-------|--------|-------|
| `Ctrl+,` | פתח הגדרות | פתיחת דיאלוג הגדרות |
| `Ctrl+Q` | יציאה מהיישום | סגירת היישום לחלוטין |
| `F1` | עזרה | פתיחת מדריך משתמש זה |
| `Alt+F4` | סגור חלון | סגירת חלון ראשי (היישום נשאר במגש מערכת) |

### קיצורי בקרה

| קיצור | פעולה | תיאור |
|-------|--------|-------|
| `Ctrl+P` | החלפת מצב חשמל | החלפת הפעלה/כיבוי |
| `Ctrl+I` | מקור קלט | פתיחת בורר מקור קלט |
| `Ctrl+B` | השחרת מסך | החלפת מצב השחרת מסך |
| `Ctrl+F` | הקפאת תצוגה | החלפת מצב הקפאה |
| `Ctrl+M` | השתקת אודיו | החלפת מצב השתקת שמע (אם מופעל) |

### קיצורי ניווט

| קיצור | פעולה | תיאור |
|-------|--------|-------|
| `Ctrl+H` | פאנל היסטוריה | מיקוד בפאנל ההיסטוריה |
| `Ctrl+S` | לוח סטטוס | מיקוד בלוח הסטטוס |
| `Ctrl+1` עד `Ctrl+9` | החלפת מקרן מהירה | החלפה למקרן 1-9 (אם מוגדרים מספר) |

### ניהול חלונות

| קיצור | פעולה | תיאור |
|-------|--------|-------|
| `Ctrl+N` | מזעור למגש | מזעור למגש מערכת |
| `Ctrl+R` | שחזור חלון | שחזור ממגש מערכת (כאשר ממוקד על סמל מגש) |

> **טיפ:** לחץ `F1` בכל עת לצפייה במדריך עזרה זה!

> **הערה:** חלק מהקיצורים עשויים להיות מושבתים אם התכונה המתאימה מוסתרת בהגדרות UI Buttons.

---

## 9. פתרון בעיות

### בעיות חיבור

#### תסמין: שגיאת "Cannot connect to projector"

[Screenshot: Error dialog with red X icon. Title "Connection Error". Message: "Cannot connect to projector at 192.168.1.100:4352. Error: Connection timed out (110)." Three buttons: "Retry", "Test Network", "Cancel". Background slightly dimmed showing main window behind.]

**אבחון שלב אחר שלב:**

1. **אמת קישוריות רשת**
   ```
   פתח Command Prompt (Win+R, הקלד "cmd", לחץ Enter)
   הקלד: ping 192.168.1.100
   לחץ Enter
   ```
   - **הצלחה:** "Reply from 192.168.1.100..." → הרשת עובדת, דלג לשלב 3
   - **כישלון:** "Request timed out" → בעיית רשת, המשך לשלב 2

2. **בדוק חיבור רשת**
   - האם המחשב שלך מחובר לרשת? (בדוק מחוון Wi-Fi או Ethernet)
   - האם המקרן מופעל? (בדוק פיזית)
   - האם אתה באותה רשת כמו המקרן? (VPN עלול לגרום לבעיות)
   - נסה להתחבר לרשת שוב

3. **אמת כתובת IP מקרן**
   - אשר כתובת IP עם מנהל IT
   - בדוק אם כתובת ה-IP השתנתה (שכירות DHCP פגה)
   - נסה את התפריט הפיזי של המקרן לאימות הגדרות רשת

4. **בדוק כללי חומת אש**
   - חומת Windows עשויה לחסום פורט TCP 4352
   - השבת זמנית חומת אש לבדיקה (הפעל מחדש לאחר הבדיקה!)
   - פנה ל-IT להוספת חריג חומת אש לפורט 4352

5. **בדוק פרוטוקול PJLink**
   - פתח Settings > Connection > Test Connection Now
   - אם הבדיקה נכשלת, בדוק הודעת שגיאה לסיבת כישלון ספציפית
   - שגיאות נפוצות:
     - "Connection refused" → המקרן לא מקבל חיבורים, בדוק פורט
     - "Authentication failed" → סיסמה שגויה, בדוק Settings > Connection > Edit
     - "Timeout" → בעיית רשת, ראה שלבים 1-4 למעלה

#### תסמין: "Connection: Unstable" מוצג לעתים קרובות

**סיבות:**
- חוזק אות Wi-Fi חלש
- עומס רשת
- חומת אש מפריעה לחבילות
- בעיות בכרטיס רשת של המקרן

**פתרונות:**
- **העדף Ethernet קווי** על פני Wi-Fi לחיבור מקרן
- הגדל timeout: Settings > Connection > Command Timeout ל-15-20 שניות
- הפעל התחברות מחדש אוטומטית: Settings > Connection > Reliability > Enable automatic reconnection
- פנה ל-IT לחקור איכות רשת

#### תסמין: החיבור עובד אך פקודות נכשלות

[Screenshot: History Panel showing multiple failed operations. Entries like "14:42:15 🔌 Power On → Failed ✗ Error: Command not supported", "14:40:33 📺 Input Changed to Component → Failed ✗ Error: Invalid input", "14:38:20 🔊 Volume Control → Failed ✗ Error: Feature not available".]

**אבחון:**
- החיבור מצליח (לוח הסטטוס מציג "Connected")
- אך פקודות ספציפיות נכשלות עם שגיאות

**סיבות:**
- **דגם מקרן לא תואם** - לא כל המקרנים תומכים בכל פקודות PJLink
- **קושחת מקרן מיושנת** - עדכן קושחה (פנה ל-IT)
- **סוג פרוטוקול שגוי** - שימוש ב-PJLink אך המקרן מצפה לפרוטוקול מקורי

**פתרונות:**
1. אמת שדגם המקרן תואם: בדוק רשימת תאימות ב[README.md](../../README.md)
2. נסה PJLink כללי: Settings > Connection > Edit > Brand > "Other - PJLink Generic"
3. עדכן קושחת מקרן: פנה למנהל IT
4. דווח על בעיית תאימות: ראה [שאלות נפוצות](../FAQ.he.md) כיצד לדווח על בעיות

---

### בעיות ביצועים

#### תסמין: היישום לוקח >5 שניות להפעיל

**אבחון:**
- מדוד זמן הפעלה בפועל באמצעות שעון עצר
- השווה ליעד: <2 שניות

**סיבות נפוצות:**
- זמן הפעלה כולל זמן חיבור רשת
- פתרון DNS רשת איטי
- פיצול קובץ מסד נתונים (מצב SQLite)
- סריקת תוכנת אנטי-וירוס של קובץ הפעלה בכל השקה

**פתרונות:**
- **השבת בדיקת רשת בהפעלה:** Settings > Connection > בטל סימון "Connect to projectors on startup"
- **אל תכלול מאנטי-וירוס:** הוסף `ProjectorControl.exe` לרשימת החרגה של אנטי-וירוס (שאל IT)
- **השתמש ברשת קווית:** חיפושי DNS ב-Wi-Fi יכולים להיות איטיים
- **דחוס מסד נתונים:** Settings > Advanced > Maintenance > Compact Database (אם זמין)

#### תסמין: פקודות לוקחות >10 שניות לביצוע

**אבחון:**
- בדוק חותמות זמן בפאנל ההיסטוריה: שים לב לזמן בין לחיצה להצלחה/כישלון
- השווה ליעד: <5 שניות

**סיבות נפוצות:**
- השהיית רשת (Wi-Fi, VPN, עומס)
- מקרן איטי להגיב (קושחה ישנה)
- Timeout מוגדר גבוה מדי (ממתין תקופת timeout מלאה לפני ניסיון חוזר)

**פתרונות:**
- הגדל command timeout: Settings > Connection > Command Timeout ל-15 שניות (נותן למקרן יותר זמן)
- הפחת ניסיונות חוזרים: Settings > Connection > Retry attempts ל-1 (נכשל מהר יותר במקום ניסיונות חוזרים)
- בדוק השהיית רשת: Settings > Diagnostics > Run Network Test (בדוק זמן ping)
- השתמש ב-Ethernet קווי: מבטל השהיית Wi-Fi

#### תסמין: היישום משתמש בזיכרון מוגזם (>200 MB)

**אבחון:**
- פתח Task Manager (Ctrl+Shift+Esc)
- מצא "ProjectorControl.exe" בטאב Processes
- בדוק שימוש בזיכרון (יעד: <150 MB)

**סיבות נפוצות:**
- היסטוריית פעולות גדולה (אלפי ערכים)
- דליפת זיכרון (נדיר, פנה לתמיכה)
- מצב ניפוי שגיאות מופעל (מייצר לוגים גדולים)

**פתרונות:**
- נקה היסטוריה: Settings > Diagnostics > Clear History Cache
- השבת מצב debug: Settings > Advanced > Developer Options > בטל סימון "Enable debug mode"
- הפעל מחדש יישום: סגור ופתח מחדש לשחרור זיכרון
- אם מתמשך: ייצא דוח אבחון ופנה לתמיכה

---

### בעיות סיסמה ואבטחה

#### תסמין: "Authentication failed" בעת התחברות למקרן

**אבחון:**
- הודעת שגיאה: "Authentication failed" או "Invalid password"
- החיבור אחרת מצליח (ping עובד, הפורט נגיש)

**סיבות:**
- סיסמה שגויה הוזנה בהגדרות
- סיסמה השתנתה במקרן אך לא עודכנה ביישום
- קובץ entropy חסר (לא ניתן לפענח סיסמה מאוחסנת)

**פתרונות:**
1. **הזן מחדש סיסמה:**
   - Settings > Connection > Edit (מקרן)
   - הזן סיסמה בשדה "Password"
   - לחץ Test Connection לאימות
   - לחץ Save

2. **אמת סיסמה עם IT:**
   - אשר סיסמה נכונה עם מנהל
   - סיסמת מקרן עשויה להשתנות

3. **בדוק שקובץ entropy קיים:**
   - מיקום קובץ entropy: `%APPDATA%\ProjectorControl\.projector_entropy`
   - אם חסר: לא ניתן לפענח סיסמה, יש להזין מחדש את כל סיסמאות המקרן
   - ראה [גיבוי ושחזור אסון](../deployment/DEPLOYMENT_GUIDE.he.md#10-גיבוי-ושחזור-אסון)

#### תסמין: שכחתי סיסמת מנהל

**לצערנו, אין אפשרות שחזור.**

**מה זה אומר:**
- אינך יכול לפתוח הגדרות
- אינך יכול לשנות תצורה כלשהי
- אינך יכול להוסיף/לערוך/להסיר מקרנים

**האפשרויות שלך:**
1. **אם אתה זוכר את הסיסמה:** נסה להקליד אותה בזהירות (בדוק Caps Lock)
2. **אם יש לך גיבוי:** שחזר מגיבוי (כולל סיסמת מנהל)
3. **אם אין גיבוי:** עליך להתקין מחדש:
   - סגור יישום
   - מחק נתוני יישום: `%APPDATA%\ProjectorControl`
   - מחק קובץ entropy: `%APPDATA%\ProjectorControl\.projector_entropy`
   - הפעל יישום - אשף הפעלה ראשון מתחיל
   - הגדר מחדש הכל מאפס

> **מניעה:** רשום את סיסמת המנהל שלך ושמור אותה בבטחה! שקול שימוש במנהל סיסמאות.

---

### בעיות תצוגה וממשק משתמש

#### תסמין: החלון מחוץ למסך או גלוי חלקית

**נפוץ לאחר:**
- ניתוק מסך חיצוני
- שינוי רזולוציית תצוגה
- מעבר מתחנת עגינה למסך מחשב נייד

**תיקון מהיר:**
1. Settings > Diagnostics > Reset Window Position
2. או השתמש במקלדת:
   - לחץ על היישום בסרגל המשימות לבחירתו
   - לחץ `Alt+Space`
   - לחץ `M` (Move)
   - השתמש במקשי חצים להזזת חלון
   - לחץ `Enter` כאשר גלוי

#### תסמין: הטקסט קטן מדי או גדול מדי (קנה מידת DPI)

**אבחון:**
- הטקסט מופיע מטושטש
- רכיבי ממשק משתמש גדולים או קטנים באופן חריג
- כפתורים חתוכים

**סיבות:**
- קנה מידת DPI של Windows (125%, 150%, 200%)
- היישום אינו מודע ל-DPI

**פתרונות:**
- **הפעל מחדש יישום:** סגור לחלוטין ופתח מחדש (DPI מזוהה בהפעלה)
- **בדוק הגדרות DPI של Windows:**
  - לחיצה ימנית על שולחן עבודה > Display settings
  - בדוק הגדרת "Scale and layout"
  - היישום תומך ב-100%-400% DPI
- **אם מטושטש:** לחיצה ימנית על `ProjectorControl.exe` > Properties > Compatibility > Change high DPI settings > Override high DPI scaling behavior

#### תסמין: טקסט עברי מוצג שגוי (בעיות RTL)

[Screenshot: Main window in Hebrew with RTL layout issue. Shows some text aligned left instead of right, or mixed text direction. Example: buttons showing English text on right side and Hebrew text on left side, instead of properly mirrored layout.]

**אבחון:**
- טקסט עברי מופיע אך הפריסה שגויה
- טקסט מיושר בכיוון שגוי
- סמלים לא משוקפים

**סיבות:**
- הגדרות אזוריות של Windows לא מוגדרות לעברית
- בעיית עיבוד גופנים

**פתרונות:**
- **בדוק בחירת שפה:** Settings > General > Language > בחר "עברית Hebrew"
- **הפעל מחדש יישום:** סגור ופתח מחדש להחלה מחדש של פריסת RTL
- **אמת חבילת שפה Windows:** Windows Settings > Time & Language > Language > הוסף עברית אם חסרה
- אם מתמשך: דווח על באג עם צילום מסך (ראה [שאלות נפוצות](../FAQ.he.md))

---

### קבלת עזרה

אם ניסית את שלבי פתרון הבעיות למעלה ועדיין יש לך בעיות:

**1. בדוק את השאלות הנפוצות**
- קרא [FAQ.he.md](../FAQ.he.md) לתשובות מהירות
- חפש את הודעת השגיאה הספציפית שלך

**2. אסוף מידע אבחון**
- Settings > Diagnostics > Export Diagnostic Report
- שומר קובץ עם כל מידע המערכת, לוגים ותצורה
- שלח קובץ זה במייל למנהל ה-IT שלך או איש קשר לתמיכה

**3. בדוק לוגים של היישום**
- Settings > Advanced > Logging > Open Log Folder
- הסתכל בקובץ `.log` האחרון
- חפש ערכי "ERROR" או "FAIL"

**4. פנה למנהל IT**
- ספק דוח אבחון (משלב 2)
- תאר מה עשית כשהבעיה התרחשה
- כלול צילומי מסך אם רלוונטי

**5. דווח על באג**
- ראה [שאלות נפוצות](../FAQ.he.md) "כיצד לדווח על באג?"
- כלול דוח אבחון, צילומי מסך, שלבים לשחזור

---

## נספח א': מילון מונחים

**PJLink**
- פרוטוקול רשת סטנדרטי בתעשייה לשליטה במקרנים
- משתמש בפורט TCP 4352
- נתמך על ידי רוב המותגים העיקריים של מקרנים

**מגש המערכת**
- אזור הודעות Windows (פינה ימנית תחתונה של סרגל המשימות)
- מציג יישומי רקע
- גישה דרך סמל חץ קטן אם מוסתר

**DPAPI (Data Protection API)**
- מערכת הצפנה מובנית של Windows
- משמש להצפנת סיסמאות מקרן
- דורש קובץ entropy לפענוח

**קובץ Entropy**
- קובץ מיוחד (`.projector_entropy`) המשמש להצפנה
- ממוקם ב-`%APPDATA%\ProjectorControl\.projector_entropy`
- יש לגבות או סיסמאות מוצפנות אובדות

**SQLite**
- מצב מסד נתונים עצמאי
- מאחסן נתונים בקובץ בודד במחשב שלך
- אין צורך במסד נתונים ברשת

**SQL Server**
- מצב מסד נתונים ארגוני
- מאחסן נתונים בשרת מרכזי
- מספר מחשבים משתפים תצורה

**RTL (Right-to-Left)**
- כיוון טקסט לעברית ושפות אחרות
- פריסת ממשק משתמש משוקפת (תפריטים בצד ימין במקום שמאל)

**DPI (Dots Per Inch)**
- קנה מידת רזולוציית מסך
- DPI גבוה יותר = פיקסלים קטנים יותר, תצוגה חדה יותר
- קנה מידת Windows: 100% (96 DPI), 125%, 150%, 200%, וכו'

---

## נספח ב': מיקומי קבצים

**נתוני יישום:**
- `%APPDATA%\ProjectorControl\` - תיקיית נתונים ראשית
- `%APPDATA%\ProjectorControl\projector_control.db` - קובץ מסד נתונים (מצב SQLite)
- `%APPDATA%\ProjectorControl\.projector_entropy` - קובץ entropy הצפנה
- `%APPDATA%\ProjectorControl\backups\` - קבצי גיבוי

**קבצי לוג:**
- `%APPDATA%\ProjectorControl\logs\` - לוגים של היישום
- `app.log` - לוג הפעלה נוכחי
- `app.log.1`, `app.log.2`, וכו' - לוגים ישנים שסובבו

**תצורה:**
- `%APPDATA%\ProjectorControl\config.ini` - העדפות משתמש

**הפעלת Windows:**
- `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\ProjectorControl.lnk` - קיצור דרך הפעלה (אם מופעל)

> **הערה:** `%APPDATA%` בדרך כלל מתרחב ל-`C:\Users\YourUsername\AppData\Roaming\`

---

## נספח ג': דרישות מערכת

לדרישות מערכת מלאות, ראה [README.md](../../README.md#system-requirements).

**מינימום:**
- Windows 10 (64-bit)
- 4 GB RAM
- 100 MB שטח דיסק
- קישוריות רשת למקרן

**מומלץ:**
- Windows 11 (64-bit)
- 8 GB RAM
- חיבור Ethernet קווי לרשת מקרן

**מותגי מקרן נתמכים:**
- מאומת: EPSON, Hitachi
- תואם צפוי: Panasonic, Sony, BenQ, NEC, JVC, Christie, InFocus
- דרישה: תמיכת PJLink Class 1 או Class 2

---

## נספח ד': היסטוריית גרסאות

**גרסה 1.0** (נוכחית)
- מתאים לגרסת יישום 2.0.0-rc2
- מדריך משתמש מלא ראשון
- מכסה את כל התכונות המרכזיות

**עדכונים עתידיים:**
- מדריך זה יעודכן ככל שיתווספו תכונות יישום חדשות
- בדוק [README.md](../../README.md) לגרסת יישום אחרונה

---

**סוף מדריך משתמש**

למשאבים נוספים:
- **[שאלות נפוצות](../FAQ.he.md)** - תשובות מהירות לשאלות נפוצות
- **[מדריך פריסה](../deployment/DEPLOYMENT_GUIDE.he.md)** - למנהלי IT
- **[README](../../README.md)** - מפרט טכני
- **[תיעוד אבטחה](../../SECURITY.md)** - ארכיטקטורת אבטחה

*מדריך משתמש גרסה 1.0*
*עודכן לאחרונה: 12 בפברואר 2026*
*תואם ל-Enhanced Projector Control Application גרסה 2.0.0-rc2 ואילך*
