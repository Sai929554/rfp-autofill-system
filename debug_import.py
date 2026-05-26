import sys
import os

print(f"Python Executable: {sys.executable}")
print(f"CWD: {os.getcwd()}")
print("Sys Path:")
for p in sys.path:
    print(f"  {p}")

try:
    import google
    print(f"\nGoogle package path: {google.__path__}")
except ImportError:
    print("\nCould not import google namespace")

try:
    import google.genai
    print("\nSUCCESS: google.genai imported")
except ImportError as e:
    print(f"\nFAILURE: {e}")

try:
    import google.generativeai
    print("WARNING: google.generativeai is still present")
except ImportError:
    print("google.generativeai is NOT present (Good)")
