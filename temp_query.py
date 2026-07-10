import sqlite3
import pandas as pd

conn = sqlite3.connect('database/outcome_log.db')
query = """
SELECT date_found, company, role, match_score, job_url 
FROM applications 
WHERE (verdict IS NULL OR verdict NOT IN ('Applied', 'Rejected', 'Ignore', 'No longer accepting'))
  AND match_score >= 80 
GROUP BY company, role 
HAVING max(match_score) 
ORDER BY date_found DESC, match_score DESC 
LIMIT 10
"""
df = pd.read_sql_query(query, conn)
pd.set_option('display.max_colwidth', None)
print(df.to_string(index=False))
conn.close()
