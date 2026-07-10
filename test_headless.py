from playwright.sync_api import sync_playwright

url = "https://in.linkedin.com/jobs/view/generative-ai-engineer-at-the-agentic-loop-4436823364"

def test_headless():
    with sync_playwright() as p:
        print("Launching headless browser (zero cookies/auth)...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        print(f"Navigating to {url}")
        # Wait until network is mostly idle to ensure JS renders
        try:
            page.goto(url, wait_until="networkidle", timeout=15000)
        except Exception as e:
            print(f"Navigation complete (or timed out waiting for idle): {e}")
            
        print("Searching for poster requirements block in rendered DOM...")
        
        # Look for the block
        content = page.query_selector('.job-details-module__content')
        if content:
            print(f"\n-> SUCCESS! The block DOES exist when JS is rendered. Here is the text:")
            print(f"'{content.inner_text().strip()}'")
        else:
            print("\n-> ABSENT. Even with full JS rendering, the block is hidden from logged-out users.")
            
        browser.close()

if __name__ == "__main__":
    test_headless()
