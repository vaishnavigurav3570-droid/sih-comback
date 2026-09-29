import re

def to_light_theme(text):
    # Backgrounds
    text = re.sub(r'\bbg-slate-950\b', 'bg-slate-50', text)
    text = re.sub(r'\bbg-slate-900\b', 'bg-white', text)
    text = re.sub(r'\bbg-slate-800\b', 'bg-slate-200', text)
    text = re.sub(r'\bbg-black\b', 'bg-white', text)
    text = re.sub(r'\bhover:bg-slate-800\b', 'hover:bg-slate-200', text)
    text = re.sub(r'\bhover:bg-slate-900\b', 'hover:bg-slate-100', text)
    
    # Text colors
    text = re.sub(r'\btext-white\b', 'text-slate-900', text)
    text = re.sub(r'\btext-slate-300\b', 'text-slate-700', text)
    text = re.sub(r'\btext-slate-400\b', 'text-slate-600', text)
    text = re.sub(r'\btext-slate-500\b', 'text-slate-500', text)
    text = re.sub(r'\bhover:text-white\b', 'hover:text-slate-900', text)
    
    # Borders
    text = re.sub(r'\bborder-slate-800\b', 'border-slate-300', text)
    text = re.sub(r'\bborder-slate-700\b', 'border-slate-300', text)
    text = re.sub(r'\bborder-slate-600\b', 'border-slate-400', text)
    text = re.sub(r'\bhover:border-slate-600\b', 'hover:border-slate-400', text)
    
    # Specific component tweaks
    text = re.sub(r'\bbg-slate-950/80\b', 'bg-white/80', text)
    text = re.sub(r'\bbg-slate-950/90\b', 'bg-white/90', text)
    text = re.sub(r'\bbg-slate-950/50\b', 'bg-white/50', text)
    
    # Shadow and overlays (some shadows look bad on light if they were text shadows)
    text = re.sub(r'drop-shadow-md', '', text) 
    
    return text

with open('frontend/src/App.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

content = to_light_theme(content)

with open('frontend/src/App.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("Theme updated to light mode.")
