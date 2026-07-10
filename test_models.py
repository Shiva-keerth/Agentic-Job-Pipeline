import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

prompt = """You are a strict recruiter. Evaluate this job for the candidate.

CANDIDATE: Python developer with LangChain, FastAPI, Docker, ChromaDB experience.
JOB: AI/ML Engineer at Jade Global - Build LLM-based GenAI applications, RAG pipelines, FastAPI backend.

Respond ONLY with valid JSON:
{
  "match_score": 82,
  "verdict": "Strong Match",
  "experience_required": "Not specified",
  "matched_skills": ["LangChain", "FastAPI"],
  "missing_skills": ["Kubernetes"],
  "reason": "Strong overlap in core skills."
}"""

models = ["qwen/qwen3.6-27b", "openai/gpt-oss-120b"]

for model in models:
    print(f"\n--- Testing {model} ---")
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.1
        )
        raw = response.choices[0].message.content.strip()
        print(f"RAW OUTPUT:\n{raw[:500]}")
        
        # Try parsing
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        
        parsed = json.loads(raw)
        print(f"PARSED OK: score={parsed.get('match_score')}, verdict={parsed.get('verdict')}")
    except json.JSONDecodeError as e:
        print(f"JSON PARSE FAILED: {e}")
        print(f"Content that failed: {raw[:300]}")
    except Exception as e:
        print(f"API ERROR: {e}")
