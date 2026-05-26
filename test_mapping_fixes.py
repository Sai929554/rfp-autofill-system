import re

def test_mapping():
    # Simulated LLM response
    clean_response = """
    * Vendor Legal Name: <u>innoSoul, Inc.</u>
    * Authorized Signatory: <u>Rashi Shamshabad</u>
    * Email Address: <u>bids@innosoul.com</u>
    * Fax Number: <u>(Not Provided)</u>
    * Phone Number: <u>518-400-0425</u>
    """

    CRITICAL_OVERRIDES = [
        (r'\bdate\b\s*:?\s*',                                     "05/13/2026"),
        (r'\be-?mail\b(?:\s*address)?\s*:?\s*',                   'bids@innosoul.com'),
        (r'\bfax\b(?:\s*number)?\s*:?\s*',                        ''), 
        (r'\bphone\b(?:\s*number)?\s*:?\s*',                      '518-400-0425'),
        (r'\bcompany\s*name\b|\blegal\s*business\s*name\b|\bvendor\s*name\b',   'innoSoul, Inc.'),
        (r'\bcontact\b(?:\s*person|\s*name)?\s*:?\s*',            'Rashi Shamshabad'),
        (r'^(?!.*(?:company|vendor)).*\bname\b.*',               'Rashi Shamshabad'), 
        (r'\bprinted\b.*name|\bprint\b\s*name',                  'Rashi Shamshabad'),
        (r'\btitle\b\s*:?\s*',                                    'President'),
    ]

    def mock_fill(ctx):
        ans = None
        # Pass 1: Semantic
        safe_ctx = re.escape(ctx)
        pattern = r'\b' + safe_ctx + r'\b.*?\s*:?\s*<u>(.*?)</u>'
        match = re.search(pattern, clean_response, re.IGNORECASE | re.DOTALL)
        if match:
            ans = match.group(1).strip()
            print(f"  [Pass 1] '{ctx}' matched '{pattern}' -> {ans}")
        
        # Pass 2: Overrides
        for pattern, value in CRITICAL_OVERRIDES:
            if re.search(pattern, ctx, re.IGNORECASE):
                ans = value
                print(f"  [Pass 2] Override match: '{pattern}' -> {ans}")
                break
        return ans

    print(f"Result for 'Name': {mock_fill('Name')}")
    print(f"Result for 'Company Name': {mock_fill('Company Name')}")
    print(f"Result for 'Fax': {mock_fill('Fax')}")
    print(f"Result for 'Email': {mock_fill('Email')}")

test_mapping()
