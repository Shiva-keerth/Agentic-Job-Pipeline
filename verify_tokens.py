import os
import sqlite3
import tiktoken

# Import the actual prompts used in the pipeline
from core.llm_evaluator import CANDIDATE_PROFILE, EVALUATOR_PROMPT

def verify_token_count():
    print("Fetching the longest JD (Fujitsu) from the database...")
    db_path = os.path.join("database", "outcome_log.db")
    conn = sqlite3.connect(db_path)
    
    # Get the Fujitsu JD
    query = "SELECT company, role, jd_text FROM applications ORDER BY length(jd_text) DESC LIMIT 1"
    res = conn.execute(query).fetchone()
    conn.close()
    
    if not res:
        print("No JD found.")
        return
        
    company, role, jd_text = res
    print(f"Longest JD: {company} - {role} ({len(jd_text)} characters)")
    
    # Simulate the exact prompt we send to the LLM (using the 18,000 char cap)
    capped_jd = jd_text[:18000]
    
    prompt = EVALUATOR_PROMPT.format(
        profile=CANDIDATE_PROFILE,
        company=company,
        role=role,
        jd_text=capped_jd
    )
    
    print(f"Total prompt length (JD + Profile + Instructions) is {len(prompt)} characters.")
    print("Tokenizing using tiktoken (cl100k_base) to get actual token usage...\n")
    
    # Initialize tokenizer
    encoding = tiktoken.get_encoding("cl100k_base")
    prompt_tokens = len(encoding.encode(prompt))
    max_context = 8192
    
    print(f"--- TOKEN VERIFICATION RESULTS ---")
    print(f"Actual Tokens Used:   {prompt_tokens}")
    print(f"Max Context Window:   {max_context}")
    print(f"Headroom Remaining:   {max_context - prompt_tokens} tokens")
    print("-" * 34)
    
    if prompt_tokens < max_context:
        print("VERDICT: SAFE. The 18,000 character limit comfortably fits inside the 8k token window!")
    else:
        print("VERDICT: UNSAFE. The 18,000 character limit exceeds the 8k token window. It needs to be lowered.")

if __name__ == "__main__":
    verify_token_count()
