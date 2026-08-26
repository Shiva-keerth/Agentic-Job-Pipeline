import os
import json
import sqlite3
import time
import datetime
from groq import Groq
from dotenv import load_dotenv
from core.vector_ranker import rank_jobs

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def log_telemetry(company: str, role: str, eval_type: str, model_used: str, is_fallback: bool, prompt_tokens: int, completion_tokens: int, latency_ms: float, verdict: str, reason: str):
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "outcome_log.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    timestamp = datetime.datetime.utcnow().isoformat()
    cursor.execute("""
        INSERT INTO evaluator_telemetry 
        (company, role, timestamp, eval_type, model_used, is_fallback, prompt_tokens, completion_tokens, latency_ms, verdict, reason)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (company, role, timestamp, eval_type, model_used, is_fallback, prompt_tokens, completion_tokens, latency_ms, verdict, reason))
    conn.commit()
    conn.close()


CANDIDATE_PROFILE = """
Shiva Keerth \u2014 Generative AI Engineer | Agentic AI Developer
Location: Ahmedabad/Remote | Target: 0-2 YOE permanent roles | Target CTC: \u20b98-12 LPA

TECHNICAL SKILLS:
LangChain, LangGraph, LangGraph ReAct agents, ChromaDB, FAISS, Neo4j, Neo4j Aura,
FastAPI, Docker, AWS EC2, Groq API, Llama-3.3-70B, Groq Whisper, RAG pipelines,
Graph RAG, GraphCypherQAChain, Pydantic, Supabase, SQLite, Python 3.10+,
Prompt Engineering, Multi-agent systems, Agentic AI, Knowledge Graphs,
Retrieval Augmented Generation, Vector databases, Embeddings, LLM fine-tuning,
Tavily Search, BeautifulSoup4, Playwright, Streamlit, APScheduler

PROJECTS:
OmniMind AI \u2014 Enterprise Knowledge Graph + Graph-RAG platform.
Stack: Neo4j Aura, LangChain GraphCypherQAChain, Groq Whisper STT,
Llama-3.3-70B inference, Pydantic data validation.
Deployed: Hugging Face Spaces. Repo: github.com/Shiva-keerth/OmniMind-AI-Enterprise

Dual-Domain Agentic RAG Platform \u2014 Production multi-agent system.
Stack: LangGraph ReAct agents, ChromaDB vector store, Tavily Search tool,
Docker containerization, AWS EC2 deployment.
Domains: Healthcare document QA + Financial data analysis.

SkillMatch AI \u2014 AI-powered workforce recommendation engine.
Stack: 6-signal TF-IDF scoring, 3-tier RBAC, Groq Llama-3, FastAPI backend,
Supabase database, Streamlit UI. 600-job dataset.

EXPERIENCE:
Infolabz Pvt. Ltd. \u2014 AI & Data Science Intern (8 months)
Data Analytics, Machine Learning pipelines, Python automation

EDUCATION:
B.Tech Information Technology \u2014 Indus University, Ahmedabad
CGPA: 9.57 | Graduated: May 2026
"""

import re

EXPERIENCE_KILLERS = [
    "senior engineer", "lead engineer", "principal engineer", 
    "director", "manager", "architect", "tech lead"
]

def pre_filter_experience(jd_text: str, role_title: str) -> tuple[bool, str]:
    """Returns (True, matched_string) if JD should be DISQUALIFIED before LLM call, else (False, '').
    
    Uses text normalization + multiple targeted patterns to catch every experience format:
    en-dashes, em-dashes, "X to Y years", long-distance "X years of ... experience", etc.
    """
    text_to_check = (jd_text + " " + role_title).lower()
    
    # ── STEP 0: Normalize Unicode dashes to plain hyphens ──
    # This is THE fix for "3–6 years" (en-dash) and "3—6 years" (em-dash)
    text_to_check = text_to_check.replace('\u2013', '-')   # en-dash
    text_to_check = text_to_check.replace('\u2014', '-')   # em-dash
    text_to_check = text_to_check.replace('\u2012', '-')   # figure-dash
    text_to_check = text_to_check.replace('\u2015', '-')   # horizontal bar
    
    # ── STEP 1: Title/role keyword killers ──
    for killer in EXPERIENCE_KILLERS:
        match = re.search(rf'\b{re.escape(killer)}\b', text_to_check)
        if match:
            return True, match.group(0)
    
    # ── STEP 2: Experience patterns (multiple simple regexes > one fragile mega-regex) ──
    # All patterns target first-number >= 2 via ([2-9]|\d{2,})
    
    NUM = r'([2-9]|\d{2,})'          # any integer >= 2
    YRS = r'(?:years?|yrs?)'          # "year", "years", "yr", "yrs"
    
    patterns = [
        # P1: "3-6 years" or "4 - 6 years" or "4-6years" (range with hyphen, spaces optional)
        rf'{NUM}\+?\s*-\s*\d+\s*{YRS}',
        
        # P2: "4 to 8 years" or "3 to 6 Years" (range with "to")
        rf'{NUM}\s+to\s+\d+\s*{YRS}',
        
        # P3: "5+ years" or "2+ yrs" (explicit plus sign)
        rf'{NUM}\+\s*{YRS}',
        
        # P4: "3 years of production NLP/ML experience" — long-distance bridge (up to 80 chars)
        # Uses .{{0,80}}? instead of (\w+\s+){{0,2}} so slashes, commas, etc. don't break it
        rf'{NUM}\+?\s*{YRS}\s+of\s+.{{0,80}}?\b(?:experience|exp)\b',
        
        # P5: "experience: 4-6 years" or "Exp- 4-6years" (label then number)
        rf'(?:experience|exp)\s*[:\-|]+\s*{NUM}',
        
        # P6: "minimum 3 years" or "at least 2 years"
        rf'(?:minimum|at\s*least|atleast|min\.?)\s*{NUM}\+?\s*{YRS}',
        
        # P7: "3 years hands-on" or "5 years of professional ..." (contextual adjectives)
        rf'{NUM}\+?\s*{YRS}\s+(?:of\s+)?(?:hands[\s-]on|professional|industry|relevant|related|proven|practical|prior|total|overall|software|production)',
        
        # P8: "3 years of building" or "5 years working with" (action verbs after bridge)
        rf'{NUM}\+?\s*{YRS}\s+(?:of\s+)?(?:.{{0,40}}?\b)?(?:building|working|developing|designing|leading|managing|shipping|deploying)',

        # P9: catch simple "2 years" if immediately followed by experience context
        rf'{NUM}\s*{YRS}(?:\s+of)?\s+(?:work\s+)?(?:experience|exp)\b',

        # P10: requires 2 years
        rf'(?:requires|required|minimum|min)\s+(?:of\s+)?{NUM}\s*{YRS}',
    ]
    
    for pat in patterns:
        match = re.search(pat, text_to_check, re.IGNORECASE)
        if match:
            return True, match.group(0)
    
    return False, ""

COMPANY_BLACKLIST = {
    "scoutit",
}

def is_blacklisted(company: str) -> bool:
    return company.lower().strip() in COMPANY_BLACKLIST

AGGREGATOR_SIGNALS = [
    "one platform. every opportunity",
    "powered by ai. apply now",
    "we connect candidates",
    "our client is seeking",
    "confidential company",
]

def has_aggregator_signals(jd_text: str) -> bool:
    jd_lower = jd_text.lower()
    return any(signal in jd_lower for signal in AGGREGATOR_SIGNALS)

EVALUATOR_PROMPT = """You are a strict Senior Technical Recruiter evaluating a job match.

CANDIDATE PROFILE:
{profile}

JOB TO EVALUATE:
Company: {company}
Role: {role}
Full JD:
{jd_text}

INSTRUCTIONS — follow this exact order:

STEP 1 — MANDATORY EXPERIENCE CHECK (do this FIRST, before looking at skills):
Read the ENTIRE JD carefully and extract the experience requirement.
Look for phrases like "X years", "X+ years", "X-Y years", "X to Y years", "minimum X years",
"at least X years", "Exp: X", or any similar phrasing.

DISQUALIFY IMMEDIATELY (set "verdict" to "DISQUALIFIED" and "match_score" to 0) if ANY of these are true:
  a) The JD mentions ANY experience requirement of 2 or more years. Examples that MUST be disqualified:
     "2+ years", "3-6 years", "3 to 6 years", "5+ years", "2-3 years", "minimum 3 years".
     Even if the tech stack is a perfect match, you MUST still disqualify. NO EXCEPTIONS.
  b) The role title or JD implies Senior / Lead / Principal / Staff / Manager / Director level.
  c) The role is Contract / Freelance / Gig with no permanent track.

ONLY proceed to Step 2 if the experience requirement is 0-1 years, "fresher", "entry-level",
"new grad", or NOT mentioned at all.

STEP 2 — TECH STACK MATCH (only if Step 1 passed):
- List which of the candidate's skills directly appear or are implied in the JD.
- List any hard requirements in the JD that the candidate completely lacks.
- If the candidate lacks more than 3 hard requirements, set verdict to "Poor Fit".

STEP 3 — FINAL SCORE (only if Step 1 passed):
- Score 0-100 based on genuine skill overlap, not keyword presence.
- 80-100: Strong match, candidate should prioritize this application.
- 60-79: Good fit, worth applying with a tailored cover letter.
- 40-59: Partial fit, apply only if volume is low.
- Below 40: Poor fit, skip.

Respond ONLY with a valid JSON object. No preamble, no markdown, no explanation outside the JSON:
{{
  "match_score": <0-100 integer>,
  "verdict": "<DISQUALIFIED | Poor Fit | Partial Fit | Good Fit | Strong Match>",
  "experience_required": "<what the JD states or 'Not specified'>",
  "matched_skills": ["<skill1>", "<skill2>"],
  "missing_skills": ["<skill1>", "<skill2>"],
  "reason": "<2-3 sentences max explaining the score>"
}}"""


def evaluate_job(job: dict, jd_text: str) -> dict:
    is_external = "[EXTERNAL_APPLY_FLAG]" in jd_text
    job["is_external"] = is_external
    clean_jd = jd_text.replace("[EXTERNAL_APPLY_FLAG]", "").strip()
    
    prompt = EVALUATOR_PROMPT.format(
        profile=CANDIDATE_PROFILE,
        company=job["company"],
        role=job["role"],
        jd_text=clean_jd[:1500]  # Groq context limit guard
    )

    # Model fallback chain: GPT OSS primary (clean JSON), Qwen backup
    models = ["openai/gpt-oss-120b", "qwen/qwen3.6-27b"]
    last_error = "Unknown error"

    for i, model in enumerate(models):
        try:
            start_time = time.time()
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1024,
                temperature=0.1   # Low temp for consistent structured output
            )
            latency_ms = (time.time() - start_time) * 1000
            raw = response.choices[0].message.content.strip()

            # Strip Qwen's <think>...</think> chain-of-thought block
            if "<think>" in raw and "</think>" in raw:
                raw = raw.split("</think>")[-1].strip()

            # Strip markdown fences if model adds them
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]

            result = json.loads(raw)
            
            # Apply external penalty logic (conditional on short JD)
            if job.get("is_external", False) and len(clean_jd.split()) < 150:
                result["match_score"] = max(0, result.get("match_score", 0) - 30)
                result["reason"] = f"[External Penalty applied due to short JD] {result.get('reason', '')}"

            prompt_t = response.usage.prompt_tokens if hasattr(response, 'usage') and hasattr(response.usage, 'prompt_tokens') else 0
            comp_t = response.usage.completion_tokens if hasattr(response, 'usage') and hasattr(response.usage, 'completion_tokens') else 0
            
            log_telemetry(
                company=job["company"], role=job["role"], eval_type='LLM',
                model_used=model, is_fallback=bool(i > 0),
                prompt_tokens=prompt_t, completion_tokens=comp_t,
                latency_ms=latency_ms, verdict=result.get("verdict", "UNKNOWN"), reason=result.get("reason", "")
            )

            return result

        except json.JSONDecodeError as e:
            print(f"[Evaluator] JSON parse failed on {model} for {job['role']} @ {job['company']}. Trying next model.")
            last_error = f"JSON parse failed: {e}"
            continue
        except Exception as e:
            print(f"[Evaluator] {model} failed: {e}. Trying next model.")
            last_error = str(e)
            continue

    print(f"[Evaluator] All models failed for {job['role']} @ {job['company']}")
    log_telemetry(
        company=job["company"], role=job["role"], eval_type='ERROR',
        model_used="ALL_MODELS_FAILED", is_fallback=True,
        prompt_tokens=0, completion_tokens=0, latency_ms=0.0,
        verdict="ERROR", reason=last_error
    )
    return None


def fetch_jd_from_db(db_id: str) -> str:
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "outcome_log.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT jd_text FROM applications WHERE id = ?", (db_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row and row[0] else ""


def update_score_in_db(db_id: str, score: float, verdict: str):
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "outcome_log.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE applications SET match_score = ?, verdict = ? WHERE id = ?",
        (score, verdict, db_id)
    )
    conn.commit()
    conn.close()


def run_evaluation(top_n: int = 15):
    print("[Evaluator] Fetching top ranked jobs from ChromaDB...")
    ranked = rank_jobs(top_n=top_n)

    if not ranked:
        print("[Evaluator] No jobs to evaluate. Run vector_ranker first.")
        return

    print(f"[Evaluator] Evaluating {len(ranked)} jobs via Groq...\n")
    results = []

    for job in ranked:
        jd_text = fetch_jd_from_db(job["db_id"])
        if not jd_text:
            continue

        if is_blacklisted(job["company"]) or has_aggregator_signals(jd_text):
            print(f"  [X] Blacklisted/aggregator: {job['role']} @ {job['company']}")
            update_score_in_db(job["db_id"], 0, "BLACKLISTED")
            log_telemetry(job["company"], job["role"], 'BLACKLIST', 'regex', False, 0, 0, 0.0, 'BLACKLISTED', 'Blacklisted company or aggregator signal found.')
            results.append({**job, "match_score": 0, "verdict": "BLACKLISTED", "reason": "Blacklisted company or aggregator signal found."})
            continue

        is_filtered, match_str = pre_filter_experience(jd_text, job["role"])
        if is_filtered:
            print(f"  [X] Pre-filtered (experience): {job['role']} @ {job['company']} (Matched: '{match_str}')")
            update_score_in_db(job["db_id"], 0, "DISQUALIFIED")
            log_telemetry(job["company"], job["role"], 'PRE_FILTER', 'regex', False, 0, 0, 0.0, 'DISQUALIFIED', f"Matched: '{match_str}'")
            results.append({**job, "match_score": 0, "verdict": "DISQUALIFIED", "reason": f"Pre-filtered based on experience keywords. (Matched: '{match_str}')"})
            continue

        print(f"Evaluating: {job['role']} @ {job['company']}")
        evaluation = evaluate_job(job, jd_text)

        if not evaluation:
            continue

        # Write score back to DB
        update_score_in_db(job["db_id"], evaluation["match_score"], evaluation["verdict"])

        results.append({**job, **evaluation})

        # Print summary line
        flag = "[X]" if evaluation["verdict"] == "DISQUALIFIED" else \
               "[!]" if evaluation["match_score"] < 60 else "[V]"
        print(f"  {flag} Score: {evaluation['match_score']} | {evaluation['verdict']}")
        safe_reason = evaluation['reason'][:100].encode('ascii', 'ignore').decode('ascii')
        print(f"     Reason: {safe_reason}")
        print()

        time.sleep(0.5)   # Groq rate limit buffer

    # Summary
    qualified   = [r for r in results if r["verdict"] not in ["DISQUALIFIED", "BLACKLISTED"]]
    disqualified = [r for r in results if r["verdict"] == "DISQUALIFIED"]
    blacklisted = [r for r in results if r["verdict"] == "BLACKLISTED"]
    strong      = [r for r in qualified if r["match_score"] >= 80]

    print("=" * 55)
    print(f"EVALUATION COMPLETE")
    print(f"  Total evaluated:  {len(results)}")
    print(f"  Disqualified:     {len(disqualified)}  (experience mismatch)")
    print(f"  Blacklisted:      {len(blacklisted)}  (fake/aggregator)")
    print(f"  Strong matches:   {len(strong)}  (score >= 80)")
    print(f"  Worth applying:   {len(qualified)}  (score >= 40)")
    print("=" * 55)

    return results


if __name__ == "__main__":
    run_evaluation(top_n=15)
