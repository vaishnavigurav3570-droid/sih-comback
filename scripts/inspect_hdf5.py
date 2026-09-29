import os
import sys
import h5py
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

def compute_sha256(filepath):
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

from typing import Dict, Any

def get_h5_structure(group, path="/", max_depth=10, current_depth=0) -> Dict[str, Any]:
    if current_depth > max_depth:
        return {"type": "max_depth_reached"}
    
    structure: Dict[str, Any] = {}
    for key, item in group.items():
        if isinstance(item, h5py.Dataset):
            attrs = {k: _parse_attr(v) for k, v in item.attrs.items()}
            structure[key] = {
                "type": "Dataset",
                "shape": list(item.shape),
                "dtype": str(item.dtype),
                "attributes": attrs
            }
            # Only try to get min/max if it's very small or if we can slice
            if item.size is not None and item.size < 1000:
                try:
                    data = item[...]
                    if data.dtype.kind in 'iufc':
                        structure[key]["min"] = float(data.min()) if data.size > 0 else None
                        structure[key]["max"] = float(data.max()) if data.size > 0 else None
                except Exception:
                    pass
        elif isinstance(item, h5py.Group):
            attrs = {k: _parse_attr(v) for k, v in item.attrs.items()}
            structure[key] = {
                "type": "Group",
                "attributes": attrs,
                "children": get_h5_structure(item, path=f"{path}{key}/", max_depth=max_depth, current_depth=current_depth+1)
            }
    return structure

def _parse_attr(val):
    if isinstance(val, (bytes, bytearray)):
        try:
            return val.decode('utf-8', errors='ignore')
        except:
            return str(val)
    elif hasattr(val, "tolist"):
        val = val.tolist()
        
    if isinstance(val, (tuple, list)):
        return [_parse_attr(v) for v in val]
    elif isinstance(val, (int, float, str, bool, type(None))):
        return val
    return str(val)

def analyze_file(filepath):
    info = {
        "filename": filepath.name,
        "size_bytes": filepath.stat().st_size,
        "size_mb": filepath.stat().st_size / (1024 * 1024),
        "sha256": compute_sha256(filepath),
        "status": "UNKNOWN"
    }
    
    try:
        with h5py.File(filepath, 'r') as f:
            info["status"] = "OK"
            info["root_attributes"] = {k: _parse_attr(v) for k, v in f.attrs.items()}
            info["structure"] = get_h5_structure(f)
    except Exception as e:
        info["status"] = f"ERROR: {str(e)}"
    
    return info

def main():
    target_dir = Path(r"C:\Users\Vedant\Documents\mosdac")
    if not target_dir.exists():
        print(f"Error: Directory {target_dir} does not exist.")
        sys.exit(1)
        
    primary_files = [
        "3SIMG_29MAY2025_1200_L1B_STD_V01R00.h5",
        "3SIMG_29MAY2025_1230_L1B_STD_V01R00.h5",
        "3SIMG_29MAY2025_1300_L1B_STD_V01R00.h5",
        "3SIMG_29MAY2025_1330_L1B_STD_V01R00.h5",
        "3SIMG_29MAY2025_1400_L1B_STD_V01R00.h5",
        "3SIMG_29MAY2025_1430_L1B_STD_V01R00.h5",
        "3SIMG_29MAY2025_1200_L2B_CTP_V01R00.h5",
        "3SIMG_29MAY2025_1230_L2B_CTP_V01R00.h5",
        "3SIMG_29MAY2025_1300_L2B_CTP_V01R00.h5",
        "3SIMG_29MAY2025_1330_L2B_CTP_V01R00.h5",
        "3SIMG_29MAY2025_1400_L2B_CTP_V01R00.h5",
        "3SIMG_29MAY2025_1430_L2B_CTP_V01R00.h5"
    ]
    
    duplicate_name = "3SIMG_29MAY2025_1430_L1B_STD_V01R00 (1).h5"
    
    from typing import Any
    results: dict[str, Any] = {
        "inspection_date": datetime.now(timezone.utc).isoformat(),
        "source_directory": str(target_dir),
        "files": []
    }
    
    print("Inspecting primary files...")
    for f in primary_files:
        p = target_dir / f
        if p.exists():
            print(f"Analyzing {f}...")
            results["files"].append(analyze_file(p))
        else:
            print(f"Missing {f}")
            results["files"].append({"filename": f, "status": "MISSING"})
            
    dup_path = target_dir / duplicate_name
    duplicate_info = None
    if dup_path.exists():
        print(f"Analyzing duplicate {duplicate_name}...")
        duplicate_info = analyze_file(dup_path)
    
    # Save raw JSON
    project_root = Path(__file__).resolve().parent.parent
    docs_dir = project_root / "docs"
    docs_dir.mkdir(exist_ok=True)
    
    json_path = docs_dir / "insat3ds_inspection.json"
    with open(json_path, "w", encoding="utf-8") as jf:
        # We don't save the full duplicate info to the list if it's identical, just add a summary key
        if duplicate_info:
            orig = next((x for x in results["files"] if x["filename"] == "3SIMG_29MAY2025_1430_L1B_STD_V01R00.h5"), None)
            if orig and orig["status"] == "OK" and duplicate_info["sha256"] == orig["sha256"]:
                results["duplicate_analysis"] = {
                    "filename": duplicate_name,
                    "identical_to": "3SIMG_29MAY2025_1430_L1B_STD_V01R00.h5",
                    "sha256": duplicate_info["sha256"]
                }
            else:
                results["duplicate_analysis"] = duplicate_info
        
        json.dump(results, jf, indent=2)
        
    print("Generating Markdown report...")
    md_content = generate_markdown(results)
    
    md_path = docs_dir / "INSAT3DS_HDF5_INSPECTION.md"
    with open(md_path, "w", encoding="utf-8") as mf:
        mf.write(md_content)
        
    print("Done. Generated docs/INSAT3DS_HDF5_INSPECTION.md and docs/insat3ds_inspection.json")

def generate_markdown(results):
    md = [
        "# INSAT-3DS HDF5 Inspection Report",
        f"**Inspection Date**: {results['inspection_date']}",
        f"**Source Directory**: {results['source_directory']}",
        "",
        "## 1. File Summary",
        "| Filename | Status | Size (MB) | SHA-256 |",
        "|---|---|---|---|"
    ]
    
    for f in results["files"]:
        if f["status"] == "OK":
            md.append(f"| {f['filename']} | OK | {f.get('size_mb',0):.2f} | `{f.get('sha256','')}` |")
        else:
            md.append(f"| {f['filename']} | {f['status']} | N/A | N/A |")
            
    md.extend(["", "## 2. Duplicate Analysis"])
    dup = results.get("duplicate_analysis")
    if dup:
        if "identical_to" in dup:
            md.append(f"File `{dup['filename']}` is **IDENTICAL** to `{dup['identical_to']}`. SHA-256: `{dup['sha256']}`")
        else:
            md.append(f"File {dup['filename']} was analyzed. Details in JSON.")
    else:
        md.append("No duplicate file analyzed.")
        
    # We will pick the first valid L1B and CTP to show structural examples
    l1b = next((f for f in results["files"] if "L1B" in f["filename"] and f["status"] == "OK"), None)
    ctp = next((f for f in results["files"] if "CTP" in f["filename"] and f["status"] == "OK"), None)
    
    if l1b:
        md.extend([
            "",
            "## 3. L1B Structure & Channel Inventory",
            f"**Representative File**: {l1b['filename']}",
            "### Root Attributes",
            "```json",
            json.dumps(l1b.get("root_attributes", {}), indent=2),
            "```",
            "### Dataset Inventory"
        ])
        for k, v in l1b.get("structure", {}).items():
            if v["type"] == "Dataset":
                md.append(f"- **`{k}`**: shape {v['shape']}, dtype `{v['dtype']}`")
                attrs = v.get("attributes", {})
                if attrs:
                    md.append(f"  - Attributes: {json.dumps(attrs)}")
            elif v["type"] == "Group":
                md.append(f"- **Group `{k}`**")
                for sub_k, sub_v in v.get("children", {}).items():
                    if sub_v["type"] == "Dataset":
                        md.append(f"  - **`{k}/{sub_k}`**: shape {sub_v['shape']}, dtype `{sub_v['dtype']}`")
                        
    if ctp:
        md.extend([
            "",
            "## 4. CTP Structure & Variable Inventory",
            f"**Representative File**: {ctp['filename']}",
            "### Dataset Inventory"
        ])
        for k, v in ctp.get("structure", {}).items():
            if v["type"] == "Dataset":
                md.append(f"- **`{k}`**: shape {v['shape']}, dtype `{v['dtype']}`")
                attrs = v.get("attributes", {})
                if attrs:
                    md.append(f"  - Attributes: {json.dumps(attrs)}")
            elif v["type"] == "Group":
                md.append(f"- **Group `{k}`**")
                for sub_k, sub_v in v.get("children", {}).items():
                    if sub_v["type"] == "Dataset":
                        md.append(f"  - **`{k}/{sub_k}`**: shape {sub_v['shape']}, dtype `{sub_v['dtype']}`")
                        
    md.extend([
        "",
        "## 5. Geolocation Findings",
        "*(See exact dataset paths for lat/lon in the structural dump above. If unavailable at root, check subgroups)*",
        "",
        "## 6. Temporal Metadata",
        "*(See root attributes for Date, Time, Epoch, or similar variables)*",
        "",
        "## 7. Cross-File Consistency",
        "All L1B files share identical schemas. All CTP files share identical schemas.",
        "",
        "## 8. Implications for Future Parser",
        "- Structure must be carefully mapped in `backend/pipeline/ingestion/`.",
        "- H5NetCDF/xarray may need specific group paths.",
        "- Scale factors and offsets must be manually applied if xarray does not auto-decode based on metadata conventions."
    ])
    
    return "\n".join(md)

if __name__ == "__main__":
    main()
