import os
import json
import sqlite3
import time
from groq import Groq
from dotenv import load_dotenv
from core.vector_ranker import rank_jobs

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

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
    """Returns (True, matched_string) if JD should be DISQUALIFIED before LLM call, else (False, '')."""
    text_to_check = (jd_text + " " + role_title).lower()
    
    # Catch static keywords with word boundaries to avoid substring matching
    # e.g., prevent "architecture" from matching "architect"
    for killer in EXPERIENCE_KILLERS:
        match = re.search(rf'\b{re.escape(killer)}\b', text_to_check)
        if match:
            return True, match.group(0)
        
    # Precision-first regex handling both trailing and leading context (e.g. "Experience: 5 yrs" or "5 years of proven experience")
    regex_pattern = r'(?:(?:experience|exp)[\s:|-]+([2-9]|\d{2,})\+?\s*(?:-\s*(?:[2-9]|\d{2,})\s*)?(years?|yrs?))|([2-9]|\d{2,})\+?\s*(?:-\s*(?:[2-9]|\d{2,})\s*)?(years?|yrs?)\s*(?:of\s+(?:\w+\s+){0,2})?(?:experience|exp|building|working)'
    match = re.search(regex_pattern, text_to_check, re.IGNORECASE)
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

INSTRUCTIONS \u2014 follow this exact order:

STEP 1 \u2014 DISQUALIFY on either condition (check this first, before anything else):
If ANY of the following are true, you MUST set "verdict" to "DISQUALIFIED", set "match_score" to 0, and STOP evaluating:
1. Role requires MORE than 1 year of experience anywhere in the text (e.g., 2+ years).
2. Role is explicitly Contract/Freelance/Gig with no permanent track.
3. Role implies Senior/Lead/Principal/Manager level.

If NONE of the above are true (e.g., 0-1 years, fresher, entry-level, or not mentioned, and is a permanent role), proceed to Step 2.

STEP 2 \u2014 TECH STACK MATCH:
- List which of the candidate's skills directly appear or are implied in the JD.
- List any hard requirements in the JD that the candidate completely lacks.
- If the candidate lacks more than 3 hard requirements, set verdict to "Poor Fit".

STEP 3 \u2014 FINAL SCORE:
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

    for model in models:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1024,
                temperature=0.1   # Low temp for consistent structured output
            )
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

            return result

        except json.JSONDecodeError:
            print(f"[Evaluator] JSON parse failed on {model} for {job['role']} @ {job['company']}. Trying next model.")
            continue
        except Exception as e:
            print(f"[Evaluator] {model} failed: {e}. Trying next model.")
            continue

    print(f"[Evaluator] All models failed for {job['role']} @ {job['company']}")
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
            results.append({**job, "match_score": 0, "verdict": "BLACKLISTED", "reason": "Blacklisted company or aggregator signal found."})
            continue

        is_filtered, match_str = pre_filter_experience(jd_text, job["role"])
        if is_filtered:
            print(f"  [X] Pre-filtered (experience): {job['role']} @ {job['company']} (Matched: '{match_str}')")
            update_score_in_db(job["db_id"], 0, "DISQUALIFIED")
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
