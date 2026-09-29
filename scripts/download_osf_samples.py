import requests
import json
import urllib.request
import os

def download_partial(url, filepath, size=1024):
    headers = {"Range": f"bytes=0-{size}"}
    r = requests.get(url, headers=headers)
    with open(filepath, 'wb') as f:
        f.write(r.content)

def main():
    root_url = "https://api.osf.io/v2/nodes/h8tw5/files/osfstorage/"
    
    # We will just fetch the API manually to get the exact download URLs for:
    # 1. may23.csv
    # 2. polar_MUM190720194254.nc
    # 3. polar_KKL200517202223.nc (Wait, KKL 200517 is May 2020. No overlap with May 2023)
    
    # Let's get download URLs
    # Since we know the API structure from before, we can search the nodes.
    
    # For now, let's just write a script that iterates and finds the download links.
    url = "https://api.osf.io/v2/nodes/h8tw5/files/osfstorage/"
    found_may23 = None
    found_mum = None
    
    while url and (not found_may23 or not found_mum):
        r = requests.get(url)
        data = r.json()
        
        # files might be inside folders. Let's do a quick BFS.
        q = [url]
        while q and (not found_may23 or not found_mum):
            curr = q.pop(0)
            res = requests.get(curr).json()
            for item in res.get('data', []):
                name = item.get('attributes', {}).get('name')
                kind = item.get('attributes', {}).get('kind')
                if kind == 'file':
                    if name == 'may23.csv':
                        found_may23 = item['links']['download']
                    elif name == 'polar_MUM190720194254.nc':
                        found_mum = item['links']['download']
                elif kind == 'folder':
                    q.append(item['relationships']['files']['links']['related']['href'])
        
        break
        
    print(f"may23.csv URL: {found_may23}")
    print(f"polar_MUM190720194254.nc URL: {found_mum}")
    
    if found_may23:
        download_partial(found_may23, "may23_sample.csv", size=2048)
        print("--- may23.csv Sample ---")
        with open("may23_sample.csv", "r", encoding="utf-8", errors="ignore") as f:
            print(f.read())
            
if __name__ == "__main__":
    main()
