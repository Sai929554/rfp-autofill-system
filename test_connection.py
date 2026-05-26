from google import genai
import os
from dotenv import load_dotenv
import traceback

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')

with open("connection_log.txt", "w") as f:
    f.write(f"API Key present: {bool(api_key)}\n")
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents='Test connection'
        )
        f.write(f"Success: {response.text}\n")
    except Exception as e:
        f.write("Error:\n")
        f.write(traceback.format_exc())
