import re

with open('frontend/src/App.tsx', 'r', encoding='utf-8') as f:
    text = f.read()

text = re.sub(r'\btext-slate-100\b', 'text-slate-900', text)
text = re.sub(r'\btext-indigo-300\b', 'text-indigo-700', text)
text = re.sub(r'\btext-emerald-300\b', 'text-emerald-700', text)
text = re.sub(r'\btext-red-300/80\b', 'text-red-800', text)
text = re.sub(r'\bbg-indigo-900/50\b', 'bg-indigo-100', text) # Multimodal fusion block in system view

with open('frontend/src/App.tsx', 'w', encoding='utf-8') as f:
    f.write(text)

print("Fixed lingering dark colors.")
