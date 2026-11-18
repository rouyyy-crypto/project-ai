import sqlite3


def init_db():
    # יצירת או פתיחת חיבור לקובץ מסד הנתונים בתיקייה הנוכחית
    conn = sqlite3.connect('band_data.db')
    cursor = conn.cursor()

    # 1. יצירת טבלת נגנים (תואם בדיוק לעמודות מהאקסס)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS musicians (
        id_musician INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT,
        address TEXT,
        instrument TEXT NOT NULL,
        rate REAL NOT NULL,
        status TEXT,
        notes TEXT
    )
    ''')

    # 2. יצירת טבלת אולמות
    # מרחק: 1 = ללא תוספת, 2 = תוספת קלאסית, 3 = תוספת קיצונית
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS venues (
        id_venue INTEGER PRIMARY KEY AUTOINCREMENT,
        venue_name TEXT NOT NULL,
        address TEXT NOT NULL,
        distance_category INTEGER CHECK(distance_category IN (1, 2, 3)) NOT NULL,
        notes TEXT
    )
    ''')

    # שמירת השינויים (Commit) וסגירת החיבור
    conn.commit()
    conn.close()
    print("הטבלאות musicians ו-venues נוצרו בהצלחה לפי האפיון המעודכן!")

if __name__ == '__main__':
    init_db()