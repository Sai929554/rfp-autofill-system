from services.generator import create_filled_pdf

def generate_test_pdf():
    # Simulate the text flow
    raw_text = "Legal Company Name <u>InnoSoul, Inc.</u>\nYear Established <u>2003</u>"
    
    pdf_buffer = create_filled_pdf(raw_text)
    
    with open("test_output.pdf", "wb") as f:
        f.write(pdf_buffer.getvalue())
    print("PDF generated: test_output.pdf")

if __name__ == "__main__":
    generate_test_pdf()
