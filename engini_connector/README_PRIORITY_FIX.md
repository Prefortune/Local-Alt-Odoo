# פתרון בעיית השדות החסרים של פריורטי

## הבעיה
השגיאה מראה שהשדות החדשים של פריורטי לא קיימים במסד הנתונים:
```
ERROR: column res_partner.priority_custname does not exist
```

## הסיבה
השדות החדשים הוגדרו במודל `priority_customers.py` אבל לא נוצרו במסד הנתונים.

## הפתרון
יש כמה דרכים לפתור את הבעיה:

### דרך 1: עדכון המודול (מומלץ)
1. היכנסו ל-Odoo
2. לכו ל-Apps > Update Apps List
3. חפשו את המודול "Engini Connector"
4. לחצו על "Upgrade" או "Update"

### דרך 2: הרצת Migration ידנית
אם עדכון המודול לא עובד, הרצו את הסקריפט הבא במסד הנתונים:

```sql
-- הרצה ישירה במסד הנתונים PostgreSQL
\i /path/to/migration_priority_fields.sql
```

### דרך 3: יצירת השדות ידנית
הרצו את הפקודות הבאות במסד הנתונים:

```sql
-- הוספת השדות הבסיסיים
ALTER TABLE res_partner ADD COLUMN IF NOT EXISTS priority_custname VARCHAR;
ALTER TABLE res_partner ADD COLUMN IF NOT EXISTS priority_cust INTEGER;
ALTER TABLE res_partner ADD COLUMN IF NOT EXISTS priority_custdes VARCHAR;
-- וכן הלאה לכל השדות...
```

## שדות שנוספו
המודל מוסיף את השדות הבאים לטבלת `res_partner`:

### שדות זיהוי
- `priority_custname` - מספר לקוח פריורטי
- `priority_cust` - ID לקוח פריורטי

### פרטי לקוח
- `priority_custdes` - שם לקוח פריורטי
- `priority_custdeslong` - שם לקוח מורחב פריורטי
- `priority_ecustdes` - שם לועזי פריורטי
- `priority_statdes` - סטטוס פריורטי

### פרטי קשר
- `priority_phone` - מספר טלפון פריורטי
- `priority_fax` - פקס פריורטי
- `priority_email` - דואר אלקטרוני פריורטי

### פרטי עסק
- `priority_businesstype` - תחום עיסוק פריורטי
- `priority_mcustname` - מס' לקוח מרכז פריורטי
- `priority_ctypecode` - קוד סוג לקוח פריורטי

### כתובות
- `priority_address` - כתובת פריורטי
- `priority_address2` - כתובת - שורה 2 פריורטי
- `priority_address3` - כתובת - שורה 3 פריורטי
- `priority_state_name` - עיר ומדינה פריורטי
- `priority_zip_code` - מיקוד פריורטי
- `priority_countryname` - ארץ פריורטי

### פרטי מס ועסק
- `priority_wtaxnum` - מס' חברה פריורטי
- `priority_vatnum` - מספר תיק במע"מ פריורטי

### פרטי סוכן
- `priority_agentcode` - מס' סוכן פריורטי
- `priority_agentname` - שם סוכן פריורטי
- `priority_commission` - עמלת הסוכן(%) פריורטי

### תנאי תשלום
- `priority_paycode` - קוד תנאי תשלום פריורטי
- `priority_paydes` - תנאי תשלום פריורטי
- `priority_max_credit` - תיקרת אשראי פריורטי
- `priority_max_obligo` - תיקרת אובליגו פריורטי

### שדות מיוחדים
- `priority_spec1` עד `priority_spec20` - שדות מיוחדים 1-20

### שדות נוספים
- `priority_gpsx`, `priority_gpsy` - קואורדינטות GPS
- `priority_currency_code` - מטבע הלקוח פריורטי
- `priority_lang_code` - קוד שפה פריורטי

## אימות הפתרון
לאחר הפתרון, בדקו שהשדות קיימים:

```sql
-- בדיקה שהשדות קיימים
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'res_partner' 
AND column_name LIKE 'priority_%';
```

## הערות חשובות
1. **גיבוי**: לפני ביצוע שינויים, בצעו גיבוי של מסד הנתונים
2. **בדיקה**: בדקו שהשדות נוצרו לפני הפעלת המערכת
3. **תאימות**: המודול תואם ל-Odoo 18 Community

## תמיכה
אם יש בעיות נוספות, בדקו:
1. לוגי השרת
2. הרשאות מסד הנתונים
3. תאימות גרסאות Odoo
