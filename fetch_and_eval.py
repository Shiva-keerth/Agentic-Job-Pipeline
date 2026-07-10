import os
import json
import requests
import time
from bs4 import BeautifulSoup
from core.llm_evaluator import evaluate_job, pre_filter_experience, is_blacklisted, has_aggregator_signals

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
    )
}

from scrapers.linkedin_scraper import fetch_jd_text

print("Fetching latest GenAI roles from LinkedIn and passing through LLM evaluator...")
# Targeting both GenAI and AI engineer to ensure we get 10
urls = [
    "https://www.linkedin.com/jobs/search/?keywords=Generative+AI+Engineer&location=India&f_E=2&f_JT=F&f_TPR=r86400&start=0",
    "https://www.linkedin.com/jobs/search/?keywords=AI+Engineer&location=India&f_E=2&f_JT=F&f_TPR=r86400&start=0"
]

valid_jobs = []
for url in urls:
    r = requests.get(url, headers=HEADERS, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")
    cards = soup.find_all("div", class_="base-card")

    for card in cards:
        if len(valid_jobs) >= 10: # Limit to 10 perfectly evaluated jobs
            break
            
        try:
            title_tag = card.find("h3", class_="base-search-card__title")
            company_tag = card.find("h4", class_="base-search-card__subtitle")
            link_tag = card.find("a", class_="base-card__full-link")
            
            title = title_tag.get_text(strip=True) if title_tag else ""
            company = company_tag.get_text(strip=True) if company_tag else ""
            link = link_tag["href"].split("?")[0] if link_tag else ""
            
            if not title or not link: continue
            if is_blacklisted(company): continue
            
            # Print without weird characters for Windows terminal
            safe_title = title.encode('ascii', 'ignore').decode('ascii')
            safe_company = company.encode('ascii', 'ignore').decode('ascii')
            print(f"Checking: {safe_title} @ {safe_company}")
            
            jd_text = fetch_jd_text(link)
            if not jd_text or has_aggregator_signals(jd_text): continue
            is_filtered, match_str = pre_filter_experience(jd_text, title)
            if is_filtered: 
                print(f" -> Rejected by pre-filter (Matched: '{match_str}')")
                continue
            
            job_dict = {"company": company, "role": title, "job_url": link}
            eval_res = evaluate_job(job_dict, jd_text)
            
            if eval_res and eval_res.get("verdict") not in ["DISQUALIFIED", "BLACKLISTED"] and eval_res.get("match_score", 0) >= 70:
                valid_jobs.append({"title": title, "company": company, "url": link, "score": eval_res.get("match_score"), "reason": eval_res.get("reason")})
                print(f" -> ADDED! Score: {eval_res.get('match_score')}")
            else:
                score = eval_res.get("match_score", 0) if eval_res else 0
                print(f" -> Rejected by LLM (Score: {score})")
                
        except Exception as e:
            pass
        
        time.sleep(1)
        
    if len(valid_jobs) >= 10:
        break

print("\n--- FINAL EVALUATED JOBS ---")
print(json.dumps(valid_jobs, indent=2))
