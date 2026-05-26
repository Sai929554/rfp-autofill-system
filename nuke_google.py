import os
import shutil
import site
import sys
import subprocess

def install_package(package):
    print(f"Installing {package}...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def nuke_google():
    site_packages = site.getsitepackages()
    print(f"Searching in: {site_packages}")
    
    targets = ['google', 'google_genai', 'google_generativeai']
    
    for sp in site_packages:
        if os.path.isdir(sp):
            for target in targets:
                target_path = os.path.join(sp, target)
                if os.path.exists(target_path):
                    print(f"Removing corrupted package: {target_path}")
                    try:
                        shutil.rmtree(target_path)
                        print("  Deleted.")
                    except Exception as e:
                        print(f"  FAILED to delete: {e}")

    # Reinstall
    print("\nReinstalling fresh dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "cache", "purge"])
    install_package("google-genai")
    
    # Validation
    try:
        import google.genai
        print("\n\nSUCCESS! google.genai imported successfully.")
    except ImportError as e:
        print(f"\n\nFAILURE: Still cannot import: {e}")

if __name__ == "__main__":
    nuke_google()
