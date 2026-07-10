import requests
from bs4 import BeautifulSoup
import time
import random
import sqlite3
import os
from datetime import datetime

# Path to the shared database
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'database', 'outcome_log.db'))

class NaukriScraper:
    def __init__(self):
        # We use a standard User-Agent to avoid immediate 403 Forbidden errors
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive'
        }
        # Base URL for AI Engineer jobs with 0-2 years experience
        # Experience: 0 to 2 years (experience=0-2)
        self.base_url = "https://www.naukri.com/ai-engineer-jobs?experience=0-2"

    def fetch_jobs(self, num_pages=1):
        """Fetches job listings from Naukri.com"""
        print(f"Starting Naukri Scraper for AI Engineer roles (0-2 YOE)...")
        all_jobs = []

        for page in range(1, num_pages + 1):
            url = f"{self.base_url}-{page}" if page > 1 else self.base_url
            print(f"Scraping Page {page}: {url}")
            
            try:
                # Naukri heavily restricts automated requests. We add a randomized delay.
                delay = random.uniform(2.0, 5.0)
                time.sleep(delay)
                
                # We use a session to maintain cookies
                session = requests.Session()
                response = session.get(url, headers=self.headers, timeout=10)
                
                if response.status_code != 200:
                    print(f"Failed to fetch page {page}. Status Code: {response.status_code}")
                    continue
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Parse job articles (Naukri usually uses <article class="jobTuple">)
                job_articles = soup.find_all('article', class_='jobTuple')
                
                if not job_articles:
                    print(f"No jobs found on page {page}. Naukri might be blocking the request or layout changed.")
                    # In a production system, we would trigger an email alert here (Stage 2)
                    break
                
                for job in job_articles:
                    try:
                        title_elem = job.find('a', class_='title')
                        company_elem = job.find('a', class_='subTitle')
                        
                        if title_elem and company_elem:
                            title = title_elem.text.strip()
                            company = company_elem.text.strip()
                            job_url = title_elem['href']
                            
                            job_data = {
                                'platform': 'Naukri',
                                'role': title,
                                'company': company,
                                'url': job_url
                            }
                            all_jobs.append(job_data)
                            self._log_to_db(job_data)
                    except Exception as e:
                        print(f"Error parsing a job card: {e}")
                        continue
                
                print(f"Successfully scraped {len(job_articles)} jobs from page {page}.")
                
            except Exception as e:
                print(f"Exception occurred while scraping page {page}: {e}")
                
        return all_jobs

    def _log_to_db(self, job):
        """Logs the scraped job to the SQLite database if it doesn't already exist."""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Check if job already exists to avoid duplicates
            cursor.execute("SELECT id FROM applications WHERE url = ?", (job['url'],))
            if cursor.fetchone() is None:
                date_scraped = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute('''
                    INSERT INTO applications (date_scraped, platform, company, role, url, match_score, status)
                    VALUES (?, ?, ?, ?, ?, 0.0, 'pending')
                ''', (date_scraped, job['platform'], job['company'], job['role'], job['url']))
                conn.commit()
            
            conn.close()
        except Exception as e:
            print(f"Database error: {e}")

if __name__ == "__main__":
    scraper = NaukriScraper()
    jobs = scraper.fetch_jobs(num_pages=1)
    print(f"\nTotal unique jobs scraped and logged: {len(jobs)}")
