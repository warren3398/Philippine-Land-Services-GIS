"""Abra pilot: extract NPAAAD/SAFDZ from LUZON.zip to GeoPackages.
Usage: python scripts/convert_abra.py LUZON.zip --out output/abra
Requires geopandas, pyogrio. Does not alter the source archive.
"""
import argparse, json, re, tempfile, zipfile, shutil
from pathlib import Path
import geopandas as gpd

def main(src, out):
    out.mkdir(parents=True, exist_ok=True)
    report = {'province':'ABRA','status':'validation_required','layers':{}}
    with zipfile.ZipFile(src) as z:
        for kind in ('NPAAAD','SAFDZ'):
            hits=[n for n in z.namelist() if re.search(rf'(^|/)ABRA/ABRA_{kind}/ABRA_{kind}\.shp$',n,re.I)]
            if len(hits)!=1: raise ValueError(f'{kind}: expected 1 SHP, found {len(hits)}')
            folder=hits[0].rsplit('/',1)[0]+'/'
            with tempfile.TemporaryDirectory() as temp:
                for name in z.namelist():
                    base=Path(name).name
                    if name.startswith(folder) and base.lower().startswith(f'abra_{kind.lower()}.') and Path(base).suffix.lower() in ('.shp','.shx','.dbf','.prj','.cpg'):
                        with z.open(name) as f, open(Path(temp)/base,'wb') as g: shutil.copyfileobj(f,g)
                frame=gpd.read_file(Path(temp)/Path(hits[0]).name)
                if frame.crs is None or frame.empty: raise ValueError(f'{kind}: missing CRS or empty layer')
                dest=out/f'abra_{kind.lower()}.gpkg'
                frame.to_file(dest,layer=kind.lower(),driver='GPKG',index=False)
                report['layers'][kind]={'features':len(frame),'crs':str(frame.crs),'fields':list(frame.columns),'invalid_geometry':int((~frame.geometry.is_valid).sum()),'file':dest.name,'size_bytes':dest.stat().st_size}
    (out/'manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('archive',type=Path);p.add_argument('--out',type=Path,default=Path('output/abra'))
    a=p.parse_args();main(a.archive,a.out)
