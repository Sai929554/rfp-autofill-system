
import docx
import io
from fastapi import UploadFile

async def extract_text_from_file(file: UploadFile) -> list[str]:
    content = await file.read()
    return extract_text_from_bytes(content, file.filename)

def extract_text_from_bytes(content: bytes, filename: str) -> list[str]:
    filename = filename.lower()
    
    if filename.endswith('.pdf'):
        return extract_from_pdf(content)
    elif filename.endswith('.docx'):
        return extract_from_docx(content)
    elif filename.endswith('.txt'):
        return extract_from_txt(content)
    else:
        raise ValueError("Unsupported file format")

def extract_from_docx(content: bytes) -> list[str]:
    doc = docx.Document(io.BytesIO(content))
    full_text = "\n".join([para.text for para in doc.paragraphs])
    
    # Split into chunks of approx 3000 chars (safe for rate limits)
    # This roughly corresponds to 1-1.5 pages of text
    chunk_size = 3000
    chunks = [full_text[i:i+chunk_size] for i in range(0, len(full_text), chunk_size)]
    return chunks

def extract_from_pdf(content: bytes) -> list[str]:
    import pypdf
    chunks = []
    
    # Use pypdf for speed
    with io.BytesIO(content) as f:
        reader = pypdf.PdfReader(f)
        current_chunk = ""
        
        for i, page in enumerate(reader.pages):
            extract = page.extract_text() or ""
            
            # Simple chunking by length
            if len(current_chunk) + len(extract) > 25000: # Match our new larger chunk size preference
                chunks.append(current_chunk)
                current_chunk = extract
            else:
                current_chunk += "\n" + extract
                
        if current_chunk:
            chunks.append(current_chunk)
            
    return chunks

def extract_from_txt(content: bytes) -> list[str]:
    text = content.decode('utf-8')
    chunk_size = 3000
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
