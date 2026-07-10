import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
    )
}

url = "https://in.linkedin.com/jobs/view/generative-ai-engineer-at-the-agentic-loop-4436823364"
print(f"Fetching: {url}")
r = requests.get(url, headers=HEADERS, timeout=10)

if r.status_code == 200:
    soup = BeautifulSoup(r.text, "html.parser")
    full_text = soup.get_text(separator=" ", strip=True).lower()
    
    if "2+ years" in full_text or "requirements added by" in full_text:
        print("-> FOUND the requirements in the raw DOM! We just have the wrong selector.")
        # Try to find the exact container
        for div in soup.find_all("div"):
            if "requirements added by" in div.get_text(strip=True).lower():
                print(f"-> Found container class: {div.get('class')}")
                break
    else:
        print("-> ABSENT. The 'Requirements added by the job poster' block does NOT load on the logged-out page.")
else:
    print(f"Failed to fetch URL. Status: {r.status_code}")
