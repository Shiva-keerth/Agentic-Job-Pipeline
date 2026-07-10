import sqlite3
try:
    conn = sqlite3.connect('database/outcome_log.db')
    cursor = conn.cursor()
    cursor.execute("SELECT platform, company, role FROM applications WHERE LOWER(company) LIKE '%fluid%'")
    rows = cursor.fetchall()
    for r in rows:
        print(f"Platform: {r[0]}, Company: {r[1]}, Role: {r[2]}")
    if not rows:
        print("No records found for Fluid in DB.")
except Exception as e:
    print(e)
