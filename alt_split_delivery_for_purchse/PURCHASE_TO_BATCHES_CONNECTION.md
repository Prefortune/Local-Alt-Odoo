# חיבור בין הזמנות רכש למנות משלוח
## Purchase Orders to Delivery Batches Connection

---

## 🎯 **מטרת המערכת**

המערכת מאפשרת לפצל הזמנת רכש אחת למספר מנות משלוח נפרדות, כל אחת עם:
- כתובת משלוח ייעודית
- מוצרים וכמויות ספציפיות
- תאריך משלוח נפרד
- הערות ייעודיות

---

## 🔄 **זרימת העבודה (Workflow)**

### **שלב 1: יצירת הזמנת רכש**
```
Purchase Order (PO) → מוצרים + כמויות + ספק
```

### **שלב 2: פיצול למנות**
```
PO → Batch 1, Batch 2, Batch 3, ... Batch N
```

### **שלב 3: ניהול מנות**
```
כל מנה → כתובת + מוצרים + תאריך + הערות
```

### **שלב 4: יצירת משלוחים**
```
כל מנה → Stock Picking נפרד
```

---

## 🏗️ **ארכיטקטורת המודלים**

### **מודלים מרכזיים:**

#### **1. Purchase Order (הזמנת רכש)**
```python
# הרחבה של המודל הסטנדרטי
class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    
    # שדות חדשים
    alt_split_delivery_count = fields.Integer('Number of Batches')
    alt_split_delivery_ids = fields.One2many('alt.purchase.split.delivery', 'purchase_order_id')
```

#### **2. Alt Purchase Split Delivery (ניהול מנות)**
```python
class AltPurchaseSplitDelivery(models.Model):
    _name = 'alt.purchase.split.delivery'
    
    purchase_order_id = fields.Many2one('purchase.order')
    alt_delivery_index = fields.Integer('Batch Number')
    picking_id = fields.Many2one('stock.picking')  # הקשר למשלוח בפועל
    alt_scheduled_date = fields.Datetime('Delivery Date')
    alt_delivery_notes = fields.Text('Batch Notes')
```

#### **3. Stock Picking (משלוח בפועל)**
```python
# כל מנה יוצרת Stock Picking נפרד
class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    # הקשר להזמנת הרכש המקורית
    purchase_id = fields.Many2one('purchase.order')
    origin = fields.Char()  # "PO0001 - Batch 1"
```

---

## 🔗 **קשרים בין המודלים**

### **היררכיית הקשרים:**
```
Purchase Order (1)
    ↓
Alt Purchase Split Delivery (Many)
    ↓
Stock Picking (1:1)
    ↓
Stock Move Lines (Many)
```

### **פירוט הקשרים:**

#### **1. Purchase Order ↔ Alt Purchase Split Delivery**
```python
# ב-Purchase Order
alt_split_delivery_ids = fields.One2many(
    'alt.purchase.split.delivery', 
    'purchase_order_id', 
    string='Delivery Batches'
)

# ב-Alt Purchase Split Delivery
purchase_order_id = fields.Many2one(
    'purchase.order', 
    string='Purchase Order', 
    required=True
)
```

#### **2. Alt Purchase Split Delivery ↔ Stock Picking**
```python
# ב-Alt Purchase Split Delivery
picking_id = fields.Many2one(
    'stock.picking', 
    string='Delivery Picking'
)

# ב-Stock Picking (אוטומטי)
purchase_id = fields.Many2one(
    'purchase.order', 
    string='Purchase Order'
)
origin = fields.Char()  # "PO0001 - Batch 1"
```

---

## 📊 **דוגמה מעשית**

### **תרחיש: הזמנת חלונות**

#### **הזמנת רכש מקורית:**
```
PO0001 - הזמנת חלונות
├── ספק: חברת החלונות בע"מ
├── מוצר A: חלון PVC - 100 יח'
├── מוצר B: חלון אלומיניום - 50 יח'
└── מוצר C: דלת כניסה - 20 יח'
```

#### **פיצול למנות:**
```
PO0001 → 3 מנות משלוח

מנה 1: משלוח ראשון
├── כתובת: רח' הרצל 10, תל אביב
├── חלון PVC: 60 יח'
├── חלון אלומיניום: 30 יח'
├── תאריך: 15/10/2024
└── הערות: קומה ראשונה

מנה 2: משלוח שני
├── כתובת: רח' דיזנגוף 25, תל אביב
├── חלון PVC: 40 יח'
├── חלון אלומיניום: 20 יח'
├── תאריך: 20/10/2024
└── הערות: קומה שנייה

מנה 3: משלוח שלישי
├── כתובת: רח' בן יהודה 5, חיפה
├── דלת כניסה: 20 יח'
├── תאריך: 25/10/2024
└── הערות: כניסה ראשית
```

#### **יצירת Stock Pickings:**
```
Stock Picking 1: "PO0001 - Batch 1"
├── Origin: "PO0001 - Batch 1"
├── Partner: רח' הרצל 10, תל אביב
├── Move Lines:
│   ├── חלון PVC: 60 יח'
│   └── חלון אלומיניום: 30 יח'

Stock Picking 2: "PO0001 - Batch 2"
├── Origin: "PO0001 - Batch 2"
├── Partner: רח' דיזנגוף 25, תל אביב
├── Move Lines:
│   ├── חלון PVC: 40 יח'
│   └── חלון אלומיניום: 20 יח'

Stock Picking 3: "PO0001 - Batch 3"
├── Origin: "PO0001 - Batch 3"
├── Partner: רח' בן יהודה 5, חיפה
└── Move Lines:
    └── דלת כניסה: 20 יח'
```

---

## 🛠️ **תהליך יצירת המנות**

### **1. שלב התכנון (Wizard)**
```python
class AltPurchaseSplitWizard(models.TransientModel):
    def action_confirm_split_count(self):
        # יצירת מוצרים מההזמנה
        # יצירת שורות מנות
        # מעבר לשלב הגדרה
```

### **2. שלב ההגדרה**
```python
def action_save_batches(self):
    # שמירת תצורת המנות
    # עדכון Purchase Order
    # מעבר למצב "saved"
```

### **3. שלב היצירה**
```python
def action_create_split_deliveries(self):
    # מחיקת מנות קיימות
    # יצירת Stock Pickings
    # יצירת Alt Purchase Split Delivery records
    # עדכון מצב ל"completed"
```

---

## 📋 **תכונות המערכת**

### **1. ניהול כתובות**
- כל מנה יכולה להיות עם כתובת שונה
- יצירת שותפים חדשים אוטומטית
- עדכון כתובות קיימות

### **2. חלוקת מוצרים**
- חלוקה גמישה של מוצרים בין מנות
- מעקב אחר כמות נותרה
- התראות על חריגה מהכמות המקורית

### **3. ניהול תאריכים**
- תאריך משלוח נפרד לכל מנה
- תצוגת תאריך ללא שעה
- תמיכה בתאריכים עתידיים

### **4. הערות והערות**
- הערות ייעודיות לכל מנה
- מעקב אחר פרטי משלוח
- תמיכה בהערות ארוכות

---

## 🔄 **סנכרון עם מערכות אודו**

### **1. אינטגרציה עם Stock Management**
```python
# כל מנה יוצרת Stock Picking נפרד
picking = self.env['stock.picking'].create({
    'partner_id': partner.id,
    'picking_type_id': warehouse.in_type_id.id,
    'location_id': partner.property_stock_supplier.id,
    'location_dest_id': warehouse.lot_stock_id.id,
    'origin': f"{self.purchase_order_id.name} - Batch {line.delivery_index}",
    'purchase_id': self.purchase_order_id.id,
})
```

### **2. אינטגרציה עם Purchase Management**
```python
# עדכון Purchase Order עם מספר המנות
self.purchase_order_id.write({
    'alt_split_delivery_count': self.split_count,
})
```

### **3. אינטגרציה עם Partner Management**
```python
# יצירת שותפים חדשים למשלוח
partner = self.env['res.partner'].create({
    'name': f"{self.purchase_order_id.partner_id.name} - Batch {line.delivery_index}",
    'parent_id': self.purchase_order_id.partner_id.id,
    'type': 'delivery',
    'street': line.street,
    'city': line.city,
    'zip': line.zip,
})
```

---

## 📊 **יתרונות המערכת**

### **1. גמישות**
- חלוקה גמישה של מוצרים
- כתובות שונות לכל מנה
- תאריכים נפרדים

### **2. מעקב ושליטה**
- מעקב אחר כל מנה בנפרד
- שליטה על כמויות
- התראות על חריגות

### **3. אינטגרציה מלאה**
- עובד עם מערכות אודו הקיימות
- Stock Pickings נפרדים
- מעקב אחר משלוחים

### **4. ניהול יעיל**
- תצוגה ברורה של המנות
- ממשק משתמש אינטואיטיבי
- שמירה והמשכיות

---

## 🎯 **מקרי שימוש**

### **1. פרויקטי בנייה**
- משלוחים לכתובות שונות
- מוצרים שונים לכל אתר
- תאריכים לפי לוח זמנים

### **2. רשתות קמעונאות**
- משלוחים לחנויות שונות
- חלוקת מלאי לפי צרכים
- ניהול מחסנים

### **3. יבוא ויצוא**
- משלוחים דרך נמלים שונים
- תאריכים לפי לוחות זמנים
- ניהול מכס

---

## 🔧 **תחזוקה ותמיכה**

### **1. ניקוי נתונים**
```python
# מחיקת מנות קיימות לפני יצירת חדשות
existing_splits = self.env['alt.purchase.split.delivery'].search([
    ('purchase_order_id', '=', self.purchase_order_id.id)
])
existing_splits.unlink()
```

### **2. עדכון מצבים**
```python
# מעקב אחר מצב המנות
state = fields.Selection([
    ('count', 'Select Number of Batches'),
    ('configure', 'Configure Batches'),
    ('saved', 'Saved Configuration'),
    ('completed', 'Completed')
])
```

### **3. לוגים ועקבות**
```python
_logger.info(f"Created {self.split_count} split deliveries for purchase order {self.purchase_order_id.name}")
```

---

## 📝 **סיכום**

המערכת מאפשרת חיבור מלא בין הזמנות רכש למנות משלוח, תוך שמירה על:
- **גמישות** בחלוקת מוצרים וכתובות
- **שליטה** מלאה על כל מנה בנפרד
- **אינטגרציה** עם מערכות אודו הקיימות
- **מעקב** אחר כל שלב בתהליך
- **ניהול** יעיל של משלוחים מרובים

המערכת מתאימה למגוון רחב של מקרי שימוש, מפרויקטי בנייה ועד רשתות קמעונאות, ומספקת כלים מתקדמים לניהול משלוחים מורכבים.
