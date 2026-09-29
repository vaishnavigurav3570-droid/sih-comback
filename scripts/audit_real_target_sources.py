import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.pipeline.data_source_audit import DataSourceAuditor

def main():
    auditor = DataSourceAuditor()
    auditor.audit_local_files(r"C:\Users\Vedant\Documents\mosdac")
    auditor.audit_mosdac_api()

    print("==================================================")
    print("REAL TARGET DATA CANDIDATE MATRIX")
    print("==================================================")
    report = auditor.get_report()
    for entry in report:
        print(f"Source: {entry['source']}")
        print(f"Product: {entry['product']}")
        print(f"Modality: {entry['modality']}")
        print(f"Provenance: {entry['REAL/SYNTHETIC/UNKNOWN']}")
        print(f"Format: {entry['format']}")
        print(f"Date Coverage: {entry['date coverage']}")
        print(f"Time Resolution: {entry['time resolution']}")
        print(f"Spatial Resolution: {entry['spatial resolution']}")
        print(f"Geographic Coverage: {entry['geographic coverage']}")
        print(f"Variables: {entry['variables']}")
        print(f"Target Suitability: {entry['target suitability']}")
        print(f"Input Suitability: {entry['input suitability']}")
        print(f"29-May-2025 Availability: {entry['29-May-2025 availability']}")
        print(f"12:00-15:00 Compatibility: {entry['12:00–15:00 compatibility']}")
        print(f"Access Status: {entry['access status']}")
        print(f"Limitations: {entry['limitations']}")
        print("-" * 50)

if __name__ == "__main__":
    main()
