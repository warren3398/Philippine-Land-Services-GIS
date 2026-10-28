"""Discover and convert provincial NPAAAD/SAFDZ shapefiles from regional ZIPs.

Never silently ignore candidate shapefiles. Do not overwrite an existing
converted GeoPackage without explicit --overwrite.
"""
import argparse
import json
import re
import shutil
import tempfile
import zipfile
from pathlib import Path
import geopandas as gpd

EXTS = (".shp", ".shx", ".dbf", ".prj", ".cpg")
REQUIRED = (".shp", ".shx", ".dbf", ".prj")
FOLDER = re.compile(r"^(?P<stem>.+?)_(?P<kind>NPAAAD|SAFDZ)$", re.I)


def identify(name):
    parts = name.replace("\\", "/").split("/")
    if len(parts) < 3 or not parts[-1].lower().endswith(".shp"):
        return None
    match = FOLDER.fullmatch(parts[-2])
    if not match:
        return None
    province = parts[-3]
    stem, kind = match.group("stem"), match.group("kind").upper()
    if re.sub(r"[^a-z0-9]", "", province.lower()) != re.sub(r"[^a-z0-9]", "", stem.lower()):
        return None
    filename = Path(parts[-1]).stem
    expected = re.sub(r"[^a-z0-9]", "", (stem + "_" + kind).lower())
    actual = re.sub(r"[^a-z0-9]", "", filename.lower())
    # Accept numbered variants, e.g. APAYAO_NPAAAD1.shp.
    if not actual.startswith(expected) or not actual[len(expected):].isdigit() and actual != expected:
        return None
    slug = re.sub(r"[^a-z0-9]+", "-", province.lower()).strip("-")
    return province, slug, kind


def convert_archives(archives, output, overwrite=False):
    output.mkdir(parents=True, exist_ok=True)
    report = {"datasets": [], "errors": [], "skipped": [], "unmatched_shapefiles": [],
              "total_converted": 0}
    destinations = set()
    for archive in archives:
        with zipfile.ZipFile(archive) as z:
            members = {n.replace("\\", "/").lower(): n for n in z.namelist()}
            for shp in z.namelist():
                if not shp.lower().endswith(".shp"):
                    continue
                identity = identify(shp)
                if identity is None:
                    report["unmatched_shapefiles"].append({"archive": archive.name, "source": shp})
                    continue
                province, slug, kind = identity
                dest = output / slug / (kind.lower() + ".gpkg")
                key = (slug, kind)
                if key in destinations or (dest.exists() and not overwrite):
                    report["skipped"].append({"archive": archive.name, "source": shp,
                                              "reason": "Duplicate or output exists; overwrite disabled"})
                    continue
                destinations.add(key)
                prefix = shp[:-4]
                try:
                    with tempfile.TemporaryDirectory() as tmp:
                        local_stem = Path(prefix).name
                        for ext in EXTS:
                            source = members.get((prefix + ext).replace("\\", "/").lower())
                            if source is None:
                                if ext in REQUIRED:
                                    raise ValueError("Missing required " + ext)
                                continue
                            with z.open(source) as src, open(Path(tmp) / (local_stem + ext), "wb") as out:
                                shutil.copyfileobj(src, out)
                        frame = gpd.read_file(Path(tmp) / (local_stem + ".shp"))
                        if frame.empty or frame.crs is None:
                            raise ValueError("Empty layer or missing CRS")
                        if not frame.geometry.geom_type.isin(["Polygon", "MultiPolygon"]).all():
                            raise ValueError("Nonpolygon geometries present")
                        invalid = int((~frame.geometry.is_valid).sum())
                        if invalid:
                            raise ValueError(f"{invalid} invalid geometries")
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        with tempfile.TemporaryDirectory(dir=dest.parent) as staging:
                            candidate = Path(staging) / dest.name
                            frame.to_file(candidate, layer=kind.lower(), driver="GPKG", index=False)
                            candidate.replace(dest)
                        report["datasets"].append({
                            "region_archive": archive.name, "source": shp,
                            "province": province, "layer": kind, "features": len(frame),
                            "crs": str(frame.crs), "fields": list(frame.columns),
                            "file": str(dest.relative_to(output))
                        })
                        report["total_converted"] += 1
                except Exception as exc:
                    report["errors"].append({"archive": archive.name, "source": shp,
                                              "province": province, "layer": kind, "error": str(exc)})
    (output / "validation_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("archives", nargs="+", type=Path)
    parser.add_argument("--out", type=Path, default=Path("converted"))
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    summary = convert_archives(args.archives, args.out, overwrite=args.overwrite)
    print("Converted:", summary["total_converted"], "Errors:", len(summary["errors"]),
          "Unmatched shapefiles:", len(summary["unmatched_shapefiles"]),
          "Skipped:", len(summary["skipped"]))
