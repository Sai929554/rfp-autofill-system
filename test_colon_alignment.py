from services.llm import _align_colons

input_text = """
Legal Company Name: <u>InnoSoul, Inc.</u>
Year Established: <u>2003</u>
Legal Status: <u>Corporation</u>
Business Address: <u>349 Kinderkamack Rd Westwood, NJ 07675</u>
Primary Contact Name: <u>Rashi Shamshabad</u>
"""

expected_output_start = "Legal Company Name  : <u>InnoSoul, Inc.</u>"

print("--- Testing Alignment Fix ---")
print("Input:")
print(input_text.strip())

aligned_text = _align_colons(input_text.strip())

print("\nOutput:")
print(aligned_text)

print("\n--- Verification ---")
lines = aligned_text.split('\n')
colon_indices = []
for line in lines:
    if ':' in line:
        colon_indices.append(line.index(':'))

print(f"Colon indices: {colon_indices}")
if len(set(colon_indices)) == 1:
    print("SUCCESS: Colons are aligned.")
else:
    print("FAILURE: Colons are NOT aligned.")
