# Philippine Land Services GIS Portal v2.0 (unified)

One Python ASGI application. No separate frontend/backend folders or URL configuration.

## Start
1. Install Python 3.11+.
2. Run `pip install -r requirements.txt`.
3. If using code-only ZIP, copy your `Slope_utm.shp/.shx/.dbf/.prj/.CPG` into `data/slope/`.
4. Run `python -m uvicorn app:app --host 127.0.0.1 --port 8000` (or `RUN_WEBSITE.bat` on Windows).
5. Visit `http://127.0.0.1:8000/`.

Routes: `/` dashboard, `/eo79/` EO79 v36, `/harmonizer/` Harmonizer v2.8.1, `/api/slope/clip` slope processing. The original EO79 and Harmonizer logic is retained, with the Harmonizer mounted as a Flask WSGI application within FastAPI. Climate module is a placeholder; Erosion/Flooding has been removed.

## Known limitations
- This is a **single Python server**, not a static GitHub Pages deployment. GitHub Pages alone cannot run the application.
- Slope parcel clipping requires the nationwide slope files in `data/slope/`.
- Municipality selection needs a separate official admin boundary GeoJSON at `data/admin_boundaries.geojson` containing region/province/municipality columns.
- PDF output is an area report, not a cartographic map layout.
- EO79 v36 uses its original client-side data handling; integration is navigation/server consolidation, not a rewrite of EO79 processing.
- Harmonizer authentication remains its original login; configure `ALRMS_SESSION_SECRET`, `ALRMS_USERNAME`, and `ALRMS_PASSWORD_HASH` before public deployment. Do not use bundled default credentials or expose the server without authentication, rate limits and upload quotas.
- No live end-to-end deployment verification has been performed.
