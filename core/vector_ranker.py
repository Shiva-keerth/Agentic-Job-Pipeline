import chromadb
import sqlite3
from chromadb.utils import embedding_functions
import os

RESUME_TEXT = """
Shiva Keerth \u2014 Generative AI Engineer | Agentic AI Developer
Location: Ahmedabad/Remote | Target: 0-2 YOE permanent roles | Target CTC: \u20b98-12 LPA

TECHNICAL SKILLS:
LangChain, LangGraph, LangGraph ReAct agents, ChromaDB, FAISS, Neo4j, Neo4j Aura,
FastAPI, Docker, AWS EC2, Groq API, Llama-3.3-70B, Groq Whisper, RAG pipelines,
Graph RAG, GraphCypherQAChain, Pydantic, Supabase, SQLite, Python 3.10+,
Prompt Engineering, Multi-agent systems, Agentic AI, Knowledge Graphs,
Retrieval Augmented Generation, Vector databases, Embeddings, LLM fine-tuning,
Tavily Search, BeautifulSoup4, Playwright, Streamlit, APScheduler

PROJECTS:
OmniMind AI \u2014 Enterprise Knowledge Graph + Graph-RAG platform.
Stack: Neo4j Aura, LangChain GraphCypherQAChain, Groq Whisper STT,
Llama-3.3-70B inference, Pydantic data validation.
Deployed: Hugging Face Spaces. Repo: github.com/Shiva-keerth/OmniMind-AI-Enterprise

Dual-Domain Agentic RAG Platform \u2014 Production multi-agent system.
Stack: LangGraph ReAct agents, ChromaDB vector store, Tavily Search tool,
Docker containerization, AWS EC2 deployment.
Domains: Healthcare document QA + Financial data analysis.

SkillMatch AI \u2014 AI-powered workforce recommendation engine.
Stack: 6-signal TF-IDF scoring, 3-tier RBAC, Groq Llama-3, FastAPI backend,
Supabase database, Streamlit UI. 600-job dataset.

EXPERIENCE:
Infolabz Pvt. Ltd. \u2014 AI & Data Science Intern (8 months)
Data Analytics, Machine Learning pipelines, Python automation

EDUCATION:
B.Tech Information Technology \u2014 Indus University, Ahmedabad
CGPA: 9.57 | Graduated: May 2026
"""

def build_vector_store():
    """Embed all JDs from DB into ChromaDB. Run once, or after each scrape batch."""
    ef = embedding_functions.DefaultEmbeddingFunction()
    # Ensure correct relative path from script
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "chroma_store")
    client = chromadb.PersistentClient(path=db_path)

    # Delete and recreate collection to avoid stale embeddings
    try:
        client.delete_collection("job_jds")
    except Exception:
        pass

    collection = client.create_collection(
        name="job_jds",
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"}
    )

    sqlite_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "outcome_log.db")
    conn = sqlite3.connect(sqlite_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, company, role, job_url, jd_text
        FROM applications
        WHERE jd_text IS NOT NULL AND jd_text != ''
        AND verdict IS NULL
    """)
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("[Ranker] No JDs found in DB. Run scrapers first.")
        return

    ids      = [str(r[0]) for r in rows]
    docs     = [r[4] for r in rows]          # jd_text
    metas    = [{"company": r[1], "role": r[2], "url": r[3]} for r in rows]

    collection.add(documents=docs, ids=ids, metadatas=metas)
    print(f"[Ranker] Embedded {len(rows)} JDs into ChromaDB.")
    return collection


def rank_jobs(top_n: int = 20) -> list[dict]:
    """Return top_n jobs ranked by cosine similarity to resume."""
    ef = embedding_functions.DefaultEmbeddingFunction()
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "chroma_store")
    client = chromadb.PersistentClient(path=db_path)
    collection = client.get_collection("job_jds", embedding_function=ef)

    results = collection.query(
        query_texts=[RESUME_TEXT],
        n_results=top_n,
        include=["metadatas", "distances"]
    )

    ranked = []
    for i, meta in enumerate(results["metadatas"][0]):
        distance = results["distances"][0][i]
        similarity = round(1 - distance, 4)   # cosine distance \u2192 similarity

        # Hard discard only below 0.35 \u2014 generous threshold as per blueprint
        if similarity < 0.35:
            continue

        ranked.append({
            "db_id":      results["ids"][0][i],
            "company":    meta["company"],
            "role":       meta["role"],
            "url":        meta["url"],
            "similarity": similarity,
        })

    ranked.sort(key=lambda x: x["similarity"], reverse=True)
    print(f"[Ranker] Top {len(ranked)} jobs above 0.35 threshold:")
    for j in ranked[:5]:
        print(f"  {j['similarity']:.3f}  {j['role']} @ {j['company']}")
    return ranked


if __name__ == "__main__":
    build_vector_store()
    rank_jobs(top_n=20)
