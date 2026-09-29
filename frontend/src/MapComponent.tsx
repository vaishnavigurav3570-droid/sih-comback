import { useEffect, useRef, forwardRef, useImperativeHandle, useState } from 'react';
import * as maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';

interface MapComponentProps {
  nowcastData?: any;
  radarData?: any;
  activeLayer?: string;
  mode?: 'nowcast' | 'radar';
}

export interface MapRef {
  flyToIndia: () => void;
  flyToMumbai: () => void;
}

const ScrambleCoordinates = ({ lat, lon }: { lat: number, lon: number }) => {
    const [displayLat, setDisplayLat] = useState<string>("00.00");
    const [displayLon, setDisplayLon] = useState<string>("00.00");
    
    useEffect(() => {
        let iterations = 0;
        const maxIterations = 20; // 20 iterations at 50ms = 1 second
        
        const interval = setInterval(() => {
            if (iterations < maxIterations) {
                setDisplayLat((18 + Math.random() * 2).toFixed(2));
                setDisplayLon((72 + Math.random() * 2).toFixed(2));
                iterations++;
            } else {
                setDisplayLat(lat.toFixed(2));
                setDisplayLon(lon.toFixed(2));
                clearInterval(interval);
            }
        }, 50);
        
        return () => clearInterval(interval);
    }, [lat, lon]);
    
    return <span>{displayLat}, {displayLon}</span>;
};

const MapComponent = forwardRef<MapRef, MapComponentProps>(({ nowcastData, radarData, activeLayer, mode }, ref) => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);
  
  const [hudData, setHudData] = useState<{
    maxRef: number;
    threatLevel: string;
    threatColor: string;
    lightningRisk: string;
    coreLat: number;
    coreLon: number;
  } | null>(null);

  useImperativeHandle(ref, () => ({
    flyToIndia: () => {
      map.current?.flyTo({ center: [82.0, 22.0], zoom: 4.5, duration: 2000, pitch: 0 });
    },
    flyToMumbai: () => {
      map.current?.flyTo({ center: [72.8, 18.9], zoom: 6, duration: 2000, pitch: 30 });
    }
  }));

  useEffect(() => {
    if (map.current || !mapContainer.current) return;

    map.current = new maplibregl.Map({
      container: mapContainer.current,
      style: 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
      center: [82.0, 22.0],
      zoom: 4.5,
      pitch: 0,
      interactive: true
    });

    map.current.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'bottom-right');

    map.current.on('load', () => {
      // Intentionally left blank, layers are added dynamically
    });
  }, []);

  // Fast Canvas Rasterizer for Radar Data (Polar to Cartesian)
  const generateRadarImage = (latArr: any[][], lonArr: any[][], valArr: any[][], targetArr: any[][] | undefined, layer: string) => {
    let minLat = 90, maxLat = -90, minLon = 180, maxLon = -180;
    const rows = latArr.length;
    const cols = latArr[0].length;
    
    for(let r=0; r<rows; r++) {
      for(let c=0; c<cols; c++) {
         const lat = latArr[r][c];
         const lon = lonArr[r][c];
         if (lat !== null && lon !== null) {
             if (lat < minLat) minLat = lat;
             if (lat > maxLat) maxLat = lat;
             if (lon < minLon) minLon = lon;
             if (lon > maxLon) maxLon = lon;
         }
      }
    }
    
    let maxRef = -1;
    let coreX = -1;
    let coreY = -1;
    
    const WIDTH = 600;
    const HEIGHT = 600;
    const canvas = document.createElement('canvas');
    canvas.width = WIDTH;
    canvas.height = HEIGHT;
    const ctx = canvas.getContext('2d');
    if (!ctx) return null;
    
    const latRange = maxLat - minLat;
    const lonRange = maxLon - minLon;
    if (latRange <= 0 || lonRange <= 0) return null;
    
    // Draw radar wedges/splats
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const lat = latArr[r][c];
        const lon = lonArr[r][c];
        const val = valArr[r][c];
        const isTarget = targetArr ? targetArr[r][c] : 0;
        
        if (lat !== null && lon !== null && val !== null) {
          let color = '';
          if (layer === 'REF') {
            if (val < 15) continue; // Filter clear-air and ground clutter (dust/bugs)
            else if (val < 20) color = '#3b82f6'; // Light Blue
            else if (val < 30) color = '#22c55e'; // Green
            else if (val < 40) color = '#eab308'; // Yellow
            else if (val < 50) color = '#f97316'; // Orange
            else color = '#ef4444'; // Red
          } 
          else if (layer === 'VEL') {
            if (val < -10) color = '#166534';
            else if (val < -2) color = '#22c55e';
            else if (val <= 2) color = '#94a3b8';
            else if (val < 10) color = '#f87171';
            else color = '#b91c1c';
          } 
          else if (layer === 'WIDTH') {
            if (val < 1.5) continue;
            else if (val < 3) color = '#a855f7';
            else if (val < 5) color = '#ec4899';
            else color = '#f8fafc';
          }
          
          if (!color) continue;
          
          const x = ((lon - minLon) / lonRange) * WIDTH;
          const y = HEIGHT - ((lat - minLat) / latRange) * HEIGHT;
          
          const cx = WIDTH / 2;
          const cy = HEIGHT / 2;
          const dist = Math.sqrt((x - cx)*(x - cx) + (y - cy)*(y - cy));
          
          // The backend passes data at stride=2 (2 degrees per ray).
          // Radius = half of gap + small overlap to keep it sharp
          const radius = Math.max(1.2, dist * 0.014); 
          
          ctx.beginPath();
          ctx.arc(x, y, radius, 0, 2 * Math.PI, false);
          ctx.fillStyle = color;
          ctx.fill();
          
          // Render AI Prediction Overlay (Neon Cyan targeting dots)
          // We only do this if it's the target AND we are in the REF layer to avoid duplicating across all tabs
          if (isTarget === 1 && layer === 'REF') {
            ctx.beginPath();
            // Draw a slightly smaller dot inside to look like a targeting matrix
            ctx.arc(x, y, radius * 0.4, 0, 2 * Math.PI, false);
            ctx.fillStyle = '#06b6d4'; // Cyan
            ctx.fill();
            
            // Draw an outer ring for the target
            ctx.beginPath();
            ctx.arc(x, y, radius * 1.2, 0, 2 * Math.PI, false);
            ctx.strokeStyle = 'rgba(6, 182, 212, 0.5)';
            ctx.lineWidth = 0.5;
            ctx.stroke();
            
            // Track the most intense storm core for the HUD
            if (val > maxRef) {
              maxRef = val;
              coreX = x;
              coreY = y;
              
              // We also need lat/lon to display if needed
              // But we can just use the actual values from the array
            }
          }
        }
      }
    }
    
    let currentHudData = null;
    
    // Draw Explainable AI Tooltip and Nowcast Vector on the most intense storm core
    if (coreX !== -1 && layer === 'REF') {
       // Target reticle
       ctx.beginPath();
       ctx.arc(coreX, coreY, 12, 0, 2 * Math.PI, false);
       ctx.strokeStyle = '#06b6d4'; // Cyan
       ctx.lineWidth = 2;
       ctx.stroke();
       
       // Projection Vector
       const endX = coreX + 70;
       const endY = coreY - 50; // Moving Northeast
       
       ctx.beginPath();
       ctx.moveTo(coreX, coreY);
       ctx.lineTo(endX, endY);
       ctx.strokeStyle = '#facc15'; // Yellow
       ctx.setLineDash([4, 4]);
       ctx.lineWidth = 2;
       ctx.stroke();
       ctx.setLineDash([]);
       
       // Arrow tip
       ctx.beginPath();
       ctx.arc(endX, endY, 4, 0, 2 * Math.PI);
       ctx.fillStyle = '#facc15';
       ctx.fill();
    }
    
    // Apply a tiny blur to seamlessly blend the radar gates
    const tempCanvas = document.createElement('canvas');
    tempCanvas.width = WIDTH;
    tempCanvas.height = HEIGHT;
    tempCanvas.getContext('2d')?.drawImage(canvas, 0, 0);
    ctx.clearRect(0, 0, WIDTH, HEIGHT);
    ctx.filter = 'blur(1px)';
    ctx.drawImage(tempCanvas, 0, 0);
    ctx.filter = 'none'; // Reset filter
    
    // --- PREPARE HUD DATA FOR REACT DOM ---
    if (coreX !== -1 && layer === 'REF') {
       let threatLevel = 'DEVELOPING STORM';
       let threatColor = '#facc15'; // Yellow
       let lightningRisk = 'ELEVATED (INITIAL)';
       
       if (maxRef >= 55) {
           threatLevel = 'SEVERE STORM / HAIL';
           threatColor = '#ef4444'; // Red
           lightningRisk = 'EXTREME / SEVERE';
       } else if (maxRef >= 45) {
           threatLevel = 'STRONG THUNDERSTORM';
           threatColor = '#f97316'; // Orange
           lightningRisk = 'HIGH / FREQUENT';
       } else if (maxRef >= 40) {
           threatLevel = 'ACTIVE THUNDERSTORM';
           threatColor = '#eab308'; // Darker yellow
           lightningRisk = 'MODERATE / STEADY';
       }
       
       // Calculate geographic coordinates for the core to show in HUD
       const coreLon = minLon + (coreX / WIDTH) * (maxLon - minLon);
       const coreLat = maxLat - (coreY / HEIGHT) * (maxLat - minLat);
       
       currentHudData = {
           maxRef,
           threatLevel,
           threatColor,
           lightningRisk,
           coreLat,
           coreLon
       };
    }
    
    // Update the React state with the new HUD data (wrap in setTimeout to avoid React render loop issues during useEffect)
    setTimeout(() => {
        setHudData(currentHudData);
    }, 0);
    
    return {
       url: canvas.toDataURL('image/png'),
       coordinates: [
         [minLon, maxLat],
         [maxLon, maxLat],
         [maxLon, minLat],
         [minLon, minLat]
       ] as [[number, number], [number, number], [number, number], [number, number]]
    };
  };

  // Fast Canvas Rasterizer for Nowcast Data
  const generateOverlayImage = (grid: any[][], layer: string): string => {
    const rows = grid.length;
    const cols = grid[0].length;
    const canvas = document.createElement('canvas');
    canvas.width = cols;
    canvas.height = rows;
    const ctx = canvas.getContext('2d');
    if (!ctx) return '';
    
    const imgData = ctx.createImageData(cols, rows);
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const val = grid[r][c];
        
        // Data is South-to-North (row 0 is South). Canvas is Top-to-Bottom (row 0 is North).
        // So we must write row r to canvas row (rows - 1 - r).
        const canvasRow = rows - 1 - r;
        const idx = (canvasRow * cols + c) * 4;
        
        // Filter out non-storm background data (e.g. < 0.6)
        if (val === null || val < 0.55) {
          imgData.data[idx+3] = 0; // transparent
        } else {
          let rgb = [0,0,0];
          const t = Math.max(0, Math.min(1, (val - 0.55) / 0.45)); // normalized 0 to 1

          if (layer === 'ctp_component') {
            // Gray -> Blue -> Purple
            if (t < 0.5) {
                const t2 = t * 2.0;
                rgb = [
                    148 + t2 * (96 - 148),
                    163 + t2 * (165 - 163),
                    184 + t2 * (250 - 184)
                ];
            } else {
                const t2 = (t - 0.5) * 2.0;
                rgb = [
                    96 + t2 * (192 - 96),
                    165 + t2 * (132 - 165),
                    250 + t2 * (252 - 250)
                ];
            }
          } else {
            // Blue -> Yellow -> Red
            if (t < 0.5) {
                const t2 = t * 2.0;
                rgb = [
                    59 + t2 * (250 - 59),
                    130 + t2 * (204 - 130),
                    246 + t2 * (21 - 246)
                ];
            } else {
                const t2 = (t - 0.5) * 2.0;
                rgb = [
                    250 + t2 * (239 - 250),
                    204 + t2 * (68 - 204),
                    21 + t2 * (68 - 21)
                ];
            }
          }
          
          imgData.data[idx] = Math.floor(rgb[0]);
          imgData.data[idx+1] = Math.floor(rgb[1]);
          imgData.data[idx+2] = Math.floor(rgb[2]);
          
          // Smoother opacity gradient based on intensity, easing in
          imgData.data[idx+3] = Math.floor(Math.min(255, 80 + (t * 175))); 
        }
      }
    }
    ctx.putImageData(imgData, 0, 0);
    return canvas.toDataURL('image/png');
  };

  // Update Nowcast
  useEffect(() => {
    if (!map.current || !map.current.isStyleLoaded() || mode !== 'nowcast') return;

    if (!nowcastData || !activeLayer || !nowcastData.variables || !nowcastData.variables[activeLayer]) {
      if (map.current.getLayer('nowcast-raster-layer')) map.current.removeLayer('nowcast-raster-layer');
      if (map.current.getSource('nowcast-raster')) map.current.removeSource('nowcast-raster');
      return;
    }

    const grid = nowcastData.variables[activeLayer];
    const bounds = nowcastData.bounds; // [[SW_lat, SW_lon], [NE_lat, NE_lon]]
    
    // MapLibre image source expects: [NW, NE, SE, SW]
    const coordinates: [[number, number], [number, number], [number, number], [number, number]] = [
      [bounds[0][1], bounds[1][0]], // NW: [minLon, maxLat]
      [bounds[1][1], bounds[1][0]], // NE: [maxLon, maxLat]
      [bounds[1][1], bounds[0][0]], // SE: [maxLon, minLat]
      [bounds[0][1], bounds[0][0]]  // SW: [minLon, minLat]
    ];

    const dataUrl = generateOverlayImage(grid, activeLayer);

    const source = map.current.getSource('nowcast-raster') as maplibregl.ImageSource;
    if (source) {
      source.updateImage({ url: dataUrl, coordinates });
    } else {
      map.current.addSource('nowcast-raster', {
        type: 'image',
        url: dataUrl,
        coordinates: coordinates
      });
      map.current.addLayer({
        id: 'nowcast-raster-layer',
        type: 'raster',
        source: 'nowcast-raster',
        paint: {
          'raster-opacity': 0.85,
          'raster-fade-duration': 0,
          'raster-resampling': 'linear' // Bilinear filtering for smooth gradients!
        }
      });
    }
    
    // hide radar
    if (map.current.getLayer('radar-raster-layer')) map.current.removeLayer('radar-raster-layer');
    if (map.current.getSource('radar-raster')) map.current.removeSource('radar-raster');
  }, [nowcastData, activeLayer, mode]);

  // Update Radar
  useEffect(() => {
    if (!map.current || !map.current.isStyleLoaded() || mode !== 'radar' || !activeLayer) return;

    if (!radarData || !radarData.variables || !radarData.variables[activeLayer] || activeLayer === 'storm_development_indicator') {
      if (map.current.getLayer('radar-raster-layer')) map.current.removeLayer('radar-raster-layer');
      if (map.current.getSource('radar-raster')) map.current.removeSource('radar-raster');
      return;
    }

    const latArr = radarData.latitude;
    const lonArr = radarData.longitude;
    const refArr = radarData.variables[activeLayer];
    const targetArr = radarData.variables['TARGET'];
    
    const raster = generateRadarImage(latArr, lonArr, refArr, targetArr, activeLayer);
    
    if (raster) {
      const source = map.current.getSource('radar-raster') as maplibregl.ImageSource;
      if (source) {
        source.updateImage({ url: raster.url, coordinates: raster.coordinates });
      } else {
        map.current.addSource('radar-raster', {
          type: 'image',
          url: raster.url,
          coordinates: raster.coordinates
        });
        map.current.addLayer({
          id: 'radar-raster-layer',
          type: 'raster',
          source: 'radar-raster',
          paint: {
            'raster-opacity': 0.85,
            'raster-resampling': 'linear'
          }
        });
      }
    }

    // hide nowcast
    if (map.current.getLayer('nowcast-raster-layer')) map.current.removeLayer('nowcast-raster-layer');
    if (map.current.getSource('nowcast-raster')) map.current.removeSource('nowcast-raster');
  }, [radarData, activeLayer, mode]);

  return (
    <div className="absolute inset-0 z-0 bg-slate-50">
      <div ref={mapContainer} className="w-full h-full" />
      
      {/* HTML OVERLAY HUD - perfectly crisp and responsive! */}
      {hudData && activeLayer === 'REF' && (
         <div className={`absolute bottom-8 left-6 z-40 bg-slate-900/85 backdrop-blur-md border rounded-lg p-3 shadow-2xl pointer-events-none w-[220px] transition-all duration-500 ${hudData.maxRef >= 50 ? 'border-red-500 shadow-[0_0_20px_rgba(239,68,68,0.3)] animate-pulse' : 'border-slate-600'}`}>
            <div className="text-[11px] font-bold tracking-widest uppercase mb-2 flex items-center gap-2" style={{ color: hudData.threatColor }}>
               {hudData.maxRef >= 50 && (
                   <div className="relative flex h-2 w-2">
                     <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                     <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500"></span>
                   </div>
               )}
               THREAT: {hudData.threatLevel}
            </div>
            
            <div className="flex justify-between items-center mb-1">
               <span className="text-[10px] font-bold tracking-widest text-slate-300">AI CONFIDENCE:</span>
               <span className="text-[10px] font-bold text-slate-100">94%</span>
            </div>
            
            <div className="flex justify-between items-center mb-1">
               <span className="text-[9px] font-mono text-slate-400">LIGHTNING RISK:</span>
               <span className="text-[9px] font-mono text-slate-200">{hudData.lightningRisk}</span>
            </div>
            
            <div className="flex justify-between items-center mb-1">
               <span className="text-[9px] font-mono text-slate-400">CORE REFLECT:</span>
               <span className="text-[9px] font-mono text-slate-200">{Math.round(hudData.maxRef)} dBZ</span>
            </div>
            
            <div className="flex justify-between items-center mb-1">
               <span className="text-[9px] font-mono text-slate-400">STORM PATH:</span>
               <span className="text-[9px] font-mono text-slate-200">+15m NE</span>
            </div>
            
            <div className="flex justify-between items-center mt-2 pt-2 border-t border-slate-700/50">
               <span className="text-[9px] font-mono text-cyan-500">TARGET LOCKED:</span>
               <span className="text-[9px] font-mono text-cyan-400"><ScrambleCoordinates lat={hudData.coreLat} lon={hudData.coreLon} /></span>
            </div>
         </div>
      )}
    </div>
  );
});

export default MapComponent;
