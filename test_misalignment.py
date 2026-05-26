from services.llm import _fix_broken_alignment

print("Testing Complex Misalignment...")

# Scenario A: Label separate from underscore/answer
case_a = """
Legal Company Name
<u>InnoSoul, Inc.</u>
"""

# Scenario B: Intervening underscores
case_b = """
Year Established
____________________
<u>2003</u>
"""

# Scenario C: Just correct
case_c = """
Legal Status: <u>Corporation</u>
"""

# Scenario D: 3-line split (Label, Underscores, Answer)
case_d = """
Label D
________________
<u>Answer D</u>
"""

with open("test_misalignment_output.txt", "w") as f:
    f.write("Testing Complex Misalignment...\n")

    f.write("\n--- TEST CASE A ---\n")
    fixed_a = _fix_broken_alignment(case_a)
    f.write(f"Original:\n{case_a.strip()}\n")
    f.write(f"Fixed:\n{fixed_a.strip()}\n")

    f.write("\n--- TEST CASE B ---\n")
    fixed_b = _fix_broken_alignment(case_b)
    f.write(f"Original:\n{case_b.strip()}\n")
    f.write(f"Fixed:\n{fixed_b.strip()}\n")

    f.write("\n--- TEST CASE C ---\n")
    fixed_c = _fix_broken_alignment(case_c)
    f.write(f"Original:\n{case_c.strip()}\n")
    f.write(f"Fixed:\n{fixed_c.strip()}\n")

    f.write("\n--- TEST CASE D ---\n")
    fixed_d = _fix_broken_alignment(case_d)
    f.write(f"Original:\n{case_d.strip()}\n")
    f.write(f"Fixed:\n{fixed_d.strip()}\n")
    
    def is_inline(text):
        return "<u>" in text and text.strip().index("<u>") > 0

    f.write("\nResults:\n")
    f.write(f"Case A inline? {is_inline(fixed_a)}\n")
    f.write(f"Case B inline? {is_inline(fixed_b)}\n")
