import requests
import sys

def get_all_items(url, indent):
    while url:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            items = data.get('data', [])
            for item in items:
                attrs = item.get('attributes', {})
                print(f"{indent}Name: {attrs.get('name')} | Kind: {attrs.get('kind')} | Size: {attrs.get('size')}")
                if attrs.get('kind') == 'folder':
                    get_all_items(item['relationships']['files']['links']['related']['href'], indent + "  ")
            url = data.get('links', {}).get('next')
        else:
            print(f"Error accessing OSF API: {response.status_code} at {url}")
            break

if __name__ == "__main__":
    print("Exploring OSF Project h8tw5 directly...")
    sys.stdout.flush()
    get_all_items("https://api.osf.io/v2/nodes/h8tw5/files/osfstorage/", "")
