import os
import json
import sqlite3
from groq import Groq
from dotenv import load_dotenv
from core.llm_evaluator import EVALUATOR_PROMPT, CANDIDATE_PROFILE

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Get Jade Global JD
db_path = os.path.join(os.path.dirname(__file__), "database", "outcome_log.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT jd_text FROM applications WHERE company='Jade Global'")
jd = cursor.fetchone()[0]
conn.close()

prompt = EVALUATOR_PROMPT.format(
    profile=CANDIDATE_PROFILE,
    company="Jade Global",
    role="AI/ML Engineer",
    jd_text=jd[:1500]
)

print(f"Prompt length: {len(prompt)} chars")

model = "openai/gpt-oss-120b"
print(f"\n=== {model} ===")
resp = client.chat.completions.create(
    model=model,
    messages=[{"role": "user", "content": prompt}],
    max_tokens=800,
    temperature=0.1
)
raw = resp.choices[0].message.content.strip()
print(f"RAW ({len(raw)} chars):\n{raw}")
