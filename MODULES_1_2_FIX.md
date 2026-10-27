# Modules 1 and 2 Integration Fix

## Harmonizer
Fixed hardcoded root-relative CSS, logos, login/logout, inspect, processing, progress and download URLs to work under `/harmonizer/` in the unified Python server. GIS decision engine unchanged.

## EO79
The original v36 is an inline-script application, not an app.js application. It is served at `/eo79/index.html` and its `data/` directory resolves relative to that URL. Nationwide province data files must be provided separately: this package includes only `data/index.json`, not nationwide province GeoJSON files. Nationwide analysis will not work until those province data files are supplied.

## Launch
Run `RUN_WEBSITE.bat`, then visit `http://127.0.0.1:8000/`. Do not open index.html directly from File Explorer.

## Validation limits
Source paths were inspected and Python syntax checked. Full browser tests and GIS processing tests have not been performed.
