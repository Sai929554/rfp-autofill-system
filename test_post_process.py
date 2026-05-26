from services.llm import _fix_broken_alignment
import time

print("Testing Alignment Post-Processing Logic...")

# Simulation of the BAD output the user is seeing
bad_output = """
Legal Company Name                    __________________
<u>InnoSoul, Inc.</u>
Year Established                      _______
<u>2003</u>
Just a normal line here.
"""

expected_output = """
Legal Company Name                     <u>InnoSoul, Inc.</u>
Year Established                       <u>2003</u>
Just a normal line here.
"""

# Note: The spacing in expected might vary slightly depending on my replacement logic (adding one space)
# So we check if "__________________" is gone and "InnoSoul" is on the same line.

fixed = _fix_broken_alignment(bad_output)

print("--- ORIGINAL ---")
print(bad_output)
print("--- FIXED ---")
print(fixed)

if "Legal Company Name" in fixed and "InnoSoul, Inc." in fixed:
    line1 = [l for l in fixed.split('\n') if "Legal Company Name" in l][0]
    if "____" not in line1 and "InnoSoul" in line1:
        print("SUCCESS: Line 1 fixed.")
    else:
        print(f"FAILURE: Line 1 not fixed correctly: {line1}")
else:
    print("FAILURE: Line 1 content missing.")

if "Year Established" in fixed and "2003" in fixed:
    line2 = [l for l in fixed.split('\n') if "Year Established" in l][0]
    if "____" not in line2 and "2003" in line2:
        print("SUCCESS: Line 2 fixed.")
    else:
        print(f"FAILURE: Line 2 not fixed correctly: {line2}")
else:
    print("FAILURE: Line 2 content missing.")
