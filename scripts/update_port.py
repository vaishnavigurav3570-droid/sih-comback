import re
with open('frontend/src/App.tsx', 'r', encoding='utf-8') as f:
    text = f.read()
text = re.sub(r'http://localhost:8000', 'http://localhost:8001', text)
with open('frontend/src/App.tsx', 'w', encoding='utf-8') as f:
    f.write(text)
print("Port updated to 8001.")
