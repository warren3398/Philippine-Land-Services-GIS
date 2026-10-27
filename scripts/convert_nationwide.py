"""Convert every provincial NPAAAD and SAFDZ shapefile from regional ZIP archives.

Usage:
  python scripts/convert_nationwide.py LUZON.zip VISAYAS.zip MINDANAO.zip --out converted

This script never changes the source ZIP archives. Upload of output is a
separate operation, after checking validation_report.json.
"""
import argparse
import json
import re
import tempfile
import shutil
import zipfile
from pathlib import Path
import geopandas as gpd

PATTERN = re.compile(r"(?P<province>[^/]+)/(?P<stem>[^/]+)_(?P<kind>NPAAAD|SAFDZ)/(?P=stem)_(?P=kind)\.shp$", re.I)
EXTS = (".shp", ".shx", ".dbf", ".prj", ".cpg")

def convert_archives(archives, output):
    output.mkdir(parents=True, exist_ok=True)
    report = {"datasets": [], "errors": [], "total_converted": 0}
    for archive in archives:
        with zipfile.ZipFile(archive) as z:
            members = {name.lower(): name for name in z.namelist()}
            for shp in z.namelist():
                match = PATTERN.search(shp)
                if not match:
                    continue
                province = match.group("province")
                kind = match.group("kind").upper()
                prefix = shp[:-4]
                slug = re.sub(r"[^a-z0-9]+", "-", province.lower()).strip("-")
                try:
                    with tempfile.TemporaryDirectory() as tmp:
                        for ext in EXTS:
                            original = members.get((prefix + ext).lower())
                            if original is None:
                                if ext in (".shp", ".shx", ".dbf", ".prj"):
                                    raise ValueError("Missing required " + ext)
                                continue
                            with z.open(original) as source, open(Path(tmp) / (Path(prefix).name + ext), "wb") as dest:
                                shutil.copyfileobj(source, dest)
                        frame = gpd.read_file(Path(tmp) / (Path(prefix).name + ".shp"))
                        if frame.empty or frame.crs is None:
                            raise ValueError("Empty layer or missing CRS")
                        if not frame.geometry.geom_type.isin(["Polygon", "MultiPolygon"]).all():
                            raise ValueError("Nonpolygon geometries present")
                        invalid = int((~frame.geometry.is_valid).sum())
                        if invalid:
                            raise ValueError(str(invalid) + " invalid geometries")
                        folder = output / slug
                        folder.mkdir(exist_ok=True)
                        dest = folder / (kind.lower() + ".gpkg")
                        frame.to_file(dest, layer=kind.lower(), driver="GPKG", index=False)
                        report["datasets"].append({
                            "region_archive": archive.name,
                            "province": province,
                            "layer": kind,
                            "features": len(frame),
                            "crs": str(frame.crs),
                            "fields": list(frame.columns),
                            "file": str(dest.relative_to(output)),
                        })
                        report["total_converted"] += 1
                except Exception as exc:
                    report["errors"].append({"archive": archive.name, "province": province,
                                             "layer": kind, "error": str(exc)})
    (output / "validation_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("archives", nargs="+", type=Path)
    parser.add_argument("--out", type=Path, default=Path("converted"))
    args = parser.parse_args()
    summary = convert_archives(args.archives, args.out)
    print("Converted", summary["total_converted"], "datasets; errors", len(summary["errors"]))
