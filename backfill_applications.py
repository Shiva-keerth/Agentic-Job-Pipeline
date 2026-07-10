import os
from log_application import log_application

def backfill():
    print("Starting backfill of historical applications...")
    
    # 1. Jash Data Sciences
    log_application(
        platform="Direct",
        company="Jash Data Sciences",
        role="Data Scientist",
        resume="Resume_Data_Scientist_JashDS.pdf"
    )
    
    # 2. CoRover
    log_application(
        platform="Direct",
        company="CoRover",
        role="Gen AI Developer / AI ML Engineer",
        resume="Base GenAI Resume + Cover Letter"
    )
    
    # 3. Eversoft AI
    log_application(
        platform="Direct",
        company="Eversoft AI",
        role="AI Engineer",
        resume="Resume_Eversoft_AI.pdf"
    )
    
    print("Backfill complete.")

if __name__ == "__main__":
    backfill()
