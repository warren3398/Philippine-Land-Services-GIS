"""Publish validated nationwide GIS files to Cloudflare R2.

Usage: python scripts/publish_r2.py converted --dry-run
       python scripts/publish_r2.py converted --bucket YOUR_PRIVATE_BUCKET
Credentials are read from R2_ACCOUNT_ID, AWS_ACCESS_KEY_ID and
AWS_SECRET_ACCESS_KEY environment variables; never commit them.
"""
import argparse
import json
import os
from pathlib import Path


def build_plan(root):
    report_file = root / "validation_report.json"
    report = json.loads(report_file.read_text(encoding="utf-8"))
    if report.get("errors"):
        raise ValueError("Conversion has errors; upload blocked")
    datasets = report.get("datasets", [])
    if not datasets:
        raise ValueError("No converted datasets")
    files = []
    for entry in datasets:
        rel = Path(entry["file"])
        if rel.is_absolute() or ".." in rel.parts:
            raise ValueError("Unsafe output path")
        file = root / rel
        if not file.is_file() or not file.stat().st_size:
            raise ValueError("Missing or empty file: " + str(rel))
        files.append((file, "npaaad-safdz/v1/" + rel.as_posix()))
    files.append((report_file, "npaaad-safdz/v1/validation_report.json"))
    return files


def main():
    p = argparse.ArgumentParser()
    p.add_argument("output", type=Path)
    p.add_argument("--bucket")
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args()
    files = build_plan(a.output)
    for path, key in files:
        print(str(path), "->", key)
    if a.dry_run:
        print("Dry run: nothing uploaded")
        return
    if not a.bucket:
        p.error("--bucket required for upload")
    import boto3
    client = boto3.client(
        "s3",
        endpoint_url="https://" + os.environ["R2_ACCOUNT_ID"] + ".r2.cloudflarestorage.com",
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        region_name="auto",
    )
    for path, key in files:
        client.upload_file(str(path), a.bucket, key)
        print("Uploaded", key)


if __name__ == "__main__":
    main()
