const fs = require('fs');
let content = fs.readFileSync('frontend/src/CommandCenter/CommandCenter.tsx', 'utf8');
const search = '{/* RIGHT PANEL - SELECTED CELL DETAILS */}';
const replacement = `{/* LEGEND overlay on map */}
         <div className="absolute top-4 left-4 z-10 bg-slate-900/90 backdrop-blur border border-slate-700 rounded-lg p-3 pointer-events-auto flex flex-col gap-2 shadow-[0_0_15px_rgba(0,0,0,0.5)]">
            <div className="text-[9px] font-bold tracking-widest text-slate-500 uppercase border-b border-slate-700 pb-1 mb-1">SIMULATION MAP LEGEND</div>
            <div className="flex items-center gap-2 text-[10px] text-slate-300 font-mono"><div className="w-2 h-2 rounded-full bg-amber-500 border border-white"></div> OBSERVED STORM</div>
            <div className="flex items-center gap-2 text-[10px] text-slate-300 font-mono"><div className="w-4 h-0.5 bg-amber-400"></div> PROJECTED TRACK</div>
            <div className="flex items-center gap-2 text-[10px] text-slate-300 font-mono"><div className="w-2 h-2 rounded-full border border-amber-400"></div> PROJECTED POSITION</div>
            <div className="flex items-center gap-2 text-[10px] text-slate-300 font-mono"><div className="w-3 h-3 bg-red-500/20 border border-red-500 border-dashed"></div> THREAT ZONE</div>
            <div className="flex items-center gap-2 text-[10px] text-slate-300 font-mono"><div className="w-1.5 h-1.5 rounded-full bg-yellow-400"></div> SIMULATED LIGHTNING</div>
         </div>

         {/* RIGHT PANEL - SELECTED CELL DETAILS */}`;
content = content.replace(search, replacement);
fs.writeFileSync('frontend/src/CommandCenter/CommandCenter.tsx', content);
console.log('done');
