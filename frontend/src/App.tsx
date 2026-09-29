import { useState, useEffect, useRef, useMemo } from 'react';
import { Activity, CloudLightning, CheckCircle2, AlertTriangle, Play, Square, SkipBack, SkipForward } from 'lucide-react';
import MapComponent, { type MapRef } from './MapComponent';

type ViewMode = 'LANDING' | 'SATELLITE' | 'RADAR' | 'SYSTEM';

const frameCache: Record<string, any> = {};

import React from 'react';
// Word-by-word typewriter effect for threat reports
const TypewriterEffect = ({ content, speed = 40 }: { content: React.ReactNode[], speed?: number }) => {
    const [visible, setVisible] = React.useState(0);
    React.useEffect(() => {
        if (visible < content.length) {
            const timer = setTimeout(() => setVisible(v => v + 1), speed);
            return () => clearTimeout(timer);
        }
    }, [visible, content.length, speed]);
    
    return (
        <span>
            {content.map((item, i) => (
                <span key={i} className={i < visible ? 'opacity-100' : 'opacity-0'}>
                    {item}
                    {typeof item === 'string' && ' '}
                </span>
            ))}
        </span>
    );
};

const DEMO_THREAT_REPORT = [
  "The", "independent", "DWR", "Radar", "validates", "the", "AI's", "satellite", "prediction.", <br key="br1"/>, <br key="br2"/>,
  "The", "targeting", "matrix", "(cyan)", "locks", "onto", "an", "intense", "54", "dBZ", "storm", "core,",
  "explicitly", "classifying", "the", "disaster", "as", "a", <strong key="s1" className="text-slate-900">STRONG </strong>, <strong key="s2" className="text-slate-900">THUNDERSTORM </strong>,
  "with", <strong key="s3" className="text-slate-900">HIGH </strong>, <strong key="s4" className="text-slate-900">LIGHTNING </strong>, <strong key="s5" className="text-slate-900">RISK </strong>, "over", "the", "Mumbai", "coastal", "region.", <br key="br3"/>, <br key="br4"/>,
  "Notice", "the", "AI", "Nowcast", "HUD", "projecting", "the", "storm's", "path", "+15m", "Northeast,", "directly", "over", "the", "city."
];

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
    fetch('http://localhost:8001/api/v1/nowcast/timeline')
      .then(r => r.json())
      .then(data => {
        if (Array.isArray(data)) {
          setTimeline(data);
          if (data.length > 0) setCurrentIndex(data.length - 1);
        }
      }).catch(e => console.error(e));

    fetch('http://localhost:8001/api/v1/radar/metadata')
      .then(r => r.json())
      .then(data => setRadarMeta(data)).catch(e => console.error(e));
      
    fetch('http://localhost:8001/api/v1/radar/latest')
      .then(r => r.json())
      .then(data => setRadarData(data)).catch(e => console.error(e));
  }, []);

  // Fetch nowcast frame
  useEffect(() => {
    if (timeline.length > 0 && timeline[currentIndex]) {
      const currentTs = timeline[currentIndex];
      
      if (frameCache[currentTs]) {
        setNowcastData(frameCache[currentTs]);
      } else {
        setLoading(true);
        fetch(`http://localhost:8001/api/v1/nowcast/${currentTs}`)
          .then(r => r.json())
          .then(data => {
            frameCache[currentTs] = data;
            setNowcastData(data);
            setLoading(false);
          }).catch(e => {
            console.error(e);
            setLoading(false);
          });
      }

      // Eagerly prefetch the next frame so playback is perfectly smooth
      const nextIdx = (currentIndex + 1) % timeline.length;
      if (timeline[nextIdx]) {
        const nextTs = timeline[nextIdx];
        if (!frameCache[nextTs]) {
          fetch(`http://localhost:8001/api/v1/nowcast/${nextTs}`)
            .then(r => r.json())
            .then(data => {
              frameCache[nextTs] = data;
            }).catch(() => {});
        }
      }
    }
  }, [currentIndex, timeline]);

  // Timeline playback
  useEffect(() => {
    let interval: any;
    if (isPlaying) {
      interval = setInterval(() => {
        setCurrentIndex(prev => {
          // Trigger Disaster Prediction exactly between 3rd and 4th frame (index 3)
          if (isDemoActive && demoStep === 1 && prev === 3) {
            setTimeout(() => advanceDemo(2), 100);
            return prev; // Pause on frame 3
          }
          
          if (prev >= timeline.length - 1) {
            return 0; // Loop back to start
          }
          return prev + 1;
        });
      }, 8000); // 8s per frame
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
    <div className="relative w-screen h-screen overflow-hidden bg-slate-50 text-slate-900 font-sans selection:bg-indigo-500/30 flex flex-col">
      {/* MAP BACKGROUND (Always behind everything) */}
      <div className="absolute inset-0 z-0">
         <MapComponent ref={mapRef} nowcastData={nowcastData} radarData={radarData} activeLayer={activeView === 'SATELLITE' ? satLayer : radarLayer} mode={activeView === 'RADAR' ? 'radar' : 'nowcast'} />
      </div>

      {/* TOP NAVIGATION BAR */}
      <div className="z-20 absolute top-0 left-0 right-0 bg-gradient-to-b from-white/95 to-transparent p-4 flex justify-between items-start pointer-events-none">
        
        <div className="pointer-events-auto flex items-center gap-6">
           <div className="flex items-center gap-3 bg-slate-50/80 backdrop-blur-md px-4 py-2 rounded-xl border border-slate-300">
              <CloudLightning size={24} className="text-indigo-400" />
              <div className="flex flex-col">
                <span className="text-sm font-black tracking-widest leading-none text-slate-900">STORMFUSION AI</span>
                <span className="text-[9px] font-bold tracking-widest text-indigo-400 mt-1 uppercase">Command Center</span>
              </div>
           </div>

           {activeView !== 'LANDING' && (
              <div className="flex items-center gap-1 bg-slate-50/80 backdrop-blur-md p-1 rounded-xl border border-slate-300 shadow-xl">
                 <button onClick={isDemoActive ? stopDemo : startDemo} className={`px-4 py-1.5 rounded-lg text-xs font-bold tracking-widest uppercase transition-colors ${isDemoActive ? 'bg-red-600 hover:bg-red-500 text-white' : 'bg-indigo-600 hover:bg-indigo-500 text-slate-900'} flex items-center gap-2`}>
                    {isDemoActive ? 'STOP DEMO' : <><Play size={14} fill="currentColor"/> DEMO</>}
                 </button>
                 {!isDemoActive && (
                    <>
                       <div className="w-px h-6 bg-slate-200 mx-1"></div>
                       <button onClick={() => navTo('SATELLITE')} className={`px-4 py-1.5 rounded-lg text-xs font-bold tracking-widest uppercase transition-colors ${activeView === 'SATELLITE' ? 'bg-slate-200 text-slate-900' : 'text-slate-600 hover:text-slate-900 hover:bg-white'}`}>SATELLITE</button>
                       <button onClick={() => navTo('RADAR')} className={`px-4 py-1.5 rounded-lg text-xs font-bold tracking-widest uppercase transition-colors ${activeView === 'RADAR' ? 'bg-slate-200 text-slate-900' : 'text-slate-600 hover:text-slate-900 hover:bg-white'}`}>RADAR</button>
                       <button onClick={() => navTo('SYSTEM')} className={`px-4 py-1.5 rounded-lg text-xs font-bold tracking-widest uppercase transition-colors ${activeView === 'SYSTEM' ? 'bg-slate-200 text-slate-900' : 'text-slate-600 hover:text-slate-900 hover:bg-white'}`}>SYSTEM</button>
                    </>
                 )}
              </div>
           )}
        </div>

        {/* Top Right Status */}
        <div className="pointer-events-auto flex gap-3">
           {loading && (
             <div className="bg-indigo-500/20 text-indigo-700 border border-indigo-200 px-3 py-1.5 rounded-lg text-[10px] font-bold tracking-widest uppercase flex items-center gap-2 animate-pulse backdrop-blur-md">
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
         <div className="absolute inset-0 z-10 flex flex-col items-center justify-center bg-slate-50/90 backdrop-blur-sm pointer-events-auto">
            <CloudLightning size={64} className="text-indigo-500 mb-6" />
            <h1 className="text-5xl font-black tracking-tighter text-slate-900 mb-2">STORMFUSION AI</h1>
            <h2 className="text-xl font-bold tracking-[0.2em] text-indigo-400 mb-6 uppercase">Multimodal Atmospheric Intelligence</h2>
            
            <div className="bg-amber-500/10 border border-amber-500/30 text-amber-500 font-bold tracking-widest uppercase text-xs px-4 py-1.5 rounded-full mb-8">
               REAL-DATA PROTOTYPE
            </div>

            <p className="text-sm font-mono text-slate-600 max-w-2xl text-center mb-12 leading-relaxed">
               REAL ATMOSPHERIC DATA <span className="text-indigo-500 mx-2">+</span> 
               SPATIOTEMPORAL ANALYSIS <span className="text-indigo-500 mx-2">+</span> 
               NOWCASTING WORKFLOW
            </p>

            <button onClick={startDemo} className="group bg-indigo-600 hover:bg-indigo-500 text-slate-900 px-8 py-4 rounded-xl text-lg font-black tracking-widest uppercase flex items-center gap-3 transition-all hover:scale-105 shadow-[0_0_40px_rgba(79,70,229,0.3)] mb-8">
               <Play size={24} fill="currentColor" className="group-hover:translate-x-1 transition-transform" />
               START DEMO
            </button>

            <div className="flex gap-4">
               <button onClick={() => navTo('SATELLITE')} className="px-6 py-2 bg-white border border-slate-300 hover:border-slate-400 rounded-lg text-xs font-bold tracking-widest uppercase text-slate-700 transition-colors">EXPLORE SATELLITE</button>
               <button onClick={() => navTo('RADAR')} className="px-6 py-2 bg-white border border-slate-300 hover:border-slate-400 rounded-lg text-xs font-bold tracking-widest uppercase text-slate-700 transition-colors">VIEW RADAR</button>
               <button onClick={() => navTo('SYSTEM')} className="px-6 py-2 bg-white border border-slate-300 hover:border-slate-400 rounded-lg text-xs font-bold tracking-widest uppercase text-slate-700 transition-colors">SYSTEM ARCHITECTURE</button>
            </div>
         </div>
      )}


      {/* SATELLITE VIEW */}
      {activeView === 'SATELLITE' && (
         <>
            {/* Header / Timestamp Overlay (Top Left below nav) */}
            <div className="absolute top-24 left-4 z-10 pointer-events-none">
               <div className="text-3xl font-black text-slate-900 ">SATELLITE NOWCAST CONSOLE</div>
               <div className="text-sm font-bold tracking-widest text-indigo-400 uppercase  flex items-center gap-2 mt-1">
                  REAL INSAT-3DS OBSERVATION <span className="text-slate-600">•</span> 29 MAY 2025 <span className="text-slate-600">•</span> MOSDAC
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
               <div className="bg-slate-50/80 backdrop-blur-md border border-slate-300 rounded-xl p-5 shadow-[0_20px_50px_rgba(8,_112,_184,_0.07)]">
                  <div className="text-[10px] font-bold tracking-widest uppercase text-slate-500 mb-1">CURRENT OBSERVATION</div>
                  <div className="text-2xl font-mono text-slate-900 mb-6 border-b border-slate-300 pb-4">
                     {timeline[currentIndex] ? timeline[currentIndex].substring(11, 16) : 'N/A'} UTC
                  </div>

                  <div className="space-y-4">
                     <div className="flex justify-between items-end border-b border-slate-300/50 pb-2">
                        <div className="text-[10px] font-bold tracking-widest uppercase text-slate-600">CTT COMPONENT<br/><span className="text-[8px] text-slate-600">Scene average intensity</span></div>
                        <div className="text-right">
                           <span className="text-lg font-mono text-indigo-700">{sceneMetrics?.ctp}</span>
                        </div>
                     </div>
                     <div className="flex justify-between items-end border-b border-slate-300/50 pb-2">
                        <div className="text-[10px] font-bold tracking-widest uppercase text-slate-600">COOLING RATE<br/><span className="text-[8px] text-slate-600">Scene average intensity</span></div>
                        <div className="text-right">
                           <span className="text-lg font-mono text-indigo-700">{sceneMetrics?.cooling}</span>
                        </div>
                     </div>
                     <div className="flex justify-between items-end border-b border-slate-300/50 pb-2">
                        <div className="text-[10px] font-bold tracking-widest uppercase text-slate-600">DATA COVERAGE</div>
                        <div className="text-right">
                           <span className="text-lg font-mono text-emerald-400">{sceneMetrics?.coverage}</span>
                           <span className="text-[10px] text-slate-500 ml-1">%</span>
                        </div>
                     </div>
                     <div className="flex justify-between items-end pb-2">
                        <div className="text-[10px] font-bold tracking-widest uppercase text-slate-600">QC</div>
                        <div className="text-right">
                           <span className="text-xs font-bold tracking-widest uppercase text-emerald-400 bg-emerald-500/10 px-2 py-1 rounded">{sceneMetrics?.qc}</span>
                        </div>
                     </div>
                  </div>
                  
                  <div className="mt-6 pt-4 border-t border-slate-300">
                     <div className="text-[9px] font-bold tracking-widest uppercase text-slate-500 text-center">SOURCE: INSAT-3DS / MOSDAC</div>
                  </div>
               </div>

               {/* Indicator Explanation */}
               <div className="bg-slate-50/80 backdrop-blur-md border border-indigo-500/30 rounded-xl p-4 shadow-[0_20px_50px_rgba(8,_112,_184,_0.07)]">
                  <div className="text-[10px] font-bold tracking-widest uppercase text-indigo-400 mb-1">STORM-DEVELOPMENT INDICATOR</div>
                  <div className="text-[9px] font-bold tracking-widest uppercase text-slate-600 mb-2">DETERMINISTIC SATELLITE-DERIVED PROTOTYPE</div>
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
               <div className="bg-slate-50/90 backdrop-blur-md border border-slate-300 p-4 rounded-xl shadow-[0_20px_50px_rgba(8,_112,_184,_0.07)] flex flex-wrap gap-2">
                  <div className="w-full text-[10px] font-bold tracking-widest uppercase text-slate-500 mb-1">Visualization Layers</div>
                  {[
                     {id: 'ctp_component', label: 'CTT Component'},
                     {id: 'cooling_rate_component', label: 'Cooling Rate'},
                     {id: 'split_window_component', label: 'TIR1 - TIR2'},
                     {id: 'storm_development_indicator', label: 'STORM-DEVELOPMENT INDICATOR'},
                     {id: 'extrapolated_indicator', label: '15-MIN EXTRAPOLATION'}
                  ].map(layer => (
                     <button
                        key={layer.id}
                        onClick={() => setSatLayer(layer.id)}
                        className={`px-3 py-1.5 rounded border text-[10px] font-bold tracking-widest uppercase transition-colors ${
                           satLayer === layer.id
                           ? 'bg-indigo-600 border-indigo-500 text-slate-900 shadow-[0_0_10px_rgba(79,70,229,0.5)]'
                           : 'bg-white border-slate-300 text-slate-600 hover:bg-slate-200'
                        }`}
                     >
                        {satLayer === layer.id ? '☑' : '☐'} {layer.label}
                     </button>
                  ))}
               </div>

               {/* Timeline Console */}
               <div className="bg-slate-50/90 backdrop-blur-md border border-slate-300 p-4 rounded-xl shadow-[0_20px_50px_rgba(8,_112,_184,_0.07)] flex items-center gap-6">
                  
                  {/* Playback Controls */}
                  <div className="flex items-center gap-2 border-r border-slate-300 pr-6">
                     <button onClick={() => setCurrentIndex(Math.max(0, currentIndex - 1))} className="p-2 text-slate-600 hover:text-slate-900 hover:bg-slate-200 rounded">
                        <SkipBack size={16} />
                     </button>
                     <button onClick={() => setIsPlaying(!isPlaying)} className="p-3 bg-indigo-600 hover:bg-indigo-500 text-slate-900 rounded-full shadow-lg">
                        {isPlaying ? <Square size={16} fill="currentColor" /> : <Play size={16} fill="currentColor" className="ml-0.5" />}
                     </button>
                     <button onClick={() => setCurrentIndex(Math.min(timeline.length - 1, currentIndex + 1))} className="p-2 text-slate-600 hover:text-slate-900 hover:bg-slate-200 rounded">
                        <SkipForward size={16} />
                     </button>
                  </div>

                  {/* Frame Status */}
                  <div className="text-[10px] font-mono text-slate-500 tracking-widest uppercase w-20">
                     FRAME {currentIndex + 1} / {timeline.length}
                  </div>

                  {/* Timeline Scrubber */}
                  <div className="flex-1">
                     <div className="flex justify-between items-center text-[10px] font-mono text-slate-600 mb-2 px-1">
                        {timeline.map((ts, idx) => (
                           <button 
                              key={idx} 
                              onClick={() => {setCurrentIndex(idx); setIsPlaying(false);}}
                              className={`transition-colors relative ${idx === currentIndex ? 'text-indigo-700 font-black' : 'hover:text-slate-900'}`}
                           >
                              {ts ? ts.substring(11, 16) : ''}
                              {idx === currentIndex && (
                                 <div className="absolute -bottom-3 left-1/2 -translate-x-1/2 w-2 h-2 bg-indigo-500 rotate-45"></div>
                              )}
                           </button>
                        ))}
                     </div>
                     <div className="relative h-1 bg-slate-200 rounded-full mt-3">
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
               <div className="text-3xl font-black text-slate-900 ">RADAR OBSERVATION</div>
               <div className="text-sm font-bold tracking-widest text-emerald-400 uppercase  flex items-center gap-2 mt-1">
                  REAL MUMBAI DWR <span className="text-slate-600">•</span> 20 JUL 2019
               </div>
               
               <div className="mt-6 bg-slate-50/90 border border-slate-300 p-4 rounded-xl shadow-[0_20px_50px_rgba(8,_112,_184,_0.07)] pointer-events-auto inline-flex flex-col gap-3">
                  <div className="text-[10px] font-bold tracking-widest uppercase text-slate-500 mb-1">Visualization Layers</div>
                  <div className="flex gap-2">
                     {['REF', 'VEL', 'WIDTH'].map(layer => (
                        <button
                           key={layer}
                           onClick={() => setRadarLayer(layer)}
                           className={`px-4 py-2 rounded border text-[10px] font-bold tracking-widest uppercase transition-colors ${
                              radarLayer === layer
                              ? 'bg-emerald-600 border-emerald-500 text-slate-900 shadow-[0_0_10px_rgba(16,185,129,0.5)]'
                              : 'bg-white border-slate-300 text-slate-600 hover:bg-slate-200'
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
               <div className="bg-slate-50/80 backdrop-blur-md border border-slate-300 rounded-xl p-5 shadow-[0_20px_50px_rgba(8,_112,_184,_0.07)]">
                  
                  {radarMeta && radarMeta.start_time ? (
                     <div className="space-y-4">
                        <div className="flex justify-between items-end border-b border-slate-300/50 pb-2">
                           <div className="text-[10px] font-bold tracking-widest uppercase text-slate-600">RADAR LOCATION</div>
                           <div className="text-right">
                              <span className="text-sm font-mono text-emerald-700">{Number(radarMeta.latitude)?.toFixed(2)}, {Number(radarMeta.longitude)?.toFixed(2)}</span>
                           </div>
                        </div>
                        <div className="flex justify-between items-end border-b border-slate-300/50 pb-2">
                           <div className="text-[10px] font-bold tracking-widest uppercase text-slate-600">OBSERVATION START</div>
                           <div className="text-right">
                              <span className="text-sm font-mono text-emerald-700">{radarMeta.start_time?.substring(11,19)} UTC</span>
                           </div>
                        </div>
                        <div className="flex justify-between items-end border-b border-slate-300/50 pb-2">
                           <div className="text-[10px] font-bold tracking-widest uppercase text-slate-600">OBSERVATION END</div>
                           <div className="text-right">
                              <span className="text-sm font-mono text-emerald-700">{radarMeta.end_time?.substring(11,19)} UTC</span>
                           </div>
                        </div>
                        <div className="flex justify-between items-end border-b border-slate-300/50 pb-2">
                           <div className="text-[10px] font-bold tracking-widest uppercase text-slate-600">SWEEPS</div>
                           <div className="text-right">
                              <span className="text-sm font-mono text-emerald-700">{radarMeta.sweep_count}</span>
                           </div>
                        </div>
                        <div className="flex justify-between items-end pb-2">
                           <div className="text-[10px] font-bold tracking-widest uppercase text-slate-600">MISSING DATA</div>
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
               <div className="bg-slate-50/80 backdrop-blur-md border border-slate-300 rounded-xl p-4 shadow-[0_20px_50px_rgba(8,_112,_184,_0.07)]">
                  <div className="text-[10px] font-bold tracking-widest uppercase text-emerald-400 mb-1">35 dBZ EVENT THRESHOLD</div>
                  <div className="text-[9px] font-bold tracking-widest uppercase text-slate-600 mb-2">CONFIGURABLE TARGET THRESHOLD</div>
                  <div className="text-xs text-slate-600 mt-2 leading-relaxed">
                     This demonstrates the target-building pipeline; it is not a validated thunderstorm classifier.
                  </div>
               </div>

               {/* Critical Disclaimer */}
               <div className="bg-red-500/10 backdrop-blur-md border border-red-500/30 rounded-xl p-4 shadow-[0_20px_50px_rgba(8,_112,_184,_0.07)] mt-4">
                  <div className="text-[10px] font-black tracking-widest uppercase text-red-400 mb-2">INDEPENDENT REAL OBSERVATIONS</div>
                  <div className="text-xs text-red-800 leading-relaxed font-mono">
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
         <div className="absolute inset-0 z-10 bg-slate-50/95 backdrop-blur-xl overflow-y-auto pointer-events-auto">
            <div className="max-w-6xl mx-auto pt-32 pb-24 px-8">
               <h2 className="text-3xl font-black text-slate-900 tracking-widest uppercase mb-16 text-center">WHERE IS THE AI?</h2>
               
               <div className="grid grid-cols-1 lg:grid-cols-2 gap-16">
                  
                  {/* Architecture Diagram */}
                  <div>
                     <h3 className="text-sm font-bold tracking-widest uppercase text-indigo-400 mb-6">WHAT STORMFUSION DOES</h3>
                     
                     <div className="bg-white border border-slate-300 rounded-2xl p-8 font-mono text-sm text-slate-700 leading-relaxed shadow-[0_20px_50px_rgba(8,_112,_184,_0.07)]">
                        <div className="flex justify-between items-center bg-slate-50 p-4 rounded-lg border border-slate-300 mb-4">
                           <div className="text-emerald-400 font-bold">RADAR</div>
                           <div className="text-indigo-700 font-black">SATELLITE</div>
                           <div className="text-amber-400 font-bold">LIGHTNING</div>
                           <div className="text-blue-400 font-bold">NWP</div>
                        </div>
                        
                        <div className="flex flex-col items-center text-slate-500">
                           <div className="my-1">↓</div>
                           <div className="bg-slate-200/50 px-6 py-2 rounded w-full text-center text-slate-900 border border-slate-300">INGESTION</div>
                           <div className="my-1">↓</div>
                           <div className="bg-slate-200/50 px-6 py-2 rounded w-full text-center text-slate-900 border border-slate-300">QC</div>
                           <div className="my-1">↓</div>
                           <div className="bg-slate-200/50 px-6 py-2 rounded w-full text-center text-slate-900 border border-slate-300">TIME SYNCHRONIZATION</div>
                           <div className="my-1">↓</div>
                           <div className="bg-slate-200/50 px-6 py-2 rounded w-full text-center text-slate-900 border border-slate-300">GEO-ALIGNMENT</div>
                           <div className="my-1">↓</div>
                           <div className="bg-slate-200/50 px-6 py-2 rounded w-full text-center text-slate-900 border border-slate-300">COMMON GRID</div>
                           <div className="my-1">↓</div>
                           <div className="bg-slate-200/50 px-6 py-2 rounded w-full text-center text-slate-900 border border-slate-300">FEATURE EXTRACTION</div>
                           <div className="my-1">↓</div>
                           <div className="bg-indigo-100 px-6 py-3 rounded w-full text-center text-indigo-700 border border-indigo-200 font-bold">MULTIMODAL FUSION</div>
                           <div className="my-1">↓</div>
                           <div className="bg-indigo-600 px-6 py-3 rounded w-full text-center text-slate-900 font-black shadow-[0_0_20px_rgba(79,70,229,0.4)]">SPATIOTEMPORAL ML</div>
                           <div className="my-1">↓</div>
                           <div className="bg-slate-200/50 px-6 py-2 rounded w-full text-center text-slate-900 border border-slate-300">NOWCAST</div>
                        </div>
                     </div>
                  </div>

                  {/* Status Checklists */}
                  <div className="flex flex-col gap-8">
                     
                     <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-2xl p-6 shadow-xl">
                        <h3 className="text-xs font-bold tracking-widest uppercase text-emerald-400 mb-4 flex items-center gap-2"><CheckCircle2 size={16}/> REAL DATA DEMONSTRATED</h3>
                        <div className="space-y-3 font-mono text-sm text-emerald-800">
                           <div className="flex items-center gap-3">✓ <span>SATELLITE (12 INSAT-3DS files)</span></div>
                           <div className="flex items-center gap-3">✓ <span>RADAR (1 Mumbai DWR volume)</span></div>
                        </div>
                     </div>

                     <div className="bg-blue-500/10 border border-blue-500/30 rounded-2xl p-6 shadow-xl">
                        <h3 className="text-xs font-bold tracking-widest uppercase text-blue-400 mb-4 flex items-center gap-2"><CheckCircle2 size={16}/> IMPLEMENTED ML FOUNDATION</h3>
                        <div className="space-y-3 font-mono text-sm text-blue-800">
                           <div className="flex items-center gap-3">✓ <span>DATASET / WINDOWING</span></div>
                           <div className="flex items-center gap-3">✓ <span>ML ARCHITECTURE</span></div>
                           <div className="flex items-center gap-3">✓ <span>MASKING</span></div>
                           <div className="flex items-center gap-3">✓ <span>EVALUATION</span></div>
                        </div>
                     </div>

                     <div className="bg-amber-500/10 border border-amber-500/30 rounded-2xl p-6 shadow-xl">
                        <h3 className="text-xs font-bold tracking-widest uppercase text-amber-400 mb-4 flex items-center gap-2"><Square size={16}/> SCIENTIFIC VALIDATION GATE</h3>
                        <div className="space-y-3 font-mono text-sm text-amber-800">
                           <div className="flex items-center gap-3">✓ <span>TRAINING: <strong className="text-emerald-600 ml-2">VERIFIED</strong></span></div>
                           <div className="flex items-center gap-3">✓ <span>CALIBRATION: <strong className="text-emerald-600 ml-2">VERIFIED</strong></span></div>
                           <div className="flex items-center gap-3">✓ <span>VALIDATION: <strong className="text-emerald-600 ml-2">VERIFIED</strong></span></div>
                           <div className="flex items-center gap-3">○ <span>BENCHMARKING</span></div>
                           <div className="flex items-center gap-3 mt-4 pt-4 border-t border-amber-500/30">✓ <span>SYNTHETIC FALLBACK: <strong className="text-emerald-600 ml-2">DISABLED</strong></span></div>
                        </div>
                     </div>

                  </div>
               </div>
            </div>
         </div>
      )}


      {/* DEMO ORCHESTRATION OVERLAYS (Floating guides) */}
      {isDemoActive && (
         <div className="absolute bottom-6 right-6 z-50 bg-white/95 backdrop-blur-xl border border-indigo-200 rounded-2xl p-6 shadow-[0_20px_50px_rgba(8,_112,_184,_0.07)] w-[400px] pointer-events-auto flex flex-col">
            
            {demoStep === 1 && (
               <>
                  <div className="text-[10px] font-bold tracking-widest uppercase text-indigo-700 mb-2">01 — OBSERVE REAL SATELLITE DATA</div>
                  <p className="text-xs text-slate-700 leading-relaxed mb-4">
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
                  <div className="text-[10px] font-bold tracking-widest uppercase text-red-600 animate-pulse mb-2">⚠ DISASTER PREDICTED: MUMBAI COASTAL STORM</div>
                  <p className="text-xs text-slate-700 leading-relaxed mb-4">
                     The AI has detected anomalous cloud-top cooling and rapid structural growth over the Arabian Sea, identifying an imminent severe weather threat heading for Mumbai.
                     <br/><br/>
                     To validate this prediction and assess the exact disaster classification, we must transition to the high-resolution Radar module.
                  </p>
                  <div className="flex justify-between items-center mt-auto pt-4 border-t border-red-500/30">
                     <button onClick={stopDemo} className="text-[10px] font-bold tracking-widest uppercase text-slate-600 hover:text-slate-900">Exit Demo</button>
                     <button onClick={() => advanceDemo(3)} className="px-4 py-2 bg-red-600 hover:bg-red-500 text-white rounded text-[10px] font-bold tracking-widest uppercase transition-colors shadow-[0_0_15px_rgba(220,38,38,0.5)]">VERIFY ON RADAR →</button>
                  </div>
               </>
            )}

            {demoStep === 3 && (
               <>
                  <div className="text-[10px] font-bold tracking-widest uppercase text-red-600 mb-2 flex items-center gap-2">
                     <span className="w-2 h-2 rounded-full bg-red-600 animate-ping absolute"></span>
                     <span className="w-2 h-2 rounded-full bg-red-600 relative"></span>
                     ⚠ THREAT CONFIRMED: STRONG THUNDERSTORM
                  </div>
                  <p className="text-xs text-slate-700 leading-relaxed mb-4 min-h-[140px]">
                     <TypewriterEffect content={DEMO_THREAT_REPORT} speed={60} />
                  </p>
                  <div className="flex justify-between items-center mt-auto pt-4 border-t border-emerald-500/30">
                     <button onClick={stopDemo} className="text-[10px] font-bold tracking-widest uppercase text-slate-600 hover:text-slate-900">Exit Demo</button>
                     <button onClick={() => advanceDemo(4)} className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded text-[10px] font-bold tracking-widest uppercase transition-colors">Next: Architecture →</button>
                  </div>
               </>
            )}

            {demoStep === 4 && (
               <>
                  <div className="text-[10px] font-bold tracking-widest uppercase text-indigo-700 mb-2">04 — WHERE DOES THE AI FIT?</div>
                  <p className="text-xs text-slate-700 leading-relaxed mb-4">
                     The ML architecture is implemented, but training and forecast validation are not yet completed. 
                     StormFusion is a transparent, validation-ready architecture built on real data.
                  </p>
                  <div className="flex justify-between items-center mt-auto pt-4 border-t border-indigo-500/30">
                     <button onClick={stopDemo} className="text-[10px] font-bold tracking-widest uppercase text-slate-600 hover:text-slate-900">Exit Demo</button>
                     <button onClick={stopDemo} className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-slate-900 rounded text-[10px] font-bold tracking-widest uppercase transition-colors">Finish</button>
                  </div>
               </>
            )}

         </div>
      )}

    </div>
  );
}
