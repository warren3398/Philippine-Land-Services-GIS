# Cloudflare R2 nationwide catalog integration

This adds a **read-only inventory endpoint**, not a finished map generator.

## Server configuration

Configure these as **server-side secrets** on the Flask hosting platform (never in GitHub or browser JavaScript):

- `R2_ACCESS_KEY_ID`: R2 S3 API token access key ID with Object Read access
- `R2_SECRET_ACCESS_KEY`: matching R2 S3 API token secret
- `R2_ACCOUNT_ID`: optional; defaults to the configured Cloudflare account ID

Existing Flask login is required to call the catalog. The private bucket is `npaaad-safdz-data`.

## API

`GET /api/nationwide/catalog`

Optional filters: `?island=luzon&province=mountain-province`. The response lists exact R2 keys, sizes, validation status, and the provisional SAFDZ warning. It never returns secrets or signs downloads.

The inventory scans `nationwide/{luzon|visayas|mindanao}/{province}/{npaaad|safdz}.gpkg` and `provisional/.../safdz.gpkg`. Provisional files remain separate from validated datasets and are marked `classification_analysis_allowed: false`.

## Next development

- Add administrative boundary database and polygon selection
- Add server-side GPKG download, geometry validation, spatial clipping, and CRS-safe exports
- Exclude unverified Mountain Province classifications from classification-based area summaries
- Implement request limits, background jobs, caching, and downloadable map layouts
- Test the endpoint on a deployed Flask server with secrets configured

Do not deploy with the repository's local default credentials; configure `ALRMS_USERNAME`, `ALRMS_PASSWORD_HASH`, and `ALRMS_SESSION_SECRET` securely before any public deployment.
