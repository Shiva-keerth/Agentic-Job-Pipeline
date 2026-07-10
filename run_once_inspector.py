from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(user_agent=(
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
    ))
    page.goto(
        "https://www.naukri.com/ai-engineer-jobs?experience=0",
        wait_until="networkidle",
        timeout=30000
    )
    # Save full rendered HTML to file
    with open("naukri_rendered.html", "w", encoding="utf-8") as f:
        f.write(page.content())
    print("Saved. Open naukri_rendered.html in browser and inspect job card classes.")
    browser.close()
