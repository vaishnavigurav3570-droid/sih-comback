import { useState, useEffect, useRef, useMemo } from 'react';
import { Activity, CloudLightning, Radio, Map as MapIcon, Database, CheckCircle2, AlertTriangle, Play, Square, ChevronRight, ChevronLeft, FastForward, Info, SkipBack, SkipForward } from 'lucide-react';
import MapComponent, { type MapRef } from './MapComponent';

type ViewMode = 'LANDING' | 'SATELLITE' | 'RADAR' | 'SYSTEM';

export default function App() {
  const [activeView, setActiveView] = useState<ViewMode>('LANDING');
  
  // Demo state
  const [isDemoActive, setIsDemoActive] = useState(false);
  const [demoStep, setDemoStep] = useState(1); // 1: Playback, 2: Extrapolation, 3: Radar, 4: AI Fit
  
  // Data state
  const [timeline, setTimeline] = useState<string[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [nowcastData, setNowcastData] = useState<any>(null);
  const [radarMeta, setRadarMeta] = useState<any>(null);
  const [radarData, setRadarData] = useState<any>(null);
  
  // Satellite Controls
  const [satLayer, setSatLayer] = useState<string>('storm_development_indicator');
  const [isPlaying, setIsPlaying] = useState(false);
  const [loading, setLoading] = useState(false);
  
  // Radar Controls
  const [radarLayer, setRadarLayer] = useState<string>('REF');

  const mapRef = useRef<MapRef>(null);

  // Fetch initial metadata
  useEffect(() => {
    fetch('http://localhost:8000/api/v1/dashboard/nowcast/timeline')
      .then(r => r.json())
      .then(data => {
        if (Array.isArray(data)) {
          setTimeline(data);
          if (data.length > 0) setCurrentIndex(data.length - 1);
        }
      }).catch(e => console.error(e));

    fetch('http://localhost:8000/api/v1/dashboard/radar/metadata')
      .then(r => r.json())
      .then(data => setRadarMeta(data)).catch(e => console.error(e));
      
    fetch('http://localhost:8000/api/v1/dashboard/radar/latest')
      .then(r => r.json())
      .then(data => setRadarData(data)).catch(e => console.error(e));
  }, []);

  // Fetch nowcast frame
  useEffect(() => {
    if (timeline.length > 0 && timeline[currentIndex]) {
      setLoading(true);
      fetch(`http://localhost:8000/api/v1/dashboard/nowcast/${timeline[currentIndex]}`)
        .then(r => r.json())
        .then(data => {
          setNowcastData(data);
          setLoading(false);
        }).catch(e => {
          console.error(e);
          setLoading(false);
        });
    }
  }, [currentIndex, timeline]);

  // Timeline playback
  useEffect(() => {
    let interval: any;
    if (isPlaying) {
      interval = setInterval(() => {
        setCurrentIndex(prev => {
          if (prev >= timeline.length - 1) {
            setIsPlaying(false); // Auto-pause at end
            
            // Auto-advance demo to step 2 if we are in step 1
            if (isDemoActive && demoStep === 1) {
                setTimeout(() => advanceDemo(2), 1000);
            }
            
            return prev;
          }
          return prev + 1;
        });
      }, 1500); // 1.5s per frame
    }
    return () => clearInterval(interval);
  }, [isPlaying, timeline.length, isDemoActive, demoStep]);

  // Demo orchestration
  const startDemo = () => {
    setActiveView('SATELLITE');
    setIsDemoActive(true);
    setDemoStep(1);
    setSatLayer('storm_development_indicator');
    setCurrentIndex(0);
    setTimeout(() => {
      mapRef.current?.flyToIndia();
      setIsPlaying(true);
    }, 500);
  };

  const advanceDemo = (step: number) => {
    setDemoStep(step);
    if (step === 2) {
      setActiveView('SATELLITE');
      setSatLayer('extrapolated_indicator');
      setCurrentIndex(timeline.length - 1);
      setIsPlaying(false);
      mapRef.current?.flyToIndia();
    } else if (step === 3) {
      setActiveView('RADAR');
      setRadarLayer('REF');
      setIsPlaying(false);
      mapRef.current?.flyToMumbai();
    } else if (step === 4) {
      setActiveView('SYSTEM');
      setIsPlaying(false);
    }
  };

  const stopDemo = () => {
    setIsDemoActive(false);
    setIsPlaying(false);
  };

  // Nav Handlers
  const navTo = (view: ViewMode) => {
    stopDemo();
    setActiveView(view);
    if (view === 'SATELLITE') {
      mapRef.current?.flyToIndia();
    } else if (view === 'RADAR') {
      mapRef.current?.flyToMumbai();
    }
  };
  
  // Calculate scene metrics
  const sceneMetrics = useMemo(() => {
    if (!nowcastData || !nowcastData.variables) return null;
    
    const getSceneAvg = (varName: string) => {
      const grid = nowcastData.variables[varName];
      if (!grid) return null;
      let sum = 0, count = 0;
      for (let r=0; r<grid.length; r++) {
         for (let c=0; c<grid[0].length; c++) {
            if (grid[r][c] !== null) {
               sum += grid[r][c];
               count++;
            }
         }
      }
      return count > 0 ? (sum / count).toFixed(3) : 'N/A';
    };
    
    return {
      ctp: getSceneAvg('ctp_component'),
      cooling: getSceneAvg('cooling_rate_component'),
      tir: getSceneAvg('split_window_component'),
      grad: getSceneAvg('gradient_component'),
      coverage: nowcastData.metrics?.coverage_percent?.toFixed(1) || 'N/A',
      qc: nowcastData.metrics?.qc_flags || 'UNKNOWN'
    };
  }, [nowcastData]);


  return (
    <div className="relative w-screen h-screen overflow-hidden bg-slate-950 text-slate-100 font-sans selection:bg-indigo-500/30 flex flex-col">
      {/* MAP BACKGROUND (Always behind everything) */}
      <div className="absolute inset-0 z-0">
         <MapComponent ref={mapRef} nowcastData={nowcastData} radarData={radarData} activeLayer={activeView === 'SATELLITE' ? satLayer : radarLayer} mode={activeView === 'RADAR' ? 'radar' : 'nowcast'} />
      </div>

      {/* TOP NAVIGATION BAR */}
      <div className="z-20 absolute top-0 left-0 right-0 bg-gradient-to-b from-slate-950/90 to-transparent p-4 flex justify-between items-start pointer-events-none">
        
        <div className="pointer-events-auto flex items-center gap-6">
           <div className="flex items-center gap-3 bg-slate-950/80 backdrop-blur-md px-4 py-2 rounded-xl border border-slate-800">
              <CloudLightning size={24} className="text-indigo-400" />
              <div className="flex flex-col">
                <span className="text-sm font-black tracking-widest leading-none text-white">STORMFUSION AI</span>
                <span className="text-[9px] font-bold tracking-widest text-indigo-400 mt-1 uppercase">Command Center</span>
              </div>
           </div>

           {activeView !== 'LANDING' && (
              <div className="flex items-center gap-1 bg-slate-950/80 backdrop-blur-md p-1 rounded-xl border border-slate-800 shadow-xl">
                 <button onClick={startDemo} className="px-4 py-1.5 rounded-lg text-xs font-bold tracking-widest uppercase transition-colors bg-indigo-600 hover:bg-indigo-500 text-white flex items-center gap-2">
                    <Play size={14} fill="currentColor"/> DEMO
                 </button>
                 <div className="w-px h-6 bg-slate-800 mx-1"></div>
                 <button onClick={() => navTo('SATELLITE')} className={`px-4 py-1.5 rounded-lg text-xs font-bold tracking-widest uppercase transition-colors ${activeView === 'SATELLITE' && !isDemoActive ? 'bg-slate-800 text-white' : 'text-slate-400 hover:text-white hover:bg-slate-900'}`}>SATELLITE</button>
                 <button onClick={() => navTo('RADAR')} className={`px-4 py-1.5 rounded-lg text-xs font-bold tracking-widest uppercase transition-colors ${activeView === 'RADAR' && !isDemoActive ? 'bg-slate-800 text-white' : 'text-slate-400 hover:text-white hover:bg-slate-900'}`}>RADAR</button>
                 <button onClick={() => navTo('SYSTEM')} className={`px-4 py-1.5 rounded-lg text-xs font-bold tracking-widest uppercase transition-colors ${activeView === 'SYSTEM' && !isDemoActive ? 'bg-slate-800 text-white' : 'text-slate-400 hover:text-white hover:bg-slate-900'}`}>SYSTEM</button>
              </div>
           )}
        </div>

        {/* Top Right Status */}
        <div className="pointer-events-auto flex gap-3">
           {loading && (
             <div className="bg-indigo-500/20 text-indigo-300 border border-indigo-500/50 px-3 py-1.5 rounded-lg text-[10px] font-bold tracking-widest uppercase flex items-center gap-2 animate-pulse backdrop-blur-md">
                <Activity size={12} /> LOADING DATA...
             </div>
           )}
           <div className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-3 py-1.5 rounded-lg text-[10px] font-bold tracking-widest uppercase backdrop-blur-md">
              REAL-DATA PROTOTYPE
           </div>
        </div>
      </div>


      {/* LANDING VIEW */}
      {activeView === 'LANDING' && (
         <div className="absolute inset-0 z-10 flex flex-col items-center justify-center bg-slate-950/90 backdrop-blur-sm pointer-events-auto">
            <CloudLightning size={64} className="text-indigo-500 mb-6" />
            <h1 className="text-5xl font-black tracking-tighter text-white mb-2">STORMFUSION AI</h1>
            <h2 className="text-xl font-bold tracking-[0.2em] text-indigo-400 mb-6 uppercase">Multimodal Atmospheric Intelligence</h2>
            
            <div className="bg-amber-500/10 border border-amber-500/30 text-amber-500 font-bold tracking-widest uppercase text-xs px-4 py-1.5 rounded-full mb-8">
               REAL-DATA PROTOTYPE
            </div>

            <p className="text-sm font-mono text-slate-400 max-w-2xl text-center mb-12 leading-relaxed">
               REAL ATMOSPHERIC DATA <span className="text-indigo-500 mx-2">+</span> 
               SPATIOTEMPORAL ANALYSIS <span className="text-indigo-500 mx-2">+</span> 
               NOWCASTING WORKFLOW
            </p>

            <button onClick={startDemo} className="group bg-indigo-600 hover:bg-indigo-500 text-white px-8 py-4 rounded-xl text-lg font-black tracking-widest uppercase flex items-center gap-3 transition-all hover:scale-105 shadow-[0_0_40px_rgba(79,70,229,0.3)] mb-8">
               <Play size={24} fill="currentColor" className="group-hover:translate-x-1 transition-transform" />
               START DEMO
            </button>

            <div className="flex gap-4">
               <button onClick={() => navTo('SATELLITE')} className="px-6 py-2 bg-slate-900 border border-slate-800 hover:border-slate-600 rounded-lg text-xs font-bold tracking-widest uppercase text-slate-300 transition-colors">EXPLORE SATELLITE</button>
               <button onClick={() => navTo('RADAR')} className="px-6 py-2 bg-slate-900 border border-slate-800 hover:border-slate-600 rounded-lg text-xs font-bold tracking-widest uppercase text-slate-300 transition-colors">VIEW RADAR</button>
               <button onClick={() => navTo('SYSTEM')} className="px-6 py-2 bg-slate-900 border border-slate-800 hover:border-slate-600 rounded-lg text-xs font-bold tracking-widest uppercase text-slate-300 transition-colors">SYSTEM ARCHITECTURE</button>
            </div>
         </div>
      )}


      {/* SATELLITE VIEW */}
      {activeView === 'SATELLITE' && (
         <>
            {/* Header / Timestamp Overlay (Top Left below nav) */}
            <div className="absolute top-24 left-4 z-10 pointer-events-none">
               <div className="text-3xl font-black text-white drop-shadow-md">SATELLITE NOWCAST CONSOLE</div>
               <div className="text-sm font-bold tracking-widest text-indigo-400 uppercase drop-shadow-md flex items-center gap-2 mt-1">
                  REAL INSAT-3DS OBSERVATION <span className="text-slate-400">•</span> 29 MAY 2025 <span className="text-slate-400">•</span> MOSDAC
               </div>
               
               {satLayer === 'extrapolated_indicator' && (
                  <div className="mt-4 bg-amber-500/90 text-black px-4 py-2 rounded-lg font-black tracking-widest uppercase inline-block shadow-lg border border-amber-400 pointer-events-auto animate-pulse">
                     <AlertTriangle size={16} className="inline mr-2 mb-1" />
                     EXTRAPOLATED • NOT VALIDATED FORECAST
                     <div className="text-[9px] font-bold text-amber-900/80 mt-1">DETERMINISTIC PROTOTYPE • NOT A CALIBRATED PROBABILITY</div>
                  </div>
               )}
            </div>

            {/* Right Analysis Panel */}
            <div className="absolute top-24 right-4 z-10 w-80 flex flex-col gap-4 pointer-events-auto">
               <div className="bg-slate-950/80 backdrop-blur-md border border-slate-800 rounded-xl p-5 shadow-2xl">
                  <div className="text-[10px] font-bold tracking-widest uppercase text-slate-500 mb-1">CURRENT OBSERVATION</div>
                  <div className="text-2xl font-mono text-white mb-6 border-b border-slate-800 pb-4">
                     {typeof timeline[currentIndex] === 'string' ? timeline[currentIndex].substring(11, 16) : 'N/A'} UTC
                  </div>

                  <div className="space-y-4">
                     <div className="flex justify-between items-end border-b border-slate-800/50 pb-2">
                        <div className="text-[10px] font-bold tracking-widest uppercase text-slate-400">CTT COMPONENT<br/><span className="text-[8px] text-slate-600">Scene average intensity</span></div>
                        <div className="text-right">
                           <span className="text-lg font-mono text-indigo-300">{sceneMetrics?.ctp}</span>
                        </div>
                     </div>
                     <div className="flex justify-between items-end border-b border-slate-800/50 pb-2">
                        <div className="text-[10px] font-bold tracking-widest uppercase text-slate-400">COOLING RATE<br/><span className="text-[8px] text-slate-600">Scene average intensity</span></div>
                        <div className="text-right">
                           <span className="text-lg font-mono text-indigo-300">{sceneMetrics?.cooling}</span>
                        </div>
                     </div>
                     <div className="flex justify-between items-end border-b border-slate-800/50 pb-2">
                        <div className="text-[10px] font-bold tracking-widest uppercase text-slate-400">DATA COVERAGE</div>
                        <div className="text-right">
                           <span className="text-lg font-mono text-emerald-400">{sceneMetrics?.coverage}</span>
                           <span className="text-[10px] text-slate-500 ml-1">%</span>
                        </div>
                     </div>
                     <div className="flex justify-between items-end pb-2">
                        <div className="text-[10px] font-bold tracking-widest uppercase text-slate-400">QC</div>
                        <div className="text-right">
                           <span className="text-xs font-bold tracking-widest uppercase text-emerald-400 bg-emerald-500/10 px-2 py-1 rounded">{sceneMetrics?.qc}</span>
                        </div>
                     </div>
                  </div>
                  
                  <div className="mt-6 pt-4 border-t border-slate-800">
                     <div className="text-[9px] font-bold tracking-widest uppercase text-slate-500 text-center">SOURCE: INSAT-3DS / MOSDAC</div>
                  </div>
               </div>

               {/* Indicator Explanation */}
               <div className="bg-slate-950/80 backdrop-blur-md border border-indigo-500/30 rounded-xl p-4 shadow-2xl">
                  <div className="text-[10px] font-bold tracking-widest uppercase text-indigo-400 mb-1">STORM-DEVELOPMENT INDICATOR</div>
                  <div className="text-[9px] font-bold tracking-widest uppercase text-slate-400 mb-2">DETERMINISTIC SATELLITE-DERIVED PROTOTYPE</div>
                  <div className="h-1.5 w-full bg-gradient-to-r from-blue-500 via-amber-500 to-red-500 rounded-full mt-3"></div>
                  <div className="flex justify-between text-[8px] font-bold tracking-widest text-slate-500 mt-1 uppercase">
                     <span>Low Intensity</span>
                     <span>High Intensity</span>
                  </div>
               </div>
            </div>

            {/* Bottom Controls (Timeline + Layers) */}
            <div className="absolute bottom-6 left-6 right-[22rem] z-10 pointer-events-auto flex flex-col gap-4">
               {/* Layer Control Panel */}
               <div className="bg-slate-950/90 backdrop-blur-md border border-slate-800 p-4 rounded-xl shadow-2xl flex flex-wrap gap-2">
                  <div className="w-full text-[10px] font-bold tracking-widest uppercase text-slate-500 mb-1">Visualization Layers</div>
                  {[
                     {id: 'ctp_component', label: 'CTT Component'},
                     {id: 'cooling_rate_component', label: 'Cooling Rate'},
                     {id: 'split_window_component', label: 'TIR1 - TIR2'},
                     {id: 'storm_development_indicator', label: 'STORM-DEVELOPMENT INDICATOR'},
                     {id: 'extrapolated_indicator', label: '30-MIN EXTRAPOLATION'}
                  ].map(layer => (
                     <button
                        key={layer.id}
                        onClick={() => setSatLayer(layer.id)}
                        className={`px-3 py-1.5 rounded border text-[10px] font-bold tracking-widest uppercase transition-colors ${
                           satLayer === layer.id
                           ? 'bg-indigo-600 border-indigo-500 text-white shadow-[0_0_10px_rgba(79,70,229,0.5)]'
                           : 'bg-slate-900 border-slate-700 text-slate-400 hover:bg-slate-800'
                        }`}
                     >
                        {satLayer === layer.id ? '☑' : '☐'} {layer.label}
                     </button>
                  ))}
               </div>

               {/* Timeline Console */}
               <div className="bg-slate-950/90 backdrop-blur-md border border-slate-800 p-4 rounded-xl shadow-2xl flex items-center gap-6">
                  
                  {/* Playback Controls */}
                  <div className="flex items-center gap-2 border-r border-slate-800 pr-6">
                     <button onClick={() => setCurrentIndex(Math.max(0, currentIndex - 1))} className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded">
                        <SkipBack size={16} />
                     </button>
                     <button onClick={() => setIsPlaying(!isPlaying)} className="p-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-full shadow-lg">
                        {isPlaying ? <Square size={16} fill="currentColor" /> : <Play size={16} fill="currentColor" className="ml-0.5" />}
                     </button>
                     <button onClick={() => setCurrentIndex(Math.min(timeline.length - 1, currentIndex + 1))} className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded">
                        <SkipForward size={16} />
                     </button>
                  </div>

                  {/* Frame Status */}
                  <div className="text-[10px] font-mono text-slate-500 tracking-widest uppercase w-20">
                     FRAME {currentIndex + 1} / {timeline.length}
                  </div>

                  {/* Timeline Scrubber */}
                  <div className="flex-1">
                     <div className="flex justify-between items-center text-[10px] font-mono text-slate-400 mb-2 px-1">
                        {timeline.map((ts, idx) => (
                           <button 
                              key={idx} 
                              onClick={() => {setCurrentIndex(idx); setIsPlaying(false);}}
                              className={`transition-colors relative ${idx === currentIndex ? 'text-indigo-400 font-bold' : 'hover:text-white'}`}
                           >
                              {typeof ts === 'string' ? ts.substring(11, 16) : String(ts)}
                              {idx === currentIndex && (
                                 <div className="absolute -bottom-3 left-1/2 -translate-x-1/2 w-2 h-2 bg-indigo-500 rotate-45"></div>
                              )}
                           </button>
                        ))}
                     </div>
                     <div className="relative h-1 bg-slate-800 rounded-full mt-3">
                        <div 
                           className="absolute top-0 left-0 h-full bg-indigo-500 rounded-full transition-all duration-300"
                           style={{ width: `${(currentIndex / Math.max(1, timeline.length - 1)) * 100}%` }}
                        />
                     </div>
                  </div>
               </div>
            </div>
         </>
      )}


      {/* RADAR VIEW */}
      {activeView === 'RADAR' && (
         <>
            {/* Header Overlay */}
            <div className="absolute top-24 left-4 z-10 pointer-events-none">
               <div className="text-3xl font-black text-white drop-shadow-md">RADAR OBSERVATION</div>
               <div className="text-sm font-bold tracking-widest text-emerald-400 uppercase drop-shadow-md flex items-center gap-2 mt-1">
                  REAL MUMBAI DWR <span className="text-slate-400">•</span> 20 JUL 2019
               </div>
               
               <div className="mt-6 bg-slate-950/90 border border-slate-800 p-4 rounded-xl shadow-2xl pointer-events-auto inline-flex flex-col gap-3">
                  <div className="text-[10px] font-bold tracking-widest uppercase text-slate-500 mb-1">Visualization Layers</div>
                  <div className="flex gap-2">
                     {['REF', 'VEL', 'WIDTH'].map(layer => (
                        <button
                           key={layer}
                           onClick={() => setRadarLayer(layer)}
                           className={`px-4 py-2 rounded border text-[10px] font-bold tracking-widest uppercase transition-colors ${
                              radarLayer === layer
                              ? 'bg-emerald-600 border-emerald-500 text-white shadow-[0_0_10px_rgba(16,185,129,0.5)]'
                              : 'bg-slate-900 border-slate-700 text-slate-400 hover:bg-slate-800'
                           }`}
                        >
                           {layer === 'REF' ? 'Reflectivity' : layer === 'VEL' ? 'Velocity' : 'Width'}
                        </button>
                     ))}
                  </div>
               </div>
            </div>

            {/* Right Analysis Panel */}
            <div className="absolute top-24 right-4 z-10 w-80 flex flex-col gap-4 pointer-events-auto">
               <div className="bg-slate-950/80 backdrop-blur-md border border-slate-800 rounded-xl p-5 shadow-2xl">
                  
                  {radarMeta && radarMeta.start_time ? (
                     <div className="space-y-4">
                        <div className="flex justify-between items-end border-b border-slate-800/50 pb-2">
                           <div className="text-[10px] font-bold tracking-widest uppercase text-slate-400">RADAR LOCATION</div>
                           <div className="text-right">
                              <span className="text-sm font-mono text-emerald-300">{Number(radarMeta.latitude)?.toFixed(2)}, {Number(radarMeta.longitude)?.toFixed(2)}</span>
                           </div>
                        </div>
                        <div className="flex justify-between items-end border-b border-slate-800/50 pb-2">
                           <div className="text-[10px] font-bold tracking-widest uppercase text-slate-400">OBSERVATION START</div>
                           <div className="text-right">
                              <span className="text-sm font-mono text-emerald-300">{radarMeta.start_time?.substring(11,19)} UTC</span>
                           </div>
                        </div>
                        <div className="flex justify-between items-end border-b border-slate-800/50 pb-2">
                           <div className="text-[10px] font-bold tracking-widest uppercase text-slate-400">OBSERVATION END</div>
                           <div className="text-right">
                              <span className="text-sm font-mono text-emerald-300">{radarMeta.end_time?.substring(11,19)} UTC</span>
                           </div>
                        </div>
                        <div className="flex justify-between items-end border-b border-slate-800/50 pb-2">
                           <div className="text-[10px] font-bold tracking-widest uppercase text-slate-400">SWEEPS</div>
                           <div className="text-right">
                              <span className="text-sm font-mono text-emerald-300">{radarMeta.sweep_count}</span>
                           </div>
                        </div>
                        <div className="flex justify-between items-end pb-2">
                           <div className="text-[10px] font-bold tracking-widest uppercase text-slate-400">MISSING DATA</div>
                           <div className="text-right">
                              <span className="text-xs font-bold tracking-widest uppercase text-emerald-400 bg-emerald-500/10 px-2 py-1 rounded">HANDLED</span>
                           </div>
                        </div>
                     </div>
                  ) : (
                     <div className="text-xs text-slate-500 font-mono text-center py-4">Radar metadata unavailable.</div>
                  )}
               </div>

               {/* Target Builder */}
               <div className="bg-slate-950/80 backdrop-blur-md border border-slate-800 rounded-xl p-4 shadow-2xl">
                  <div className="text-[10px] font-bold tracking-widest uppercase text-emerald-400 mb-1">35 dBZ EVENT THRESHOLD</div>
                  <div className="text-[9px] font-bold tracking-widest uppercase text-slate-400 mb-2">CONFIGURABLE TARGET THRESHOLD</div>
                  <div className="text-xs text-slate-400 mt-2 leading-relaxed">
                     This demonstrates the target-building pipeline; it is not a validated thunderstorm classifier.
                  </div>
               </div>

               {/* Critical Disclaimer */}
               <div className="bg-red-500/10 backdrop-blur-md border border-red-500/30 rounded-xl p-4 shadow-2xl mt-4">
                  <div className="text-[10px] font-black tracking-widest uppercase text-red-400 mb-2">INDEPENDENT REAL OBSERVATIONS</div>
                  <div className="text-xs text-red-300/80 leading-relaxed font-mono">
                     SATELLITE CASE: 29 MAY 2025<br/>
                     RADAR CASE: 20 JUL 2019<br/><br/>
                     NOT A PAIRED TRAINING SAMPLE.
                  </div>
               </div>
            </div>
         </>
      )}


      {/* SYSTEM ARCHITECTURE VIEW */}
      {activeView === 'SYSTEM' && (
         <div className="absolute inset-0 z-10 bg-slate-950/95 backdrop-blur-xl overflow-y-auto pointer-events-auto">
            <div className="max-w-6xl mx-auto pt-32 pb-24 px-8">
               <h2 className="text-3xl font-black text-white tracking-widest uppercase mb-16 text-center">WHERE IS THE AI?</h2>
               
               <div className="grid grid-cols-1 lg:grid-cols-2 gap-16">
                  
                  {/* Architecture Diagram */}
                  <div>
                     <h3 className="text-sm font-bold tracking-widest uppercase text-indigo-400 mb-6">WHAT STORMFUSION DOES</h3>
                     
                     <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 font-mono text-sm text-slate-300 leading-relaxed shadow-2xl">
                        <div className="flex justify-between items-center bg-slate-950 p-4 rounded-lg border border-slate-800 mb-4">
                           <div className="text-emerald-400 font-bold">RADAR</div>
                           <div className="text-indigo-400 font-bold">SATELLITE</div>
                           <div className="text-amber-400 font-bold">LIGHTNING</div>
                           <div className="text-blue-400 font-bold">NWP</div>
                        </div>
                        
                        <div className="flex flex-col items-center text-slate-500">
                           <div className="my-1">↓</div>
                           <div className="bg-slate-800/50 px-6 py-2 rounded w-full text-center text-white border border-slate-700">INGESTION</div>
                           <div className="my-1">↓</div>
                           <div className="bg-slate-800/50 px-6 py-2 rounded w-full text-center text-white border border-slate-700">QC</div>
                           <div className="my-1">↓</div>
                           <div className="bg-slate-800/50 px-6 py-2 rounded w-full text-center text-white border border-slate-700">TIME SYNCHRONIZATION</div>
                           <div className="my-1">↓</div>
                           <div className="bg-slate-800/50 px-6 py-2 rounded w-full text-center text-white border border-slate-700">GEO-ALIGNMENT</div>
                           <div className="my-1">↓</div>
                           <div className="bg-slate-800/50 px-6 py-2 rounded w-full text-center text-white border border-slate-700">COMMON GRID</div>
                           <div className="my-1">↓</div>
                           <div className="bg-slate-800/50 px-6 py-2 rounded w-full text-center text-white border border-slate-700">FEATURE EXTRACTION</div>
                           <div className="my-1">↓</div>
                           <div className="bg-indigo-900/50 px-6 py-3 rounded w-full text-center text-indigo-300 border border-indigo-500/50 font-bold">MULTIMODAL FUSION</div>
                           <div className="my-1">↓</div>
                           <div className="bg-indigo-600 px-6 py-3 rounded w-full text-center text-white font-black shadow-[0_0_20px_rgba(79,70,229,0.4)]">SPATIOTEMPORAL ML</div>
                           <div className="my-1">↓</div>
                           <div className="bg-slate-800/50 px-6 py-2 rounded w-full text-center text-white border border-slate-700">NOWCAST</div>
                        </div>
                     </div>
                  </div>

                  {/* Status Checklists */}
                  <div className="flex flex-col gap-8">
                     
                     <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-2xl p-6 shadow-xl">
                        <h3 className="text-xs font-bold tracking-widest uppercase text-emerald-400 mb-4 flex items-center gap-2"><CheckCircle2 size={16}/> REAL DATA DEMONSTRATED</h3>
                        <div className="space-y-3 font-mono text-sm text-emerald-100/80">
                           <div className="flex items-center gap-3">✓ <span>SATELLITE (12 INSAT-3DS files)</span></div>
                           <div className="flex items-center gap-3">✓ <span>RADAR (1 Mumbai DWR volume)</span></div>
                        </div>
                     </div>

                     <div className="bg-blue-500/10 border border-blue-500/30 rounded-2xl p-6 shadow-xl">
                        <h3 className="text-xs font-bold tracking-widest uppercase text-blue-400 mb-4 flex items-center gap-2"><CheckCircle2 size={16}/> IMPLEMENTED ML FOUNDATION</h3>
                        <div className="space-y-3 font-mono text-sm text-blue-100/80">
                           <div className="flex items-center gap-3">✓ <span>DATASET / WINDOWING</span></div>
                           <div className="flex items-center gap-3">✓ <span>ML ARCHITECTURE</span></div>
                           <div className="flex items-center gap-3">✓ <span>MASKING</span></div>
                           <div className="flex items-center gap-3">✓ <span>EVALUATION</span></div>
                        </div>
                     </div>

                     <div className="bg-amber-500/10 border border-amber-500/30 rounded-2xl p-6 shadow-xl">
                        <h3 className="text-xs font-bold tracking-widest uppercase text-amber-400 mb-4 flex items-center gap-2"><Square size={16}/> SCIENTIFIC VALIDATION GATE</h3>
                        <div className="space-y-3 font-mono text-sm text-amber-100/80">
                           <div className="flex items-center gap-3">○ <span>TRAINING: <strong className="text-red-400 ml-2">NONE</strong></span></div>
                           <div className="flex items-center gap-3">○ <span>CALIBRATION: <strong className="text-red-400 ml-2">NONE</strong></span></div>
                           <div className="flex items-center gap-3">○ <span>VALIDATION: <strong className="text-red-400 ml-2">NOT COMPLETED</strong></span></div>
                           <div className="flex items-center gap-3">○ <span>BENCHMARKING</span></div>
                           <div className="flex items-center gap-3 mt-4 pt-4 border-t border-amber-500/30">○ <span>SYNTHETIC FALLBACK: <strong className="text-emerald-400 ml-2">DISABLED</strong></span></div>
                        </div>
                     </div>

                  </div>
               </div>
            </div>
         </div>
      )}


      {/* DEMO ORCHESTRATION OVERLAYS (Floating guides) */}
      {isDemoActive && (
         <div className="absolute bottom-6 right-6 z-50 bg-indigo-950/90 backdrop-blur-xl border border-indigo-500/50 rounded-2xl p-6 shadow-2xl w-[400px] pointer-events-auto flex flex-col">
            
            {demoStep === 1 && (
               <>
                  <div className="text-[10px] font-bold tracking-widest uppercase text-indigo-400 mb-2">01 — OBSERVE REAL SATELLITE DATA</div>
                  <p className="text-xs text-slate-300 leading-relaxed mb-4">
                     We begin by ingesting, quality-controlling, and grid-aligning 6 real INSAT-3DS observations. 
                     This is not synthetic data; it is processing real frames sequentially.
                  </p>
                  <div className="flex justify-between items-center mt-auto">
                     <div className="text-[9px] font-bold tracking-widest uppercase text-emerald-400">REAL OBSERVATION</div>
                     {/* The useEffect auto-advances to step 2 after timeline finishes playing */}
                     <div className="text-[10px] font-mono text-slate-500">Auto-playing...</div>
                  </div>
               </>
            )}

            {demoStep === 2 && (
               <>
                  <div className="text-[10px] font-bold tracking-widest uppercase text-indigo-400 mb-2">02 — FROM OBSERVATION TO EXTRAPOLATION</div>
                  <p className="text-xs text-slate-300 leading-relaxed mb-4">
                     We extract features (like Cooling Rate) to generate a Deterministic Indicator. 
                     Then, using phase-correlation, we calculate apparent cloud motion for a 30-minute extrapolation.
                  </p>
                  <div className="flex justify-between items-center mt-auto pt-4 border-t border-indigo-500/30">
                     <button onClick={stopDemo} className="text-[10px] font-bold tracking-widest uppercase text-slate-400 hover:text-white">Exit Demo</button>
                     <button onClick={() => advanceDemo(3)} className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded text-[10px] font-bold tracking-widest uppercase transition-colors">Next: Radar →</button>
                  </div>
               </>
            )}

            {demoStep === 3 && (
               <>
                  <div className="text-[10px] font-bold tracking-widest uppercase text-indigo-400 mb-2">03 — REAL RADAR OBSERVATION</div>
                  <p className="text-xs text-slate-300 leading-relaxed mb-4">
                     We switch to an independent DWR radar volume to demonstrate the target-building pipeline. 
                     Notice the dates differ—these are NOT combined into one paired training sample, preserving scientific integrity.
                  </p>
                  <div className="flex justify-between items-center mt-auto pt-4 border-t border-indigo-500/30">
                     <button onClick={stopDemo} className="text-[10px] font-bold tracking-widest uppercase text-slate-400 hover:text-white">Exit Demo</button>
                     <button onClick={() => advanceDemo(4)} className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded text-[10px] font-bold tracking-widest uppercase transition-colors">Next: Architecture →</button>
                  </div>
               </>
            )}

            {demoStep === 4 && (
               <>
                  <div className="text-[10px] font-bold tracking-widest uppercase text-indigo-400 mb-2">04 — WHERE DOES THE AI FIT?</div>
                  <p className="text-xs text-slate-300 leading-relaxed mb-4">
                     The ML architecture is implemented, but training and forecast validation are not yet completed. 
                     StormFusion is a transparent, validation-ready architecture built on real data.
                  </p>
                  <div className="flex justify-between items-center mt-auto pt-4 border-t border-indigo-500/30">
                     <button onClick={stopDemo} className="text-[10px] font-bold tracking-widest uppercase text-slate-400 hover:text-white">Exit Demo</button>
                     <button onClick={stopDemo} className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-[10px] font-bold tracking-widest uppercase transition-colors">Finish</button>
                  </div>
               </>
            )}

         </div>
      )}

    </div>
  );
}
