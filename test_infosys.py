import re

regex_pattern = r'(?:(?:experience|exp)[\s:|-]+([2-9]|\d{2,})\+?\s*(?:-\s*(?:[2-9]|\d{2,})\s*)?(years?|yrs?))|([2-9]|\d{2,})\+?\s*(?:-\s*(?:[2-9]|\d{2,})\s*)?(years?|yrs?)\s*(?:of\s+(?:\w+\s+){0,2})?(?:experience|exp|building|working)'

# Explicitly using re.IGNORECASE
new_regex = re.compile(regex_pattern, re.IGNORECASE)

print("\n--- CASED VALIDATION TESTS (re.IGNORECASE) ---")
tests = [
    "Experience: 7-9 Yrs",
    "5 YEARS of relevant experience",
    "experience of 5+ years" # Known recall gap, should fail
]

for t in tests:
    match = new_regex.search(t)
    print(f"String: '{t}'")
    if match:
        print(f"-> MATCHED SPAN: '{match.group(0)}'")
    else:
        print("-> FAILED TO MATCH (Known Recall Gap / Negative Test)")

print("\n")
