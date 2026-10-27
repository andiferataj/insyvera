from .config import settings

class Storage:
    def __init__(self):
        self.client = None
        if settings.storage == "s3":
            import boto3
            self.client = boto3.client("s3", endpoint_url=settings.s3_endpoint,
                aws_access_key_id=settings.s3_access, aws_secret_access_key=settings.s3_secret)

    def path(self, key):
        target = (settings.data_dir / "objects" / key).resolve()
        if not target.is_relative_to((settings.data_dir / "objects").resolve()):
            raise ValueError("Invalid storage key")
        return target

    def ready(self):
        if self.client:
            try:
                self.client.head_bucket(Bucket=settings.bucket)
            except self.client.exceptions.ClientError as exc:
                if exc.response["Error"]["Code"] in ("404", "NoSuchBucket"):
                    self.client.create_bucket(Bucket=settings.bucket)
                else:
                    raise
        else:
            (settings.data_dir / "objects").mkdir(parents=True, exist_ok=True)

    def put(self, key, content):
        if self.client:
            self.client.put_object(Bucket=settings.bucket, Key=key, Body=content)
        else:
            target = self.path(key)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)

    def get(self, key):
        if self.client:
            return self.client.get_object(Bucket=settings.bucket, Key=key)["Body"].read()
        return self.path(key).read_bytes()

    def delete(self, key):
        if self.client:
            self.client.delete_object(Bucket=settings.bucket, Key=key)
        else:
            self.path(key).unlink(missing_ok=True)

storage = Storage()
