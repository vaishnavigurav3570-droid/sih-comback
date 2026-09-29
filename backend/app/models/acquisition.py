from dataclasses import dataclass
from typing import List, Optional

@dataclass
class RadarAcquisitionRequest:
    status: str
    source: str
    stations: List[str]
    requested_window_ist: List[str]
    preferred_times_ist: List[str]
    format: Optional[str]
    access_route: Optional[str]

@dataclass
class LightningAcquisitionRequest:
    status: str
    source: str
    requested_window_ist: List[str]
    format: Optional[str]
    access_route: Optional[str]

@dataclass
class TargetAcquisitionManifest:
    event_date: str
    region: str
    radar: RadarAcquisitionRequest
    lightning: LightningAcquisitionRequest
    scientific_status: str

    @classmethod
    def from_dict(cls, data: dict) -> 'TargetAcquisitionManifest':
        radar = RadarAcquisitionRequest(**data['radar'])
        lightning = LightningAcquisitionRequest(**data['lightning'])
        return cls(
            event_date=data['event_date'],
            region=data['region'],
            radar=radar,
            lightning=lightning,
            scientific_status=data['scientific_status']
        )
