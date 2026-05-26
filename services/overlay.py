import io
import pdfplumber
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from pypdf import PdfWriter, PdfReader

def normalize_text(text):
    return text.replace('_', '').strip()

def get_context_for_blank(blank_top, blank_bottom, blank_x0, words):
    """
    Finds the label to the LEFT of a blank on the same row.
    Returns only the NEAREST words to prevent concatenated contexts.
    """
    left_words = []
    # STRICT vertical tolerance — only match words on the exact same row
    v_tol = 3  
    for word in words:
        if word['bottom'] >= blank_top - v_tol and word['top'] <= blank_bottom + v_tol:
            # Word must be to the left
            if word['x1'] <= blank_x0 + 5:
                # Limit horizontal distance to 150px to avoid picking up previous fields' labels
                if blank_x0 - word['x1'] < 150:
                    left_words.append(word)
    
    if left_words:
        # Sort by x1 (end of word) descending to find the closest words first
        left_words.sort(key=lambda w: w['x1'], reverse=True)
        
        # Take words starting from the right (closest to blank) until a large gap is found
        nearest_words = []
        last_x1 = blank_x0
        for w in left_words:
            gap = last_x1 - w['x1']
            if gap > 35: # Increased from 25 to 35 to handle labels like "Company Name:"
                break
            nearest_words.append(w)
            last_x1 = w['x0']
        
        if nearest_words:
            nearest_words.sort(key=lambda w: w['x0'])
            return " ".join([w['text'] for w in nearest_words]).strip()
    
    # Fallback Strategy: Look slightly ABOVE the blank
    above_words = []
    for word in words:
        if word['bottom'] >= blank_top - 15 and word['bottom'] <= blank_top + 2:
            if word['x0'] >= blank_x0 - 20 and word['x0'] <= blank_x0 + 100:
                above_words.append(word)
    
    if above_words:
        above_words.sort(key=lambda w: (w['top'], w['x0']))
        return " ".join([w['text'] for w in above_words]).strip()

    return ""

def is_blank_filled(blank_x0, blank_top, blank_bottom, blank_width, words):
    """
    Checks if a line/blank already contains written text by looking at words
    resting in its immediate writable area.
    """
    filled_text = []
    min_x = blank_x0 + 5 
    max_x = blank_x0 + blank_width - 5
    min_y = blank_top - 16
    max_y = blank_bottom + 2
    
    for word in words:
        if word['bottom'] >= min_y and word['top'] <= max_y:
            # Check for horizontal intersection
            if word['x1'] > min_x and word['x0'] < max_x:
                clean_w = word['text'].replace('_', '').replace('.', '').strip()
                if clean_w:
                    filled_text.append(clean_w)
                    
    return len("".join(filled_text)) > 2

def analyze_pdf_for_blanks(pdf_bytes):
    """
    Scans the PDF to find potential blank lines (underscores) AND graphical lines.
    Returns a list of dicts: {'page': N, 'x': val, 'y': val, 'width': val, 'page_height': val}
    """
    blanks = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for i, page in enumerate(pdf.pages):
            # Capture dynamic page size
            page_height = page.height
            page_width = page.width
            
            try:
                page_words = page.extract_words()
            except:
                page_words = []
            
            # Strategy 1: Text Underscores
            chars = page.chars
            current_blank = None
            
            for char in chars:
                if char['text'] == '_':
                    if current_blank is None:
                        current_blank = {
                            'page': i,
                            'x0': char['x0'],
                            'top': char['top'], # distance from top
                            'bottom': char['bottom'], 
                            'width': char['width'],
                            'height': char['height'],
                            'page_height': page_height # CRITICAL FIX
                        }
                    else:
                        current_blank['width'] += char['width']
                else:
                    if current_blank:
                        if current_blank['width'] > 20: 
                            if not is_blank_filled(current_blank['x0'], current_blank['top'], current_blank['bottom'], current_blank['width'], page_words):
                                current_blank['context'] = get_context_for_blank(
                                    current_blank['top'], current_blank['bottom'], current_blank['x0'], page_words
                                )
                                blanks.append(current_blank)
                        current_blank = None
            
            if current_blank and current_blank['width'] > 20:
                if not is_blank_filled(current_blank['x0'], current_blank['top'], current_blank['bottom'], current_blank['width'], page_words):
                    current_blank['context'] = get_context_for_blank(
                        current_blank['top'], current_blank['bottom'], current_blank['x0'], page_words
                    )
                    blanks.append(current_blank)
            
            # Strategy 2: Graphical Lines (Rects/Lines/Curves)
            for line in page.lines:
                if line['width'] > 30:
                    if not is_blank_filled(line['x0'], line['top'], line['bottom'], line['width'], page_words):
                        context = get_context_for_blank(line['top'], line['bottom'], line['x0'], page_words)
                        blanks.append({
                            'page': i,
                            'x0': line['x0'],
                            'top': line['top'],
                            'bottom': line['bottom'],
                            'width': line['width'],
                            'height': 2,
                            'page_height': page_height,
                            'context': context
                        })
            
            for rect in page.rects:
                if rect['height'] < 3 and rect['width'] > 30:
                    if not is_blank_filled(rect['x0'], rect['top'], rect['bottom'], rect['width'], page_words):
                        context = get_context_for_blank(rect['top'], rect['bottom'], rect['x0'], page_words)
                        blanks.append({
                            'page': i,
                            'x0': rect['x0'],
                            'top': rect['top'],
                            'bottom': rect['bottom'],
                            'width': rect['width'],
                            'height': rect['height'],
                            'page_height': page_height,
                            'context': context
                        })
            
            # Added Strategy 2.1: Curves (sometimes lines are drawn as paths)
            for curve in page.curves:
                if curve['width'] > 30 and curve['height'] < 3:
                    if not is_blank_filled(curve['x0'], curve['top'], curve['bottom'], curve['width'], page_words):
                        context = get_context_for_blank(curve['top'], curve['bottom'], curve['x0'], page_words)
                        blanks.append({
                            'page': i,
                            'x0': curve['x0'],
                            'top': curve['top'],
                            'bottom': curve['bottom'],
                            'width': curve['width'],
                            'height': curve['height'],
                            'page_height': page_height,
                            'context': context
                        })
            
            # Strategy 3: Table Cells (Empty Cells)
            try:
                tables = page.find_tables()
                for table in tables:
                    for row in table.rows:
                        for cell in row.cells:
                            if not cell: continue
                            cell_bbox = (cell[0], cell[1], cell[2], cell[3])
                            cell_text = page.crop(cell_bbox).extract_text()
                            clean_cell_text = cell_text.strip() if cell_text else ""
                            is_genuine_blank = False
                            if not clean_cell_text or clean_cell_text in ["_", ".", "N/A"]:
                                is_genuine_blank = True
                            elif len(clean_cell_text) < 35:
                                if clean_cell_text.endswith(":") or clean_cell_text.endswith("|"):
                                    is_genuine_blank = True
                                elif ":" in clean_cell_text:
                                    parts = clean_cell_text.split(":")
                                    after_colon = parts[-1].replace("|", "").replace("_", "").strip()
                                    if len(after_colon) == 0:
                                        is_genuine_blank = True
                            
                            if is_genuine_blank:
                                cell_words = page.crop(cell_bbox).extract_words()
                                context_x1 = max([w['x1'] for w in cell_words]) if cell_words else cell[0] + 2
                                
                                lines_in_cell = [line for line in cell_text.split('\n') if line.strip()]
                                if len(lines_in_cell) > 1:
                                    h_step = (cell[3] - cell[1]) / len(lines_in_cell)
                                    for idx, line_text in enumerate(lines_in_cell):
                                        line_height = 20
                                        blanks.append({
                                            'page': i,
                                            'x0': cell[0] + 2,
                                            'context_x1': context_x1,
                                            'top': cell[1] + (idx * h_step),
                                            'bottom': min(cell[1] + (idx * h_step) + line_height, cell[3]),
                                            'width': cell[2] - cell[0],
                                            'height': h_step - 2,
                                            'page_height': page_height,
                                            'context': line_text.strip(),
                                            'is_table_cell': True
                                        })
                                else:
                                    blanks.append({
                                        'page': i,
                                        'x0': cell[0] + 2,
                                        'context_x1': context_x1,
                                        'top': cell[1],
                                        'bottom': cell[3] - 2,
                                        'width': cell[2] - cell[0],
                                        'height': cell[3] - cell[1],
                                        'page_height': page_height,
                                        'context': clean_cell_text,
                                        'is_table_cell': True
                                    })
            except Exception as e:
                print(f"Error finding tables on page {i}: {e}")
            
            # Strategy 5: Checkboxes (Small Rectangles)
            for rect in page.rects:
                w = rect['width']
                h = rect['height']
                if 6 <= w <= 25 and 6 <= h <= 25 and abs(w - h) < 5:
                    ctx_words = []
                    for word in page_words:
                        # Checkboxes usually have text to the RIGHT or LEFT
                        # Increase search radius to 300px to catch long labels
                        if word['bottom'] >= rect['top'] - 10 and word['top'] <= rect['bottom'] + 10:
                            if (word['x1'] <= rect['x0'] and word['x0'] >= rect['x0'] - 300) or \
                               (word['x0'] >= rect['x1'] and word['x1'] <= rect['x1'] + 300):
                                ctx_words.append(word)
                    
                    if ctx_words:
                        ctx_words.sort(key=lambda w: w['x0'])
                        context = " ".join([w['text'] for w in ctx_words]).strip()
                        blanks.append({
                            'page': i,
                            'x0': rect['x0'],
                            'top': rect['top'],
                            'bottom': rect['bottom'],
                            'width': w,
                            'height': h,
                            'page_height': page_height,
                            'context': context,
                            'is_checkbox': True
                        })

    # --- SPATIAL DEDUPLICATION (Fixes Overlapping) ---
    # Increase tolerance for deduplication to 15px to catch slightly shifted overlaps
    blanks.sort(key=lambda b: (b['page'], b['top'], b['x0']))
    
    unique_blanks = []
    for b in blanks:
        is_dup = False
        for u in unique_blanks:
            if b['page'] == u['page']:
                # If centers are within 15px of each other, they are the same field
                dist = ((b['x0'] - u['x0'])**2 + (b['top'] - u['top'])**2)**0.5
                if dist < 15:
                    is_dup = True
                    # Priority: Table Cell > Graphic Line > Text Underscore
                    # This ensures we don't print twice in the same box
                    if b.get('is_table_cell') or b.get('is_checkbox'):
                        u.update(b)
                    break
        if not is_dup:
            unique_blanks.append(b)

    # Secondary Semantic dedup for overlapping boxes/lines
    final_blanks = []
    for b in unique_blanks:
        is_duplicate = False
        for f in final_blanks:
            if b['page'] == f['page']:
                # Check for vertical intersection
                v_intersect = (b['top'] < f['bottom'] - 1 and b['bottom'] > f['top'] + 1)
                # Check for horizontal overlap
                h_overlap = (max(b['x0'], f['x0']) < min(b['x0'] + b['width'], f['x0'] + f['width']) - 2)
                
                if v_intersect and h_overlap:
                    is_duplicate = True
                    # Preserve the more "featured" blank
                    if b.get('is_table_cell') or b.get('is_checkbox'):
                        f.update(b)
                    break
        if not is_duplicate:
            final_blanks.append(b)

    print(f"Overlay Analysis: Found {len(final_blanks)} distinct blanks.")
    return final_blanks

def create_overlay_pdf(blanks, full_response):
    """
    Generates a transparent PDF with answers at the blank locations.
    """
    import re
    
    # Remove markdown bolding to prevent regex from tripping on asterisks
    clean_response = full_response.replace('**', '').replace('__', '')
    
    answers = re.findall(r'<u>(.*?)</u>', clean_response, re.DOTALL)
    
    # Fallback: If no <u> tags found, try to extract sequentially from markdown bullet points
    if not answers:
        bullet_matches = re.findall(r'^[*-]\s*.*?\s*:\s*(.+)$', clean_response, re.MULTILINE)
        if bullet_matches:
            answers = [ans.strip() for ans in bullet_matches]

    used_answer_indices = set()
    blank_to_answer = {}
    print(f"Overlay Engine: Attempting to fill {len(blanks)} blanks...")
    
    # Pass 1: Semantic Matching for blanks that have context (like table cell labels)
    for i, blank in enumerate(blanks):
        context = blank.get('context', '')
        is_checkbox = blank.get('is_checkbox', False)
        if context:
            # --- HEADER/KEYWORD BLOCKER ---
            # Skip if context is just a number (e.g. "1.") or a reserved section header keyword.
            reserved_keywords = ["DEFAULT", "INSURANCE", "SCOPE", "AWARD", "CONTRACT", "PERIOD", "AWARD", "BIDDER", "SECTION", "APPENDIX", "REQUIREMENTS", "QUALIFICATIONS", "CRITERIA", "INSTRUCTIONS"]
            clean_ctx_upper = context.strip().upper().rstrip(":")
            if re.match(r'^\d+\.?$', context) or len(context) < 2 or any(k == clean_ctx_upper for k in reserved_keywords):
                continue
                
            # Clean context for multi-line cells: Take the first line only
            context = context.split('\n')[0].strip()
            # Strip sub-labels in parentheses like (legal entity) or (signature)
            context = re.sub(r'\(.*?\)', '', context).strip()
            
            # Fuzzy Match: Use the first 3 words of the context to find the line in the AI response
            # This handles cases where the AI adds/removes "(legal entity)" or colons.
            ctx_words = context.split()
            fuzzy_ctx = " ".join(ctx_words[:3]) if len(ctx_words) > 3 else context
            
            # Escape for regex but allow some flexibility in the middle
            safe_ctx = re.escape(fuzzy_ctx)
            # Use \b word boundaries to prevent "Name" matching "Company Name"
            pattern = r'\b' + safe_ctx + r'\b.*?\s*:?\s*<u>(.*?)</u>'
            
            match = re.search(pattern, clean_response, re.IGNORECASE | re.DOTALL)
            
            if match:
                ans = match.group(1).strip()
                # Strip all placeholder text - leave blank instead
                bad_phrases = ["information not available", "not provided", "not applicable", "n/a"]
                if any(p in ans.lower() for p in bad_phrases):
                    ans = ""
                blank_to_answer[i] = ans
                continue
                
        if context and (len(context) > 3 or is_checkbox):
            
            # Clean context for regex (ignore extra spaces/newlines)
            clean_ctx = r'\s*'.join(re.escape(word) for word in context.split())
            
            if is_checkbox:
                # Match both [X] format and bare "Label: X" format from AI
                # Pattern 1: [X] Yes  or  Yes [X]
                cb_regex_brackets = r'\[[xX]\]\s*' + clean_ctx + r'|' + clean_ctx + r'\s*\[[xX]\]'
                # Pattern 2: "No: X"  or  "Yes: X"  (bare X after colon)
                cb_regex_bare = clean_ctx + r'\s*:\s*X\b'
                match = re.search(cb_regex_brackets + r'|' + cb_regex_bare, clean_response, re.IGNORECASE)
                if match:
                    blank_to_answer[i] = "X"
                continue
                
            # Search for the context followed by <u>...</u> in the LLM response
            # Use \b to ensure exact label matching
            match = re.search(r'\b' + clean_ctx + r'\b\s*:?\s*<u>(.*?)</u>', clean_response, re.IGNORECASE | re.DOTALL)
            
            # If the LLM failed to use <u> tags and just output markdown (e.g. * Label:\n  Answer)
            if not match:
                # loose match: Label -> optional colon/newlines -> capture up to next newline
                loose_regex = clean_ctx + r'\s*:?\s*\n?\s*([^\n]+)'
                match = re.search(loose_regex, clean_response, re.IGNORECASE)
                
                if match:
                    ans = match.group(1).strip()
                    # Reject if we accidentally captured the next bullet point or label
                    if ans.startswith('* ') or ans.startswith('- ') or ans.endswith(':'):
                        match = None

            if match:
                ans = match.group(1).strip()
                # Strip all placeholder text
                bad_phrases = ["information not available", "not provided", "not applicable", "n/a"]
                if any(p in ans.lower() for p in bad_phrases):
                    ans = ""
                blank_to_answer[i] = ans
                
                # Mark this answer as used so sequential matching skips it
                for j in range(len(answers)):
                    if j not in used_answer_indices and answers[j] == ans:
                        used_answer_indices.add(j)
                        break

    print(f"Overlay Matching: Successfully mapped {len(blank_to_answer)} answers to blanks semantically.")
    
    # Pass 2: Critical Field Override
    # Uses regex word-boundary matching to PRECISELY identify fields and inject correct values.
    # This runs AFTER semantic matching and OVERRIDES any wrong values the AI placed.
    # Uses \b word boundaries to prevent 'date' matching 'candidate', 'title' matching 'subtitle', etc.
    from datetime import datetime
    current_date_str = datetime.now().strftime("%m/%d/%Y")
    CRITICAL_OVERRIDES = [
        # Today's Date: Dynamic
        (r'\bdate\b\s*:?\s*',                                     current_date_str),
        
        # Email: Catch "E-mail:", "Email address", etc.
        (r'\be-?mail\b(?:\s*address)?\s*:?\s*',                   'bids@innosoul.com'),
        
        # Fax
        (r'\bfax\b(?:\s*number)?\s*:?\s*',                        ''), 
        
        # Phone / Telephone / Contact / Mobile (Requested: all same number)
        (r'\b(?:phone|telephone|contact|mobile|cell)\b(?:\s*number)?\s*:?\s*', '518-400-0425'),
        
        # Company Name: Priority match
        (r'\bcompany\b(?:\s*name)?|\blegal\s*business\s*name\b|\bvendor\s*name\b', 'innoSoul, Inc.'),
        
        # "By" means Company Name as per user request
        (r'\bby\b\s*:?\s*',                                       'innoSoul, Inc.'),
        
        # Contact Name / Person (Exclude Company/Vendor keywords)
        (r'\bcontact\b(?:\s*person|\s*name)?\s*:?\s*',            'Rashi Shamshabad'),
        (r'^(?!.*(?:company|vendor|by)).*\bname\b.*',            'Rashi Shamshabad'), 
        (r'\bprinted\b.*name|\bprint\b\s*name',                  'Rashi Shamshabad'),
        
        # Title / Address
        (r'\btitle\b\s*:?\s*',                                    'President'),
        (r'\baddress\b(?:\s*line\s*1)?\s*:?\s*',                  '349 Kinderkamack Rd, Westwood, NJ 07675'),
        (r'\bcity/state/zip\b',                                    'Westwood, NJ 07675'),
    ]

    for i, blank in enumerate(blanks):
        if blank.get('is_checkbox'):
            continue
        ctx = blank.get('context', '').lower().strip()
        for pattern, value in CRITICAL_OVERRIDES:
            if re.search(pattern, ctx, re.IGNORECASE):
                print(f"Override MATCH: '{pattern}' matched '{ctx}' -> {value}")
                blank_to_answer[i] = value
                break

    if not blank_to_answer:
        print("Overlay Warning: Found NO matching answers for the blanks.")
    else:
        print(f"Overlay Engine: Final match count: {len(blank_to_answer)} / {len(blanks)}")

    packet = io.BytesIO()
    can = canvas.Canvas(packet)
    
    current_page = 0
    
    for i, blank in enumerate(blanks):
        if i in blank_to_answer:
            text = blank_to_answer[i]
            
            # Handle page switching
            target_page = blank['page']
            while current_page < target_page:
                can.showPage()
                current_page += 1
                
            # Clean up double names (if answer contains its own label)
            context_str = blank.get('context', '')
            clean_text = text.strip()
            
            # Remove "Date:" from "Date: May 22, 2024" to prevent printing double names
            if context_str and clean_text.lower().startswith(context_str.lower()):
                clean_text = clean_text[len(context_str):].strip()
                if clean_text.startswith(":"):
                    clean_text = clean_text[1:].strip()
            
            text = clean_text

            is_checkbox = blank.get('is_checkbox', False)
            is_table_cell = blank.get('is_table_cell', False)
            
            # --- GLOBAL TEXT CLEANUP ---
            # 1. Strip brackets
            text = text.replace('[ ]', '').replace('[]', '').strip()
            # 2. Block SIGNATURE_PLACEHOLDER from non-signature fields
            if 'SIGNATURE_PLACEHOLDER' in text or 'SIGNATURE_PLACEHOLDER' in text.upper():
                context_lower_check = blank.get('context', '').lower()
                if not any(w in context_lower_check for w in ['signature', 'sign', ' by', 'vendor signature']):
                    continue  # Skip — don't render on non-signature fields
            # 3. Strip remaining bad placeholder text
            bad = ['not provided', 'not applicable', 'n/a', 'information not available']
            if any(b in text.lower() for b in bad):
                continue  # Leave blank, render nothing
            
            if is_checkbox or text.upper() in ["X", "[X]", "SELECTED", "CHECKED"]:
                y_pos = blank['page_height'] - blank['bottom'] + 2
                x_pos = blank['x0'] + (blank['width'] / 2) - 4
                if "X" in text.upper() or "SELECTED" in text.upper() or "CHECKED" in text.upper():
                    can.setFont("Helvetica-Bold", 12)
                    can.drawString(x_pos, y_pos, "X")
                continue
            
            # Final cleanup for non-checkbox text
            text = text.replace('[X]', 'X').replace('[', '').replace(']', '')

            # Smart Placement Logic
            if is_table_cell:
                # Use context_x1 if available to start exactly after the label/pipe
                if 'context_x1' in blank:
                    x_pos = blank['context_x1'] + 4
                else:
                    label_width = min(len(context_str) * 5.2, 120) 
                    x_pos = blank['x0'] + label_width + 4
                
                if blank['height'] > 30:
                    # Tall table cell: Label is at the top, so draw near the top
                    y_pos = blank['page_height'] - blank['top'] - 15
                else:
                    # Short table cell: Label is at the bottom, so draw near the bottom
                    # Calibrated to +2.0 for better baseline seating in table cells
                    y_pos = blank['page_height'] - blank['bottom'] + 2.0
            else:
                # Thin line or underscore: Draw resting on the bottom
                y_pos = blank['page_height'] - blank['bottom'] + 1.5
                x_pos = blank['x0'] + 2
            
            # Clean up the AI output
            if "NOT PROVIDED" in text.upper():
                text = ""

            context_lower = blank.get('context', '').lower()
            
            # Only draw signature if the context explicitly mentions signature/by
            is_sig_field = any(w in context_lower for w in ['signature', 'sign', 'by:', 'vendor signature'])
            
            if is_sig_field and ("SIGNATURE" in text.upper() or text.strip().upper() in ["S", "SIG"]):
                # For signatures, draw the signature image
                import os
                BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                SIGNATURE_PATH = os.path.join(BASE_DIR, "static", "signature.png")
                
                if os.path.exists(SIGNATURE_PATH):
                    try:
                        from services.utils import get_cropped_image_data
                        from reportlab.lib.utils import ImageReader
                        cropped_img = get_cropped_image_data(SIGNATURE_PATH)
                        img_source = ImageReader(cropped_img) if cropped_img else ImageReader(SIGNATURE_PATH)
                        
                        # Decrease signature size drastically to prevent overlap
                        img_width = 80
                        img_height = 25
                        can.drawImage(img_source, x_pos, y_pos - 10, width=img_width, height=img_height, mask='auto', preserveAspectRatio=True)
                    except Exception as e:
                        print(f"Error drawing signature: {e}")
                        can.drawString(x_pos, y_pos, "[Signature Image Error]")
                else:
                     can.drawString(x_pos, y_pos, "[Signature]")
            else:
                # --- SMART WRAPPING & SCALING (Fixes Overflow) ---
                base_font_size = 10.0
                can.setFont("Helvetica", base_font_size)
                
                # Check if text exceeds blank width
                text_width = can.stringWidth(text, "Helvetica", base_font_size)
                available_width = blank['width'] - 10
                
                if text_width > available_width:
                    # If cell is tall enough, wrap into two lines
                    if blank['height'] > 25 and len(text) > 30:
                        words = text.split()
                        mid = len(words) // 2
                        line1 = " ".join(words[:mid])
                        line2 = " ".join(words[mid:])
                        can.drawString(x_pos, y_pos + 10, line1)
                        can.drawString(x_pos, y_pos, line2)
                    else:
                        # Scale down font size dynamically
                        ratio = available_width / text_width
                        new_size = max(base_font_size * ratio, 6.0)
                        can.setFont("Helvetica", new_size)
                        can.drawString(x_pos, y_pos, text)
                else:
                    can.drawString(x_pos, y_pos, text)
            
    can.save()
    packet.seek(0)
    return packet

def fill_pdf_overlay(original_pdf_bytes, full_response):
    """
    Original PDF + Overlay = Filled PDF
    """
    blanks = analyze_pdf_for_blanks(original_pdf_bytes)
    
    if not blanks:
        return None
        
    overlay_packet = create_overlay_pdf(blanks, full_response)
    new_pdf = PdfReader(overlay_packet)
    original_pdf = PdfReader(io.BytesIO(original_pdf_bytes))
    output = PdfWriter()
    
    for i in range(len(original_pdf.pages)):
        page = original_pdf.pages[i]
        
        # Merge if we have an overlay page for this index
        if i < len(new_pdf.pages):
             page.merge_page(new_pdf.pages[i])
             
        output.add_page(page)
        
    out_buffer = io.BytesIO()
    output.write(out_buffer)
    out_buffer.seek(0)
    return out_buffer
