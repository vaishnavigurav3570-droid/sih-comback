const fs = require('fs');
let content = fs.readFileSync('frontend/src/CommandCenter/CommandCenter.tsx', 'utf8');
const search = '<details className="border border-slate-700 rounded-lg overflow-hidden group" open>';
const replacement = `                 <div className="mt-4 mb-2">
                    <button onClick={() => {
                       setIsPlaying(true);
                       setSelectedCellId('SF-014');
                       setActiveLayers(['CELLS', 'THREAT_ZONE', 'TRACKS', 'LIGHTNING']);
                    }} className="w-full py-3 bg-cyan-600 hover:bg-cyan-500 text-white rounded shadow-[0_0_15px_rgba(6,182,212,0.4)] text-[11px] font-black tracking-widest transition-all flex items-center justify-center gap-2 animate-pulse">
                       <Play className="w-4 h-4 fill-current" /> RUN TRACK FORECAST
                    </button>
                 </div>

                 <details className="border border-slate-700 rounded-lg overflow-hidden group" open>`;
content = content.replace(search, replacement);
fs.writeFileSync('frontend/src/CommandCenter/CommandCenter.tsx', content);
console.log('done run button');
