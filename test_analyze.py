import json
from services.overlay import analyze_pdf_for_blanks

with open("test_table.pdf", "rb") as f:
    pdf_bytes = f.read()

blanks = analyze_pdf_for_blanks(pdf_bytes)
print(json.dumps(blanks, indent=2))
