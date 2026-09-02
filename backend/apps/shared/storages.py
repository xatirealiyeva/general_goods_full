"""
Optional S3-backed storage for product images. Falls back to local storage
automatically (see settings.py) when AWS credentials are not configured.
"""
try:
    from storages.backends.s3boto3 import S3Boto3Storage

    class MediaStorage(S3Boto3Storage):
        location = "media"
        file_overwrite = False
except ImportError:  # django-storages / boto3 not installed in this environment
    MediaStorage = None
