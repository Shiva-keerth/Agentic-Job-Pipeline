# Agentic Job Pipeline (15-Day Push)

An automated, end-to-end AI agentic pipeline designed to scrape, rigorously filter, and evaluate job opportunities in real-time using Large Language Models. Built to eliminate the noise of modern job hunting, this system autonomously finds high-fit GenAI and AI Engineering roles.

## 🚀 Features

- **Real-time LinkedIn Scraping**: Live extraction of job postings with robust DOM monitoring and metric aggregation to detect layout changes or auth-walls.
- **Precision Pre-filtering**: Aggressive regex-based pre-filters that instantly disqualify senior roles (e.g., "5+ years experience") to save LLM inference costs and reduce noise.
- **Agentic LLM Evaluation**: Leverages LangChain and the Groq API (Llama-3) to semantically score jobs against a candidate's resume based on multiple signals.
- **Stateful Processing**: SQLite database integration to archive historical runs, track application status, and prevent duplicate evaluations of stale data.

## 🛠️ Tech Stack

- **Python 3.10+**
- **LangChain & Groq API** (Llama-3 for high-speed inference)
- **SQLite** (Persistent storage)
- **BeautifulSoup4 / Requests** (Data extraction)

## 🏗️ Architecture

1. **Scraping Engine (`scrapers/linkedin_scraper.py`)**: Fetches unauthenticated job data, with built-in observability for missing elements.
2. **Evaluation Core (`core/llm_evaluator.py`)**: 
    - Applies strict tuple-based pre-filtering `(bool, matched_span)` for actionable debugging.
    - Prompts the LLM with the job description and candidate resume to output a JSON payload containing a `score` and `reason`.
3. **Execution Loop (`fetch_and_eval.py`)**: Bypasses stale DB entries to fetch live jobs, run them through the gauntlet, and output the top highest-scored opportunities.

## ⚙️ Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Shiva-keerth/Agentic-Job-Pipeline.git
   cd Agentic-Job-Pipeline
   ```
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure Environment:**
   Create a `.env` file in the root directory and add your API keys:
   ```env
   GROQ_API_KEY=your_groq_api_key
   ```
4. **Run the Live Pipeline:**
   ```bash
   python fetch_and_eval.py
   ```

## 📈 Future Roadmap

- Integration with Playwright for authenticated, high-scale scraping.
- Automated cover letter generation tailored to the LLM's identified "Reason for Fit".
- Direct integration with LinkedIn Auto-Apply flows.
