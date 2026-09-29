import re

with open('frontend/src/App.tsx', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix dark top gradient
text = re.sub(r'from-slate-950/90', 'from-white/95', text)

# Fix timeline active text
text = re.sub(r'text-indigo-400 font-bold', 'text-indigo-700 font-black', text)

# Make demo floating boxes light mode but distinct
text = re.sub(r'bg-indigo-950/90', 'bg-white/95', text)
text = re.sub(r'border border-indigo-500/50', 'border border-indigo-200', text)
text = re.sub(r'text-indigo-400 mb-2', 'text-indigo-700 mb-2', text)
text = re.sub(r'text-indigo-300 mb-2', 'text-indigo-700 mb-2', text)
text = re.sub(r'text-slate-300 leading-relaxed', 'text-slate-600 leading-relaxed', text)
text = re.sub(r'text-slate-400 leading-relaxed', 'text-slate-600 leading-relaxed', text)

# Add heavy drop shadows to floating panels to make them pop (professional glassmorphism)
text = re.sub(r'shadow-2xl', 'shadow-[0_20px_50px_rgba(8,_112,_184,_0.07)]', text)

with open('frontend/src/App.tsx', 'w', encoding='utf-8') as f:
    f.write(text)

print("UI Polish complete.")
