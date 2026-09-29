import os
import sys
import json
import shutil
import tempfile
import subprocess
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

temp_dir = tempfile.mkdtemp()
project_root = Path(__file__).resolve().parent.parent
mdapi_path = project_root / "mosdac_client" / "mdapi.py"

shutil.copy(str(mdapi_path), temp_dir)

config = {
    "user_credentials": {
        "username/email": os.getenv("MOSDAC_USERNAME"),
        "password": os.getenv("MOSDAC_PASSWORD")
    },
    "search_parameters": {
        "datasetId": "3SIMG_L1B_STD",
        "startTime": "2025-05-29",
        "endTime": "2025-05-29",
        "count": "10", 
        "boundingBox": "",
        "gId": ""
    },
    "download_settings": {
        "download_path": temp_dir,
        "organize_by_date": False,
        "skip_user_input": True,
        "generate_error_logs": False,
        "error_logs_dir": ""
    }
}

with open(os.path.join(temp_dir, "config.json"), "w") as f:
    json.dump(config, f)

wrapper_code = """
import sys
import json
import mdapi

TARGETS = ["3SIMG_29MAY2025_1200_L1B_STD_V01R00"]
orig_download_data = mdapi.download_data

def custom_download_data(access_token, record_id, identifier, prod_date, counter, total_files):
    if identifier in TARGETS:
        return orig_download_data(access_token, record_id, identifier, prod_date, counter, total_files)
    return "MOCK"

mdapi.download_data = custom_download_data
mdapi.skip_user_input = True
mdapi.logout = lambda: None

try:
    mdapi.main()
except SystemExit:
    pass
"""
with open(os.path.join(temp_dir, "wrapper.py"), "w") as f:
    f.write(wrapper_code)

res = subprocess.run(["python", "wrapper.py"], cwd=temp_dir, capture_output=True, text=True)
print("STDOUT:", res.stdout)
print("STDERR:", res.stderr)
print("Return code:", res.returncode)

ds_dir = os.path.join(temp_dir, "3SIMG_L1B_STD")
if os.path.exists(ds_dir):
    print("Files in ds_dir:", os.listdir(ds_dir))
else:
    print("ds_dir does not exist")
