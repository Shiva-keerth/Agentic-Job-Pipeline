"""
FINAL VERIFICATION TEST for pre_filter_experience.
Uses exact text from the user's screenshots of real JDs that previously slipped through.
Every test case MUST pass or the pipeline is not ready.
"""
import sys
sys.path.insert(0, ".")
from core.llm_evaluator import pre_filter_experience

passed = 0
failed = 0

def test(label, jd_text, role_title, should_disqualify, expected_match_fragment=None):
    global passed, failed
    result, matched = pre_filter_experience(jd_text, role_title)
    status = "PASS" if result == should_disqualify else "FAIL"
    if status == "FAIL":
        failed += 1
        print(f"  [FAIL] {label}")
        print(f"         Expected disqualify={should_disqualify}, got disqualify={result}")
        if result:
            print(f"         Matched: '{matched}'")
        else:
            print(f"         Nothing matched (should have caught it!)")
    else:
        passed += 1
        if result and expected_match_fragment:
            if expected_match_fragment.lower() not in matched.lower():
                print(f"  [WARN] {label} — matched '{matched}' (expected fragment '{expected_match_fragment}')")
            else:
                print(f"  [PASS] {label} — matched: '{matched}'")
        elif result:
            print(f"  [PASS] {label} — matched: '{matched}'")
        else:
            print(f"  [PASS] {label} — correctly allowed through")

print("=" * 70)
print("CATEGORY 1: JDs from user screenshots that MUST be disqualified")
print("=" * 70)

# --- SiftHub (en-dash "3–6 years") ---
test(
    "SiftHub: 3\u20136 years of production NLP/ML experience (en-dash)",
    "3\u20136 years of production NLP/ML experience with shipped models or pipelines used by real users. "
    "Hands-on experience building and improving production-grade RAG systems. "
    "Experience with LangChain, LlamaIndex, FastAPI, or similar agentic frameworks.",
    "Applied AI engineer",
    should_disqualify=True,
    expected_match_fragment="3-6 year"
)

# --- Nomia Ltd (en-dash "3–6 years") ---
test(
    "Nomia: 3\u20136 years of hands-on experience in AI (en-dash)",
    "3\u20136 years of hands-on experience in AI, Machine Learning and NLP. "
    "Proficient in Python, with strong command of AI and NLP libraries. "
    "Experience with Langchain and RAG architecture is essential.",
    "AI Engineer",
    should_disqualify=True,
    expected_match_fragment="3-6 year"
)

# --- Infosys (en-dash "3–6 years") ---
test(
    "Infosys: 3\u20136 years of software development experience (en-dash)",
    "3\u20136 years of software development experience. Hands-on experience in Python programming. "
    "Strong understanding of Generative AI, LLMs, Prompt Engineering, RAG, LangChain.",
    "Gen AI Developer",
    should_disqualify=True,
    expected_match_fragment="3-6 year"
)

# --- Tata Industries ("Exp- 4-6years") ---
test(
    "Tata: Exp- 4-6years (no spaces)",
    "Job Description. Skill- AI Engineer (GenAI and Agentic AI). Exp- 4-6years. Location- Hyderabad. "
    "Backend / AI: Python (FastAPI preferred), Node.js/TypeScript; LangChain, LangGraph.",
    "AI Engineer",
    should_disqualify=True,
    expected_match_fragment="4-6"
)

# --- XHawk ("2+ years of experience in Engineering") ---
test(
    "XHawk: 2+ years of experience in Engineering",
    "You are comfortable working on 10s of tasks in parallel using Claude, Codex or OpenCode. "
    "Familiarity with cloud infrastructure like VMs, containers and sandboxes. "
    "Requirements added by the job poster: 2+ years of experience in Engineering.",
    "AI Engineer",
    should_disqualify=True,
    expected_match_fragment="2+ year"
)

# --- SPADTEK ("Experience: 4 to 8 Years") ---
test(
    "SPADTEK: Experience: 4 to 8 Years (range with 'to')",
    "Job Title: AI Engineer Generative AI & Document Intelligence. "
    "Experience: 4 to 8 Years. Location: Kolkata (Hybrid/Remote).",
    "AI Engineer Generative AI Document Intelligence",
    should_disqualify=True,
    expected_match_fragment="4 to 8"
)

# --- Unilever ("5+ years") ---
test(
    "Unilever: 5+ years in software engineering",
    "5+ years in software engineering with strong full-stack capability. "
    "3+ years hands-on experience building LLM-powered or agentic applications.",
    "AI Agent Developer / Full Stack Engineer",
    should_disqualify=True,
    expected_match_fragment="5+ year"
)

# --- KnowDis AI ("2-3 years") ---
test(
    "KnowDis AI: 2-3 years listed in sidebar",
    "We are looking for a Data Scientist / GenAI Engineer. 2-3 years experience required. "
    "Location: New Delhi. Posted: 26 Jun 2026.",
    "Data Scientist / GenAI Engineer",
    should_disqualify=True,
    expected_match_fragment="2-3 year"
)

# --- HCLTech (implicit senior via context) ---
test(
    "HCLTech: 3+ years experience mentioned",
    "3+ years of experience in developing AI/ML solutions. "
    "Experience with Docker, Kubernetes, and cloud platforms. "
    "Strong understanding of NLP and transformer architectures.",
    "Artificial Intelligence Engineer",
    should_disqualify=True,
    expected_match_fragment="3+ year"
)

print()
print("=" * 70)
print("CATEGORY 2: Previously caught patterns (must still work)")
print("=" * 70)

test(
    "CodeRound AI: 6 years of experience",
    "6 years of experience in AI/ML engineering. Deep learning expertise required.",
    "AI Engineer (Up to 50LPA)",
    should_disqualify=True,
    expected_match_fragment="6 year"
)

test(
    "Sagent: 5+ years of software engineering experience",
    "5+ years of software engineering experience. Python and cloud required.",
    "AI Engineer - India",
    should_disqualify=True,
    expected_match_fragment="5+ year"
)

test(
    "Teamware Solutions: experience : 3-7 years",
    "Experience : 3-7 years. GenAI Engineer role. LangChain required.",
    "GenAI Engineer",
    should_disqualify=True,
    expected_match_fragment="3-7 year"
)

test(
    "Naveera: 15 years of experience",
    "15 years of experience in software development. Lead AI role.",
    "Lead AI & Machine Learning Engineer",
    should_disqualify=True,
    expected_match_fragment="lead engineer"
)

test(
    "CloudSutra: 15 years of industry exp",
    "15 years of industry exp required. DevOps and AI background.",
    "Hiring: AI DevOps Engineer",
    should_disqualify=True,
    expected_match_fragment="15 year"
)

test(
    "Keyword: senior engineer",
    "We are looking for a senior engineer to join our AI team.",
    "Senior AI Engineer",
    should_disqualify=True,
    expected_match_fragment="senior engineer"
)

test(
    "Keyword: architect",
    "You will serve as the AI architect for our platform.",
    "AI Architect",
    should_disqualify=True,
    expected_match_fragment="architect"
)

test(
    "Keyword: manager",
    "Report to the engineering manager. Lead a team of 5.",
    "AI Platform Engineer",
    should_disqualify=True,
    expected_match_fragment="manager"
)

test(
    "Metyis: 4 years of relevant experience",
    "4 years of relevant experience in software engineering. Python required.",
    "AI Engineer / Agent Developer",
    should_disqualify=True,
    expected_match_fragment="4"
)

test(
    "Minimum 3 years pattern",
    "Minimum 3 years of experience in machine learning. TensorFlow required.",
    "ML Engineer",
    should_disqualify=True,
    expected_match_fragment="minimum 3 year"
)

test(
    "At least 2 years pattern",
    "At least 2 years of experience in software development.",
    "Software Developer",
    should_disqualify=True,
    expected_match_fragment="at least 2 year"
)

print()
print("=" * 70)
print("CATEGORY 3: Jobs that SHOULD pass (must NOT be falsely rejected)")
print("=" * 70)

test(
    "Fresher role — no experience mentioned",
    "We are looking for a fresher to join our AI team. Python and ML basics required. "
    "LangChain knowledge is a plus. No prior experience needed.",
    "AI Developer",
    should_disqualify=False
)

test(
    "0-1 years explicitly stated",
    "0-1 years of experience. Entry level AI Developer position. "
    "Python, basic ML understanding required.",
    "AI Developer",
    should_disqualify=False
)

test(
    "1 year of experience (singular)",
    "1 year of experience preferred. Familiarity with Python and APIs.",
    "Junior AI Developer",
    should_disqualify=False
)

test(
    "Entry level — no years",
    "Entry-level position for new graduates. Build AI models using Python. "
    "LangChain and vector database knowledge is preferred.",
    "Entry Level AI Engineer",
    should_disqualify=False
)

test(
    "Company age should not trigger ('founded 10 years ago')",
    "Our company was founded 10 years ago. We build AI solutions. "
    "No experience required for this entry-level internship role.",
    "AI Intern",
    should_disqualify=False
)

test(
    "'architecture' should NOT match 'architect'",
    "You will work on the architecture of our ML platform. "
    "Microservices architecture experience is a plus. Entry-level role.",
    "ML Platform Developer",
    should_disqualify=False
)

print()
print("=" * 70)
print(f"RESULTS: {passed} PASSED, {failed} FAILED out of {passed + failed} total")
print("=" * 70)

if failed > 0:
    print("\n*** PIPELINE IS NOT READY — THERE ARE FAILURES ***")
    sys.exit(1)
else:
    print("\n*** ALL TESTS PASSED — PIPELINE IS READY FOR LIVE RUN ***")
    sys.exit(0)
