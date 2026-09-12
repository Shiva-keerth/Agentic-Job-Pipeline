import os
import json
import smtplib
import argparse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

def send_notification(json_filepath: str, min_score: int = 75):
    # Load environment variables
    load_dotenv()
    
    gmail_user = os.getenv("GMAIL_ADDRESS")
    gmail_pwd = os.getenv("GMAIL_APP_PASSWORD")
    
    if not gmail_user or not gmail_pwd:
        print("Error: GMAIL_ADDRESS or GMAIL_APP_PASSWORD not found in .env")
        return

    # Load jobs from JSON
    if not os.path.exists(json_filepath):
        print(f"Error: Could not find file {json_filepath}")
        return

    try:
        with open(json_filepath, 'r', encoding='utf-8') as f:
            jobs = json.load(f)
    except Exception as e:
        print(f"Error reading JSON: {e}")
        return

    # Filter strong matches
    strong_jobs = [j for j in jobs if j.get("score", 0) >= min_score and j.get("verdict") not in ["DISQUALIFIED", "BLACKLISTED"]]
    
    if not strong_jobs:
        print(f"No jobs found with score >= {min_score}. No email sent.")
        return

    print(f"Found {len(strong_jobs)} strong matches. Sending email...")

    # Build Email Content
    subject = f"Jobline Pipeline: {len(strong_jobs)} Strong AI Matches Found!"
    
    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; color: #333; }}
            .job-card {{ border: 1px solid #ddd; padding: 15px; margin-bottom: 20px; border-radius: 5px; }}
            .job-title {{ color: #0056b3; margin-top: 0; }}
            .company {{ font-weight: bold; font-size: 1.1em; }}
            .score {{ display: inline-block; padding: 3px 8px; background-color: #28a745; color: white; border-radius: 3px; font-weight: bold; }}
            .details {{ margin-top: 10px; font-size: 0.9em; }}
            .reason {{ font-style: italic; color: #555; margin-top: 10px; }}
            a.apply-btn {{ display: inline-block; margin-top: 10px; padding: 8px 15px; background-color: #007bff; color: white; text-decoration: none; border-radius: 4px; }}
        </style>
    </head>
    <body>
        <h2>Jobline Pipeline Alert</h2>
        <p>Your latest round found <b>{len(strong_jobs)}</b> roles scoring {min_score}+:</p>
    """
    
    for job in strong_jobs:
        score = job.get('score', 0)
        apply_type = "External Apply" if job.get("is_external_apply") else "Easy Apply"
        missing = ", ".join(job.get("missing_skills", [])) or "None"
        
        html_content += f"""
        <div class="job-card">
            <h3 class="job-title">{job.get('title', 'Unknown Role')}</h3>
            <div class="company">{job.get('company', 'Unknown Company')} <span class="score">{score} / 100</span></div>
            <div class="details">
                <b>Apply Type:</b> {apply_type} <br/>
                <b>Exp Needed:</b> {job.get('experience_required', 'Not specified')} <br/>
                <b>Missing Skills:</b> {missing} <br/>
                <b>Decision:</b> {job.get('apply_decision', '')} ({job.get('apply_reason', '')})
            </div>
            <div class="reason">"{job.get('reason', '')}"</div>
            <a href="{job.get('url', job.get('job_url', '#'))}" class="apply-btn">View Job</a>
        </div>
        """
        
    html_content += """
        <p><small>Automated by Jobline Pipeline</small></p>
    </body>
    </html>
    """

    # Setup Message
    msg = MIMEMultipart("alternative")
    msg['Subject'] = subject
    msg['From'] = gmail_user
    msg['To'] = gmail_user  # Send to yourself
    
    part = MIMEText(html_content, 'html')
    msg.attach(part)

    # Send Email
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(gmail_user, gmail_pwd)
        server.send_message(msg)
        server.quit()
        print(f"Success! Alert email sent to {gmail_user}")
    except Exception as e:
        print(f"Failed to send email: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send email notification for strong job matches.")
    parser.add_argument("json_file", help="Path to the top10_roundX_results.json file")
    parser.add_argument("--min-score", type=int, default=75, help="Minimum score to trigger an email")
    args = parser.parse_args()
    
    send_notification(args.json_file, args.min_score)
