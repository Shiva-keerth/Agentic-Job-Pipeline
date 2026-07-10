import sqlite3
c = sqlite3.connect('database/outcome_log.db')
cursor = c.cursor()
cursor.execute("SELECT count(*) FROM applications WHERE date_found LIKE '2026-07-09%'")
print(cursor.fetchone()[0])
