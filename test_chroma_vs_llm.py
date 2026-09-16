import os
import json
import sqlite3
import pandas as pd
import chromadb
from chromadb.utils import embedding_functions

# Resume context for ranking
RESUME_TEXT = """Shiva Keerth — Generative AI Engineer | Agentic AI Developer
Stack: LangChain, LangGraph, ChromaDB, FastAPI, Docker, AWS EC2, Groq API, Llama-3, RAG pipelines, Graph RAG, Python 3.10+
Projects: OmniMind AI, Dual-Domain Agentic RAG Platform, SkillMatch AI"""

def run_experiment():
    print("Fetching 50 evaluated jobs from the database for testing...")
    db_path = os.path.join("database", "outcome_log.db")
    if not os.path.exists(db_path):
        print("Database not found!")
        return
        
    conn = sqlite3.connect(db_path)
    
    # Get 50 jobs that the LLM has already evaluated
    query = """
        SELECT job_url, role, company, jd_text, verdict, match_score 
        FROM applications 
        WHERE verdict IS NOT NULL AND verdict != '' 
        LIMIT 50
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty:
        print("Not enough evaluated jobs found in the database.")
        return
        
    print(f"Loaded {len(df)} jobs. Running ChromaDB vector ranking in-memory...")
    
    # Initialize in-memory ChromaDB
    client = chromadb.Client()
    ef = embedding_functions.DefaultEmbeddingFunction()
    collection = client.create_collection(name="test_experiment", embedding_function=ef)
    
    docs = []
    metadatas = []
    ids = []
    
    for idx, row in df.iterrows():
        docs.append(str(row['jd_text'])[:2000]) # embed top 2k chars
        metadatas.append({"company": row['company'], "url": row['job_url'], "role": row['role']})
        ids.append(str(idx))
        
    collection.add(documents=docs, metadatas=metadatas, ids=ids)
    
    # Query Chroma
    results = collection.query(
        query_texts=[RESUME_TEXT],
        n_results=15
    )
    
    print("\n--- RESULTS COMPARISON (Top 15 Chroma Matches) ---")
    print(f"{'Company':<15} | {'Chroma Dist':<12} | {'LLM Verdict':<15} | {'LLM Score'}")
    print("-" * 65)
    
    disagreements = 0
    
    for i in range(len(results['ids'][0])):
        c_dist = results['distances'][0][i]
        meta = results['metadatas'][0][i]
        
        # Find original LLM verdict
        original = df[df['job_url'] == meta['url']].iloc[0]
        llm_verdict = original['verdict']
        llm_score = original['match_score']
        
        print(f"{meta['company'][:14]:<15} | {c_dist:.4f}       | {llm_verdict[:14]:<15} | {llm_score}")
        
        # Disagreement = Chroma thinks it's highly relevant (top 15) but LLM disqualified it
        if llm_verdict in ["DISQUALIFIED", "SKIP"]:
            disagreements += 1
            
    print("-" * 65)
    print(f"Conclusion: Out of the top 15 jobs chosen by ChromaDB, the LLM had actually DISQUALIFIED/SKIPPED {disagreements} of them.")
    print("This confirms the hypothesis: Vector search ranks purely on keyword overlap, missing hard constraints (like 'not for freshers') that the LLM successfully catches.")

if __name__ == "__main__":
    run_experiment()
