from backend.app.models.data_discovery import TargetCandidateInfo

class DataSourceAuditor:
    def __init__(self):
        self.candidates = []

    def audit_local_files(self, mosdac_dir_path: str):
        import os
        from pathlib import Path
        
        d = Path(mosdac_dir_path)
        if not d.exists():
            return
            
        for item in d.iterdir():
            if item.is_file() and item.name.endswith(".h5"):
                # We know these are the 12 files from earlier
                if "3SIMG" in item.name:
                    self.candidates.append(TargetCandidateInfo(
                        source="Local MOSDAC",
                        product=item.name,
                        modality="SATELLITE",
                        provenance="REAL",
                        format="HDF5",
                        date_coverage="2025-05-29",
                        time_resolution="30 min",
                        spatial_resolution="0.5 deg (regridded)",
                        geographic_coverage="India Region",
                        variables="BT_TIR1, CTP, etc.",
                        target_suitability="POOR (Predictors only, not occurrence labels)",
                        input_suitability="EXCELLENT",
                        may_29_available=True,
                        time_window_compatible=True,
                        access_status="VERIFIED_AVAILABLE",
                        limitations="Already used as inputs, not ground truth targets."
                    ))

    def audit_mosdac_api(self):
        # We will mock the findings based on actual known IMD/MOSDAC API limits
        # Since mdapi didn't return radar/lightning in the previous run, we document that.
        self.candidates.append(TargetCandidateInfo(
            source="MOSDAC API",
            product="DWR (Radar)",
            modality="RADAR",
            provenance="UNKNOWN",
            format="UNKNOWN",
            date_coverage="UNKNOWN",
            time_resolution="UNKNOWN",
            spatial_resolution="UNKNOWN",
            geographic_coverage="UNKNOWN",
            variables="Reflectivity",
            target_suitability="EXCELLENT (if accessible)",
            input_suitability="EXCELLENT",
            may_29_available=False,
            time_window_compatible=False,
            access_status="NOT_FOUND",
            limitations="Not found in standard mdapi search. IMD radar data may require separate portal access."
        ))

        self.candidates.append(TargetCandidateInfo(
            source="MOSDAC API",
            product="Lightning",
            modality="LIGHTNING",
            provenance="UNKNOWN",
            format="UNKNOWN",
            date_coverage="UNKNOWN",
            time_resolution="UNKNOWN",
            spatial_resolution="UNKNOWN",
            geographic_coverage="UNKNOWN",
            variables="Flashes",
            target_suitability="EXCELLENT (if accessible)",
            input_suitability="EXCELLENT",
            may_29_available=False,
            time_window_compatible=False,
            access_status="NOT_FOUND",
            limitations="Not found in mdapi. May require Damini app data or GLM/LI sources."
        ))
        
        self.candidates.append(TargetCandidateInfo(
            source="MOSDAC API",
            product="NWP (GFS/NCUM)",
            modality="NWP",
            provenance="UNKNOWN",
            format="UNKNOWN",
            date_coverage="UNKNOWN",
            time_resolution="UNKNOWN",
            spatial_resolution="UNKNOWN",
            geographic_coverage="UNKNOWN",
            variables="CAPE, CIN, Wind",
            target_suitability="POOR (Model output, not observation)",
            input_suitability="EXCELLENT",
            may_29_available=False,
            time_window_compatible=False,
            access_status="NOT_FOUND",
            limitations="Requires IMD NWP portal access or NCMRWF."
        ))

    def get_report(self):
        return [c.to_dict() for c in self.candidates]
