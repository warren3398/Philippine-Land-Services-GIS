"""Read-only, authenticated inventory of nationwide GeoPackages in private Cloudflare R2."""
import os
from collections import defaultdict
from flask import Blueprint, jsonify, request, session

r2_catalog = Blueprint("r2_catalog", __name__, url_prefix="/api/nationwide")
BUCKET = "npaaad-safdz-data"
ACCOUNT_ID = "0e04aa79dc466dcc79933a8293463a9a"
VALID_LAYERS = {"npaaad.gpkg": "npaaad", "safdz.gpkg": "safdz"}
VALID_ISLANDS = {"luzon", "visayas", "mindanao"}


def _client():
    import boto3
    from botocore.config import Config
    key = os.environ.get("R2_ACCESS_KEY_ID")
    secret = os.environ.get("R2_SECRET_ACCESS_KEY")
    if not key or not secret:
        raise RuntimeError("R2 credentials are not configured on the server")
    return boto3.client(
        "s3",
        endpoint_url=f"https://{os.environ.get('R2_ACCOUNT_ID', ACCOUNT_ID)}.r2.cloudflarestorage.com",
        aws_access_key_id=key,
        aws_secret_access_key=secret,
        region_name="auto",
        config=Config(signature_version="s3v4", retries={"max_attempts": 3}),
    )


def _objects(client, prefix):
    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=BUCKET, Prefix=prefix):
        for obj in page.get("Contents", []):
            yield obj


@r2_catalog.before_request
def require_login():
    if not session.get("logged_in"):
        return jsonify(error="Login required"), 401


@r2_catalog.get("/catalog")
def catalog():
    """List dataset presence, not a spatial intersection or a completed GIS analysis."""
    island = request.args.get("island", "").strip().lower()
    province = request.args.get("province", "").strip().lower()
    if island and island not in VALID_ISLANDS:
        return jsonify(error="Invalid island"), 400
    if province and (not island or not province.replace("-", "").isalnum()):
        return jsonify(error="Specify a valid island and province slug"), 400
    prefix = "nationwide/" + (island + "/" if island else "") + (province + "/" if province else "")
    try:
        client = _client()
        entries = defaultdict(lambda: {"npaaad": None, "safdz": None, "provisional_safdz": None})
        for obj in _objects(client, prefix):
            parts = obj["Key"].split("/")
            if len(parts) != 4 or parts[0] != "nationwide" or parts[1] not in VALID_ISLANDS:
                continue
            layer = VALID_LAYERS.get(parts[3])
            if not layer:
                continue
            row = entries[(parts[1], parts[2])]
            row[layer] = {"key": obj["Key"], "size_bytes": obj["Size"], "status": "validated"}
        # Provisional datasets must never silently replace validated datasets.
        for obj in _objects(client, "provisional/" + (island + "/" if island else "") + (province + "/" if province else "")):
            parts = obj["Key"].split("/")
            if len(parts) == 4 and parts[0] == "provisional" and parts[1] in VALID_ISLANDS and parts[3] == "safdz.gpkg":
                entries[(parts[1], parts[2])]["provisional_safdz"] = {
                    "key": obj["Key"], "size_bytes": obj["Size"],
                    "status": "provisional", "classification_analysis_allowed": False,
                    "warning": "Unverified classes and incomplete feature recovery; do not use for classification-based computations",
                }
        result = [
            {"island": isl, "province": prov, **layers}
            for (isl, prov), layers in sorted(entries.items())
        ]
        return jsonify(bucket=BUCKET, datasets=result, provinces=len(result),
                       notice="Inventory only. Municipality/barangay clipping requires a separate spatial service.")
    except RuntimeError as exc:
        return jsonify(error=str(exc)), 503
    except Exception:
        return jsonify(error="R2 inventory unavailable; check server configuration and permissions"), 502
