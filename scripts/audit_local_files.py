import os
from pathlib import Path

def audit_local():
    mosdac_dir = Path(r"C:\Users\Vedant\Documents\mosdac")
    print(f"Auditing directory: {mosdac_dir}")
    if not mosdac_dir.exists():
        print("Directory does not exist.")
        return
        
    for item in mosdac_dir.iterdir():
        if item.is_file():
            size_mb = item.stat().st_size / (1024 * 1024)
            print(f"File: {item.name}, Size: {size_mb:.2f} MB")
            
if __name__ == "__main__":
    audit_local()
