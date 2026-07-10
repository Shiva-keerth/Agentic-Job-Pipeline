import requests
from bs4 import BeautifulSoup
import json

url = "https://in.linkedin.com/jobs/view/generative-ai-engineer-at-headway-tek-inc-4432750263"
headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
    )
}

try:
    r = requests.get(url, headers=headers, timeout=10)
    print("Status:", r.status_code)
    soup = BeautifulSoup(r.text, "html.parser")
    
    # Let's find "No longer accepting applications"
    closed_div = soup.find(text=lambda t: t and "No longer accepting applications" in t)
    print("Closed banner found?", bool(closed_div))
    
    # Let's find the JD
    desc = soup.find("div", class_="show-more-less-html__markup")
    if desc:
        print("\nDesc length:", len(desc.get_text(separator=" ", strip=True)))
    
    # Let's find "Requirements added by the job poster"
    reqs = soup.find_all("li", class_="description__job-criteria-item")
    print("\nJob Criteria:")
    for req in reqs:
        print("-", req.get_text(strip=True))
        
    print("\nAll text snippets containing 'years of work experience':")
    for elem in soup.find_all(text=lambda t: t and "years of work experience" in t.lower()):
        print("->", elem.strip())

except Exception as e:
    print("Error:", e)
