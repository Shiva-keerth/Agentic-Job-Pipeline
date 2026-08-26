"""
Round 18: AI Engineer / GenAI pipeline — 15 Results Target
Fresh keywords — all previous rounds 1-17 excluded
"""
import os, sys, json, time, random, io, re

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

ALLOWED_ROLE_KEYWORDS = [
    "ai engineer", "gen ai", "genai", "generative ai", "llm engineer",
    "llm developer", "agentic", "prompt engineer", "ai developer",
    "nlp engineer", "ai software engineer", "machine learning engineer",
    "ml engineer", "applied ai", "ai backend", "conversational ai",
    "foundation model", "ai product engineer", "associate ai",
    "software engineer", "forward deployed engineer", "ai agent",
    "ai/ml engineer", "ai ml engineer", "junior ai", "trainee ai",
    "python developer", "python engineer", "backend engineer",
    "ai intern", "ai associate", "language model", "rag engineer",
    "llmops", "mlops engineer", "ai platform engineer",
]

BLOCKED_ROLE_KEYWORDS = [
    "data scientist", "research analyst", "research scientist",
    "technical writer", "applied scientist", "data analyst",
    "data engineer", "business analyst", "cloud engineer",
    "devops", "content writer", "seo", "marketing",
    "sales", "account manager", "hr", "recruiter",
    "product manager", "project manager", "scrum",
    "data entry", "support engineer", "qa engineer",
    "test engineer", "tester", "network engineer",
    "customer support", "operations", "finance",
    "blockchain", "web3", "embedded", "firmware",
]

CORE_GAP_SIGNALS = [
    "java", "c++", "c#", "scala", "golang", "go lang", "rust",
    "r language", "r programming", "rstudio",
    "computer vision", "opencv", "image processing",
    "video generation", "diffusion model", "stable diffusion",
    "oracle", "mainframe", "cobol",
    "salesforce", "sap", "erp",
    "itsm", "servicenow",
    "3+ years", "4+ years", "5+ years",
]

TOOL_GAP_SIGNALS = [
    "llamaindex", "llamaparse", "crewai", "autogen", "langflow",
    "tableau", "powerbi", "power bi", "grafana", "kibana",
    "xgboost", "lightgbm", "catboost", "celery", "redis", "kafka",
    "mlflow", "wandb", "node.js", "react", "angular", "vue",
    "snowflake", "databricks", "rlhf", "n8n", "airflow",
    "kubernetes", "ci/cd", "jenkins", "typescript",
    "postgresql", "mysql", "terraform",
]

# ── Load ALL previous rounds to exclude URLs and companies ──
prev_files = [
    f"top10_results.json",
    *[f"top10_round{i}_results.json" for i in range(2, 18)]
]

# No hardcoded company blacklist. We rely on deduplication (URL and Company|Title)
# and experience filters to reject senior roles.
EXCLUDE_COMPANIES = set()

EXCLUDE_URLS = set()
PREV_SEEN_KEYS = set()

for pf in prev_files:
    try:
        if os.path.exists(pf):
            with open(pf, "r", encoding="utf-8") as f:
                prev = json.load(f)
                for j in prev:
                    EXCLUDE_URLS.add(j.get("url", j.get("job_url", "")).strip())
                    
                    # Instead of blacklisting the whole company, just blacklist this specific role at this company
                    c_name = j.get("company", "").strip().lower()
                    t_name = j.get("title", j.get("role", "")).strip().lower()
                    if c_name and t_name:
                        PREV_SEEN_KEYS.add(f"{c_name}|{t_name}")
    except Exception as e:
        print(f"Error loading {pf}: {e}")

print(f"Loaded {len(EXCLUDE_URLS)} previous URLs and {len(PREV_SEEN_KEYS)} specific previous roles to exclude.")

# ── Round 18: Completely fresh keywords ──
SEARCH_KEYWORDS = [
    "AI Backend Engineer India entry level",
    "Junior Applied AI Developer India",
    "LLM software engineer Python fresher",
    "GenAI application builder India",
    "AI NLP developer India junior",
    "AI logic developer India fresher",
    "RAG pipeline builder India entry level",
    "Agentic workflow developer India",
    "Python AI integration engineer India",
    "Junior foundation model engineer India",
    "AI inference developer India fresher",
    "FastAPI AI backend India junior",
    "Conversational AI application developer India",
    "AI/ML prototype developer India fresher",
    "Junior prompt and RAG developer India"
]

ATS_SELECTORS = [
    "div#content", "div.job__description", "div.posting-body",
    "div.content", "div.posting-description",
    "div[data-automation-id='jobPostingDescription']",
    "div[class*='jobDescription']", "div[class*='job-description']",
    "section.job-description", "div.job-description__content",
    "div#description", "div.description",
    "div.iCIMS_JobContent", "div.dang-inner-html",
    "div[class*='JobDescription']", "div[class*='job-detail']",
    "article.job", "article", "main",
]

def is_role_allowed(title):
    title_lower = title.lower()
    for blocked in BLOCKED_ROLE_KEYWORDS:
        if blocked in title_lower:
            return False, f"Blocked: '{blocked}'"
    for allowed in ALLOWED_ROLE_KEYWORDS:
        if allowed in title_lower:
            return True, f"Matched: '{allowed}'"
    return False, "Not in whitelist"

def analyze_apply_decision(missing_skills):
    if not missing_skills:
        return "APPLY", "No missing skills — perfect match!"
    missing_text = " ".join([s.lower() for s in missing_skills])
    core_gaps = [s for s in CORE_GAP_SIGNALS if s in missing_text]
    tool_gaps = [s for s in TOOL_GAP_SIGNALS if s in missing_text]
    if core_gaps:
        return "SKIP", f"Core gaps: {', '.join(core_gaps)}"
    elif tool_gaps:
        return "APPLY", f"Tool gaps only (learnable): {', '.join(tool_gaps)}"
    return "APPLY", "Missing skills are optional tools"

def fetch_external_jd(url):
    try:
        time.sleep(random.uniform(2, 4))
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return ""
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup.find_all(["nav", "header", "footer", "script", "style"]):
            tag.decompose()
        best = ""
        for sel in ATS_SELECTORS:
            try:
                el = soup.select_one(sel)
                if el:
                    t = el.get_text(separator=" ", strip=True)
                    if len(t) > len(best):
                        best = t
            except Exception:
                continue
        if len(best) < 150:
            for tag in soup.find_all(["div", "section", "article"]):
                t = tag.get_text(separator=" ", strip=True)
                if 150 < len(t) < 10000 and len(t) > len(best):
                    best = t
        return best[:6000]
    except Exception:
        return ""

def fetch_jd_text(job_url):
    is_external = False
    try:
        time.sleep(random.uniform(2.5, 4.5))
        r = requests.get(job_url, headers=HEADERS, timeout=12)
        if r.status_code != 200:
            return "", False
        soup = BeautifulSoup(r.text, "html.parser")
        page_lower = soup.get_text(separator=" ", strip=True).lower()
        if "no longer accepting applications" in page_lower:
            return "[CLOSED]", False
        for el in soup.find_all(class_=["similar-jobs", "people-also-viewed"]):
            el.decompose()
        desc = soup.find("div", class_="show-more-less-html__markup")
        jd = desc.get_text(separator=" ", strip=True) if desc else ""
        if not jd or len(jd) < 80:
            for sel in ["div.description__text", "section.show-more-less-html", "div[class*='description']"]:
                try:
                    el = soup.select_one(sel)
                    if el:
                        c = el.get_text(separator=" ", strip=True)
                        if len(c) > len(jd):
                            jd = c
                except Exception:
                    continue
        if not jd or len(jd) < 80:
            ext_url = None
            match = re.search(r'"applyUrl"\s*:\s*"(https?://[^"]+)"', r.text)
            if match:
                ext_url = match.group(1).replace("\\u003d", "=").replace("\\u0026", "&")
            if not ext_url:
                for a in soup.find_all("a", href=True):
                    href = a.get("href", "")
                    if "linkedin.com" not in href and href.startswith("http"):
                        if any(k in href.lower() for k in ["/jobs/", "/careers/", "/apply", "/job/", "/opening"]):
                            ext_url = href
                            break
            if ext_url:
                print(f"        [EXTERNAL] {ext_url[:80]}...")
                jd = fetch_external_jd(ext_url)
                is_external = True
        if not jd or len(jd) < 80:
            return "", is_external
        return jd, is_external
    except Exception:
        return "", False

def scrape_search_page(keyword, start=0):
    url = (
        f"https://www.linkedin.com/jobs/search/"
        f"?keywords={keyword.replace(' ', '+')}"
        f"&location=India"
        f"&f_E=2"
        f"&f_JT=F"
        f"&f_TPR=r172800"
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
    TARGET = 15
    valid_jobs = []
    seen_urls = set(EXCLUDE_URLS)
    seen_keys = set(PREV_SEEN_KEYS)
    role_rejected = 0

    print(f"{'='*62}")
    print(f"  JOBLINE PIPELINE — ROUND 18 (Target: {TARGET} Results)")
    print(f"  2-Day Window | LinkedIn Public Search")
    print(f"  Excluding {len(EXCLUDE_URLS)} URLs + {len(PREV_SEEN_KEYS)} previous roles")
    print(f"  Keywords: {len(SEARCH_KEYWORDS)}")
    print(f"{'='*62}\n")

    for kw_idx, keyword in enumerate(SEARCH_KEYWORDS):
        if len(valid_jobs) >= TARGET:
            break
        print(f"\n[{kw_idx+1}/{len(SEARCH_KEYWORDS)}] '{keyword}'")

        cards = []
        for start in [0, 25, 50, 75]:
            page = scrape_search_page(keyword, start=start)
            cards.extend(page)
            if not page:
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

            dedup_key = f"{company.lower().strip()}|{title.lower().strip()}"
            if dedup_key in seen_keys:
                continue

            seen_urls.add(link)
            seen_keys.add(dedup_key)

            if is_blacklisted(company):
                continue

            role_ok, role_reason = is_role_allowed(title)
            if not role_ok:
                role_rejected += 1
                print(f"    [ROLE] '{title[:60]}' — {role_reason}")
                continue

            safe_t = title.encode('ascii', 'ignore').decode('ascii')
            safe_c = company.encode('ascii', 'ignore').decode('ascii')
            print(f"    Checking: {safe_t[:55]} @ {safe_c[:30]}")

            jd_text, is_external = fetch_jd_text(link)

            if jd_text == "[CLOSED]":
                print(f"      -> Skipped (CLOSED)")
                continue
            if not jd_text:
                print(f"      -> Skipped (empty JD)")
                continue
            if has_aggregator_signals(jd_text):
                print(f"      -> Skipped (aggregator)")
                continue

            is_filtered, match_str = pre_filter_experience(jd_text, title)
            if is_filtered:
                print(f"      -> Rejected (exp: '{match_str}')")
                continue

            job_dict = {"company": company, "role": title, "job_url": link}
            eval_res = evaluate_job(job_dict, jd_text)

            if not eval_res:
                print(f"      -> Skipped (LLM error)")
                continue

            score = eval_res.get("match_score", 0)
            verdict = eval_res.get("verdict", "")

            if verdict in ["DISQUALIFIED", "BLACKLISTED"] or score < 60:
                print(f"      -> Rejected (Score: {score}, {verdict})")
                continue

            missing_skills = eval_res.get("missing_skills", [])
            apply_decision, apply_reason = analyze_apply_decision(missing_skills)

            valid_jobs.append({
                "title": title,
                "company": company,
                "url": link,
                "score": score,
                "verdict": verdict,
                "reason": eval_res.get("reason", ""),
                "experience_required": eval_res.get("experience_required", "Not specified"),
                "matched_skills": eval_res.get("matched_skills", []),
                "missing_skills": missing_skills,
                "apply_decision": apply_decision,
                "apply_reason": apply_reason,
                "is_external_apply": is_external,
            })
            apply_type = "External" if is_external else "Easy Apply"
            print(f"      -> ADDED! Score:{score} | {verdict} | {apply_decision} | {apply_type}")
            print(f"         #{len(valid_jobs)}/{TARGET}")

        time.sleep(random.uniform(3, 6))

    print(f"\n{'='*62}")
    print(f"  DONE: {len(valid_jobs)} Qualified Jobs Found")
    print(f"  Role rejected: {role_rejected}")
    print(f"{'='*62}\n")

    valid_jobs.sort(key=lambda x: x["score"], reverse=True)

    for i, job in enumerate(valid_jobs, 1):
        apply_type = "External" if job["is_external_apply"] else "Easy Apply"
        print(f"--- Job #{i} [{apply_type}] ---")
        print(f"  Role:       {job['title']}")
        print(f"  Company:    {job['company']}")
        print(f"  Score:      {job['score']}")
        print(f"  Verdict:    {job['verdict']}")
        print(f"  Decision:   {job['apply_decision']}")
        print(f"  Exp needed: {job['experience_required']}")
        print(f"  Skills OK:  {', '.join(job['matched_skills'][:7]) or 'N/A'}")
        print(f"  Missing:    {', '.join(job['missing_skills'][:4]) or 'None'}")
        print(f"  Reason:     {job['reason'][:120]}")
        print(f"  LINK:       {job['url']}")
        print()

    output_file = "top10_round18_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(valid_jobs, f, indent=2, ensure_ascii=False)
    print(f"Saved to {output_file}")
    apply_c = sum(1 for j in valid_jobs if j["apply_decision"] == "APPLY")
    skip_c = sum(1 for j in valid_jobs if j["apply_decision"] == "SKIP")
    print(f"SUMMARY: {apply_c} to APPLY | {skip_c} to SKIP")

if __name__ == "__main__":
    main()
