import re

def test_regex():
    full_response = """
Here are the extracted details:
* **Legal Business Name:** InnoSoul, Inc.
* Date: (Not Provided)
- Phone Number: 555-1234
    """
    
    clean_response = full_response.replace('**', '').replace('__', '')
    answers = re.findall(r'<u>(.*?)</u>', clean_response, re.DOTALL)
    if not answers:
        bullet_matches = re.findall(r'^[*-]\s*.*?\s*:\s*(.+)$', clean_response, re.MULTILINE)
        answers = [ans.strip() for ans in bullet_matches]
        
    print("Extracted answers:", answers)

test_regex()
