import os

def safe_remove(path):
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except:
        pass