import requests
import sqlite3
import time
from datetime import datetime

TITLE_FILTER = [
    "ai", "ml", "machine learning", "generative", "llm",
    "langchain", "nlp", "deep learning", "data scientist",
    "genai", "prompt", "rag", "agentic", "ai engineer"
]

def title_is_relevant(title: str) -> bool:
    t = title.lower()
    return any(k in t for k in TITLE_FILTER)

def scrape_remotive() -> list[dict]:
    try:
        r = requests.get(
            "https://remotive.com/api/remote-jobs",
            params={"category": "software-dev", "limit": 100},
            timeout=15
        )
        if r.status_code != 200:
            print(f"[Remotive] Status {r.status_code}")
            return []
    except Exception as e:
        print(f"[Remotive] Request failed: {e}")
        return []

    jobs_raw = r.json().get("jobs", [])
    jobs = []

    for job in jobs_raw:
        title = job.get("title", "")
        if not title_is_relevant(title):
            continue

        # Filter out US/EU only roles
        location = job.get("candidate_required_location", "Worldwide")
        excluded = ["usa only", "us only", "europe only", "uk only",
                    "canada only", "australia only", "latin america only"]
        if any(ex in location.lower() for ex in excluded):
            continue

        jobs.append({
            "platform":   "Remotive",
            "role":       title,
            "company":    job.get("company_name", "Unknown"),
            "job_url":    job.get("url", ""),
            "jd_text":    job.get("description", ""),
            "date_found": datetime.now().strftime("%Y-%m-%d %H:%M"),
        })
        print(f"[Remotive] \u2713 {title} @ {job.get('company_name')}")

    return jobs


def save_to_db(jobs: list[dict]):
    if not jobs:
        return
    import os
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "outcome_log.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    inserted = 0
    for job in jobs:
        try:
            # Near-duplicate JD check
            cursor.execute(
                "SELECT jd_text FROM applications WHERE platform = 'Remotive'"
            )
            existing = [r[0][:200] for r in cursor.fetchall() if r[0]]
            if job["jd_text"][:200] in existing:
                continue

            cursor.execute("""
                INSERT OR IGNORE INTO applications
                    (date_found, platform, company, role, job_url, jd_text)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                job["date_found"], job["platform"],
                job["company"],   job["role"],
                job["job_url"],   job["jd_text"]
            ))
            if cursor.rowcount:
                inserted += 1
        except Exception as e:
            print(f"[DB] Insert error: {e}")
    conn.commit()
    conn.close()
    print(f"[Remotive] Saved {inserted} new jobs.")


if __name__ == "__main__":
    jobs = scrape_remotive()
    save_to_db(jobs)
    print(f"Total: {len(jobs)}")
