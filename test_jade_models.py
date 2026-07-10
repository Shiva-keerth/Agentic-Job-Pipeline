import os
import json
import sqlite3
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Get Jade Global JD
db_path = os.path.join(os.path.dirname(__file__), "database", "outcome_log.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT jd_text FROM applications WHERE company='Jade Global'")
jd = cursor.fetchone()[0][:1500]
conn.close()

prompt = f"""You are a strict Senior Technical Recruiter. Respond ONLY with valid JSON. No thinking, no explanation.

JOB: AI/ML Engineer at Jade Global
JD: {jd[:800]}

CANDIDATE: Python dev with LangChain, FastAPI, Docker, ChromaDB.

{{"match_score": <0-100>, "verdict": "<Strong Match|Good Fit|Poor Fit>", "reason": "<1 sentence>"}}"""

models = ["qwen/qwen3.6-27b", "openai/gpt-oss-120b"]
for model in models:
    print(f"\n=== {model} ===")
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            temperature=0.1
        )
        raw = resp.choices[0].message.content.strip()
        print(f"RAW ({len(raw)} chars):\n{raw[:600]}")
        
        # Strip think tags
        if "<think>" in raw and "</think>" in raw:
            raw = raw.split("</think>")[-1].strip()
            print(f"\nAFTER STRIP ({len(raw)} chars):\n{raw[:400]}")
        
        parsed = json.loads(raw)
        print(f"\nPARSED: {parsed}")
    except Exception as e:
        print(f"ERROR: {e}")
