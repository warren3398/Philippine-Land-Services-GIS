"""Parcel-bounded SAFDZ reader. Stream provincial concatenated gzip GeoJSON from R2."""
import gzip
import json
import os
import tempfile
from urllib.parse import quote
from urllib.request import Request, urlopen
import ijson
from shapely.geometry import shape, box

R2 = 'https://pub-97016449b28c4233ac1dfb3dee40477a.r2.dev'
MAX_COMPRESSED_BYTES = 600 * 1024 * 1024
MAX_RETURNED_FEATURES = 25000

def _read(key):
    req = Request(R2 + '/' + quote(key, safe='/'), headers={'User-Agent':'PLS-GIS/1.0','Accept-Encoding':'identity'})
    return urlopen(req, timeout=60)

def _json(key):
    with _read(key) as r:
        return json.load(r)

def filtered_province(province, bbox):
    if not isinstance(province,str) or not province or any(x not in 'abcdefghijklmnopqrstuvwxyz0123456789-_' for x in province):
        raise ValueError('Invalid province')
    if not isinstance(bbox,list) or len(bbox)!=4:
        raise ValueError('Invalid parcel bounds')
    coords = [float(x) for x in bbox]
    if not (-180<=coords[0]<coords[2]<=180 and -90<=coords[1]<coords[3]<=90):
        raise ValueError('Invalid geographic bounds; parcel must be WGS84')
    index = _json('index.json')
    entry = next((p for p in index.get('provinces',[]) if str(p.get('province','')).lower().replace(' ','-') == province), None)
    if not entry:
        raise ValueError('Province not available in SAFDZ index')
    manifest_path = entry['path']
    manifest = _json(manifest_path)
    parts = manifest.get('parts') or manifest.get('chunks') or manifest.get('files')
    if not isinstance(parts,list) or not parts:
        raise ValueError('Missing provincial data parts')
    directory = manifest_path.rsplit('/',1)[0]+'/'
    query = box(*coords)
    features = []
    bytes_seen = 0
    # Store compressed bytes on disk; parse gzip and features incrementally.
    with tempfile.TemporaryFile() as compressed:
        for part in parts:
            name = part if isinstance(part,str) else next((part.get(k) for k in ('path','file','filename','name','url') if part.get(k)),None)
            if not isinstance(name,str) or name.startswith(('http:','https:','/')) or '..' in name.split('/'):
                raise ValueError('Invalid provincial part path')
            if name.startswith('data/'):
                name = name[5:]
            key = name if name.startswith(directory) else directory + name
            with _read(key) as response:
                while True:
                    chunk = response.read(1024*1024)
                    if not chunk: break
                    bytes_seen += len(chunk)
                    if bytes_seen > MAX_COMPRESSED_BYTES:
                        raise ValueError('Province exceeds compressed size limit')
                    compressed.write(chunk)
        compressed.seek(0)
        with gzip.GzipFile(fileobj=compressed,mode='rb') as unzipped:
            for feature in ijson.items(unzipped,'features.item',use_float=True):
                geometry = feature.get('geometry')
                if not geometry: continue
                try:
                    if shape(geometry).intersects(query):
                        features.append(feature)
                except (ValueError,TypeError):
                    continue
                if len(features)>MAX_RETURNED_FEATURES:
                    raise ValueError('Too many matching SAFDZ features; use a smaller parcel')
    return {'type':'FeatureCollection','features':features}
