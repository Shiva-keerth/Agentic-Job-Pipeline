"""
Round 14: AI Engineer / GenAI pipeline — External ATS Support + Fresh Keywords.
- NEW: Added Round 13 exclusions to ensure zero repeats.
- Uses completely fresh keywords.
- STRICT experience filter: rejects roles requiring 2+ years.
- STRICT role whitelist: Only AI/GenAI/LLM/Python engineer roles.
- 2-day window (r172800).
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

# ── ROLE TITLE WHITELIST ──
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
]

# ── ROLE TITLE BLACKLIST ──
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

# ── TOOL-GAP keywords: Missing these = still apply ──
TOOL_GAP_SIGNALS = [
    "llamaindex", "llamaparse", "crewai", "autogen", "langflow",
    "tableau", "powerbi", "power bi", "grafana", "kibana",
    "xgboost", "lightgbm", "catboost", "svm", "random forest",
    "celery", "redis", "kafka", "terraform",
    "mlflow", "wandb", "weights & biases", "dvc",
    "node.js", "react", "angular", "vue",
    "snowflake", "databricks",
    "rlhf", "dpo", "reward modeling",
    "n8n", "airflow", "prefect",
    "kubernetes", "ci/cd", "jenkins",
    "typescript", "postgresql", "mysql", "microsoft copilot",
]

# ── CORE-GAP keywords: Missing these = SKIP ──
CORE_GAP_SIGNALS = [
    "java", "c++", "c#", "scala", "golang", "go lang", "rust",
    "r language", "r programming", "rstudio",
    "computer vision", "opencv", "image processing",
    "video generation", "diffusion model", "stable diffusion",
    "oracle", "mainframe", "cobol",
    "salesforce", "sap", "erp",
    "itsm", "servicenow",
    "sampling analytics",
    "3+ years", "4+ years", "5+ years",
]

def is_role_allowed(title: str) -> tuple:
    title_lower = title.lower()
    for blocked in BLOCKED_ROLE_KEYWORDS:
        if blocked in title_lower:
            return False, f"Blocked role type: '{blocked}'"
    for allowed in ALLOWED_ROLE_KEYWORDS:
        if allowed in title_lower:
            return True, f"Matched allowed role: '{allowed}'"
    return False, "Role title not in AI Engineer whitelist"


def analyze_apply_decision(missing_skills: list) -> tuple:
    if not missing_skills:
        return "APPLY", "No missing skills — perfect match!"
    missing_text = " ".join([s.lower() for s in missing_skills])
    core_gaps_found = [s for s in CORE_GAP_SIGNALS if s in missing_text]
    tool_gaps_found = [s for s in TOOL_GAP_SIGNALS if s in missing_text]
    if core_gaps_found:
        return "SKIP", f"Core skill gaps: {', '.join(core_gaps_found)}"
    elif tool_gaps_found:
        return "APPLY", f"Only tool gaps (learnable): {', '.join(tool_gaps_found)}"
    else:
        return "APPLY", "Missing skills appear to be optional tools, not core blockers"


# ── Exclusion list: ALL previous rounds 1-13 ──
EXCLUDE_URLS = set()
EXCLUDE_COMPANIES = {
    # Big IT — always block
    "hcltech", "virtusa", "cognizant", "infosys", "strategic ventures-in",
    "wisdomai", "quest global", "centreax technologies",
    "honeywell", "accenture", "wipro", "tcs",
    "tech mahindra", "mphasis", "ltimindtree", "hexaware",
    # Rounds 6-8
    "unifiedai", "trkfly ai", "avix labs", "goldman sachs", "visa shuttle",
    "nxtwave", "capgemini", "lexsi labs", "mstack ai", "m moser associates",
    "elevenlabs", "vahan.ai", "fello", "brillius technologies", "huntingcube",
    "aicines.ai", "clobrix technologies", "kipi.ai", "ust", "coderound ai",
    "hire feed", "mccormick flavor solutions", "gartner", "bayone solutions",
    "amazon", "spg consulting", "mccormick & company", "mccormick",
    "nielsen", "brainware university",
    # Rounds 9-11
    "freight tiger", "xlscout", "rudocode", "rooman technologies", "birlasoft",
    "shield", "shriram general insurance co. ltd.", "jobgether",
    "automation builders.ai", "swish",
    "ariedge", "workspeak", "streevia", "babaclick", "scoutit india",
    "wealthnest.ai", "thermo fisher scientific", "digimaxx ai solutions",
    "zensar technologies", "namo cloud solutions inc",
    # Round 12
    "moleculyst", "rivirtual inc", "juicelabs ai", "ai vidya",
    "solventum", "workbudi", "appinventiv",
    # Round 13
    "medinex workforce", "naresh i technologies", "zenithbyte", 
    "kapariai", "engagezy ai", "hired", "quik hire staffing"
}

prev_files = [
    "top10_results.json", "top10_round2_results.json", "top10_round3_results.json",
    "top10_round4_results.json", "top10_round5_results.json", "top10_round6_results.json",
    "top10_round7_results.json", "top10_round8_results.json", "top10_round9_results.json",
    "top10_round10_results.json", "top10_round11_results.json", "top10_round12_results.json",
    "top10_round13_results.json",
]
for pf in prev_files:
    try:
        if os.path.exists(pf):
            with open(pf, "r", encoding="utf-8") as f:
                prev = json.load(f)
                for j in prev:
                    EXCLUDE_URLS.add(j.get("url", j.get("job_url", "")).strip())
                    EXCLUDE_COMPANIES.add(j["company"].strip().lower())
    except Exception as e:
        print(f"Error loading {pf}: {e}")

print(f"Loaded {len(EXCLUDE_URLS)} previous URLs and {len(EXCLUDE_COMPANIES)} companies to exclude.")

# ── Round 14 — FRESH keywords ──
SEARCH_KEYWORDS = [
    "AI engineer fresher remote India",
    "LLM application developer junior India",
    "LangGraph Python developer entry level India",
    "GenAI startup engineer junior Bengaluru",
    "RAG developer junior remote India",
    "Prompt engineer fresher India 2026",
    "AI backend developer junior Hyderabad",
    "generative AI python fresher India",
    "multi-agent systems developer junior India",
    "AI/ML engineer fresher remote India",
    "FastAPI LLM developer junior India",
    "Vector Database RAG developer entry level India"
]

# ─────────────────────────────────────────────────────────────
#  ENHANCED JD FETCHER — handles Easy Apply + External ATS
# ─────────────────────────────────────────────────────────────

ATS_SELECTORS = [
    "div#content", "div.job__description", "div.posting-body",
    "div.content", "div.posting-description", "div.section-wrapper.page-centered",
    "div[data-automation-id='jobPostingDescription']",
    "div[class*='jobDescription']", "div[class*='job-description']",
    "section.job-description", "div.job-description__content",
    "div#description", "div.description",
    "div.iCIMS_JobContent", "div.iCIMS_Expandable_Container",
    "div.job-desc", "div.jd-desc", "div.dang-inner-html",
    "section.styles_job-desc-container__txpYf",
    "div#requisitionDescriptionInterface\\.ID_DESCRIPTION_TEXT",
    "div[class*='JobDescription']", "div[class*='job-detail']",
    "div[id*='description']", "div[id*='job-detail']",
    "article.job", "article", "main",
]

def fetch_external_jd(url: str) -> str:
    try:
        time.sleep(random.uniform(2, 4))
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return ""
        soup = BeautifulSoup(r.text, "html.parser")

        for tag in soup.find_all(["nav", "header", "footer", "script", "style", "noscript"]):
            tag.decompose()

        best_text = ""
        for selector in ATS_SELECTORS:
            try:
                el = soup.select_one(selector)
                if el:
                    t = el.get_text(separator=" ", strip=True)
                    if len(t) > len(best_text):
                        best_text = t
            except Exception:
                continue

        if len(best_text) < 150:
            candidates = soup.find_all(["div", "section", "article"])
            for c in candidates:
                t = c.get_text(separator=" ", strip=True)
                if 150 < len(t) < 10000 and len(t) > len(best_text):
                    best_text = t

        return best_text[:6000] if best_text else ""
    except Exception as e:
        return ""

def fetch_jd_text(job_url: str) -> tuple:
    is_external = False
    try:
        time.sleep(random.uniform(2.5, 4.5))
        r = requests.get(job_url, headers=HEADERS, timeout=12)
        if r.status_code != 200:
            return "", False

        soup = BeautifulSoup(r.text, "html.parser")
        page_text_lower = soup.get_text(separator=" ", strip=True).lower()

        if "no longer accepting applications" in page_text_lower:
            return "[CLOSED]", False

        for sidebar in soup.find_all(class_=["similar-jobs", "people-also-viewed"]):
            sidebar.decompose()

        desc = soup.find("div", class_="show-more-less-html__markup")
        jd = desc.get_text(separator=" ", strip=True) if desc else ""

        if not jd or len(jd) < 80:
            for selector in [
                "div.description__text",
                "div.job-view-layout jobs-details",
                "section.show-more-less-html",
                "div[class*='description--is-expanded']",
                "div[class*='description']",
            ]:
                try:
                    el = soup.select_one(selector)
                    if el:
                        candidate = el.get_text(separator=" ", strip=True)
                        if len(candidate) > len(jd):
                            jd = candidate
                except Exception:
                    continue

        if not jd or len(jd) < 80:
            external_url = None
            src = r.text
            match = re.search(r'"applyUrl"\s*:\s*"(https?://[^"]+)"', src)
            if match:
                external_url = match.group(1).replace("\\u003d", "=").replace("\\u0026", "&")

            if not external_url:
                for a_tag in soup.find_all("a", href=True):
                    href = a_tag.get("href", "")
                    if "linkedin.com" not in href and href.startswith("http"):
                        cls = " ".join(a_tag.get("class", []))
                        if any(k in cls.lower() for k in ["apply", "topcard__link"]):
                            external_url = href
                            break

            if not external_url:
                for a_tag in soup.find_all("a", href=True):
                    href = a_tag.get("href", "")
                    if "linkedin.com" not in href and href.startswith("http"):
                        if any(k in href.lower() for k in ["/jobs/", "/careers/", "/apply", "/job/", "/opening"]):
                            external_url = href
                            break

            if external_url:
                print(f"        [EXTERNAL] Following: {external_url[:80]}...")
                jd = fetch_external_jd(external_url)
                is_external = True

        if not jd or len(jd) < 80:
            return "", is_external

        poster_reqs = soup.find("div", class_="job-details-module__content") or \
                      soup.find("ul", class_="description__job-criteria-list")
        if poster_reqs:
            jd += " \n\nREQUIREMENTS: " + poster_reqs.get_text(separator=" ", strip=True)

        return jd, is_external
    except Exception:
        return "", False

def scrape_search_page(keyword: str, start: int = 0) -> list:
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
    TARGET = 10
    valid_jobs = []
    seen_urls = set(EXCLUDE_URLS)
    seen_keys = set()
    role_rejected_count = 0
    external_fetched_count = 0

    print(f"{'='*60}")
    print(f"  JOBLINE PIPELINE — ROUND 14 (External ATS Support)")
    print(f"  2-Day Window | Easy Apply + External Company Sites")
    print(f"  Excluding {len(EXCLUDE_URLS)} previous jobs + {len(EXCLUDE_COMPANIES)} companies")
    print(f"  Searching across {len(SEARCH_KEYWORDS)} fresh keywords")
    print(f"{'='*60}\n")

    for kw_idx, keyword in enumerate(SEARCH_KEYWORDS):
        if len(valid_jobs) >= TARGET:
            break

        print(f"\n[{kw_idx+1}/{len(SEARCH_KEYWORDS)}] Searching: '{keyword}'")

        cards = []
        for page_start in [0, 25, 50]:
            page_cards = scrape_search_page(keyword, start=page_start)
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

            role_ok, role_reason = is_role_allowed(title)
            if not role_ok:
                role_rejected_count += 1
                safe_title = title.encode('ascii', 'ignore').decode('ascii')
                print(f"    [ROLE FILTER] Rejected '{safe_title}' — {role_reason}")
                continue

            safe_title = title.encode('ascii', 'ignore').decode('ascii')
            safe_company = company.encode('ascii', 'ignore').decode('ascii')
            print(f"    Checking: {safe_title} @ {safe_company}")

            jd_text, is_external = fetch_jd_text(link)

            if jd_text == "[CLOSED]":
                print(f"      -> Skipped (job is CLOSED)")
                continue
            if not jd_text:
                print(f"      -> Skipped (empty JD — private/JS-rendered page)")
                continue
            if has_aggregator_signals(jd_text):
                print(f"      -> Skipped (aggregator)")
                continue

            if is_external:
                external_fetched_count += 1
                print(f"      [EXTERNAL JD fetched — {len(jd_text)} chars]")
                jd_text += " [EXTERNAL_APPLY_FLAG]"

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
            apply_type = "🌐 External" if is_external else "⚡ Easy Apply"
            print(f"      -> ADDED! Score: {score} | {verdict} | {apply_decision} | {apply_type}")
            print(f"         #{len(valid_jobs)}/{TARGET} collected")

        time.sleep(random.uniform(3, 6))

    print(f"\n\n{'='*60}")
    print(f"  FINAL RESULTS: {len(valid_jobs)} Qualified AI Engineer Jobs")
    print(f"  Easy Apply: {sum(1 for j in valid_jobs if not j['is_external_apply'])}  |  External: {sum(1 for j in valid_jobs if j['is_external_apply'])}")
    print(f"  External JDs fetched during run: {external_fetched_count}")
    print(f"  (Role filter rejected {role_rejected_count} non-AI-Engineer roles)")
    print(f"{'='*60}\n")

    valid_jobs.sort(key=lambda x: x["score"], reverse=True)

    for i, job in enumerate(valid_jobs, 1):
        apply_type = "🌐 External" if job['is_external_apply'] else "⚡ Easy Apply"
        print(f"--- Job #{i} [{apply_type}] ---")
        print(f"  Role:       {job['title']}")
        print(f"  Company:    {job['company']}")
        print(f"  Score:      {job['score']}")
        print(f"  Verdict:    {job['verdict']}")
        print(f"  Experience: {job['experience_required']}")
        print(f"  Decision:   {job['apply_decision']}")
        print(f"  Why:        {job['apply_reason']}")
        print(f"  Reason:     {job['reason']}")
        skills_ok = ', '.join(job['matched_skills'][:8]) if job['matched_skills'] else 'N/A'
        missing = ', '.join(job['missing_skills'][:5]) if job['missing_skills'] else 'None'
        print(f"  Skills OK:  {skills_ok}")
        print(f"  Missing:    {missing}")
        print(f"  LINK:       {job['url']}")
        print()

    output_file = "top10_round14_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(valid_jobs, f, indent=2, ensure_ascii=False)
    print(f"Results saved to {output_file}")
    apply_count = sum(1 for j in valid_jobs if j['apply_decision'] == 'APPLY')
    skip_count = sum(1 for j in valid_jobs if j['apply_decision'] == 'SKIP')
    print(f"SUMMARY: {apply_count} to APPLY | {skip_count} to SKIP")

if __name__ == "__main__":
    main()
