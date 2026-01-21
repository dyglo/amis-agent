from __future__ import annotations

from dataclasses import dataclass

from amis_agent.core.config import get_settings


@dataclass(frozen=True)
class S3ClientConfig:
    enabled: bool
    bucket: str | None
    region: str | None


def load_s3_config() -> S3ClientConfig:
    settings = get_settings()
    return S3ClientConfig(
        enabled=settings.s3_enabled,
        bucket=settings.s3_bucket,
        region=settings.aws_region,
    )


def get_s3_client():
    cfg = load_s3_config()
    if not cfg.enabled:
        return None
    if not cfg.bucket or not cfg.region:
        raise ValueError("S3_ENABLED is true but S3_BUCKET or AWS_REGION is missing")
    try:
        import boto3  # type: ignore
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError("boto3_missing: install boto3 to use S3") from exc
    return boto3.client("s3", region_name=cfg.region)
