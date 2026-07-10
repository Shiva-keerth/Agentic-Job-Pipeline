import json
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
    )
}

url = "https://www.linkedin.com/jobs/search/?keywords=Generative+AI+Engineer&location=India&f_E=2&f_JT=F&f_TPR=r86400&start=0"
r = requests.get(url, headers=HEADERS, timeout=10)
soup = BeautifulSoup(r.text, "html.parser")
cards = soup.find_all("div", class_="base-card")

jobs = []
for card in cards:
    try:
        title_tag  = card.find("h3", class_="base-search-card__title")
        company_tag = card.find("h4", class_="base-search-card__subtitle")
        link_tag   = card.find("a", class_="base-card__full-link")
        
        title   = title_tag.get_text(strip=True) if title_tag else "Unknown"
        company = company_tag.get_text(strip=True) if company_tag else "Unknown"
        link    = link_tag["href"].split("?")[0] if link_tag else ""
        
        t_low = title.lower()
        if "ai" in t_low or "generative" in t_low or "machine learning" in t_low:
            jobs.append({"title": title, "company": company, "url": link})
            if len(jobs) >= 10:
                break
    except:
        pass

print(json.dumps(jobs, indent=2))
