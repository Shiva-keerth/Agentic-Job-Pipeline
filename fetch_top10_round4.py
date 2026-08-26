"""
Round 4: Scrape LinkedIn, evaluate via LLM, return 10 NEW qualified jobs.
- Excludes all jobs from Rounds 1, 2, and 3.
- Automatically excludes companies from all previous rounds.
- Searches deeper pages (25, 50, 75, 100) and uses fresh keyword variations.
"""
import os, sys, json, time, random, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import requests
from bs4 import BeautifulSoup
from core.llm_evaluator import evaluate_job, pre_filter_experience, is_blacklisted, has_aggregator_signals

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36"
    )
}

# ── Exclusion list: all URLs and Companies from previous rounds ──
EXCLUDE_URLS = set()
EXCLUDE_COMPANIES = {
    "hcltech", "virtusa", "cognizant", "infosys", "strategic ventures-in",
    "wisdomai", "quest global", "centreax technologies",
    "honeywell technologies", "honeywell",
}

prev_files = ["top10_results.json", "top10_round2_results.json", "top10_round3_results.json"]
for pf in prev_files:
    try:
        if os.path.exists(pf):
            with open(pf, "r", encoding="utf-8") as f:
                prev = json.load(f)
                for j in prev:
                    EXCLUDE_URLS.add(j["url"].strip())
                    EXCLUDE_COMPANIES.add(j["company"].strip().lower())
    except Exception as e:
        print(f"Error loading {pf}: {e}")

print(f"Loaded {len(EXCLUDE_URLS)} previous URLs and {len(EXCLUDE_COMPANIES)} companies to exclude.")

SEARCH_KEYWORDS = [
    "AI Engineer fresher",
    "Generative AI 0-1 years",
    "Junior LLM Engineer",
    "Entry level Python AI",
    "RAG Developer",
    "Junior Machine Learning Engineer",
    "Prompt Engineer entry level",
    "Agentic AI Engineer",
    "AI Solutions Developer fresher",
    "NLP Engineer entry level"
]


def fetch_jd_text(job_url: str) -> str:
    """Fetch full JD text from a LinkedIn job page. Returns empty string if closed/empty."""
    try:
        time.sleep(random.uniform(2.5, 4.5))
        r = requests.get(job_url, headers=HEADERS, timeout=12)
        if r.status_code != 200:
            return ""
        soup = BeautifulSoup(r.text, "html.parser")

        # Skip closed jobs
        page_text = soup.get_text(separator=" ", strip=True).lower()
        if "no longer accepting applications" in page_text:
            return "[CLOSED]"

        for sidebar in soup.find_all(class_=["similar-jobs", "people-also-viewed"]):
            sidebar.decompose()

        desc = soup.find("div", class_="show-more-less-html__markup")
        jd = desc.get_text(separator=" ", strip=True) if desc else ""

        if not jd or len(jd) < 50:
            return ""  # Too short = broken page

        poster_reqs = soup.find("div", class_="job-details-module__content") or \
                      soup.find("ul", class_="description__job-criteria-list")
        if poster_reqs:
            jd += " \n\n REQUIREMENTS ADDED BY JOB POSTER: " + poster_reqs.get_text(separator=" ", strip=True)

        # External apply check
        apply_btn = soup.find("button", class_="apply-button") or soup.find("a", class_="apply-button")
        is_external = False
        if apply_btn:
            btn_text = apply_btn.get_text(strip=True).lower()
            if "easy apply" not in btn_text:
                is_external = True
        else:
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


def scrape_search_page(keyword: str, time_range: str = "r604800", start: int = 0) -> list[dict]:
    """Scrape one page of LinkedIn search results."""
    url = (
        f"https://www.linkedin.com/jobs/search/"
        f"?keywords={keyword.replace(' ', '+')}"
        f"&location=India"
        f"&f_E=2"
        f"&f_JT=F"
        f"&f_TPR={time_range}"
        f"&start={start}"
    )
    try:
        time.sleep(random.uniform(2, 5))
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return []
    except Exception:
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    cards = soup.find_all("div", class_="base-card")
    results = []

    for card in cards:
        try:
            title_tag = card.find("h3", class_="base-search-card__title")
            company_tag = card.find("h4", class_="base-search-card__subtitle")
            link_tag = card.find("a", class_="base-card__full-link")

            title = title_tag.get_text(strip=True) if title_tag else ""
            company = company_tag.get_text(strip=True) if company_tag else ""
            link = link_tag["href"].split("?")[0] if link_tag else ""

            if title and link:
                results.append({"title": title, "company": company, "link": link})
        except Exception:
            continue

    return results


def main():
    TARGET = 10
    valid_jobs = []
    seen_urls = set(EXCLUDE_URLS)
    seen_keys = set()

    print(f"{'='*60}")
    print(f"  JOBLINE PIPELINE — ROUND 4 (Fresh {TARGET} Jobs)")
    print(f"  Excluding {len(EXCLUDE_URLS)} previous jobs + {len(EXCLUDE_COMPANIES)} companies")
    print(f"  Searching past 7 days across {len(SEARCH_KEYWORDS)} keywords")
    print(f"{'='*60}\n")

    for kw_idx, keyword in enumerate(SEARCH_KEYWORDS):
        if len(valid_jobs) >= TARGET:
            break

        print(f"\n[{kw_idx+1}/{len(SEARCH_KEYWORDS)}] Searching: '{keyword}'")

        # Scrape deeper pages
        cards = []
        for page_start in [0, 25, 50, 75, 100]:
            page_cards = scrape_search_page(keyword, time_range="r604800", start=page_start)
            cards.extend(page_cards)
            if not page_cards:
                break

        print(f"    Found {len(cards)} cards")

        for card in cards:
            if len(valid_jobs) >= TARGET:
                break

            title = card["title"]
            company = card["company"]
            link = card["link"]

            if link in seen_urls:
                continue

            if company.lower().strip() in EXCLUDE_COMPANIES:
                continue

            dedup_key = f"{company.lower().strip()}|{title.lower().strip()}"
            if dedup_key in seen_keys:
                continue
            
            seen_urls.add(link)
            seen_keys.add(dedup_key)

            if is_blacklisted(company):
                continue

            safe_title = title.encode('ascii', 'ignore').decode('ascii')
            safe_company = company.encode('ascii', 'ignore').decode('ascii')
            print(f"    Checking: {safe_title} @ {safe_company}")

            jd_text = fetch_jd_text(link)
            if jd_text == "[CLOSED]":
                print(f"      -> Skipped (job is CLOSED)")
                continue
            if not jd_text:
                print(f"      -> Skipped (empty JD or broken page)")
                continue
            if has_aggregator_signals(jd_text):
                print(f"      -> Skipped (aggregator)")
                continue

            is_filtered, match_str = pre_filter_experience(jd_text, title)
            if is_filtered:
                print(f"      -> Rejected (experience: '{match_str}')")
                continue

            job_dict = {"company": company, "role": title, "job_url": link}
            eval_res = evaluate_job(job_dict, jd_text)

            if not eval_res:
                print(f"      -> Skipped (LLM error)")
                continue

            score = eval_res.get("match_score", 0)
            verdict = eval_res.get("verdict", "")

            if verdict in ["DISQUALIFIED", "BLACKLISTED"] or score < 60:
                print(f"      -> Rejected by LLM (Score: {score}, Verdict: {verdict})")
                continue

            valid_jobs.append({
                "title": title,
                "company": company,
                "url": link,
                "score": score,
                "verdict": verdict,
                "reason": eval_res.get("reason", ""),
                "experience_required": eval_res.get("experience_required", "Not specified"),
                "matched_skills": eval_res.get("matched_skills", []),
                "missing_skills": eval_res.get("missing_skills", []),
            })
            print(f"      -> ADDED! Score: {score} | Verdict: {verdict}")
            print(f"         #{len(valid_jobs)}/{TARGET} collected")

        time.sleep(random.uniform(3, 6))

    print(f"\n\n{'='*60}")
    print(f"  FINAL RESULTS: {len(valid_jobs)} Qualified Jobs (Round 4)")
    print(f"{'='*60}\n")

    valid_jobs.sort(key=lambda x: x["score"], reverse=True)

    for i, job in enumerate(valid_jobs, 1):
        print(f"--- Job #{i} ---")
        print(f"  Role:       {job['title']}")
        print(f"  Company:    {job['company']}")
        print(f"  Score:      {job['score']}")
        print(f"  Verdict:    {job['verdict']}")
        print(f"  Experience: {job['experience_required']}")
        print(f"  Reason:     {job['reason']}")
        skills_ok = ', '.join(job['matched_skills'][:8]) if job['matched_skills'] else 'N/A'
        missing = ', '.join(job['missing_skills'][:5]) if job['missing_skills'] else 'None'
        print(f"  Skills OK:  {skills_ok}")
        print(f"  Missing:    {missing}")
        print(f"  LINK:       {job['url']}")
        print()

    with open("top10_round4_results.json", "w", encoding="utf-8") as f:
        json.dump(valid_jobs, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to top10_round4_results.json")


if __name__ == "__main__":
    main()
