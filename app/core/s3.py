import os
import json
import boto3
from datetime import datetime

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")

s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

def upload_json_to_s3(folder: str, filename: str, data: dict):
    key = f"{folder}/{filename}"

    s3.put_object(
        Bucket=AWS_S3_BUCKET,
        Key=key,
        Body=json.dumps(data, indent=2),
        ContentType="application/json"
    )

    return key


def backup_dacum_card(session_id: str, payload: dict):
    filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.json"

    return upload_json_to_s3(
        folder=f"dacum-cards/{session_id}",
        filename=filename,
        data=payload
    )


def backup_cos_structure(project_id: str, payload: dict):
    filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.json"

    return upload_json_to_s3(
        folder=f"cocs-projects/{project_id}/cos",
        filename=filename,
        data=payload
    )


def backup_ccp_profile(project_id: str, payload: dict):
    filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.json"

    return upload_json_to_s3(
        folder=f"cocs-projects/{project_id}/ccp",
        filename=filename,
        data=payload
    )


def backup_csp_content(project_id: str, payload: dict):
    filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.json"

    return upload_json_to_s3(
        folder=f"cocs-projects/{project_id}/csp",
        filename=filename,
        data=payload
    )
