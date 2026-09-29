import { useState, useEffect, Component } from 'react';
import type { ReactNode } from 'react';
import { Play, Pause, Square, AlertTriangle, ShieldAlert, Cpu, Activity, Zap, CloudRain } from 'lucide-react';
import SimulationMap from './SimulationMap';
import { getSimulationState } from './simulationEngine';

class SimulationErrorBoundary extends Component<{ children: ReactNode }, { hasError: boolean }> {
  constructor(props: { children: ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="w-full h-screen bg-slate-950 flex flex-col items-center justify-center text-slate-200">
           <AlertTriangle className="w-16 h-16 text-red-500 mb-4" />
           <h1 className="text-2xl font-black tracking-widest text-red-500 mb-2">STORMFUSION COMMAND CENTER</h1>
           <h2 className="text-lg font-bold tracking-widest text-slate-400 mb-8">SIMULATION ERROR</h2>
           <button onClick={() => window.location.reload()} className="px-6 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded text-xs font-bold tracking-widest uppercase transition-colors">
              [RESTART SCENARIO]
           </button>
        </div>
      );
    }
    return this.props.children;
  }
}

interface CommandCenterProps {
  onExit: () => void;
}

export function InternalCommandCenter({ onExit }: CommandCenterProps) {
  const [timeOffset, setTimeOffset] = useState(0); // 0 to 60
  const [isPlaying, setIsPlaying] = useState(false);
  const [selectedCellId, setSelectedCellId] = useState<string | null>(null);
  const [activeLayers, setActiveLayers] = useState<string[]>(['CELLS', 'THREAT_ZONE', 'TRACKS', 'LIGHTNING']);
  
  const [radarMode, setRadarMode] = useState<'REFLECTIVITY' | 'VELOCITY' | 'SPECTRUM_WIDTH'>('REFLECTIVITY');
  const [satelliteVisible, setSatelliteVisible] = useState(false);
  const [nwpVisible, setNwpVisible] = useState(false);
  const [demoStep, setDemoStep] = useState(0);
  
  const state = getSimulationState(timeOffset);
  const selectedCell = state.cells.find(c => c.id === selectedCellId);

  // Playback loop
  useEffect(() => {
    if (!isPlaying) return;
    const interval = setInterval(() => {
      setTimeOffset(prev => {
        if (prev >= 60) {
          setIsPlaying(false);
          return 60;
        }
        return prev + 1;
      });
    }, 150); // 150ms per minute of simulation
    return () => clearInterval(interval);
  }, [isPlaying]);

  const toggleLayer = (layer: string) => {
    setActiveLayers(prev => prev.includes(layer) ? prev.filter(l => l !== layer) : [...prev, layer]);
  };

  const startDemo = () => {
    setTimeOffset(0);
    setDemoStep(1);
    setSelectedCellId('SF-014');
    setIsPlaying(true);
  };

  return (
    <div className="w-full h-screen bg-slate-950 flex flex-col text-slate-200 font-sans overflow-hidden">
      {/* HEADER */}
      <header className="h-14 bg-slate-900 border-b border-slate-700 flex items-center justify-between px-6 z-10 shrink-0">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <Cpu className="text-cyan-500 w-5 h-5" />
            <h1 className="font-bold tracking-widest text-sm text-slate-100">STORMFUSION <span className="text-cyan-500">AI</span> COMMAND CENTER</h1>
          </div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 bg-amber-500/20 border border-amber-500/50 text-amber-400 rounded text-[10px] font-bold tracking-widest uppercase animate-pulse">
              SIMULATION MODE
            </span>
            <span className="px-2 py-0.5 bg-slate-800 border border-slate-600 text-slate-400 rounded text-[10px] font-bold tracking-widest uppercase">
              CONCEPT DEMONSTRATION
            </span>
            <span className="px-2 py-0.5 bg-red-900/40 border border-red-500/50 text-red-400 rounded text-[10px] font-bold tracking-widest uppercase">
              NOT A REAL FORECAST
            </span>
          </div>
        </div>
        <div className="flex items-center bg-slate-800/80 backdrop-blur-md rounded-xl p-1 border border-slate-600 shadow-sm">
           <button onClick={onExit} className="px-4 py-1.5 rounded-lg text-xs font-bold tracking-widest uppercase text-slate-400 hover:text-slate-200 transition-colors flex items-center gap-2">
              ○ REAL DATA
           </button>
           <div className="px-4 py-1.5 rounded-lg text-xs font-bold tracking-widest uppercase bg-slate-700 text-amber-500 shadow-sm border border-slate-600">
              ● SIMULATION
           </div>
        </div>
      </header>

      {/* MAIN CONTENT */}
      <div className="flex-1 relative flex">
        
        {/* MAP AREA */}
        <div className="flex-1 relative">
           <SimulationMap 
              state={state} 
              onCellSelect={setSelectedCellId} 
              activeLayers={activeLayers} 
              radarMode={radarMode}
              satelliteVisible={satelliteVisible}
              nwpVisible={nwpVisible}
           />

           {/* MAP OVERLAY: LEFT SIDE (General Stats) */}
           <div className="absolute top-4 left-4 z-10 w-64 space-y-4 pointer-events-none">
              <div className="bg-slate-900/80 backdrop-blur border border-slate-700 rounded-lg p-4 pointer-events-auto">
                 <h2 className="text-[10px] font-bold tracking-widest text-slate-400 mb-3 border-b border-slate-700 pb-2">SYSTEM OVERVIEW</h2>
                 <div className="grid grid-cols-2 gap-4">
                    <div>
                       <div className="text-2xl font-light text-slate-100">{state.cells.length}</div>
                       <div className="text-[9px] font-bold tracking-widest text-cyan-500">ACTIVE STORMS</div>
                    </div>
                    <div>
                       <div className="text-2xl font-light text-amber-400">1</div>
                       <div className="text-[9px] font-bold tracking-widest text-amber-500">INTENSIFYING</div>
                    </div>
                 </div>
              </div>
              
              <div className="bg-slate-900/80 backdrop-blur border border-slate-700 rounded-lg p-4 pointer-events-auto">
                 <h2 className="text-[10px] font-bold tracking-widest text-slate-400 mb-3 border-b border-slate-700 pb-2">SIMULATED NWP</h2>
                 <div className="space-y-2">
                    <div className="flex justify-between items-center">
                       <span className="text-[9px] font-mono text-slate-500">CAPE</span>
                       <span className="text-[10px] font-mono text-slate-300">{Math.round(state.nwpSummary.cape)} J/kg</span>
                    </div>
                    <div className="flex justify-between items-center">
                       <span className="text-[9px] font-mono text-slate-500">WIND SHEAR</span>
                       <span className="text-[10px] font-mono text-slate-300">{Math.round(state.nwpSummary.shear)} m/s</span>
                    </div>
                    <div className="flex justify-between items-center">
                       <span className="text-[9px] font-mono text-slate-500">REL HUMIDITY</span>
                       <span className="text-[10px] font-mono text-slate-300">{Math.round(state.nwpSummary.rh)}%</span>
                    </div>
                 </div>
              </div>

              <div className="bg-slate-900/80 backdrop-blur border border-slate-700 rounded-lg p-4 pointer-events-auto flex flex-col gap-4">
                 <div>
                    <h2 className="text-[10px] font-bold tracking-widest text-slate-400 mb-2">RADAR SIMULATION</h2>
                    <div className="flex bg-slate-800 rounded p-1">
                       <button onClick={() => setRadarMode('REFLECTIVITY')} className={`flex-1 text-[9px] font-bold py-1 rounded transition-colors ${radarMode === 'REFLECTIVITY' ? 'bg-cyan-600 text-white' : 'text-slate-400 hover:text-white'}`}>REFL</button>
                       <button onClick={() => setRadarMode('VELOCITY')} className={`flex-1 text-[9px] font-bold py-1 rounded transition-colors ${radarMode === 'VELOCITY' ? 'bg-cyan-600 text-white' : 'text-slate-400 hover:text-white'}`}>VEL</button>
                       <button onClick={() => setRadarMode('SPECTRUM_WIDTH')} className={`flex-1 text-[9px] font-bold py-1 rounded transition-colors ${radarMode === 'SPECTRUM_WIDTH' ? 'bg-cyan-600 text-white' : 'text-slate-400 hover:text-white'}`}>WIDTH</button>
                    </div>
                 </div>
                 
                 <div>
                    <h2 className="text-[10px] font-bold tracking-widest text-slate-400 mb-2">MULTIMODAL FUSION</h2>
                    <div className="space-y-2">
                       <label className="flex items-center gap-2 cursor-pointer">
                          <input type="checkbox" checked={satelliteVisible} onChange={(e) => setSatelliteVisible(e.target.checked)} className="rounded border-slate-600 bg-slate-800 text-cyan-500" />
                          <span className="text-[10px] font-bold tracking-widest text-slate-300 uppercase">SATELLITE (SIMULATED)</span>
                       </label>
                       <label className="flex items-center gap-2 cursor-pointer">
                          <input type="checkbox" checked={nwpVisible} onChange={(e) => setNwpVisible(e.target.checked)} className="rounded border-slate-600 bg-slate-800 text-cyan-500" />
                          <span className="text-[10px] font-bold tracking-widest text-slate-300 uppercase">NWP (SIMULATED)</span>
                       </label>
                    </div>
                 </div>
              </div>

              {demoStep === 0 && (
                <div className="bg-cyan-900/40 backdrop-blur border border-cyan-500/50 rounded-lg p-4 pointer-events-auto shadow-[0_0_15px_rgba(6,182,212,0.2)]">
                   <h2 className="text-[11px] font-bold tracking-widest text-cyan-400 mb-2">GUIDED SCENARIO</h2>
                   <p className="text-xs text-slate-300 mb-4 leading-relaxed">
                      Experience the complete StormFusion operational workflow using simulated deterministic data.
                   </p>
                   <button onClick={startDemo} className="w-full py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded text-[10px] font-bold tracking-widest transition-colors flex items-center justify-center gap-2">
                      <Play className="w-3 h-3" /> START SCENARIO
                   </button>
                </div>
              )}
           </div>

           {/* TIMELINE BOTTOM */}
           <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-10 w-2/3 bg-slate-900/90 backdrop-blur border border-slate-700 rounded-lg p-3 flex items-center gap-4">
              <button onClick={() => setIsPlaying(!isPlaying)} className="p-2 hover:bg-slate-800 rounded text-slate-300 hover:text-white transition-colors">
                 {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
              </button>
              <button onClick={() => { setIsPlaying(false); setTimeOffset(0); }} className="p-2 hover:bg-slate-800 rounded text-slate-300 hover:text-white transition-colors">
                 <Square className="w-4 h-4" />
              </button>
              
              <div className="flex-1 relative px-2">
                 <input 
                    type="range" 
                    min="0" 
                    max="60" 
                    value={timeOffset} 
                    onChange={(e) => { setTimeOffset(parseInt(e.target.value)); setIsPlaying(false); }}
                    className="w-full h-1 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-cyan-500"
                 />
                 <div className="flex justify-between mt-2 text-[9px] font-bold tracking-widest text-slate-500">
                    <button onClick={() => { setTimeOffset(0); setIsPlaying(false); }} className={`hover:text-cyan-400 ${timeOffset === 0 ? 'text-cyan-500' : ''}`}>NOW</button>
                    <button onClick={() => { setTimeOffset(15); setIsPlaying(false); }} className={`hover:text-cyan-400 ${timeOffset === 15 ? 'text-cyan-500' : ''}`}>+15m</button>
                    <button onClick={() => { setTimeOffset(30); setIsPlaying(false); }} className={`hover:text-cyan-400 ${timeOffset === 30 ? 'text-cyan-500' : ''}`}>+30m</button>
                    <button onClick={() => { setTimeOffset(45); setIsPlaying(false); }} className={`hover:text-cyan-400 ${timeOffset === 45 ? 'text-cyan-500' : ''}`}>+45m</button>
                    <button onClick={() => { setTimeOffset(60); setIsPlaying(false); }} className={`hover:text-cyan-400 ${timeOffset === 60 ? 'text-cyan-500' : ''}`}>+60m</button>
                 </div>
              </div>
           </div>

           {/* LAYER CONTROLS */}
           <div className="absolute bottom-4 right-4 z-10 bg-slate-900/90 backdrop-blur border border-slate-700 rounded-lg p-3 flex flex-col gap-2 pointer-events-auto">
              <h3 className="text-[9px] font-bold tracking-widest text-slate-500 uppercase mb-1">Simulated Layers</h3>
              {['CELLS', 'THREAT_ZONE', 'TRACKS', 'LIGHTNING'].map(layer => (
                 <label key={layer} className="flex items-center gap-2 cursor-pointer group">
                    <input type="checkbox" checked={activeLayers.includes(layer)} onChange={() => toggleLayer(layer)} className="w-3 h-3 rounded bg-slate-800 border-slate-600 text-cyan-500 focus:ring-cyan-500" />
                    <span className="text-[10px] font-mono text-slate-400 group-hover:text-slate-200 transition-colors">{layer.replace('_', ' ')}</span>
                 </label>
              ))}
           </div>
        </div>

        {/* GUIDED DEMO OVERLAY */}
        {isPlaying && (
           <div className="absolute bottom-24 left-1/2 -translate-x-1/2 z-50 bg-slate-900/95 backdrop-blur-xl border border-amber-500/30 rounded-2xl p-6 shadow-[0_20px_50px_rgba(0,_0,_0,_0.5)] w-[400px] flex flex-col items-center text-center">
              <div className="text-[10px] font-bold tracking-widest uppercase text-amber-500 mb-2 flex items-center gap-2">
                 <Play className="w-3 h-3 animate-pulse" />
                 SCENARIO PLAYBACK: T+{timeOffset} MIN
              </div>
              <h3 className="text-lg font-black tracking-widest text-slate-100 mb-2">
                 {timeOffset < 10 && "01 — OBSERVE"}
                 {timeOffset >= 10 && timeOffset < 20 && "02 — DETECT"}
                 {timeOffset >= 20 && timeOffset < 30 && "03 — EXPLAIN"}
                 {timeOffset >= 30 && timeOffset < 40 && "04 — PREDICT"}
                 {timeOffset >= 40 && timeOffset < 50 && "05 — THREAT ZONE"}
                 {timeOffset >= 50 && timeOffset < 55 && "06 — ALERT"}
                 {timeOffset >= 55 && timeOffset < 60 && "07 — MULTIMODAL AI"}
                 {timeOffset === 60 && "08 — SYSTEM COMPLETION"}
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                 {timeOffset < 10 && "Monitoring synoptic conditions and base atmospheric variables."}
                 {timeOffset >= 10 && timeOffset < 20 && "Identifying initial convective signatures and rapid cooling."}
                 {timeOffset >= 20 && timeOffset < 30 && "Multimodal indicators converging. High cloud-top cooling and strengthening reflectivity."}
                 {timeOffset >= 30 && timeOffset < 40 && "AI forecasting intensity growth and spatial path (+30m)."}
                 {timeOffset >= 40 && timeOffset < 50 && "Issuing geospatial impact polygon based on extrapolated convective core."}
                 {timeOffset >= 50 && timeOffset < 55 && "Disseminating emergency notification based on high confidence."}
                 {timeOffset >= 55 && timeOffset < 60 && "Full spatiotemporal fusion complete, awaiting human validation."}
                 {timeOffset === 60 && "Simulation complete. Evaluated all simulated metrics."}
              </p>
           </div>
        )}

        {/* RIGHT PANEL - SELECTED CELL DETAILS */}
        <div className="w-80 bg-slate-900 border-l border-slate-700 flex flex-col overflow-y-auto shrink-0 relative z-20">
           {selectedCell ? (
              <div className="p-5 flex flex-col gap-6">
                 <div>
                    <div className="flex items-center justify-between mb-1">
                       <h2 className="text-xl font-light text-slate-100">CELL {selectedCell.id}</h2>
                       <span className={`px-2 py-0.5 rounded text-[9px] font-bold tracking-widest ${selectedCell.lifecycleStage === 'INTENSIFYING' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30 animate-pulse' : 'bg-slate-800 text-slate-400 border border-slate-700'}`}>
                          {selectedCell.lifecycleStage}
                       </span>
                    </div>
                    <p className="text-[9px] font-mono text-slate-500">SIMULATED TRACKING ENGAGED</p>
                 </div>

                 <div className="grid grid-cols-2 gap-3">
                    <div className="bg-slate-800/50 rounded p-3 border border-slate-700/50">
                       <div className="text-[9px] font-bold tracking-widest text-slate-500 mb-1">INTENSITY</div>
                       <div className="text-lg font-light text-slate-200">{Math.round(selectedCell.intensity)}<span className="text-xs text-slate-500">/100</span></div>
                    </div>
                    <div className="bg-slate-800/50 rounded p-3 border border-slate-700/50">
                       <div className="text-[9px] font-bold tracking-widest text-slate-500 mb-1">MOTION</div>
                       <div className="text-sm font-mono text-slate-200">NE {selectedCell.motionSpeed} <span className="text-[9px] text-slate-500">km/h</span></div>
                    </div>
                 </div>

                 <details className="border border-slate-700 rounded-lg overflow-hidden group" open>
                    <summary className="bg-slate-800 px-3 py-2 border-b border-slate-700 flex items-center justify-between cursor-pointer hover:bg-slate-700/80 transition-colors">
                       <span className="text-[10px] font-bold tracking-widest text-slate-300 group-open:text-white">WHY IS THIS CELL FLAGGED?</span>
                       <div className="flex items-center gap-2">
                          <span className="text-[8px] px-1 bg-amber-500/20 text-amber-500 rounded border border-amber-500/30">SIMULATED</span>
                          <span className="text-slate-500 group-open:rotate-180 transition-transform">▼</span>
                       </div>
                    </summary>
                    <div className="p-3 space-y-3 bg-slate-900/50">
                       
                       <div className="space-y-1">
                          <div className="flex justify-between text-[10px] font-bold tracking-widest">
                             <span className="text-cyan-400 flex items-center gap-1"><CloudRain className="w-3 h-3"/> SATELLITE</span>
                             <span className="text-slate-400">{selectedCell.cloudTopTemp.toFixed(1)} °C</span>
                          </div>
                          <div className="h-1.5 w-full bg-slate-800 rounded overflow-hidden">
                             <div className="h-full bg-cyan-500" style={{ width: `${Math.min(100, Math.max(0, (-50 - selectedCell.cloudTopTemp) * 4))}%` }}></div>
                          </div>
                          <p className="text-[9px] text-slate-400 font-mono">Cloud-top cooling at {selectedCell.coolingRate.toFixed(1)} K/hr</p>
                       </div>

                       <div className="space-y-1">
                          <div className="flex justify-between text-[10px] font-bold tracking-widest">
                             <span className="text-emerald-400 flex items-center gap-1"><Activity className="w-3 h-3"/> RADAR</span>
                             <span className="text-slate-400">{Math.round(selectedCell.radarReflectivity)} dBZ</span>
                          </div>
                          <div className="h-1.5 w-full bg-slate-800 rounded overflow-hidden">
                             <div className="h-full bg-emerald-500" style={{ width: `${(selectedCell.radarReflectivity / 75) * 100}%` }}></div>
                          </div>
                          <p className="text-[9px] text-slate-400 font-mono">Strong convective core detected</p>
                       </div>

                       <div className="space-y-1">
                          <div className="flex justify-between text-[10px] font-bold tracking-widest">
                             <span className="text-amber-400 flex items-center gap-1"><Zap className="w-3 h-3"/> LIGHTNING</span>
                             <span className="text-slate-400">{selectedCell.lightningActivity}</span>
                          </div>
                          <div className="h-1.5 w-full bg-slate-800 rounded overflow-hidden">
                             <div className="h-full bg-amber-500" style={{ width: `${selectedCell.lightningFlashRate * 2}%` }}></div>
                          </div>
                          <p className="text-[9px] text-slate-400 font-mono">Flash rate: {selectedCell.lightningFlashRate} / 5min</p>
                       </div>

                       <div className="space-y-1">
                          <div className="flex justify-between text-[10px] font-bold tracking-widest">
                             <span className="text-blue-400 flex items-center gap-1"><CloudRain className="w-3 h-3"/> NWP</span>
                             <span className="text-slate-400">{Math.round(selectedCell.cape)} J/kg</span>
                          </div>
                          <div className="h-1.5 w-full bg-slate-800 rounded overflow-hidden">
                             <div className="h-full bg-blue-500" style={{ width: `${Math.min(100, selectedCell.cape / 30)}%` }}></div>
                          </div>
                          <p className="text-[9px] text-slate-400 font-mono">High CAPE environment</p>
                       </div>

                    </div>
                    <div className="bg-slate-800/80 px-3 py-2 flex items-center justify-between border-t border-slate-700">
                       <span className="text-[10px] font-bold tracking-widest text-slate-400">MULTIMODAL EVIDENCE</span>
                       <span className={`text-[10px] font-bold tracking-widest ${selectedCell.intensity > 70 ? 'text-red-400' : 'text-amber-400'}`}>
                          {selectedCell.intensity > 70 ? 'HIGH' : 'ELEVATED'}
                       </span>
                    </div>
                  </details>

                 {/* STORMFUSION ALERT CENTER */}
                 {selectedCell.intensity > 80 && (
                    <div className="fixed bottom-16 right-16 z-50 animate-bounce">
                       <div className="border-2 border-red-500 bg-red-950/95 backdrop-blur-xl rounded-xl overflow-hidden shadow-[0_0_50px_rgba(239,68,68,0.6)] w-[420px]">
                          <div className="bg-red-600 px-4 py-3 flex items-center gap-3 border-b border-red-500">
                             <ShieldAlert className="w-6 h-6 text-white animate-pulse" />
                             <span className="text-sm font-black tracking-widest text-white uppercase">STORMFUSION ALERT CENTER</span>
                          </div>
                          <div className="p-5">
                             <div className="text-sm font-black text-red-400 tracking-widest mb-3 border-b border-red-500/30 pb-2 flex justify-between">
                                <span>SIMULATED HIGH SEVERITY</span>
                                <span className="text-white">CELL {selectedCell.id}</span>
                             </div>
                             <p className="text-xs leading-relaxed text-red-200 font-mono mb-4">
                                Illustrative convective-development alert generated from simulated multimodal inputs. Projected to impact coastal regions in +30 MIN.
                             </p>
                             <div className="flex gap-2">
                                <div className="bg-red-900/50 px-2 py-1 rounded border border-red-500/30 text-[10px] font-bold text-red-300">INT: {Math.round(selectedCell.intensity)}</div>
                                <div className="bg-red-900/50 px-2 py-1 rounded border border-red-500/30 text-[10px] font-bold text-red-300">DIR: NE {selectedCell.motionSpeed}km/h</div>
                             </div>
                          </div>
                       </div>
                    </div>
                 )}

              </div>
           ) : (
              <div className="p-6 flex flex-col items-center justify-center h-full text-center opacity-50">
                 <AlertTriangle className="w-8 h-8 text-slate-500 mb-4" />
                 <p className="text-xs font-bold tracking-widest text-slate-400">NO CELL SELECTED</p>
                 <p className="text-[10px] text-slate-500 mt-2">Click a simulated storm cell on the map to view detailed operational metrics.</p>
              </div>
           )}
        </div>
      </div>
      
      {/* FOOTER */}
      <footer className="h-8 bg-slate-900 border-t border-slate-700 flex items-center px-4 justify-between shrink-0 text-[9px] font-mono text-slate-500 uppercase tracking-widest">
         <div>REAL OBSERVATIONS: <span className="text-slate-600">NOT USED</span></div>
         <div>AI OUTPUT: <span className="text-amber-600/70">SIMULATED</span></div>
         <div>FORECAST: <span className="text-slate-600">ILLUSTRATIVE</span></div>
      </footer>
    </div>
  );
}

export default function CommandCenter(props: CommandCenterProps) {
  return (
    <SimulationErrorBoundary>
      <InternalCommandCenter {...props} />
    </SimulationErrorBoundary>
  );
}
