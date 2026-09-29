export interface TrackPoint {
  leadTimeMin: number;
  lat: number;
  lon: number;
}

export interface SimulatedStormCell {
  id: string;
  lat: number;
  lon: number;
  intensity: number; // 0-100
  growthRate: number; // e.g. 5 per 10min
  motionDirection: number; // degrees
  motionSpeed: number; // km/h
  lightningActivity: 'LOW' | 'ELEVATED' | 'HIGH' | 'SEVERE';
  lightningFlashRate: number; // flashes per 5 min
  cloudTopTemp: number; // celsius
  coolingRate: number; // K/hr
  radarReflectivity: number; // dBZ
  cape: number; // J/kg
  cin: number; // J/kg
  windShear: number; // m/s
  lifecycleStage: 'FORMING' | 'DEVELOPING' | 'INTENSIFYING' | 'MATURE' | 'WEAKENING';
  threatZonePolygon: [number, number][]; // [lon, lat] array for polygon
  radiusKm: number;
  projectedTrack: TrackPoint[]; // discrete future points
}

export interface SimulationState {
  timeOffsetMin: number; // 0 to 60
  cells: SimulatedStormCell[];
  overallAgreement: 'LOW' | 'MODERATE' | 'HIGH';
  nwpSummary: {
    cape: number;
    cin: number;
    shear: number;
    rh: number;
    temp: number;
  }
}

// Helper to interpolate between two values
const lerp = (start: number, end: number, t: number) => start + (end - start) * t;

// Initial coordinates for SF-014 (Intensifying cell off Mumbai coast)
const START_LAT_014 = 18.85;
const START_LON_014 = 72.60;

const END_LAT_014 = 19.10;
const END_LON_014 = 72.85; // Moves Northeast towards Mumbai

export const getSimulationState = (timeOffsetMin: number): SimulationState => {
  // Normalize time between 0 and 1 (0 = NOW, 1 = +60 MIN)
  const t = Math.max(0, Math.min(1, timeOffsetMin / 60));
  
  // SF-014 (The primary threat cell)
  const intensity_014 = 75 + Math.sin(t * Math.PI) * 20; // Peaks at 95 around +30min
  const ref_014 = lerp(45, 65, Math.sin(t * Math.PI)); // Peaks at 65 dBZ
  const ctt_014 = lerp(-60, -78, Math.sin(t * Math.PI)); // Drops to -78C
  
  let lifecycle_014: SimulatedStormCell['lifecycleStage'] = 'DEVELOPING';
  if (t > 0.1 && t < 0.4) lifecycle_014 = 'INTENSIFYING';
  else if (t >= 0.4 && t < 0.7) lifecycle_014 = 'MATURE';
  else if (t >= 0.7) lifecycle_014 = 'WEAKENING';

  let lightning_014: SimulatedStormCell['lightningActivity'] = 'ELEVATED';
  if (intensity_014 > 85) lightning_014 = 'SEVERE';
  else if (intensity_014 > 70) lightning_014 = 'HIGH';

  const currentLat_014 = lerp(START_LAT_014, END_LAT_014, t);
  const currentLon_014 = lerp(START_LON_014, END_LON_014, t);
  const radius_014 = lerp(15, 30, Math.sin(t * Math.PI)); // Storm grows then shrinks

    // Calculate future track points
    const generateTrack = (lat: number, lon: number): TrackPoint[] => {
      // 38 km/h = ~0.63 km/min. In 15 mins = 9.5 km.
      // Direction 45 deg (NE).
      return [15, 30, 45, 60].map(lead => {
         const distKm = lead * (38 / 60);
         // approx lat/lon offset
         const latOffset = (distKm / 111) * Math.cos(45 * Math.PI / 180);
         const lonOffset = (distKm / 105) * Math.sin(45 * Math.PI / 180);
         return { leadTimeMin: lead, lat: lat + latOffset, lon: lon + lonOffset };
      });
    };
    
    // Generate a widening threat zone around the projected cell track
    const generateThreatZone = (lat: number, lon: number, track: TrackPoint[]): [number, number][] => {
      if (track.length === 0) return [];
      const endPt = track[track.length - 1];
      const startWidthLon = 15 / 105;
      const startWidthLat = 15 / 111;
      const endWidthLon = 40 / 105; // widens to 40km at the end
      const endWidthLat = 40 / 111;
      
      // Calculate perpendicular offsets for 45 deg (NW and SE)
      const dxSE = Math.cos(-45 * Math.PI / 180);
      const dySE = Math.sin(-45 * Math.PI / 180);
      const dxNW = Math.cos(135 * Math.PI / 180);
      const dyNW = Math.sin(135 * Math.PI / 180);

      // We make a cone from current position to +60 position
      return [
        [lon + dxNW * startWidthLon, lat + dyNW * startWidthLat], // Start NW
        [endPt.lon + dxNW * endWidthLon, endPt.lat + dyNW * endWidthLat], // End NW
        [endPt.lon + (endPt.lon - lon)*0.2, endPt.lat + (endPt.lat - lat)*0.2], // Tip (further NE)
        [endPt.lon + dxSE * endWidthLon, endPt.lat + dySE * endWidthLat], // End SE
        [lon + dxSE * startWidthLon, lat + dySE * startWidthLat], // Start SE
        [lon - (endPt.lon - lon)*0.1, lat - (endPt.lat - lat)*0.1], // Base (slightly SW)
        [lon + dxNW * startWidthLon, lat + dyNW * startWidthLat], // Close polygon
      ];
    };
    
    const track_014 = generateTrack(currentLat_014, currentLon_014);

  const cell_014: SimulatedStormCell = {
    id: 'SF-014',
    lat: currentLat_014,
    lon: currentLon_014,
    intensity: intensity_014,
    growthRate: (intensity_014 - (75 + Math.sin((t-0.1) * Math.PI) * 20)), // Rate of change
    motionDirection: 45, // NE
    motionSpeed: 38,
    lightningActivity: lightning_014,
    lightningFlashRate: Math.round(lerp(12, 45, Math.sin(t * Math.PI))),
    cloudTopTemp: ctt_014,
    coolingRate: t < 0.5 ? -8.1 : 2.5,
    radarReflectivity: ref_014,
    cape: lerp(2200, 1500, t),
    cin: lerp(-18, -45, t),
    windShear: lerp(21, 15, t),
    lifecycleStage: lifecycle_014,
    radiusKm: radius_014,
    projectedTrack: track_014,
    threatZonePolygon: generateThreatZone(currentLat_014, currentLon_014, track_014)
  };

  // SF-002 (A secondary weaker cell forming to the south)
  const currentLat_002 = lerp(18.20, 18.40, t);
  const currentLon_002 = lerp(72.70, 72.90, t);
  const intensity_002 = lerp(30, 60, t);
  
    const track_002 = generateTrack(currentLat_002, currentLon_002);

  const cell_002: SimulatedStormCell = {
    id: 'SF-002',
    lat: currentLat_002,
    lon: currentLon_002,
    intensity: intensity_002,
    growthRate: 3.5,
    motionDirection: 45,
    motionSpeed: 38,
    lightningActivity: intensity_002 > 50 ? 'ELEVATED' : 'LOW',
    lightningFlashRate: Math.round(lerp(2, 15, t)),
    cloudTopTemp: lerp(-30, -55, t),
    coolingRate: -4.2,
    radarReflectivity: lerp(25, 48, t),
    cape: lerp(1800, 1600, t),
    cin: lerp(-20, -30, t),
    windShear: 18,
    lifecycleStage: t < 0.5 ? 'FORMING' : 'DEVELOPING',
    radiusKm: lerp(8, 18, t),
    projectedTrack: track_002,
    threatZonePolygon: generateThreatZone(currentLat_002, currentLon_002, track_002)
  };

  return {
    timeOffsetMin,
    cells: [cell_014, cell_002],
    overallAgreement: intensity_014 > 80 ? 'HIGH' : 'MODERATE',
    nwpSummary: {
      cape: cell_014.cape,
      cin: cell_014.cin,
      shear: cell_014.windShear,
      rh: lerp(82, 88, Math.sin(t * Math.PI)),
      temp: lerp(29, 26, t)
    }
  };
};
