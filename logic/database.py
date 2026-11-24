import sqlite3


def init_db():
    conn = sqlite3.connect('band_data.db')
    cursor = conn.cursor()

    # 1. טבלת נגנים
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

    # 2. טבלת אולמות
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS venues (
        id_venue INTEGER PRIMARY KEY AUTOINCREMENT,
        venue_name TEXT NOT NULL,
        address TEXT NOT NULL,
        distance_category INTEGER CHECK(distance_category IN (1, 2, 3)) NOT NULL,
        notes TEXT
    )
    ''')

    # 3. יומן תאריכים תפוסים (לצורך סינון זמינות)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS booked_dates (
        id_booked INTEGER PRIMARY KEY AUTOINCREMENT,
        event_date TEXT NOT NULL UNIQUE,
        description TEXT
    )
    ''')

    # 4. טבלת לידים נכנסים (הלב של ה-MVP)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS leads (
        id_lead INTEGER PRIMARY KEY AUTOINCREMENT,
        client_name TEXT,
        client_phone TEXT,
        event_date TEXT,
        event_type TEXT,
        venue_name TEXT,
        requested_instruments TEXT,
        quoted_price REAL,
        chat_transcript TEXT,
        status TEXT DEFAULT 'ממתין לאישור'
    )
    ''')

    conn.commit()
    conn.close()
    print("כל 4 הטבלאות (נגנים, אולמות, יומן תפוס ולידים) אותחלו בהצלחה!")

if __name__ == '__main__':
    init_db()