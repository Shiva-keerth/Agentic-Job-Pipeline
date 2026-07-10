import json
from core.llm_evaluator import evaluate_job

def test_evaluator_penalty():
    print("Testing external penalty logic...")
    
    # Simulate a scraped external job
    scraped_jd = "[EXTERNAL_APPLY_FLAG]\n\nThis is a very short JD for a GenAI Engineer. We need you to build AI things."
    job_info = {
        "company": "Fake Startup",
        "role": "Generative AI Engineer",
        "job_url": "http://fake.com"
    }
    
    res = evaluate_job(job_info, scraped_jd)
    print("\nResult:")
    print(json.dumps(res, indent=2))
    
    if res.get("is_external"):
        print("\n-> SUCCESS: Flag was detected.")
    else:
        print("\n-> FAILED: Flag was not detected.")
        
    if "External Penalty applied" in res.get("reason", ""):
        print("-> SUCCESS: Penalty was applied.")
    else:
        print("-> FAILED: Penalty was not applied.")

if __name__ == "__main__":
    test_evaluator_penalty()
