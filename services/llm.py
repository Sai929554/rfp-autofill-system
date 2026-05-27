import google.generativeai as genai
import os
import re
from dotenv import load_dotenv

load_dotenv()

# =========================
# CONFIG
# =========================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY not found in environment variables.")

genai.configure(api_key=GEMINI_API_KEY)

MODEL_NAME = "gemini-2.5-flash"
response = model.generate_content(prompt)

# =========================
# PROMPTS
# =========================

FORM_FILLING_PROMPT = """You are an AI-powered Government RFP Proposal Automation Assistant.

====================================================
STRICT ALIGNMENT AND TAGGING (MANDATORY)
====================================================
1. **WRAP EVERY FILLED ANSWER IN <u> TAGS.** (Example: Name: <u>InnoSoul, Inc.</u>)
2. The Label and the Answer MUST be on the **SAME LINE**.
3. **NEVER OUTPUT UNDERSCORES (`____`)**. Every blank MUST be replaced with an answer or left empty.
4. **CHECKBOXES**: If the PDF has checkboxes like [ ] Yes [ ] No, output ONLY the selected label followed by `: X`. Example: `No: X`. **NEVER use square brackets in your answer.**
   - **CRITICAL**: For multiple-choice questions, **ONLY SELECT ONE** option. Choose the single most accurate option based on the Company Profile.
5. **DO NOT write "Not Applicable", "N/A", "Not Available", or any placeholder text.** If info is missing, leave it blank.

====================================================
SYSTEM ROLE
====================================================
You are an expert in: Government RFP responses, Procurement documentation, Technical proposal writing, Vendor compliance responses, IT consulting proposals, Contract questionnaires, Proposal automation.
You must generate highly accurate, professional, procurement-ready responses.

====================================================
INPUT DOCUMENTS
====================================================
DOCUMENT 1: COMPANY PROFILE (Context)
{company_profile}

DOCUMENT 2: RFP DOCUMENT (To be filled)
{form_content}

====================================================
PRIMARY OBJECTIVE
====================================================
1. Extract relevant information from the company profile.
2. Understand every RFP question and requirement in Document 2.
3. **MANDATORY**: You MUST output the ENTIRE content of DOCUMENT 2 exactly as it is, but replace every underscore (____) with the correct answer wrapped in <u></u> tags.
4. Keep all existing text, labels, and headers. DO NOT summarize or rewrite the document.
5. Fill the RFP intelligently and contextually.

====================================================
STRICT RULES
====================================================
1. NEVER hallucinate. ONLY use information explicitly present in the company profile.
2. If information is missing, **LEAVE THE FIELD BLANK**. DO NOT output any placeholder text like "Information Not Available".
3. Maintain professional government proposal language.
4. **MANDATORY DATA PRIORITY** (always fill these even if not explicitly in profile):
    - **Vendor Legal Name / Company Name**: innoSoul, Inc.
    - **Authorized Signatory / President / Printed Name**: Rashi Shamshabad
    - **Title**: President
    - **Date**: {current_date}
    - **Email Address**: bids@innosoul.com
    - **Phone Number**: 518-400-0425
    - **Fax Number**: (Not Provided)
    - **Street Address**: 349 Kinderkamack Rd, Westwood, NJ 07675
5. **CHECKBOXES**: Output only the word "Selected" or "X" for checkboxes. DO NOT use square brackets `[]` in your final output.
6. Keep all other names, addresses, and contract IDs exactly as written in the Profile.

====================================================
DOCUMENT ANALYSIS PROCESS
====================================================
STEP 1: Extract Company overview, history, experience, references, methodologies, staffing, certifications, compliance, security practices, etc.
STEP 2: Identify Questions, Forms, Tables, Mandatory requirements, etc.
STEP 3: SEMANTIC MATCHING - Match intent to correct source content.
STEP 4: RESPONSE GENERATION - Procurement-ready, technically accurate.

Accuracy > Completeness. Every answer must be traceable. Your final output must look like it was written by an experienced government proposal manager.
"""

QA_PROMPT = """You are a compliance-focused assistant.

Answer strictly using the company profile below.

If the answer does not exist, respond exactly:

Information not found in company profile

Company Profile:
{company_profile}

Question:
{question}
"""

# =========================
# CORE LLM CALL
# =========================

def _llm_call(prompt: str, max_retries: int = 3) -> str:
    import time, re as _re
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt
            )
            return response.text.strip()

        except Exception as e:
            err_str = str(e)
            # Handle Rate Limit (429) - parse retry delay and wait
            if "429" in err_str or "ResourceExhausted" in err_str or "quota" in err_str.lower():
                # Try to parse the retry delay from error message
                delay_match = _re.search(r'retry[_\s]delay[^0-9]*(\d+)', err_str, _re.IGNORECASE)
                wait_sec = int(delay_match.group(1)) + 5 if delay_match else 30
                
                if attempt < max_retries - 1:
                    print(f"Rate limit hit. Waiting {wait_sec}s before retry {attempt+2}/{max_retries}...")
                    time.sleep(wait_sec)
                    continue
                else:
                    raise RuntimeError(
                        f"API rate limit reached (free tier: 20 requests/day). "
                        f"Please wait a few minutes and try again, or upgrade your Gemini API plan."
                    )
            # Other errors - fail immediately
            raise RuntimeError(f"Gemini failure: {err_str}")

# =========================
# PUBLIC FUNCTIONS
# =========================

def generate_form_answers(profile_text: str, form_text: str) -> str:
    from datetime import datetime
    current_date = datetime.now().strftime("%m/%d/%Y")
    
    prompt = FORM_FILLING_PROMPT.format(
        company_profile=profile_text,
        form_content=form_text,
        current_date=current_date
    )

    raw = _llm_call(prompt)
    fixed = _fix_broken_alignment(raw)
    return _align_colons(fixed)

def answer_question(profile_text: str, question: str) -> str:
    prompt = QA_PROMPT.format(
        company_profile=profile_text,
        question=question,
    )
    return _llm_call(prompt)

# =========================
# POST-PROCESSING FIXES
# =========================

def _fix_broken_alignment(text: str) -> str:
    """
    Fix cases where labels, underscores, and answers
    are split across lines by the model.
    """
    lines = text.split("\n")
    pass1_lines = []
    i = 0

    while i < len(lines):
        line = lines[i].rstrip()

        # Merge: label + <u>answer</u> on next line
        if (
            i + 1 < len(lines)
            and lines[i + 1].strip().startswith("<u>")
            and "_" not in line
            and not line.endswith(">")
        ):
            pass1_lines.append(line + " " + lines[i + 1].strip())
            i += 2
            continue

        # Merge: underscores replaced by next line answer
        if i + 1 < len(lines) and re.search(r"_+$", line):
            pass1_lines.append(re.sub(r"_+$", lines[i + 1].strip(), line))
            i += 2
            continue

        pass1_lines.append(line)
        i += 1
        
    # Pass 2: Failsafe - Replace any remaining long underscores with NOT PROVIDED
    # This specifically targets cases where the LLM just parroted the blanks
    final_lines = []
    for line in pass1_lines:
        # valid underscore replacement
        # Replace sequences of 3 or more underscores that are NOT part of a tag (unlikely but safe)
        # We replace them with <u>NOT PROVIDED</u> 
        if "___" in line:
            # We use regex to replace isolated underscores or training underscores
            # Be careful not to replace underscores inside filenames or something, but form blanks are usually long
            fixed_line = re.sub(r'_{3,}', '<u>NOT PROVIDED</u>', line)
            final_lines.append(fixed_line)
        else:
            final_lines.append(line)

    return '\n'.join(final_lines)

def _align_colons(text: str) -> str:
    """
    Aligns colons in the text to the same vertical column.
    It groups consecutive lines that have colons and aligns them.
    """
    lines = text.split('\n')
    aligned_lines = []
    block_lines = []

    def process_block(block):
        if not block:
            return []
        
        # Calculate max label length
        max_len = 0
        valid_lines = []
        
        # First pass: find max length
        for line in block:
            if ':' in line:
                label_part = line.split(':', 1)[0]
                # Heuristic: If label is too long (e.g. > 60 chars), it might be a sentence, not a label.
                # Skip alignment for that line to avoid weird gaps.
                if len(label_part) < 60:
                     max_len = max(max_len, len(label_part))
        
        if max_len == 0:
            return block

        # Max length should effectively be max_len, but let's add no extra padding?
        # Actually usually nice to have 1 space after longest label. 
        
        result = []
        for line in block:
            if ':' in line:
                parts = line.split(':', 1)
                label = parts[0]
                value = parts[1]
                
                if len(label) < 60:
                    padding = ' ' * (max_len - len(label))
                    # Reconstruct: Label + Padding + : + Value
                    # Ensure value starts with a space if it doesn't has one?
                    # Usually "Label: Value" -> "Label      : Value"
                    result.append(f"{label}{padding}:{value}")
                else:
                    result.append(line)
            else:
                result.append(line)
        return result

    for line in lines:
        # Check if line looks like "Label: Value"
        # We start a block if we see potential alignment candidates
        # We break block on empty lines or headers
        
        is_candidate = ':' in line and not line.strip().startswith('<b>') # Don't align headers usually
        
        if is_candidate:
            block_lines.append(line)
        else:
            if block_lines:
                aligned_lines.extend(process_block(block_lines))
                block_lines = []
            aligned_lines.append(line)
    
    # Flush remaining
    if block_lines:
        aligned_lines.extend(process_block(block_lines))

    return '\n'.join(aligned_lines)
