import os

def test_endpoints():
    print("Testing if there are any syntax errors in overlay.py...")
    try:
        import services.overlay
        print("overlay.py imported successfully!")
    except Exception as e:
        import traceback
        traceback.print_exc()

test_endpoints()
