# NPAAAD/SAFDZ–CLUP Harmonizer v2.8.1

Local Windows GIS application for harmonization and integration of NPAAAD/SAFDZ into CLUP.

## Main features
- NPAAAD/SAFDZ master CRS workflow
- ELU description mapping to AGR, BU, or Other/Ignore
- Land Cover 2025 integration
- Harmonization Decision field
- Poultry shapefile clipping and area identification
- NPAAAD and SAFDZ area matrices with official category descriptions
- Shapefile and Excel outputs
- Geometry validation/cleaning without geometry simplification
- Windows desktop shortcut and local login protection

## Windows installation
1. Download the release ZIP and extract it to a normal folder.
2. Run `INSTALL_AND_RUN.bat`.
3. Allow the first installation to download required Python packages.
4. Use the desktop shortcut created by the installer for later runs.

## Default local login
- Username: `ALRMS`
- Password: `ALRMS001`

For shared/public deployments, configure credentials and the Flask session secret using environment variables instead of relying on defaults.

## Version
v2.8.1 is the GitHub-ready packaging of the current approved Harmonizer build. Runtime GIS behavior is retained from the approved v2.7 line while repository hygiene/version metadata are updated for ongoing releases.
