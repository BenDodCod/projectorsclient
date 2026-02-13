# שאלות נפוצות (FAQ)

**גרסה:** 1.0
**עודכן לאחרונה:** 12 בפברואר 2026
**גרסת היישום:** 2.0.0-rc2

---

## תוכן עניינים

1. [שאלות כלליות](#1-שאלות-כלליות)
2. [התקנה והגדרה](#2-התקנה-והגדרה)
3. [שימוש ביישום](#3-שימוש-ביישום)
4. [פתרון בעיות](#4-פתרון-בעיות)
5. [פריסה ארגונית (למנהלי IT)](#5-פריסה-ארגונית-למנהלי-it)
6. [אבטחה ואישורים](#6-אבטחה-ואישורים)
7. [ביצועים ואיכות](#7-ביצועים-ואיכות)

---

## 1. שאלות כלליות

### מהו יישום Enhanced Projector Control?

זהו יישום מקצועי עבור Windows המאפשר שליטה במקרנים ברשת באמצעות פרוטוקול PJLink. במקום להשתמש בשלט רחוק פיזי או ללכת למקרן, תוכל לשלוט בו ישירות מהמחשב שלך דרך הרשת.

**תכונות עיקריות:**
- הפעלה/כיבוי של מקרנים
- החלפת מקורות קלט (HDMI, VGA, וכו')
- השחרת המסך במהלך מצגות
- הקפאת התצוגה
- צפייה בהיסטוריית כל הפעולות
- תמיכה בעברית מלאה עם פריסת RTL
- מצב עצמאי (SQLite) או ארגוני (SQL Server)

---

### אילו מקרנים נתמכים?

**תואמים מאומתים:**
- **EPSON** - EB-2250U, EB-2255U, EB-2265U, PowerLite סדרות
- **Hitachi** - CP-EX301N, CP-EX302N, CP-WX8255, סדרות CP-X/CP-D

**תואמים צפויים:**
(כל מקרן עם תמיכת PJLink Class 1 או Class 2 אמור לעבוד)
- **Panasonic** - PT-LB/PT-VW/PT-VX סדרות
- **Sony** - VPL סדרות
- **BenQ** - MH/MW/MS סדרות
- **NEC** - NP-M/NP-P סדרות
- **Christie** - DHD/DWU סדרות
- **InFocus** - IN סדרות
- **JVC** - DLA סדרות

**דרישות:**
- תמיכת PJLink Class 1 (מינימום) או Class 2
- קישוריות רשת TCP/IP (חוטית או אלחוטית)
- פתיחת פורט TCP 4352 (ברירת מחדל של PJLink)

> **שים לב:** המקרן שלך לא ברשימה? נסה "Other - PJLink Generic" במהלך ההתקנה. רוב המקרנים המודרניים תומכים ב-PJLink גם אם המותג לא מופיע ברשימה.

---

### האם נדרשות הרשאות מנהל להפעלת היישום?

**לא.** היישום פועל בהרשאות משתמש רגילות ואינו מצריך הרשאות מנהל.

**למה זה חשוב:**
- מורים ומציגים יכולים להשתמש ביישום ללא סיוע IT
- ניתן להפעיל את היישום מתיקיית ההפעלה של המשתמש
- ללא בעיות UAC (בקרת חשבון משתמש)

**הערה לגבי התקנה ראשונית:**
- הגדרה ראשונית אינה דורשת הרשאות מנהל
- עם זאת, ייתכן שמנהל IT ירצה להגדיר את האפליקציה עבור כל המשתמשים
- ראה [מדריך פריסה](deployment/DEPLOYMENT_GUIDE.he.md) להנחיות IT

---

### מה ההבדל בין מצב Standalone ו-Enterprise?

| תכונה | Standalone (SQLite) | Enterprise (SQL Server) |
|-------|---------------------|------------------------|
| **אחסון נתונים** | מחשב מקומי (`%APPDATA%`) | שרת SQL Server מרכזי |
| **התקנה** | פשוטה - אין דרישות שרת | דורש שרת SQL והגדרה של IT |
| **שיתוף תצורה** | לא - כל מחשב עצמאי | כן - כל המחשבים חולקים תצורה |
| **גיבוי** | ידני (קובץ SQLite + entropy) | מרכזי (SQL Server backups) |
| **משתמשים במקביל** | משתמש בודד בלבד | תמיכה במשתמשים מרובים |
| **אידיאלי עבור** | משתמשים בודדים, התקנות קטנות | ארגונים, מיקומים מרובים |
| **חוקיות רישוי** | כל מחשב נפרד | ניהול רישיונות מרכזי |

**מתי להשתמש ב-Standalone:**
- התקנת משתמש יחיד
- אין גישה ל-SQL Server
- פשטות מועדפת על שיתוף

**מתי להשתמש ב-Enterprise:**
- ארגונים עם מספר מחשבים
- ניהול מרכזי נדרש
- גיבויים אוטומטיים של SQL Server זמינים
- שיתוף תצורות מקרנים בין משתמשים

> **טיפ:** רוב המשתמשים צריכים להתחיל במצב Standalone. תמיד ניתן להעביר ל-Enterprise מאוחר יותר אם הארגון שלך גדל.

---

### האם יכול אחד להשתמש במקרן שלי בזמן שאני מחובר?

**כן**, אבל יש הגנות במקום.

**מה קורה:**
- **PJLink** הוא פרוטוקול בקשה-תגובה חסר מצב (stateless)
- מישהו אחר יכול לשלוח פקודות למקרן בו זמנית
- המקרן מעבד פקודות לפי סדר ההגעה

**הגנות ביישום:**
- היישום מזהה שינויי מצב בלתי צפויים
- לוח הסטטוס מתעדכן כדי לשקף את המצב האמיתי
- פאנל ההיסטוריה מציג את כל הפעולות (שלך + של אחרים)

**שיטות עבודה מומלצות:**
- **מצב Standalone**: תאם עם משתמשים אחרים בחדר
- **מצב Enterprise**: שקול אכיפת נעילות מבוססות משתמש (צור קשר עם IT)
- **אבטחת מקרן**: הגדר סיסמת PJLink במקרן (מגביל גישה)

---

### האם יכול יישום אחד לשלוט במספר מקרנים?

**כן**, אבל ביישום אחד מציג מקרן אחד בכל פעם.

**כיצד זה עובד:**
- הגדר מספר מקרנים ב-Settings > Connection > Add New Projector
- החלף בין מקרנים באמצעות בורר המקרנים בסרגל הכלים
- לוח הבקרה מציג את המקרן שנבחר כעת
- כל הפקודות משפיעות רק על המקרן הפעיל

**מקרים לשימוש:**
- **חדרי שיעור מרובים**: מורה שעובר בין חדרים
- **מרכזי כנסים**: טכנאי שמנהל חללים מרובים
- **אודיטוריומים**: מערכות מקרנים ראשיות + גיבוי

**מגבלות:**
- לא ניתן לשלוט בשני מקרנים בו זמנית מאותו יישום
- כל מקרן דורש תצורה עצמאית (IP, סיסמה, וכו')

> **טיפ:** השתמש בשמות ברורים למקרנים כגון "חדר כנסים A" או "כיתה 301" כדי לזהות אותם בקלות.

---

### האם היישום פועל על macOS או Linux?

**לא.** היישום זמין רק עבור **Windows 10/11 (64-bit)**.

**מדוע Windows בלבד:**
- תלות ב-Windows DPAPI להצפנת אישורים
- ספריות PyQt6 הספציפיות ל-Windows
- אינטגרציה של Windows System Tray
- אופטימיזציות עבור אפליקציות שולחן העבודה של Windows

**חלופות עבור מערכות הפעלה אחרות:**
- **בדפדפן Web**: שקול כלי ווב מבוסס PJLink (צור קשר עם IT)
- **שורת פקודה PJLink**: השתמש בכלי CLI עבור Linux/macOS
- **מכונות וירטואליות**: הפעל Windows ב-VM (לא אידיאלי לשימוש יומיומי)

---

### האם צריך להיות מחובר לאינטרנט?

**לא.** היישום פועל באופן מלא ללא חיבור אינטרנט.

**דרישות רשת:**
- **נדרש**: קישוריות רשת **מקומית** למקרן (LAN/VLAN)
- **לא נדרש**: גישה לאינטרנט או WAN

**תכונות ללא אינטרנט:**
- שליטה במקרן (הפעלה/כיבוי, החלפת קלט, וכו')
- ניהול הגדרות
- היסטוריית פעולות
- גיבוי/שחזור

**תכונות הדורשות אינטרנט:**
- בדיקת עדכונים (אופציונלי - ניתן להשבית)
- הורדת גרסאות חדשות (ידני)

> **טיפ:** אידיאלי עבור רשתות מבודדות או סביבות אבטחה גבוהה ללא חיבור אינטרנט.

---

### כמה עולה היישום?

בדוק עם ארגונך או מנהל ה-IT שלך לגבי רישוי ותמחור.

היישום מופץ תחת [הוסף פרטי רישוי כאן - לא הוגדר במסמכים].

---

### איפה מאוחסנים הנתונים שלי?

**מצב Standalone (SQLite):**
```
%APPDATA%\ProjectorControl\
├── projector_control.db    (מסד נתונים SQLite)
├── .projector_entropy       (קובץ הצפנה - קריטי!)
├── config.ini               (העדפות משתמש)
├── logs\                    (לוגים של יישום)
└── backups\                 (גיבויים ידניים)
```

**מצב Enterprise (SQL Server):**
- מסד נתונים: `ProjectorControl` על שרת SQL Server
- הגדרות מקומיות: `%APPDATA%\ProjectorControl\config.ini`
- קובץ Entropy: `%APPDATA%\ProjectorControl\.projector_entropy` (עדיין נדרש!)

**הערה:** `%APPDATA%` בדרך כלל מתרחב ל-`C:\Users\YourUsername\AppData\Roaming\`

---

### איך מסירים את היישום?

**מצב Standalone (הסרה מלאה):**

1. **סגור את היישום:**
   - לחץ ימין על סמל המגש > יציאה
   - ודא שהתהליך אינו פועל ב-Task Manager

2. **מחק את היישום הראשי:**
   - מחק את `ProjectorControl.exe` מהמיקום שבו שמרת אותו

3. **מחק נתונים של יישום (אופציונלי):**
   ```
   מחק את התיקייה: %APPDATA%\ProjectorControl\
   ```
   **אזהרה:** זה מוחק את כל ההגדרות, סיסמאות מוצפנות, והיסטוריה.

4. **הסר מההפעלה (אם מופעל):**
   - מחק קיצור דרך מ-`%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\`

**מצב Enterprise:**
- אותם שלבים כמו למעלה
- תצורות המקרנים המשותפות נשארות על שרת SQL (לא מושפעות)

---

## 2. התקנה והגדרה

### כיצד מתקינים את היישום?

**היישום הוא קובץ הפעלה יחיד ללא דרישות התקנה.**

**שלבי התקנה:**

1. **הורד** את `ProjectorControl.exe` מהמקור שלך (מנהל IT, שרת פיצול וכו')

2. **שמור** לכל מיקום נגיש:
   - `C:\Users\YourName\Desktop\` (שולחן עבודה)
   - `C:\Users\YourName\Documents\` (מסמכים)
   - `C:\Program Files\ProjectorControl\` (כל המשתמשים - דורש הרשאות מנהל)

3. **הפעל** - לחץ פעמיים על `ProjectorControl.exe`

4. **אשר התראת אבטחה** (אם מופיעה):
   - Windows עשוי להציג "Windows Protected your PC"
   - לחץ "More info" ואז "Run anyway"
   - זה נורמלי עבור קבצי EXE לא חתומים

5. **השלם הגדרה ראשונית:**
   - אשף הפעלה ראשון מופיע אוטומטית
   - עקוב אחר [שלבי האשף](#כיצד-משלימים-את-אשף-ההפעלה-הראשון)

**זהו זה!** אין DLLs, תלויות, או רישום נדרשים.

---

### כיצד משלימים את אשף ההפעלה הראשון?

אשף ההפעלה הראשון לוקח כ-**5 דקות** ומדריך אותך דרך 6 שלבים:

**שלב 1: בחירת שפה**
- בחר **English** או **עברית (Hebrew)**
- לחץ Next

**שלב 2: הגדרת סיסמת מנהל**
- צור סיסמה עם:
  - לפחות 8 תווים
  - אות גדולה אחת לפחות
  - מספר אחד לפחות
  - תו מיוחד אחד לפחות (!@#$%^&*)
- **כתוב את הסיסמה במקום בטוח!** אין אפשרות שחזור.

**שלב 3: בחירת מצב מסד נתונים**
- **Standalone (SQLite)** - מומלץ לרוב המשתמשים
- **Enterprise (SQL Server)** - רק אם מנהל IT נתן לך פרטי חיבור

**שלב 4: תצורת מקרן**
- שם מקרן: "חדר כנסים A" (שם ידידותי)
- כתובת IP: `192.168.1.100` (שאל את IT)
- פורט: `4352` (ברירת מחדל של PJLink)
- מותג: בחר מהרשימה או "Other - PJLink Generic"
- סיסמה: השאר ריק אם המקרן אין לו סיסמה
- לחץ "Test Connection" כדי לאמת

**שלב 5: התאמה אישית של UI (אופציונלי)**
- ברירות המחדל המומלצות נבחרות מראש
- פשוט לחץ Next

**שלב 6: השלמה**
- סקור את הסיכום
- לחץ Finish כדי לפתוח את החלון הראשי

**מה אם צריך לדלג?**
- כפתור "Skip for now" זמין בשלב 4 (תצורת מקרן)
- תוכל להוסיף מקרנים מאוחר יותר ב-Settings

> **טיפ:** הכן את כתובת ה-IP של המקרן שלך לפני שתתחיל את האשף כדי להקל על התהליך.

---

### שכחתי את סיסמת המנהל שלי. מה לעשות?

**מצטער, אין אפשרות שחזור סיסמה.**

זה החלטת אבטחה מכוונת - היישום משתמש בהאשינג bcrypt חד כיווני, מה שאומר שהסיסמה לא נשמרת בשום מקום והיא בלתי הפיכה.

**האפשרויות שלך:**

**1. אם יש לך גיבוי:**
- שחזר מקובץ גיבוי שנוצר כאשר ידעת את הסיסמה
- פתור: Settings > Backup > Restore from Backup
- הסיסמה הישנה תשוחזר

**2. אם אין גיבוי:**
- **חייב להתקין מחדש מאפס:**
  1. סגור את היישום
  2. מחק: `%APPDATA%\ProjectorControl\`
  3. מחק: `%APPDATA%\ProjectorControl\.projector_entropy`
  4. הפעל את היישום - אשף הפעלה ראשון יתחיל
  5. צור סיסמה חדשה
  6. הגדר מחדש את כל המקרנים

**למניעה:**
- כתוב את סיסמת המנהל במקום בטוח
- שקול שימוש במנהל סיסמאות
- צור גיבויים באופן קבוע (Settings > Backup)

---

### איפה מאוחסנות הגדרות היישום?

**מצב Standalone:**
```
%APPDATA%\ProjectorControl\
├── projector_control.db     ← תצורות מקרנים, היסטוריה
├── .projector_entropy       ← הצפנה (קריטי!)
├── config.ini               ← העדפות UI
└── logs\app.log            ← לוגים
```

**מצב Enterprise:**
```
SQL Server:
└── ProjectorControl database ← תצורות מקרנים משותפות

Local (%APPDATA%\ProjectorControl\):
├── .projector_entropy       ← הצפנה (עדיין נדרש!)
├── config.ini               ← העדפות UI מקומיות
└── logs\app.log            ← לוגים מקומיים
```

**הערות חשובות:**
- **קובץ Entropy** (`.projector_entropy`) הוא **קריטי** - ללא אותו, סיסמאות מוצפנות אינן ניתנות לפענוח
- גבה **גם** את מסד הנתונים **וגם** את קובץ ה-entropy
- העדפות UI (`config.ini`) מאוחסנות מקומית גם במצב Enterprise

---

### כיצד מעבירים הגדרות למחשב אחר?

**מצב Standalone - העברה מלאה:**

**במחשב המקור:**
1. Settings > Backup > Create Backup
2. שמור קובץ גיבוי ל-`backup.enc`
3. העתק גם את קובץ ה-entropy:
   ```
   העתק: %APPDATA%\ProjectorControl\.projector_entropy
   ```

**במחשב היעד:**
1. התקן את `ProjectorControl.exe`
2. הפעל והשלם אשף הפעלה ראשון (צור סיסמת מנהל חדשה)
3. סגור את היישום
4. העתק את קובץ ה-entropy ל-`%APPDATA%\ProjectorControl\.projector_entropy`
5. הפעל מחדש את היישום
6. Settings > Backup > Restore from Backup
7. בחר `backup.enc`

**מצב Enterprise - פשוט יותר:**
- פשוט התקן את היישום במחשב חדש
- בחר **Enterprise (SQL Server)** באשף הפעלה ראשון
- הזן פרטי חיבור של SQL Server
- כל התצורות נטענות אוטומטית מהשרת!

**הערה:** קובץ ה-entropy עדיין נדרש גם במצב Enterprise.

---

### כיצד מוסיפים מקרן נוסף?

אחרי ההגדרה הראשונית, תוכל להוסיף מקרנים נוספים:

**שלבים:**
1. פתח **Settings** (סמל גלגל שיניים או `Ctrl+,`)
2. עבור ל-**Connection** tab
3. לחץ **Add New Projector** (כפתור כחול בתחתית)
4. מלא פרטי מקרן:
   - **שם**: "אולם הדרכה B"
   - **כתובת IP**: `192.168.1.101`
   - **פורט**: `4352`
   - **מותג**: בחר מהרשימה
   - **סיסמה**: אופציונלי
5. לחץ **Test Connection**
6. אם הבדיקה עברה, לחץ **Save**

**החלפה בין מקרנים:**
- השתמש בבורר המקרנים בסרגל הכלים (אם יותר ממקרן אחד הוגדר)
- בחר איזה מקרן לשלוט בו
- כל הבקרות משפיעות על המקרן שנבחר

---

### איך משנים שפת ממשק ל-עברית?

**דרך 1: מהגדרות (אם היישום כבר פועל):**
1. פתח **Settings** (⚙️ או `Ctrl+,`)
2. עבור ל-**General** tab
3. תחת "Language Preferences" בחר **עברית (Hebrew)**
4. לחץ **Apply**
5. הממשק עובר מיד לעברית עם פריסת RTL

**דרך 2: מאשף הפעלה ראשון:**
- בשלב 1 של האשף, בחר **עברית (Hebrew)**
- היישום כולו יהיה בעברית מההתחלה

**מה משתנה:**
- כל תוויות הכפתורים בעברית
- כל פריטי התפריט בעברית
- פריסת RTL (תפריטים בצד ימין, יישור טקסט ימינה)
- הודעות שגיאה ודיאלוגים בעברית
- סמלי כיוון משתקפים

**מה נשאר באנגלית:**
- שמות מותגים טכניים (EPSON, Hitachi)
- כתובות IP ופורטים
- קוד ופקודות טכניות

---

## 3. שימוש ביישום

### כיצד מדליקים את המקרן?

**שלבים:**
1. ודא שלוח הסטטוס מציג **"מחובר"** (Connected)
2. לחץ על הכפתור הירוק **"הפעלה"** (Power On)
3. המקרן מתחיל להתחמם (30-60 שניות)
4. לוח הסטטוס מתעדכן ל-**"מתחמם"** (Warming Up)
5. אחרי החימום: **"פועל"** (On)

**מה קורה:**
- היישום שולח פקודת Power On דרך PJLink
- מנורת המקרן מתחילה להתחמם
- הסטטוס מתעדכן אוטומטית
- פאנל ההיסטוריה מציג "הפעלה → הצלחה ✓"

**טיפים:**
- אל תלחץ על הכפתור מספר פעמים - הפקודה נשלחה בפעם הראשונה
- זמן החימום תלוי במודל המקרן (בדרך כלל 30-60 שניות)
- אם הסטטוס לא מתעדכן תוך 2 דקות, בדוק חיבור רשת

---

### כיצד מכבים את המקרן?

**שלבים:**
1. לחץ על הכפתור האדום **"כיבוי"** (Power Off)
2. אשר שאתה רוצה לכבות (אם מופיע דיאלוג אישור)
3. המקרן מתחיל להתקרר (60-90 שניות)
4. לוח הסטטוס מתעדכן ל-**"מתקרר"** (Cooling Down)
5. אחרי הקירור: **"כבוי"** (Off)

**אזהרה חשובה:**
> **לעולם אל תנתק מקרן מהחשמל מיד אחרי כיבוי!** תן למקרן להתקרר במלואו כדי להגן על המנורה.

**טיפים:**
- דלג על דיאלוג אישור: Settings > General > בטל סימון "Confirm before power off"
- זמן קירור תלוי במודל (בדרך כלל 60-90 שניות)

---

### כיצד מחליפים מקור קלט (HDMI, VGA)?

**שלבים:**
1. לחץ על כפתור התפריט הנפתח **"מקור קלט"** (Input Source)
2. רשימת קלטים זמינים תופיע:
   - HDMI1, HDMI2 (קלטים דיגיטליים)
   - VGA (קלט אנלוגי)
   - Component, Network (תלוי במקרן)
3. בחר את הקלט הרצוי
4. המקרן עובר לקלט החדש (2-5 שניות)
5. לוח הסטטוס מתעדכן: "קלט: HDMI1"

**שים לב:**
- הקלטים הזמינים תלויים במודל המקרן שלך
- אם קלט חסר, המקרן שלך לא תומך בו
- קלטים לא מחוברים עשויים להופיע אך יכשלו בעת בחירה

---

### כיצד משתמשים במגש המערכת (System Tray)?

**מזעור למגש המערכת:**
1. לחץ על כפתור **מזעור** בחלון הראשי
2. החלון נעלם והסמל עובר למגש (תחתית ימין)
3. הודעה מאשרת שהוא עדיין פועל

**בקרת הפעלה מהירה מהמגש:**
1. לחץ **ימין** על סמל המגש 📽️
2. תפריט מופיע עם פעולות מהירות:
   - **הפעלה** (Power On)
   - **כיבוי** (Power Off)
   - **השחרת מסך** (Blank Screen)
   - **הצג חלון ראשי** (Show Main Window)
   - **הגדרות** (Settings)
   - **יציאה** (Exit)
3. בחר פעולה - היא מתבצעת ברקע
4. הודעה מאשרת הצלחה

**צפייה בסטטוס מהמגש:**
- רחף עם העכבר מעל סמל המגש
- טול-טיפ מופיע עם:
  - שם המקרן
  - מצב הפעלה
  - קלט נוכחי

**שחזור החלון:**
- **לחיצה כפולה** על סמל המגש
- או: לחץ ימין > "הצג חלון ראשי"

> **טיפ:** השאר את היישום פועל במגש המערכת לגישה מיידית לאורך היום!

---

### מה עושה כפתור "השחרת מסך" (Blank Screen)?

**מה זה עושה:**
- משחיר מיד את התמונה המוקרנת לשחור
- המקרן נשאר דלוק (לא כמו כיבוי)
- המחשב שלך ממשיך לעדכן כרגיל
- השמע ממשיך (אם מופעל)

**מתי להשתמש:**
- להסתיר תוכן רגיש זמנית במהלך מצגת
- השהייה בין קטעי מצגת
- שמור על ריכוז הקהל במהלך דיונים

**שלבים:**
1. לחץ על כפתור **"השחרת מסך"** (Blank Screen, צהוב)
2. המסך המוקרן מיד שחור
3. הכפתור משתנה ל-**"ביטול השחרה"** (Unblank Screen)
4. לחץ שוב כדי לשחזר את התמונה

**טיפ:** השחרת מסך מהירה יותר מכיבוי והדלקה מחדש. השתמש בזה להשהיות קצרות.

---

### כיצד צופים בהיסטוריית פעולות?

**מיקום:**
- פאנל ההיסטוריה בצד ימין של החלון הראשי

**מה מוצג:**
- כל פעולה עם:
  - **זמן** - מתי בוצעה (HH:MM:SS)
  - **סמל** - סוג פעולה (🔌 הפעלה, 📺 קלט, ⚪ השחרה, וכו')
  - **פעולה** - מה בוצע
  - **סטטוס** - הצלחה ✓ או כישלון ✗

**שימוש:**
- **גלול** לראות ערכים ישנים יותר
- **רחף** מעל ערך לפרטים נוספים
- **לחץ ימין** לאפשרויות:
  - העתק פרטים
  - הצג הודעה מלאה (עבור כישלונות)
  - נקה ערך זה
  - נקה כל ההיסטוריה
  - ייצא היסטוריה

**פענוח ערכים:**
- ✓ **הצלחה (סימון ירוק)** - הפעולה הושלמה בהצלחה
- ✗ **כישלון (X אדום)** - הפעולה נכשלה - לחץ לראות פרטי שגיאה

**טיפ:** אם אתה רואה דפוסים של כישלונות (למשל, "החלפת קלט" תמיד נכשלת), זה מצביע על בעיית תאימות עם המקרן שלך.

---

### כיצד מבדקים את החיבור למקרן?

**באופן ידני:**
1. פתח **Settings** (⚙️)
2. עבור ל-**Connection** tab
3. לחץ **"Test Connection Now"**
4. המתן מספר שניות לתוצאות

**בדיקה מוצלחת מציגה:**
- ✓ סטטוס חיבור
- זמן תגובה (ping)
- שם דגם המקרן
- גרסת קושחה
- חותמת זמן של בדיקה אחרונה

**בדיקה שנכשלה מציגה:**
- ✗ שגיאת חיבור
- הודעת שגיאה (timeout, refused, וכו')
- הצעות אבחון
- קישור לפתרון בעיות

**מתי להריץ בדיקה:**
- אם אתה מבחין בזמני תגובה איטיים
- לפני מצגות חשובות
- אם רואה כישלונות תכופים בפאנל ההיסטוריה

---

## 4. פתרון בעיות

### "לא ניתן להתחבר למקרן" - מה לעשות?

**אבחון שלב-אחר-שלב:**

**שלב 1: בדוק קישוריות רשת**
```cmd
פתח Command Prompt (Win+R, הקלד "cmd", לחץ Enter)
הקלד: ping 192.168.1.100
לחץ Enter
```
- **הצלחה:** "Reply from 192.168.1.100..." → הרשת עובדת, דלג לשלב 3
- **כישלון:** "Request timed out" → בעיית רשת, המשך לשלב 2

**שלב 2: בדוק חיבור רשת**
- האם המחשב שלך מחובר לרשת? (בדוק אינדיקטור Wi-Fi או Ethernet)
- האם המקרן דלוק? (בדוק פיזית)
- האם אתה באותה רשת כמו המקרן? (VPN יכול לגרום לבעיות)

**שלב 3: אמת כתובת IP של המקרן**
- אשר את כתובת ה-IP עם מנהל IT
- בדוק אם כתובת ה-IP השתנתה (חכירת DHCP פגה)
- נסה את התפריט הפיזי של המקרן לאמת הגדרות רשת

**שלב 4: בדוק חומת אש**
- חומת האש של Windows עשויה לחסום פורט TCP 4352
- השבת זמנית את חומת האש לבדיקה (הפעל מחדש לאחר הבדיקה!)
- צור קשר עם IT להוסיף חריגת חומת אש לפורט 4352

**שלב 5: בדוק פרוטוקול PJLink**
- Settings > Connection > Test Connection Now
- אם הבדיקה נכשלת, בדוק הודעת שגיאה לסיבת כישלון ספציפית

---

### פקודות איטיות (>10 שניות) - איך לתקן?

**אבחון:**
- בדוק חותמות זמן בפאנל ההיסטוריה
- שים לב לזמן בין לחיצה להצלחה/כישלון

**סיבות נפוצות:**
- חביון רשת (Wi-Fi, VPN, עומס)
- מקרן איטי להגיב (קושחה ישנה)
- Timeout מוגדר גבוה מדי

**פתרונות:**

**1. הגדל timeout של פקודה:**
- Settings > Connection > Command Timeout ל-15 שניות
- נותן למקרן יותר זמן להגיב

**2. הקטן ניסיונות חוזרים:**
- Settings > Connection > Retry attempts ל-1
- נכשל מהר במקום לנסות שוב

**3. בדוק חביון רשת:**
- Settings > Diagnostics > Run Network Test
- בדוק זמן ping

**4. השתמש ב-Ethernet חוטי:**
- מבטל חביון Wi-Fi
- חיבור יציב ומהיר יותר

---

### "אימות נכשל" בעת התחברות למקרן

**אבחון:**
- הודעת שגיאה: "Authentication failed" או "Invalid password"
- החיבור אחרת מוצלח (ping עובד, פורט נגיש)

**סיבות:**
- סיסמה שגויה הוזנה בהגדרות
- סיסמה השתנתה במקרן אך לא עודכנה ביישום
- קובץ entropy חסר (לא יכול לפענח סיסמה מאוחסנת)

**פתרונות:**

**1. הזן מחדש סיסמה:**
- Settings > Connection > Edit (מקרן)
- הזן סיסמה בשדה "Password"
- לחץ Test Connection לאימות
- לחץ Save

**2. אמת סיסמה עם IT:**
- אשר סיסמה נכונה עם מנהל
- ייתכן שסיסמת המקרן השתנתה

**3. בדוק שקובץ entropy קיים:**
- מיקום: `%APPDATA%\ProjectorControl\.projector_entropy`
- אם חסר: לא ניתן לפענח סיסמה, חייב להזין מחדש את כל סיסמאות המקרנים

---

### היישום לוקח >5 שניות להפעיל

**אבחון:**
- מדוד זמן אמיתי באמצעות שעון עצר
- השווה ליעד: <2 שניות

**סיבות נפוצות:**
- זמן הפעלה כולל זמן חיבור רשת
- רזולוציית DNS איטית ברשת
- פיצול קובץ מסד נתונים (מצב SQLite)
- אנטי וירוס סורק קובץ EXE בכל הפעלה

**פתרונות:**

**1. השבת בדיקת רשת בהפעלה:**
- Settings > Connection > בטל סימון "Connect to projectors on startup"

**2. הוצא מאנטי וירוס:**
- הוסף `ProjectorControl.exe` לרשימת החרגות אנטי וירוס (שאל IT)

**3. השתמש ברשת חוטית:**
- חיפושי DNS של Wi-Fi יכולים להיות איטיים

**4. דחוס מסד נתונים:**
- Settings > Advanced > Maintenance > Compact Database (אם זמין)

---

### שכחתי את סיסמת המנהל

**למרבה הצער, אין אפשרות שחזור.**

**האפשרויות שלך:**

**1. אם יש לך גיבוי:**
- שחזר מקובץ גיבוי (כולל סיסמת מנהל)

**2. אם אין גיבוי:**
- חייב להתקין מחדש:
  1. סגור את היישום
  2. מחק: `%APPDATA%\ProjectorControl\`
  3. מחק: `%APPDATA%\ProjectorControl\.projector_entropy`
  4. הפעל את היישום - אשף הפעלה ראשון מתחיל
  5. צור סיסמה חדשה
  6. הגדר מחדש את כל המקרנים

**למניעה:**
- כתוב את סיסמת המנהל במקום בטוח
- שקול מנהל סיסמאות
- צור גיבויים באופן קבוע

---

### החלון נמצא מחוץ למסך (לא נראה)

**נפוץ לאחר:**
- ניתוק מסך חיצוני
- שינוי רזולוציית תצוגה
- מעבר מתחנת עגינה למסך מחשב נייד

**תיקון מהיר:**

**אפשרות 1: דרך הגדרות**
- Settings > Diagnostics > Reset Window Position

**אפשרות 2: דרך מקלדת**
1. לחץ על היישום בשורת המשימות כדי לבחור אותו
2. לחץ `Alt+Space`
3. לחץ `M` (Move)
4. השתמש במקשי החצים כדי להזיז את החלון
5. לחץ `Enter` כאשר נראה

---

### טקסט עברי מוצג בצורה שגויה (בעיות RTL)

**אבחון:**
- טקסט עברי מופיע אך הפריסה שגויה
- טקסט מיושר בכיוון הלא נכון
- סמלים לא משתקפים

**פתרונות:**

**1. בדוק בחירת שפה:**
- Settings > General > Language > בחר "עברית (Hebrew)"

**2. הפעל מחדש את היישום:**
- סגור ופתח מחדש כדי להחיל מחדש פריסת RTL

**3. אמת חבילת שפה של Windows:**
- Windows Settings > Time & Language > Language
- הוסף עברית אם חסר

**4. אם נמשך:**
- דווח על באג עם צילום מסך (ראה [FAQ](FAQ.he.md))

---

### קבלת עזרה

אם ניסית את שלבי פתרון הבעיות למעלה ועדיין יש בעיות:

**1. בדוק את ה-FAQ**
- קרא את [FAQ.md](FAQ.he.md) לתשובות מהירות

**2. אסוף מידע אבחון:**
- Settings > Diagnostics > Export Diagnostic Report
- שולח קובץ עם כל מידע המערכת, לוגים, ותצורה

**3. בדוק לוגים של יישום:**
- Settings > Advanced > Logging > Open Log Folder
- הסתכל על קובץ `.log` העדכני ביותר
- חפש ערכי "ERROR" או "FAIL"

**4. צור קשר עם מנהל IT:**
- ספק דוח אבחון (משלב 2)
- תאר מה עשית כשהבעיה התרחשה
- כלול צילומי מסך אם רלוונטי

---

## 5. פריסה ארגונית (למנהלי IT)

### כיצד פורסים ל-מחשבים מרובים?

**סקירה כללית:**
- היישום הוא קובץ EXE יחיד - פשוט להפצה
- תומך בשני מצבי פריסה: Standalone ו-Enterprise
- אין תלויות של installer או registry

**שיטות פריסה:**

**1. שרת קבצים משותף:**
```powershell
# העתק EXE לשרת קבצים
Copy-Item "ProjectorControl.exe" "\\fileserver\software\ProjectorControl\"

# יצור קיצור דרך בתיקיית Startup של משתמשים
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\ProjectorControl.lnk")
$Shortcut.TargetPath = "\\fileserver\software\ProjectorControl\ProjectorControl.exe"
$Shortcut.Save()
```

**2. Group Policy (GPO):**
- יצור GPO חדש: Computer Configuration > Policies > Software Settings
- הקצה את `ProjectorControl.exe` כחבילת תוכנה
- העתק לתיקיית SYSVOL
- המחשבים מתקינים בהפעלה הבאה

**3. SCCM/Intune:**
- ארוז `ProjectorControl.exe` כאפליקציה
- צור פקודת התקנה: `copy ProjectorControl.exe "%ProgramFiles%\ProjectorControl\"`
- יעד למכשירים או קבוצות משתמשים

**4. סקריפט PowerShell מרחוק:**
```powershell
function Deploy-ToComputer {
    param([string]$ComputerName)

    $session = New-PSSession -ComputerName $ComputerName
    Copy-Item "ProjectorControl.exe" -Destination "C:\Program Files\ProjectorControl\" -ToSession $session
    Invoke-Command -Session $session -ScriptBlock {
        $WshShell = New-Object -ComObject WScript.Shell
        $Shortcut = $WshShell.CreateShortcut("C:\ProgramData\Microsoft\Windows\Start Menu\Programs\ProjectorControl.lnk")
        $Shortcut.TargetPath = "C:\Program Files\ProjectorControl\ProjectorControl.exe"
        $Shortcut.Save()
    }
    Remove-PSSession $session
}

# פרוס ל-מחשבים מרובים
$computers = Get-Content "computers.txt"
$computers | ForEach-Object { Deploy-ToComputer -ComputerName $_ }
```

**אתחול ראשוני מרכזי (אופציונלי):**
- הגדר מחשב אחד עם כל תצורות המקרנים
- צור גיבוי: Settings > Backup > Create Backup
- העתק קובץ גיבוי + entropy file למחשבים אחרים
- שחזר בכל מחשב: Settings > Backup > Restore from Backup

> **עבור פריסה ארגונית מלאה, ראה [מדריך פריסה](deployment/DEPLOYMENT_GUIDE.he.md)**

---

### כיצד מגדירים SQL Server עבור מצב Enterprise?

**דרישות SQL Server:**
- SQL Server 2016+ (כל מהדורה: Express, Standard, Enterprise)
- SQL Server Authentication או Windows Authentication
- גישת רשת לשרת SQL (פורט 1433)

**תהליך הגדרה:**

**שלב 1: צור מסד נתונים**
```sql
-- התחבר ל-SQL Server כ-sa או sysadmin
CREATE DATABASE ProjectorControl
    COLLATE SQL_Latin1_General_CP1_CI_AS;
GO

USE ProjectorControl;
GO
```

**שלב 2: צור משתמש יישום (SQL Authentication)**
```sql
-- צור login ברמת שרת
CREATE LOGIN projector_app_user
    WITH PASSWORD = 'YourSecurePassword123!';
GO

-- צור משתמש במסד הנתונים
USE ProjectorControl;
CREATE USER projector_app_user FOR LOGIN projector_app_user;
GO

-- הענק הרשאות
ALTER ROLE db_datareader ADD MEMBER projector_app_user;
ALTER ROLE db_datawriter ADD MEMBER projector_app_user;
ALTER ROLE db_ddladmin ADD MEMBER projector_app_user;  -- עבור migrations
GO
```

**שלב 3 (חלופי): השתמש ב-Windows Authentication**
```sql
-- צור login עבור קבוצת משתמשי Windows
CREATE LOGIN [DOMAIN\ProjectorUsers] FROM WINDOWS;
GO

USE ProjectorControl;
CREATE USER [DOMAIN\ProjectorUsers] FOR LOGIN [DOMAIN\ProjectorUsers];
GO

-- הענק הרשאות
ALTER ROLE db_datareader ADD MEMBER [DOMAIN\ProjectorUsers];
ALTER ROLE db_datawriter ADD MEMBER [DOMAIN\ProjectorUsers];
ALTER ROLE db_ddladmin ADD MEMBER [DOMAIN\ProjectorUsers];
GO
```

**שלב 4: בדוק קישוריות**
```powershell
# בדוק חיבור מתחנת עבודת לקוח
Test-NetConnection -ComputerName "sqlserver.domain.local" -Port 1433
```

**שלב 5: הגדר לקוחות**
- הפעל `ProjectorControl.exe` בתחנת עבודה
- אשף הפעלה ראשון > שלב 3: בחר **Enterprise (SQL Server)**
- הזן פרטי חיבור:
  - **שרת**: `sqlserver.domain.local` או כתובת IP
  - **מסד נתונים**: `ProjectorControl`
  - **אימות**: SQL Server או Windows
  - **שם משתמש/סיסמה**: (עבור SQL Auth)
- בדוק חיבור
- השלם את האשף

> **עבור תהליך מפורט, ראה [מדריך פריסה - SQL Server](deployment/DEPLOYMENT_GUIDE.he.md#5-sql-server-preparation)**

---

### כמה חיבורים במקביל תומך מצב Enterprise?

**SQL Server מצב Enterprise תומך ב-חיבורים במקביל ללא הגבלה.**

**ארכיטקטורת חיבור:**
- כל לקוח שומר על connection pool משלו (5 חיבורים כברירת מחדל)
- SQL Server מטפל במספר לקוחות באמצעות ריבוי משימות
- אין נעילת רשומות - עיצוב ללא התנגשויות

**בדיקות ביצועים:**
- **10 לקוחות במקביל**: אין ירידה בביצועים
- **50 לקוחות במקביל**: <5% overhead
- **100+ לקוחות**: שקול אופטימיזציות SQL Server

**שיקולים:**
- **גודל connection pool**: Settings > Advanced > Connection Pool Size (ברירת מחדל: 5)
- **פסי רוחב רשת**: כל לקוח שולח פקודות PJLink + שאילתות SQL
- **משאבי SQL Server**: RAM, CPU, חיבורים מקס (תלוי במהדורה)

**מגבלות SQL Server Edition:**
- **Express**: מקס 1 GB RAM, 10 GB DB, אין מגבלת חיבורים קשה
- **Standard**: 128 GB RAM, 524 PB DB, 32,767 חיבורים מקס
- **Enterprise**: ללא הגבלה (תלוי בחומרה)

**המלצות:**
- **<20 לקוחות**: SQL Server Express מספיק
- **20-100 לקוחות**: SQL Server Standard
- **100+ לקוחות**: שקול SQL Server Enterprise + ניטור ביצועים

---

### כיצד מעבירים מ-Standalone ל-Enterprise?

**תהליך העברה:**

**שלב 1: צור גיבוי במחשב Standalone**
1. פתח את היישום במצב Standalone
2. Settings > Backup > Create Backup
3. שמור את `backup.enc`
4. העתק גם את `%APPDATA%\ProjectorControl\.projector_entropy`

**שלב 2: הגדר SQL Server**
- עקוב אחר [הוראות הגדרת SQL Server](#כיצד-מגדירים-sql-server-עבור-מצב-enterprise)
- צור מסד נתונים `ProjectorControl`
- הגדר משתמש יישום עם הרשאות

**שלב 3: שחזר גיבוי ל-SQL Server**
1. התקן את היישום במחשב עם גישת SQL
2. אשף הפעלה ראשון > בחר **Enterprise (SQL Server)**
3. הזן פרטי חיבור SQL Server
4. לאחר התחברות:
   - Settings > Backup > Restore from Backup
   - בחר `backup.enc` מהגדרות Standalone
   - הזן סיסמת מנהל מההגדרה המקורית
5. תצורות מקרנים נטענות אוטומטית ל-SQL Server

**שלב 4: פרוס למחשבים נוספים**
- התקן `ProjectorControl.exe` בכל המחשבים
- בחר **Enterprise (SQL Server)** באשף הפעלה ראשון
- הזן אותם פרטי חיבור SQL
- כל התצורות זמינות מיד (שיתוף מרכזי)

**הערות:**
- **קובץ Entropy** עדיין נדרש על כל מחשב (להצפנת DPAPI)
- **סיסמת מנהל** נקבעת בנפרד בכל מחשב (לא משותפת)
- **תצורות מקרנים** משותפות בכל המחשבים (SQL Server)

---

### האם Windows Authentication תומך במצב Enterprise?

**כן.** מצב Enterprise תומך הן ב-SQL Server Authentication והן ב-Windows Authentication.

**Windows Authentication (מומלץ):**

**יתרונות:**
- אין סיסמאות לאחסן ביישום
- Single Sign-On (SSO) - משתמשים מאומתים אוטומטית
- אבטחה משופרת (Kerberos)
- ניהול מרכזי דרך Active Directory

**דרישות:**
- SQL Server באותו domain או domain מהימן
- חשבון מחשב/משתמש צריך גישה ל-SQL Server
- יציאות Kerberos (88, 464) פתוחות

**הגדרה:**

**1. SQL Server - צור login עבור קבוצת domain:**
```sql
CREATE LOGIN [DOMAIN\ProjectorUsers] FROM WINDOWS;
GO

USE ProjectorControl;
CREATE USER [DOMAIN\ProjectorUsers] FOR LOGIN [DOMAIN\ProjectorUsers];
GO

ALTER ROLE db_datareader ADD MEMBER [DOMAIN\ProjectorUsers];
ALTER ROLE db_datawriter ADD MEMBER [DOMAIN\ProjectorUsers];
ALTER ROLE db_ddladmin ADD MEMBER [DOMAIN\ProjectorUsers];
GO
```

**2. Active Directory - הוסף משתמשים לקבוצה:**
- צור קבוצה: `DOMAIN\ProjectorUsers`
- הוסף חשבונות משתמשים או מחשבים

**3. לקוח - בחר Windows Authentication:**
- אשף הפעלה ראשון > Enterprise (SQL Server)
- סוג אימות: **Windows Authentication**
- אין להזין שם משתמש/סיסמה
- לחץ Test Connection

**SQL Authentication (חלופה):**
- דורש שם משתמש/סיסמה
- סיסמה מאוחסנת מוצפנת (DPAPI + entropy file)
- שימושי עבור חשבונות שאינם domain

---

### כיצד עוקבים אחר שימוש ומעקב אחר ביקורת?

**מצב Standalone - ביקורת מקומית:**
- **לוגי יישום**: `%APPDATA%\ProjectorControl\logs\app.log`
- **היסטוריית פעולות**: `projector_control.db` טבלת `operation_history`
- **שאילתה SQL**:
  ```sql
  SELECT timestamp, operation, projector_name, status, error_message
  FROM operation_history
  ORDER BY timestamp DESC
  LIMIT 100;
  ```

**מצב Enterprise - ביקורת מרכזית:**

**1. שאילתת SQL Server ישירה:**
```sql
-- חבר ל-SQL Server כ-sysadmin
USE ProjectorControl;
GO

-- 100 הפעולות האחרונות
SELECT TOP 100
    oh.timestamp,
    oh.operation,
    pc.projector_name,
    oh.status,
    oh.error_message,
    oh.user_id,  -- אם מיושם
    oh.computer_name  -- אם מיושם
FROM operation_history oh
INNER JOIN projector_config pc ON oh.projector_id = pc.id
ORDER BY oh.timestamp DESC;

-- פעולות כושלות 7 הימים האחרונים
SELECT
    oh.timestamp,
    oh.operation,
    pc.projector_name,
    oh.error_message
FROM operation_history oh
INNER JOIN projector_config pc ON oh.projector_id = pc.id
WHERE oh.status = 'Failed'
    AND oh.timestamp >= DATEADD(day, -7, GETDATE())
ORDER BY oh.timestamp DESC;
```

**2. ביקורת ברמת SQL Server (Advanced):**
```sql
-- הפעל SQL Server Audit
CREATE SERVER AUDIT ProjectorControlAudit
TO FILE (FILEPATH = 'D:\SQLAudit\', MAXSIZE = 100 MB)
WITH (ON_FAILURE = CONTINUE);
GO

ALTER SERVER AUDIT ProjectorControlAudit WITH (STATE = ON);
GO

-- בצע ביקורת על פעולות מסד נתונים
USE ProjectorControl;
GO

CREATE DATABASE AUDIT SPECIFICATION ProjectorControlDB_Audit
FOR SERVER AUDIT ProjectorControlAudit
ADD (INSERT, UPDATE, DELETE ON DATABASE::ProjectorControl BY [public])
WITH (STATE = ON);
GO
```

**3. ניטור עם Power BI/Excel:**
- התחבר ל-SQL Server מ-Power BI
- שאול טבלת `operation_history`
- צור דשבורדים עבור:
  - שימוש במקרנים לאורך זמן
  - שיעורי כישלון לפי מקרן
  - חיבורים מקסימליים במקביל
  - זמני תגובה ממוצעים

---

### האם ניתן לשלב עם Active Directory לניהול משתמשים?

**כרגע, לא ישירות.** היישום אינו מתממשק עם AD עבור ניהול משתמשים.

**מה תומך:**
- **Windows Authentication** עבור חיבור SQL Server (Single Sign-On)
- **הרשאות מבוססות קבוצות** דרך קבוצות AD ל-SQL Server

**מה לא תומך:**
- הרשאות ברמת תכונות מבוססות תפקיד AD (למשל, "רק מורים יכולים לכבות")
- כניסת משתמש AD ליישום עצמו (רק סיסמת מנהל מקומית)

**פתרונות:**

**אפשרות 1: הרשאות SQL Server דרך קבוצות AD**
```sql
-- צור קבוצות AD שונות
CREATE LOGIN [DOMAIN\ProjectorAdmins] FROM WINDOWS;  -- מנהלים מלאים
CREATE LOGIN [DOMAIN\ProjectorUsers] FROM WINDOWS;   -- משתמשים רגילים (קריאה בלבד)

-- הענק הרשאות שונות
USE ProjectorControl;

-- מנהלים - מלא
GRANT SELECT, INSERT, UPDATE, DELETE ON SCHEMA::dbo TO [DOMAIN\ProjectorAdmins];

-- משתמשים - קריאה בלבד
GRANT SELECT ON SCHEMA::dbo TO [DOMAIN\ProjectorUsers];
```
**מגבלה:** אכיפה ברמת מסד נתונים, לא ברמת UI

**אפשרות 2: Group Policy להגבלת גישה**
- השתמש ב-GPO כדי להגביל מי יכול להפעיל את `ProjectorControl.exe`
- או: פרוס רק למשתמשים מורשים דרך SCCM/Intune

**בקשות עתידיות:**
- שקול שילוב מלא של AD/LDAP עבור ניהול משתמשים מבוסס תפקידים
- צור קשר עם מפתחים להצעות תכונות

---

## 6. אבטחה ואישורים

### כיצד סיסמאות מאוחסנות?

**היישום משתמש באבטחה רב-שכבתית:**

**סיסמת מנהל:**
- **bcrypt hashing** עם cost factor 14 (2^14 = 16,384 איטרציות)
- לא נשמרת ולא ניתנת לפענוח - רק אימות hash
- מאוחסנת ב-`projector_control.db` טבלת `admin_config`
- חד-כיוונית - אין אפשרות שחזור

**סיסמאות מקרנים:**
- **Windows DPAPI (Data Protection API)** הצפנה
- מצריך קובץ **entropy** (`.projector_entropy`) לפענוח
- התלות במשתמש + מחשב - לא ניתן לפענוח במכשיר אחר ללא קובץ entropy
- מאוחסנת מוצפנת ב-`projector_control.db` או SQL Server

**קבצי גיבוי:**
- **AES-256-GCM** הצפנה
- הצפנה מבוססת סיסמה (PBKDF2-HMAC-SHA256, 100,000 איטרציות)
- מוגן הן על ידי סיסמת מנהל והן על ידי קובץ entropy

---

### מדוע קובץ ה-entropy קריטי?

**קובץ ה-entropy (`.projector_entropy`) הוא CRITICAL** להצפנה ולפענוח.

**מה זה עושה:**
- נתונים אקראיים בני 256 ביטים המשמשים כ-"מלח" עבור הצפנת DPAPI
- מייחד הצפנה למחשב ולמשתמש ספציפיים
- נוצר אוטומטית בהפעלה ראשונה

**מדוע זה קריטי:**
- ללא זה, **סיסמאות מקרן מוצפנות אינן ניתנות לפענוח**
- התקנת Windows מחדש → entropy file אובד → סיסמאות אבודות
- מעבר למחשב חדש → חייב להעתיק entropy file

**היכן הוא נמצא:**
```
%APPDATA%\ProjectorControl\.projector_entropy
```
בדרך כלל: `C:\Users\YourName\AppData\Roaming\ProjectorControl\.projector_entropy`

**גיבוי עד כמה חשוב:**

**תרחישי אובדן:**
1. **התקנת Windows מחדש** → entropy file נמחק
2. **כשל דיסק קשיח** → entropy file אובד
3. **הסרה בטעות** → entropy file נמחק
4. **מעבר למחשב חדש** → entropy file לא מועבר

**תוצאות:**
- לא ניתן לפענח **שום** סיסמת מקרן
- חייב להזין מחדש את **כל** סיסמאות המקרנים ידנית
- קבצי גיבוי חסרי תועלת (מוצפנים עם אותו entropy)

**שיטות עבודה מומלצות לגיבוי:**
1. **גבה קבוע:**
   ```powershell
   # העתק ל-network share
   Copy-Item "$env:APPDATA\ProjectorControl\.projector_entropy" "\\fileserver\backups\ProjectorControl\"
   ```

2. **כלול בגיבויי מערכת:**
   - ודא שכלי הגיבוי שלך כולל `%APPDATA%`
   - בדוק ש-`.projector_entropy` כלול

3. **אחסן בטוח:**
   - שמור עותקים ב-מספר מיקומים
   - אבטחה פיזית (USB בכספת, cloud encrypted)

> **אזהרה:** טפל בקובץ entropy כמו סיסמת אב - כל מי שיש לו גישה אליו + ל-מסד הנתונים המוצפן יכול לפענח סיסמאות!

---

### האם היישום מועד לניצול או פרצות אבטחה?

**היישום עוצב עם אבטחה כעדיפות עליונה.**

**מדדי אבטחה:**
- **0 פרצות קריטיות/גבוהות** ביציאת v2.0
- **ביקורת קוד** על ידי מומחי אבטחה (צוות פנימי)
- **תלות:** כל הספריות עדכניות (2026-02)

**מאפייני אבטחה:**

**1. מניעת SQL Injection:**
- **100%** שאילתות SQL משתמשות בפרמטרים
- אף שאילתה לא משתמשת ב-f-strings או concatenation
- בדיקות אוטומטיות עבור SQL injection patterns

**2. הצפנת סיסמאות:**
- **bcrypt** (cost 14) לסיסמת מנהל
- **Windows DPAPI** לסיסמאות מקרנים
- **AES-256-GCM** לגיבויים
- אין סיסמאות בטקסט פשוט בזיכרון (נמחקות מיד)

**3. אימות קלט:**
- כתובות IP מאומתות (regex + ספרייה `ipaddress` של Python)
- פורטים מאומתים (טווח 1-65535)
- נתיבי קבצים מנותקים (למנוע path traversal)

**4. הקשחת רשת:**
- תקשורת PJLink מוצפנת באופן אופציונלי (אם הפרוטוקול תומך)
- timeout קבועים (למנוע DoS)
- Circuit breaker למניעת מכות כושלות חוזרות

**5. לוגים מאובטחים:**
- סיסמאות אף פעם לא נרשמות בלוגים (redacted)
- כתובות IP מטושטשות (3 octets אחרונים masked)
- הודעות שגיאה לא חושפות מבנה מערכת פנימי

**פרצות ידועות:**
- **אף אחת** נכון לגרסה 2.0.0-rc2

**דיווח על פרצות:**
- ראה [SECURITY.md](../../SECURITY.md) להנחיות גילוי אחראי
- אל תגלה פומבי - דווח בפרטיות למפתחים

---

### כיצד מגבים בצורה מאובטחת את תצורות המקרנים?

**מצב Standalone - גיבוי ידני:**

**שלב 1: צור גיבוי מוצפן**
1. פתח **Settings > Backup > Create Backup**
2. בחר מיקום לשמור: `backup-YYYY-MM-DD.enc`
3. הזן סיסמת מנהל לאימות
4. היישום יוצר גיבוי מוצפן AES-256-GCM

**שלב 2: גבה את קובץ ה-entropy (קריטי!)**
```powershell
# העתק את קובץ entropy
Copy-Item "$env:APPDATA\ProjectorControl\.projector_entropy" "D:\Backups\ProjectorControl\"
```

**שלב 3: אחסן בצורה מאובטחת**
- **אל תאחסן בטקסט פשוט**
- אפשרויות:
  - **USB מוצפן** ב-כספת פיזית
  - **Network share** עם הרשאות מוגבלות
  - **Cloud storage** (OneDrive, Google Drive מוצפן)
  - **Password manager** (אם תומך בקבצים)

**גיבוי אוטומטי עם PowerShell:**
```powershell
# סקריפט: ProjectorControl-Backup.ps1
$BackupDir = "\\fileserver\backups\ProjectorControl\$env:COMPUTERNAME"
$Date = Get-Date -Format "yyyy-MM-dd"
$SourceDB = "$env:APPDATA\ProjectorControl\projector_control.db"
$SourceEntropy = "$env:APPDATA\ProjectorControl\.projector_entropy"

# צור תיקייה אם לא קיימת
New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null

# העתק קבצים
Copy-Item $SourceDB "$BackupDir\projector_control_$Date.db"
Copy-Item $SourceEntropy "$BackupDir\.projector_entropy"

# שמור רק 30 ימים אחרונים
Get-ChildItem $BackupDir -Filter "*.db" |
    Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } |
    Remove-Item -Force

Write-Host "Backup completed: $BackupDir"
```

**התזמן עם Task Scheduler:**
```powershell
# צור scheduled task (הרץ כמשתמש נוכחי)
$Action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-File C:\Scripts\ProjectorControl-Backup.ps1"
$Trigger = New-ScheduledTaskTrigger -Daily -At 2AM
$Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable
Register-ScheduledTask -TaskName "ProjectorControl Backup" -Action $Action -Trigger $Trigger -Settings $Settings
```

**מצב Enterprise - גיבוי SQL Server:**
- שרת SQL Server מטפל בגיבויים של מסד נתונים
- עדיין גבה את קובץ ה-entropy מכל workstation
- ראה [מדריך פריסה](deployment/DEPLOYMENT_GUIDE.he.md#10-backup-and-disaster-recovery)

---

### מה הסיכונים של הפעלה ברשת לא מאובטחת?

**פרוטוקול PJLink (TCP port 4352) הוא לא מוצפן כברירת מחדל.**

**סיכונים:**

**1. האזנת סתר (Packet Sniffing):**
- **סיכון:** תוקף יכול ללכוד תנועת רשת
- **חשיפה:** פקודות PJLink (הפעלה, כיבוי, החלפת קלט)
- **סיסמאות:** PJLink מוצפן אימות MD5, אך hash יכול להילכד
- **הפחתה:** השתמש ברשת מבודדת (VLAN), אל תשדר דרך רשתות לא מהימנות

**2. התקפת Man-in-the-Middle (MITM):**
- **סיכון:** תוקף יכול ליירט ולשנות פקודות
- **חשיפה:** פקודות לא מורשות נשלחות למקרן
- **הפחתה:** השתמש ברשת מנוטרת, פילטור MAC address על switches

**3. גישה לא מורשית:**
- **סיכון:** כל מי שיכול להגיע לפורט 4352 יכול לשלוט במקרן
- **חשיפה:** כיבוי מקרנים במהלך מצגות, שינוי קלטים
- **הפחתה:** הגדר סיסמת PJLink במקרן, בידוד VLAN

**4. חשיפת אישורים:**
- **סיכון:** במחשב לא מאובטח, קובץ מסד נתונים + entropy → סיסמאות מפוענחות
- **חשיפה:** סיסמאות מקרן משותפות אם מאוחסנות ב-SQL Server לא מאובטח
- **הפחתה:** הצפנת דיסק קשיח (BitLocker), הרשאות קבצים מוגבלות

**שיטות עבודה מומלצות:**

**1. בידוד רשת (מומלץ ביותר):**
```
[מחשבי משתמשים] ---> [VLAN לקוחות: 192.168.1.0/24]
                            |
                    [Firewall/Router]
                            |
                   [VLAN מקרנים: 192.168.50.0/24]
                            |
                       [מקרנים]
```
- מקרנים ברשת נפרדת
- חוקי Firewall מאפשרים רק פורט 4352 מ-VLANs לקוחות
- חסימת תנועה inter-VLAN אחרת

**2. אבטחת מקרן:**
- הגדר סיסמת PJLink על כל המקרנים
- השבת שירותים לא בשימוש (Telnet, HTTP admin)
- עדכן קושחת מקרן באופן קבוע

**3. אבטחת Client:**
- הצפנת דיסק קשיח (BitLocker)
- חומת אש של Windows מופעלת
- הרשאות קבצים מוגבלות על `%APPDATA%\ProjectorControl\`

**4. SQL Server (Enterprise mode):**
- הצפנת חיבור SQL (TLS/SSL)
- Windows Authentication (Kerberos)
- SQL Server Audit מופעל

---

## 7. ביצועים ואיכות

### מהם יעדי הביצועים?

**יישום נבדק מול יעדים אלו:**

| מדד | יעד | תוצאה בפועל | סטטוס |
|------|------|-----------|--------|
| **זמן הפעלה** | <2 שניות | 0.9 שניות | ✅ עבר |
| **זמן ביצוע פקודה** | <5 שניות | 18ms (ממוצע) | ✅ עבר |
| **צריכת זיכרון** | <150 MB | 134 MB (יציבה) | ✅ עבר |
| **כיסוי בדיקות** | >85% | 94%+ | ✅ עבר |
| **פרצות אבטחה** | 0 קריטי/גבוה | 0 | ✅ עבר |

**פרטי ביצועים:**

**זמן הפעלה (0.9 שניות):**
- נמדד מלחיצת EXE עד חלון מוכן
- כולל טעינת PyQt6, חיבור מסד נתונים, טעינת UI
- לא כולל חיבור רשת למקרן (אופציונלי)

**זמן ביצוע פקודה (18ms ממוצע):**
- **חביון מקומי** (click → PJLink שנשלח): 18ms ממוצע
- **חביון רשת** (שנשלח → אישור מקרן): תלוי ברשת (בדרך כלל 50-200ms)
- **סה"כ** (click → אישור): בדרך כלל <500ms

**צריכת זיכרון (134 MB):**
- זיכרון יציב - אין דליפות זיכרון
- PyQt6 + Python runtime: ~80 MB
- נתוני יישום + cache: ~54 MB
- גדל לאט עם היסטוריה (1 MB ל-~10,000 ערכי היסטוריה)

---

### מדוע היישום לוקח >2 שניות להפעיל?

**אם זמן ההפעלה >2 שניות, סיבות אפשריות:**

**1. בדיקת רשת בהפעלה (נפוץ ביותר):**
- ברירת מחדל: היישום מנסה להתחבר למקרנים בהפעלה
- אם המקרן לא זמין → ממתין ל-timeout (5 שניות כברירת מחדל)
- **תיקון:** Settings > Connection > בטל סימון "Connect to projectors on startup"

**2. סריקת אנטי וירוס:**
- אנטי וירוס סורק `ProjectorControl.exe` בכל הפעלה
- יכול להוסיף 1-3 שניות
- **תיקון:** הוסף `ProjectorControl.exe` לרשימת החרגות אנטי וירוס (שאל IT)

**3. פיצול מסד נתונים SQLite:**
- לאחר אלפי ערכי היסטוריה, מסד נתונים מתפצל
- **תיקון:** Settings > Advanced > Maintenance > Compact Database (אם זמין)

**4. דיסק קשיח איטי:**
- HDD מגנטי ישן לעומת SSD
- **תיקון:** שקול SSD, או העבר `%APPDATA%` ל-דיסק מהיר יותר

**5. רזולוציית DNS איטית:**
- אם מצב Enterprise מנסה לפתור hostname של SQL Server
- **תיקון:** השתמש בכתובת IP במקום hostname לחיבור SQL Server

**אבחון:**
```powershell
# מדוד זמן הפעלה
Measure-Command { Start-Process "ProjectorControl.exe" -Wait }
```

**אופטימיזציות:**
- השבת חיבור בהפעלה
- הוצא מאנטי וירוס
- השתמש ב-SSD
- דחוס מסד נתונים מדי חודש

---

### כמה מקרנים יכול יישום אחד לטפל בהם?

**מבחינה טכנית: ללא הגבלה.** אך מגבלות מעשיות:

**מגבלות UI:**
- בורר מקרנים הופך לא יעיל עם >20 מקרנים
- זמני טעינה עולים עם מקרנים רבים (כל מקרן = שאילתת מצב)

**מגבלות ביצועים:**

| מספר מקרנים | זמן טעינה | צריכת זיכרון | מומלץ? |
|------------|------------|--------------|---------|
| 1-5 | <1 שניות | 134 MB | ✅ אידיאלי |
| 5-10 | 1-2 שניות | 140 MB | ✅ טוב |
| 10-20 | 2-4 שניות | 155 MB | ⚠️ מקובל |
| 20-50 | 4-10 שניות | 180 MB | ❌ לא מומלץ |
| 50+ | >10 שניות | >200 MB | ❌ השתמש ביישומים מרובים |

**המלצות:**

**תרחיש 1: מורה/מציג רגיל:**
- **1-3 מקרנים** - אידיאלי
- חדרים שונים שאתה עובד בהם

**תרחיש 2: טכנאי AV:**
- **5-10 מקרנים** - ניהול
- מקרנים מרובים באותו בניין

**תרחיש 3: ניהול מרכז כנסים:**
- **10-20 מקרנים** - מומלץ מקסימום
- שקול שימוש ביישומים נפרדים לכל קומה/אזור

**תרחיש 4: ארגון גדול (>20 מקרנים):**
- **השתמש במצב Enterprise** עם יישומים מרובים
- כל workstation מטפלת בקבוצת משנה של מקרנים
- ניהול מרכזי דרך SQL Server

---

### היישום תומך ב-High DPI / 4K displays?

**כן.** היישום תומך במלוא ב-High DPI ומשתפל אוטומטית.

**תמיכה:**
- **DPI scaling:** 100%-400% (1x-4x)
- **רזולוציות:** 1920x1080 (FHD), 2560x1440 (QHD), 3840x2160 (4K), 5120x2880 (5K)
- **מסכים מרובים:** מיקסים של DPI שונים נתמכים

**כיצד זה עובד:**
- PyQt6 מאתחל DPI awareness בהפעלה
- אלמנטי UI משתפלים אוטומטית
- גופנים, סמלים, ריווח מותאמים לכל DPI

**בעיות נפוצות:**

**בעיה: טקסט מטושטש ב-4K**
- **סיבה:** Windows DPI override לא מוגדר נכון
- **תיקון:**
  1. לחץ ימין על `ProjectorControl.exe` > Properties
  2. Compatibility > Change high DPI settings
  3. סמן "Override high DPI scaling behavior"
  4. בחר "Application"
  5. לחץ OK, הפעל מחדש את היישום

**בעיה: UI קטן מדי ב-100% DPI**
- **סיבה:** Windows DPI נמוך על מסך גדול
- **תיקון:** הגדל Windows DPI scaling (125% או 150%)
  - Settings > Display > Scale and layout

**בעיה: UI ענק על מסך בינוני**
- **סיבה:** Windows DPI מוגדר גבוה מדי
- **תיקון:** הקטן Windows DPI scaling

---

### כיצד מנקים קבצי לוג ישנים?

**מיקום לוגים:**
```
%APPDATA%\ProjectorControl\logs\
├── app.log         (לוג נוכחי)
├── app.log.1       (יום אתמול)
├── app.log.2       (לפני יומיים)
└── app.log.3       (לפני 3 ימים)
```

**רוטציית לוגים אוטומטית:**
- היישום סובב לוגים **יומית** בחצות
- שומר **7 ימים אחרונים** כברירת מחדל
- לוגים ישנים יותר נמחקים אוטומטית

**ניקוי ידני:**

**אפשרות 1: דרך UI**
1. Settings > Advanced > Logging
2. לחץ "Open Log Folder"
3. מחק קבצי `.log.*` ישנים (אל תמחק `app.log` - בשימוש!)

**אפשרות 2: PowerShell**
```powershell
# מחק לוגים ישנים מ-7 ימים
$LogDir = "$env:APPDATA\ProjectorControl\logs"
Get-ChildItem $LogDir -Filter "app.log.*" |
    Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-7) } |
    Remove-Item -Force

Write-Host "Old logs deleted."
```

**אפשרות 3: שינוי תצורת שמירת לוגים**
- **לא זמין כרגע ב-UI**
- שקול בקשת תכונה אם צריך שמירה ארוכה יותר

**גודל לוג:**
- **רמת Info** (ברירת מחדל): ~1-5 MB ליום
- **רמת Debug**: ~10-50 MB ליום
- 7 ימים ברמת Info: ~10-35 MB סה"כ

**טיפ:** אם אתה צריך לוגים לזמן ארוך (ביקורת/תאימות), העתק לוגים למיקום ארכיון מדי שבוע.

---

### כמה מסד הנתונים יכול לגדול?

**מצב Standalone (SQLite):**

**גודל בסיס:**
- מסד נתונים ריק: **~50 KB**
- עם 1 מקרן מוגדר: **~100 KB**
- עם 10 מקרנים מוגדרים: **~500 KB**

**גידול לאורך זמן:**
- **ערך היסטוריה**: ~200 bytes לערך
- **10 פעולות ליום**: ~2 KB ליום = ~730 KB לשנה
- **100 פעולות ליום**: ~20 KB ליום = ~7 MB לשנה

**דוגמאות:**
- **שימוש קל** (5 פעולות/יום, שנה אחת): ~150 KB
- **שימוש בינוני** (50 פעולות/יום, שנה אחת): ~3.5 MB
- **שימוש כבד** (200 פעולות/יום, 3 שנים): ~40 MB

**מגבלות SQLite:**
- **מקס גודל DB**: 281 TB (תאורטי) - מעולם לא יגיע
- **מגבלה מעשית**: <1 GB עבור ביצועים טובים
- ב->10 GB, שקול ניקוי היסטוריה או העברה ל-Enterprise

**אופטימיזציה:**

**ניקוי היסטוריה ישנה:**
- **ידני**: Settings > Diagnostics > Clear History Cache
- **SQL ידני**:
  ```sql
  -- מחק היסטוריה ישנה מ->365 ימים
  DELETE FROM operation_history
  WHERE timestamp < datetime('now', '-365 days');

  -- דחוס מסד נתונים
  VACUUM;
  ```

**מצב Enterprise (SQL Server):**
- אין מגבלת גודל מעשית
- SQL Server מטפל באופטימיזציה
- שקול ארכיון היסטוריה אחרי שנה לטבלה נפרדת

---

**סיום שאלות נפוצות (FAQ)**

לתיעוד נוסף:
- **[מדריך משתמש](user-guide/USER_GUIDE.he.md)** - הנחיות שלב-אחר-שלב לשימוש יומיומי
- **[מדריך פריסה](deployment/DEPLOYMENT_GUIDE.he.md)** - למנהלי IT
- **[README](../../README.md)** - מפרט טכני
- **[תיעוד אבטחה](../../SECURITY.md)** - ארכיטקטורת אבטחה

*FAQ גרסה 1.0*
*עודכן לאחרונה: 12 בפברואר 2026*
*תואם ל-Enhanced Projector Control Application v2.0.0-rc2 ואילך*
