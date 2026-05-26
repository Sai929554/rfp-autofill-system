from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional
from services import parser, llm, generator, overlay
import io

router = APIRouter()

# Simple in-memory store
class Store:
    company_profile_text: str = ""
    last_generated_response: str = ""
    # Store bits for overlay
    original_form_bytes: Optional[bytes] = None
    original_form_filename: str = ""
    form_text: str = ""

store = Store()

class QuestionRequest(BaseModel):
    question: str

import os

@router.post("/upload-company-profile")
async def upload_company_profile(file: UploadFile = File(...)):
    try:
        text_chunks = await parser.extract_text_from_file(file)
        if not text_chunks:
            raise HTTPException(status_code=400, detail="Could not extract text from file")
        
        full_text = "\n".join(text_chunks)
        store.company_profile_text = full_text
        
        # Persist to disk so it survives server restarts!
        with open("company_profile_cache.txt", "w", encoding="utf-8") as f:
            f.write(full_text)
            
        return {"message": "Company profile uploaded and persisted successfully", "chunks": len(text_chunks)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Load persisted profile on startup
if os.path.exists("company_profile_cache.txt"):
    try:
        with open("company_profile_cache.txt", "r", encoding="utf-8") as f:
            store.company_profile_text = f.read()
            print("Loaded persisted company profile from disk.")
    except Exception as e:
        print(f"Error loading persisted profile: {e}")

# Load persisted form bytes and filename on startup
if os.path.exists("original_form_bytes_cache.bin") and os.path.exists("original_form_filename_cache.txt"):
    try:
        with open("original_form_bytes_cache.bin", "rb") as f:
            store.original_form_bytes = f.read()
        with open("original_form_filename_cache.txt", "r", encoding="utf-8") as f:
            store.original_form_filename = f.read().strip()
        print("Loaded persisted original form from disk.")
    except Exception as e:
        print(f"Error loading persisted form cache: {e}")

# Load persisted form text on startup
if os.path.exists("form_text_cache.txt"):
    try:
        with open("form_text_cache.txt", "r", encoding="utf-8") as f:
            store.form_text = f.read()
            print("Loaded persisted form text from disk.")
    except Exception as e:
        print(f"Error loading persisted form text cache: {e}")

# Load persisted generated response on startup
if os.path.exists("last_generated_response_cache.txt"):
    try:
        with open("last_generated_response_cache.txt", "r", encoding="utf-8") as f:
            store.last_generated_response = f.read()
            print("Loaded persisted generated response from disk.")
    except Exception as e:
        print(f"Error loading persisted generated response cache: {e}")

@router.post("/upload-form")
async def upload_form(file: UploadFile = File(...)):
    try:
        import time
        t_start = time.time()
        
        # Read content once
        content = await file.read()
        print(f"File read time: {time.time() - t_start:.2f}s")
        
        # Save for later overlay
        store.original_form_bytes = content
        store.original_form_filename = file.filename
        
        # Persist to disk so it survives server restarts!
        with open("original_form_bytes_cache.bin", "wb") as f:
            f.write(content)
        with open("original_form_filename_cache.txt", "w", encoding="utf-8") as f:
            f.write(file.filename)
        
        t_extract = time.time()
        # Direct extraction from bytes, no re-reading/seeking
        text_chunks = parser.extract_text_from_bytes(content, file.filename)
        print(f"Extraction time: {time.time() - t_extract:.2f}s")
        
        full_text = "\n".join(text_chunks)
        store.form_text = full_text
        
        # Persist extracted form text to disk!
        with open("form_text_cache.txt", "w", encoding="utf-8") as f:
            f.write(full_text)
        
        print(f"Total upload processing time: {time.time() - t_start:.2f}s")
        return {"message": "Form uploaded successfully", "extracted_text_preview": full_text[:200], "full_text": full_text}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

class FillFormRequest(BaseModel):
    form_text: str

@router.post("/fill-form")
async def fill_form(request: FillFormRequest):
    if not store.company_profile_text:
        raise HTTPException(status_code=400, detail="Company profile not uploaded")
    
    try:
        full_form_text = request.form_text
        
        import time, hashlib
        start_time = time.time()
        
        # Speed Optimization 1: Truncate company profile (key info is in first 8000 chars)
        MAX_PROFILE_CHARS = 8000
        profile_to_use = store.company_profile_text[:MAX_PROFILE_CHARS]
        
        # Speed Optimization 2: Truncate large forms to prevent 400+ second waits.
        # 20000 chars covers ~15-20 pages of a standard RFP form.
        MAX_FORM_CHARS = 20000
        form_to_use = full_form_text[:MAX_FORM_CHARS]
        if len(full_form_text) > MAX_FORM_CHARS:
            print(f"Form truncated: {len(full_form_text)} → {MAX_FORM_CHARS} chars for AI. Overlay uses full PDF.")
        
        # Speed Optimization 3: Cache the last response
        cache_key = hashlib.md5((profile_to_use + form_to_use).encode()).hexdigest()
        if hasattr(store, '_cache_key') and store._cache_key == cache_key and store.last_generated_response:
            print(f"Cache HIT - returning cached response instantly.")
            return {"filled_content": store.last_generated_response}
        
        print(f"Starting processing ({len(form_to_use)} form chars, {len(profile_to_use)} profile chars)...")
        
        full_response = llm.generate_form_answers(profile_to_use, form_to_use)

        
        total_time = time.time() - start_time
        print(f"Total processing time: {total_time:.2f}s")
        
        store.last_generated_response = full_response
        store._cache_key = cache_key
        
        # Persist to disk so it survives server restarts!
        with open("last_generated_response_cache.txt", "w", encoding="utf-8") as f:
            f.write(full_response)
            
        return {"filled_content": full_response}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"LLM Error: {str(e)}")


@router.post("/ask-question")
async def ask_question(request: QuestionRequest):
    if not store.company_profile_text:
        raise HTTPException(status_code=400, detail="Company profile not uploaded")
    
    try:
        answer = llm.answer_question(store.company_profile_text, request.question)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/pdf")
async def download_pdf():
    if not store.last_generated_response:
        raise HTTPException(status_code=400, detail="No form has been filled yet")
    
    # Check if we can do overlay
    if store.original_form_bytes and store.original_form_filename.lower().endswith('.pdf'):
        try:
            # We need to extract answers from the response text
            # The response text has <u>Answer</u> tags.
            # We need a robust way to map these to the blanks.
            # Currently 'overlay.fill_pdf_overlay' expects a list of answer strings.
            # Parsing the LLM output to get a clean list of answers is "soft" logic.
            # Let's do a simple regex extraction of everything inside <u>
            import re
            
            # Pre-process to identify signature
            # We look for "Signature:" followed by a <u> tag
            # We must be robust against Markdown/HTML tags like <b>Signature:</b> or **Signature:**
            processed_response = re.sub(
                r'((?:<[^>]+>|\*+)?Signature(?:<[^>]+>|\*+)?\s*:?\s*)<u>.*?</u>', 
                r'\1<u>[[SIGNATURE_PLACEHOLDER]]</u>', 
                store.last_generated_response, 
                flags=re.IGNORECASE | re.DOTALL
            )
            
            answers = re.findall(r'<u>(.*?)</u>', processed_response, re.DOTALL)
            
            # If no answers found (maybe LLM messed up tags), fallback?
            if answers:
                print(f"Overlay: Identified {len(answers)} potential answers.")
                pdf_buffer = overlay.fill_pdf_overlay(store.original_form_bytes, processed_response)
                if pdf_buffer:
                    return StreamingResponse(
                        pdf_buffer,
                        media_type="application/pdf",
                        headers={"Content-Disposition": "attachment; filename=filled_form_overlay.pdf"}
                    )
                else:
                    print("Overlay: Failed to generate PDF buffer (likely no blanks matched). Falling back.")
        except Exception as e:
            print(f"Overlay CRASHED: {e}")
            import traceback
            traceback.print_exc()
            print("Overlay: Failed to generate PDF buffer (likely no blanks matched). Returning original document.")
            # Fallback to returning the original document untouched
            return StreamingResponse(
                io.BytesIO(store.original_form_bytes),
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename=unfilled_{store.original_form_filename}"}
            )
    
    print("Overlay: Failed to generate PDF buffer (likely no blanks matched). Returning original document.")
    # Fallback to returning the original document untouched
    return StreamingResponse(
        io.BytesIO(store.original_form_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=unfilled_{store.original_form_filename}"}
    )

@router.get("/download/docx")
async def download_docx():
    if not store.last_generated_response:
        raise HTTPException(status_code=400, detail="No form has been filled yet")
    
    docx_buffer = generator.create_filled_docx(store.last_generated_response)
    return StreamingResponse(
        docx_buffer,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": "attachment; filename=filled_form.docx"}
    )

@router.get("/session-status")
async def session_status():
    return {
        "profile_uploaded": bool(store.company_profile_text),
        "form_uploaded": bool(store.original_form_bytes),
        "form_filename": store.original_form_filename or "",
        "form_text": store.form_text or "",
        "has_filled_response": bool(store.last_generated_response)
    }
