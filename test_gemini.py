from services.llm import generate_form_answers
import time

with open("test_output.txt", "w") as f:
    f.write("Testing Gemini integration...\n")
    start = time.time()
    try:
        response = generate_form_answers(
            "Company: Acme Corp. Services: Rocket Science.",
            "Name: ______\nService: ______"
        )
        f.write(f"Response: {response}\n")
        f.write(f"Time taken: {time.time() - start:.2f}s\n")
    except Exception as e:
        f.write(f"Error: {e}\n")
