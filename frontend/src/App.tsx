import { useState, useEffect } from 'react';
import { CloudLightning, Activity, ShieldAlert, Info } from 'lucide-react';
import MapComponent from './MapComponent';

// Interface matching our Pydantic model
interface ForecastProduct {
  forecast_id: string;
  created_at: string;
  valid_from: string;
  region: any;
  grid_forecasts: any[];
  sensor_health: Record<string, any>;
  data_sources_used: string[];
  model_version: string;
  is_demo_mode: boolean;
  warnings: string[];
  explanation: string | null;
}

export default function App() {
  const [forecast, setForecast] = useState<ForecastProduct | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeLeadTime, setActiveLeadTime] = useState<number>(15);

  useEffect(() => {
    const fetchNowcast = async () => {
      try {
        setLoading(true);
        // We fetch the demo data directly from our FastAPI backend
        const res = await fetch('http://localhost:8000/api/v1/forecast/now?mode=demo');
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        const data = await res.json();
        setForecast(data);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchNowcast();
    
    // Auto-refresh every 5 minutes in a real system
    const interval = setInterval(fetchNowcast, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const leadTimes = [15, 30, 60, 90];

  return (
    <div className="relative w-screen h-screen overflow-hidden bg-slate-950 text-slate-100 font-sans">
      {/* Background Map Layer */}
      <MapComponent gridForecasts={forecast?.grid_forecasts || []} />

      {/* UI Overlay - Glassmorphism */}
      <div className="absolute inset-0 pointer-events-none p-6 flex flex-col justify-between">
        
        {/* Top Header Area */}
        <div className="flex justify-between items-start pointer-events-auto">
          {/* Branding & Status */}
          <div className="backdrop-blur-xl bg-slate-900/60 border border-slate-700/50 rounded-2xl p-5 shadow-2xl flex flex-col gap-2 max-w-sm">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-indigo-500/20 rounded-lg border border-indigo-500/30 text-indigo-400">
                <CloudLightning size={24} />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white tracking-tight">StormFusion AI</h1>
                <p className="text-xs text-indigo-300 font-medium tracking-wide uppercase">Nowcasting System Prototype</p>
              </div>
            </div>
            
            {forecast?.is_demo_mode && (
              <div className="mt-2 inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-amber-500/10 border border-amber-500/20 text-amber-400 text-xs font-semibold w-max">
                <ShieldAlert size={14} />
                DEMO MODE (SYNTHETIC DATA)
              </div>
            )}
          </div>

          {/* Time & Controls */}
          <div className="backdrop-blur-xl bg-slate-900/60 border border-slate-700/50 rounded-2xl p-2 shadow-2xl flex gap-1">
            {leadTimes.map((lt) => (
              <button
                key={lt}
                onClick={() => setActiveLeadTime(lt)}
                className={`px-4 py-2 rounded-xl text-sm font-semibold transition-all duration-300 ${
                  activeLeadTime === lt 
                    ? 'bg-indigo-500 text-white shadow-[0_0_15px_rgba(99,102,241,0.5)]' 
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                }`}
              >
                +{lt} min
              </button>
            ))}
          </div>
        </div>

        {/* Bottom Area */}
        <div className="flex justify-between items-end pointer-events-auto">
          
          {/* Loading / Error / Explanation */}
          <div className="backdrop-blur-xl bg-slate-900/70 border border-slate-700/50 rounded-2xl p-5 shadow-2xl max-w-md w-full">
            {loading ? (
              <div className="flex items-center gap-3 text-indigo-400 animate-pulse">
                <Activity size={20} className="animate-spin-slow" />
                <span className="text-sm font-medium">Running Prediction Pipeline...</span>
              </div>
            ) : error ? (
              <div className="text-red-400 text-sm flex items-start gap-2">
                <ShieldAlert size={18} className="shrink-0 mt-0.5" />
                <p>Failed to connect to backend API: {error}</p>
              </div>
            ) : (
              <div className="flex flex-col gap-3">
                <div className="flex items-center gap-2 text-slate-300 border-b border-slate-700/50 pb-3">
                  <Info size={18} className="text-indigo-400" />
                  <h3 className="text-sm font-semibold">System Insights</h3>
                </div>
                <p className="text-sm text-slate-400 leading-relaxed">
                  {forecast?.explanation || "No explanation provided by the model."}
                </p>
              </div>
            )}
          </div>
          
          {/* Legend / Stats */}
          {!loading && !error && (
            <div className="backdrop-blur-xl bg-slate-900/70 border border-slate-700/50 rounded-2xl p-4 shadow-2xl flex gap-6">
              <div className="flex flex-col gap-1 text-center">
                <span className="text-3xl font-bold text-white tracking-tighter">
                  {forecast?.grid_forecasts?.length || 0}
                </span>
                <span className="text-xs text-slate-400 font-medium uppercase tracking-wider">Active Cells</span>
              </div>
              <div className="w-px bg-slate-700/50"></div>
              <div className="flex flex-col justify-center gap-2 text-xs text-slate-300">
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-red-500 shadow-[0_0_10px_rgba(239,68,68,0.5)]"></span>
                  High Risk (&gt;75%)
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-amber-500 shadow-[0_0_10px_rgba(245,158,11,0.5)]"></span>
                  Medium Risk
                </div>
              </div>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
