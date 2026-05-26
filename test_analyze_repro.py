import io
import pdfplumber
from services.overlay import analyze_pdf_for_blanks

def test_analyze():
    with open("repro.pdf", "rb") as f:
        pdf_bytes = f.read()
    
    blanks = analyze_pdf_for_blanks(pdf_bytes)
    
    print(f"Found {len(blanks)} blanks.")
    for i, b in enumerate(blanks):
        print(f"Blank {i}: Page {b['page']}, x0={b['x0']:.2f}, top={b['top']:.2f}, width={b['width']:.2f}, context='{b.get('context', '')}'")
        if b.get('is_checkbox'):
            print("  (Checkbox)")
        if b.get('is_table_cell'):
            print("  (Table Cell)")

if __name__ == "__main__":
    test_analyze()
