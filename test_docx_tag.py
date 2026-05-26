from services.generator import create_filled_docx
import os

def test_docx():
    text = "Hello <b>World</b>\nThis is <u>Underlined</u> text."
    try:
        docx_buffer = create_filled_docx(text)
        with open("test_output.docx", "wb") as f:
            f.write(docx_buffer.getvalue())
        print("Success: test_output.docx created")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_docx()
