from services.llm import generate_form_answers
import time

# Mimic the user's problematic input structure
form_snippet = """
Legal Company Name                    __________________
Year Established                      __________________
Authorized Signatory
Name: ________________
Title: ________________
"""

profile_snippet = """
Company: InnoSoul, Inc.
Established: 2003
Signatory: Rashi Shamshabad
Title: President
"""

with open("test_alignment_output.txt", "w") as f:
    f.write("Testing Alignment Fix...\n")
    try:
        response = generate_form_answers(profile_snippet, form_snippet)
        f.write("--- RESPONSE START ---\n")
        f.write(response + "\n")
        f.write("--- RESPONSE END ---\n")
        
        # Check for expected pattern
        if "Name: <u>Rashi Shamshabad</u>" in response or "Name: <u>Rashi Shamshabad</u>" in response.replace("   ", " "):
             f.write("SUCCESS: Answer is inline.\n")
        else:
             f.write("WARNING: Answer might not be inline. Check output.\n")

    except Exception as e:
        f.write(f"Error: {e}\n")
