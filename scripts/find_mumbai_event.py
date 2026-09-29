import requests

def get_all_items(url):
    items = []
    while url:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            items.extend(data.get('data', []))
            url = data.get('links', {}).get('next')
        else:
            print(f"Error accessing OSF API: {response.status_code} at {url}")
            break
    return items

def main():
    root_url = "https://api.osf.io/v2/nodes/h8tw5/files/osfstorage/"
    root_items = get_all_items(root_url)
    
    radar_url = None
    lightning_url = None
    
    for item in root_items:
        name = item.get('attributes', {}).get('name')
        if name == 'Radar_raw_data':
            radar_url = item['relationships']['files']['links']['related']['href']
        elif name == 'Lightning data':
            lightning_url = item['relationships']['files']['links']['related']['href']
            
    print("----- RADAR (Mumbai) -----")
    if radar_url:
        radar_items = get_all_items(radar_url)
        mumbai_files = sorted([i.get('attributes', {}).get('name') for i in radar_items if 'MUM' in i.get('attributes', {}).get('name', '')])
        for f in mumbai_files:
            print(f)
            
    print("\n----- LIGHTNING -----")
    if lightning_url:
        lightning_items = get_all_items(lightning_url)
        light_files = sorted([i.get('attributes', {}).get('name') for i in lightning_items])
        for f in light_files:
            print(f)

if __name__ == "__main__":
    main()
