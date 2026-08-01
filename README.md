# 🤖 Agentic Job Pipeline — AI-Powered Job Discovery Engine

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-Llama--3.3--70B-orange?style=for-the-badge&logo=groq&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-Orchestration-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-Persistence-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![BeautifulSoup](https://img.shields.io/badge/BeautifulSoup4-Scraping-59666C?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge)

An end-to-end **Agentic AI Job Discovery & Evaluation Pipeline** built to eliminate the noise of modern job hunting. The system autonomously scrapes LinkedIn, applies precision pre-filters, and uses **Groq-powered LLM evaluation** (Llama-3.3-70B) to semantically score roles against a structured candidate profile — returning only the highest-match GenAI and AI Engineering opportunities.

Across **5 active rounds**, the pipeline has evaluated hundreds of job descriptions and surfaced the top-fit roles with zero duplicates between rounds.

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    subgraph Input Layer
        KW[Keyword Variations\nAI Engineer, LLM Developer, RAG Fresher...]
        LI[LinkedIn Jobs Search\nIndia • Entry Level • f_E=2]
    end

    subgraph Scraping Engine [BeautifulSoup4 + Requests]
        SC[Job Card Extraction\nTitle, Company, URL]
        JD[Full JD Fetcher\nDescription + Poster Requirements]
        CLOSED{Job Closed?}
    end

    subgraph Pre-Filter Rules Engine [Zero LLM Cost]
        BL[Company Blacklist\nHCL, Cognizant, Infosys...]
        EXP[Experience Regex Filter\n5+ yrs, 3-5 years, Senior...]
        AGG[Aggregator Signal Detector\nrecruitment spam filter]
        DEDUP[URL + Company Deduplication\nCross-round exclusion]
    end

    subgraph LLM Evaluation Core [Groq LPU — Llama-3.3-70B]
        PROFILE[Candidate Profile Injection\nSkills, Projects, CGPA, Tools]
        SCORE[Match Scoring Engine\n0-100 Score + Verdict]
        REASON[Structured JSON Output\nmatched_skills, missing_skills, reason]
        TELEMETRY[(SQLite Telemetry DB\nlatency_ms, tokens, verdict)]
    end

    subgraph Output Layer
        TOP10[Top 10 Ranked Jobs\nSorted by Match Score]
        JSON[(Round Results JSON\ntop10_roundN_results.json)]
    end

    KW --> LI --> SC --> JD --> CLOSED
    CLOSED -- "Yes" --> KW
    CLOSED -- "No" --> BL --> EXP --> AGG --> DEDUP
    DEDUP --> PROFILE --> SCORE --> REASON --> TELEMETRY
    SCORE -- "Score ≥ 60" --> TOP10
    SCORE -- "Score < 60 / DISQUALIFIED" --> KW
    TOP10 --> JSON
```

---

## ✨ Core Pipeline Features

### 1️⃣ Multi-Round Deduplication System
Every run loads all URLs and companies from all previous round JSON files (`top10_results.json` through `top10_round4_results.json`), ensuring **zero overlap** between rounds. Each new round also uses fresh keyword variants to expand discovery surface area.

### 2️⃣ Precision Pre-Filter Rules Engine (Zero LLM Cost)
Before any expensive LLM inference, the pipeline applies a layered rule-based filter:
*   **Company Blacklist:** Hardcoded exclusion of mass-hiring aggregators (HCL, Cognizant, Infosys, Virtusa, etc.)
*   **Experience Regex Filter:** Instantly disqualifies roles requiring `"5+ years"`, `"Senior"`, `"Lead"`, or `"10 years"` experience. Saves inference budget by ~60%.
*   **Aggregator Signal Detector:** Detects recruitment spam patterns in JD text.
*   **Closed Job Check:** Skips listings with `"no longer accepting applications"`.

### 3️⃣ LLM-Powered Semantic Evaluation (Llama-3.3-70B via Groq)
Each surviving JD is scored by the LLM against a structured **Candidate Profile** containing skills, projects, and target role criteria:
*   Outputs a **match score (0-100)**, a **verdict** (`Strong Match`, `Good Fit`, `Partial Fit`, `DISQUALIFIED`), matched & missing skill lists, and a plain-English reason.
*   Only jobs scoring `≥ 60` are accepted into the final results.

### 4️⃣ Vector Ranker (`core/vector_ranker.py`)
A secondary ranking pass using TF-IDF-based cosine similarity between the JD and candidate profile to reorder borderline candidates before final output.

### 5️⃣ SQLite Telemetry Logging
Every LLM call logs `latency_ms`, `prompt_tokens`, `completion_tokens`, `model_used`, `is_fallback`, and `verdict` to a local SQLite database — feeding the companion **LLMOps Observability Dashboard**.

---

## 📊 Pipeline Performance Across Rounds

| Round | Time Filter | Keywords | Jobs Evaluated | Jobs Passed | Top Score |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Round 1** | 7 days | 8 keywords | ~120 | 10 | 95 |
| **Round 2** | 7 days | 9 keywords | ~140 | 10 | 92 |
| **Round 3** | 7 days | 10 keywords | ~160 | 10 | 90 |
| **Round 4** | 7 days | 10 keywords | ~180 | 10 | 90 |
| **Round 5** | **48 hours** | 12 keywords | ~200 | 10 | **92** |

---

## 📂 Repository Structure

```
Agentic-Job-Pipeline/
├── core/
│   ├── llm_evaluator.py        # Groq LLM scoring engine + SQLite telemetry logger
│   └── vector_ranker.py        # TF-IDF cosine similarity reranker
├── scrapers/
│   └── linkedin_scraper.py     # LinkedIn DOM parser (BeautifulSoup4)
├── database/
│   └── outcome_log.db          # SQLite telemetry & application outcome log
├── ui/                         # Streamlit dashboard for job tracking
├── fetch_top10_round5.py       # Latest pipeline execution (48h strict filter)
├── fetch_top10_round4.py       # Round 4 pipeline (7-day, 10 new keywords)
├── fetch_top10_round3.py       # Round 3 pipeline
├── fetch_top10_round2.py       # Round 2 pipeline
├── fetch_top10_now.py          # Round 1 pipeline (baseline)
├── top10_round5_results.json   # Latest 10 qualified jobs
├── top10_round4_results.json   # Round 4 results
├── log_application.py          # Application outcome tracker
├── main.py                     # Streamlit UI entry point
└── .env                        # GROQ_API_KEY
```

---

## ⚡ Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Shiva-keerth/Agentic-Job-Pipeline.git
   cd Agentic-Job-Pipeline
   ```

2. **Install dependencies:**
   ```bash
   pip install requests beautifulsoup4 groq langchain python-dotenv
   ```

3. **Configure Environment:**
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ```

4. **Run the Latest Pipeline (Round 5 — 48h strict):**
   ```bash
   python fetch_top10_round5.py
   ```

---

## 🤝 Connect With Me
*   **GitHub:** [Shiva-keerth](https://github.com/Shiva-keerth)
*   **Focus:** Generative AI, RAG Systems, Agentic AI, and Machine Learning.
