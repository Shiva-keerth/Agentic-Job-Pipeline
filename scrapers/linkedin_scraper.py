import requests
import sqlite3
import time
import random
from bs4 import BeautifulSoup
from datetime import datetime
import os

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
    )
}

POSTER_REQ_MISSES = 0

KEYWORDS = [
    "AI Engineer",
    "Generative AI Engineer",
    "Machine Learning Engineer",
    "AI Application Engineer",
    "Junior AI Engineer",
    "Associate AI Engineer",
    "AI Developer",
    "LLM Engineer",
    "NLP Engineer",
    "AI Solutions Engineer",
    "Python Backend Developer",
    "Python Developer",
    "Backend Python Engineer",
    "FastAPI Developer",
    "Backend Engineer (Python)",
    "API Developer (Python)",
    "Software Engineer (Python)",
    "Associate Software Engineer (Python)",
    "Data Scientist",
    "Junior Data Scientist",
    "Data Science Associate",
    "ML Associate",
    "AI Analyst",
    "Data Analyst (Python + SQL)",
    "Analytics Engineer",
]
# Only fetch full JD if title passes this filter — cuts request count by ~65%
TITLE_FILTER = [
    "ai", "ml", "machine learning", "generative", "llm",
    "langchain", "nlp", "deep learning", "data scientist", "genai"
]

def title_is_relevant(title: str) -> bool:
    t = title.lower()
    return any(k in t for k in TITLE_FILTER)

def fetch_jd_text(job_url: str) -> str:
    """Second request — only called for relevant titles."""
    try:
        time.sleep(random.uniform(2, 4))
        r = requests.get(job_url, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            return ""
        soup = BeautifulSoup(r.text, "html.parser")
        
        # Skip if job is closed
        closed = soup.find(string=lambda t: t and "No longer accepting applications" in t)
        if closed:
            print("  [Skip] Job is closed.")
            return ""
            
        # Isolate and remove noise sidebars
        for sidebar in soup.find_all(class_=["similar-jobs", "people-also-viewed"]):
            sidebar.decompose()

        # 1. Main JD Extraction
        desc = soup.find("div", class_="show-more-less-html__markup")
        jd = desc.get_text(separator=" ", strip=True) if desc else ""
        
        # 2. Poster Requirements Extraction (Fallback layer)
        poster_reqs = soup.find("div", class_="job-details-module__content") or soup.find("ul", class_="description__job-criteria-list")
        if poster_reqs:
            jd += " \n\n REQUIREMENTS ADDED BY JOB POSTER: " + poster_reqs.get_text(separator=" ", strip=True)
        else:
            global POSTER_REQ_MISSES
            POSTER_REQ_MISSES += 1

        # Check Easy Apply / External redirect
        apply_btn = soup.find("button", class_="apply-button") or soup.find("a", class_="apply-button")
        is_external = False
        if apply_btn:
            btn_text = apply_btn.get_text(strip=True).lower()
            if "easy apply" not in btn_text:
                is_external = True
        else:
            # Fallback for different DOMs
            for link_tag in soup.find_all("a"):
                lt_text = link_tag.get_text(strip=True).lower()
                if "apply" in lt_text and "easy" not in lt_text:
                    is_external = True
                    break
                    
        if is_external:
            jd = "[EXTERNAL_APPLY_FLAG]\n\n" + jd

        return jd
    except Exception:
        return ""

def scrape_linkedin(keyword: str, pages: int = 3) -> list[dict]:
    jobs = []
    
    for page in range(pages):
        start_offset = page * 25
        url = (
            f"https://www.linkedin.com/jobs/search/"
            f"?keywords={keyword.replace(' ', '+')}"
            f"&location=India"
            f"&f_E=2"           # Entry level
            f"&f_JT=F"          # Full-time only
            f"&f_TPR=r86400"    # Past 24 hours
            f"&start={start_offset}"
        )
        try:
            time.sleep(random.uniform(2, 5))
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code != 200:
                print(f"[LinkedIn] Status {r.status_code} for keyword: {keyword} (page {page})")
                continue
        except Exception as e:
            print(f"[LinkedIn] Request failed: {e}")
            continue

        soup = BeautifulSoup(r.text, "html.parser")
        cards = soup.find_all("div", class_="base-card")

        if not cards:
            print(f"[LinkedIn] No more cards found for '{keyword}' at page {page}")
            break

        for card in cards:
            try:
                title_tag  = card.find("h3", class_="base-search-card__title")
                company_tag = card.find("h4", class_="base-search-card__subtitle")
                location_tag = card.find("span", class_="job-search-card__location")
                link_tag   = card.find("a", class_="base-card__full-link")

                title   = title_tag.get_text(strip=True)   if title_tag   else "Unknown"
                company = company_tag.get_text(strip=True) if company_tag else "Unknown"
                location = location_tag.get_text(strip=True) if location_tag else "Unknown"
                link    = link_tag["href"].split("?")[0]   if link_tag    else ""

                if not title_is_relevant(title):
                    continue

                # Second request for full JD \u2014 only for relevant titles
                jd_text = fetch_jd_text(link) if link else ""

                jobs.append({
                    "platform":   "LinkedIn",
                    "role":       title,
                    "company":    company,
                    "location":   location,
                    "job_url":    link,
                    "jd_text":    jd_text,
                    "date_found": datetime.now().strftime("%Y-%m-%d %H:%M"),
                })
                print(f"[LinkedIn] + {title} @ {company}")

            except Exception as e:
                print(f"[LinkedIn] Error parsing card: {e}")
                continue

    if jobs:
        global POSTER_REQ_MISSES
        print(f"  [Metrics] Poster-requirements block absent: {POSTER_REQ_MISSES}/{len(jobs)} jobs (expected under unauthenticated scraping).")
        POSTER_REQ_MISSES = 0 # reset for next run

    return jobs

def save_to_db(jobs: list[dict]):
    if not jobs:
        return
    # Ensure database path is correct relative to the script run location
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "outcome_log.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    inserted = 0
    for job in jobs:
        try:
            # Strict Deduplication: Check if exact company + role or exact URL already exists
            cursor.execute("SELECT 1 FROM applications WHERE company = ? AND role = ?", (job["company"], job["role"]))
            if cursor.fetchone():
                continue  # Duplicate company/role combination
                
            cursor.execute("SELECT 1 FROM applications WHERE job_url = ?", (job["job_url"],))
            if cursor.fetchone():
                continue  # Duplicate job URL

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
    print(f"[LinkedIn] Saved {inserted} new jobs to DB (duplicates skipped)")


if __name__ == "__main__":
    all_jobs = []
    for kw in KEYWORDS[:5]:
        print(f"\n--- Scraping: {kw} ---")
        results = scrape_linkedin(kw, pages=1)
        all_jobs.extend(results)
        time.sleep(random.uniform(4, 8))   # Between keywords

    save_to_db(all_jobs)
    print(f"\nTotal scraped: {len(all_jobs)}")
