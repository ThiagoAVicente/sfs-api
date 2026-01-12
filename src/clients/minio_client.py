import os
from dataclasses import dataclass
from minio import Minio
from minio.error import S3Error
from minio.sseconfig import Rule, SSEConfig


@dataclass
class MinIOConfig:
    """MinIO configuration from environment."""
    host: str
    port: int
    access_key: str
    secret_key: str
    default_bucket: str
    secure: bool = False

    @classmethod
    def from_env(cls) -> "MinIOConfig":
        """Load configuration from environment variables."""
        return cls(
            host=os.getenv("MINIO_HOST", "localhost"),
            port=int(os.getenv("MINIO_PORT", "9000")),
            access_key=os.getenv("MINIO_ROOT_USER", "minioadmin"),
            secret_key=os.getenv("MINIO_ROOT_PASSWORD", "minioadmin"),
            default_bucket=os.getenv("SFS_FILE_BUCKET", "sfs-files"),
            secure=os.getenv("MINIO_SECURE", "false").lower() == "true",
        )


class MinIOClient:
    """MinIO client wrapper with singleton pattern."""

    _client: Minio | None = None
    config = MinIOConfig.from_env()


    @classmethod
    def get(cls) -> Minio:
        """Get or create the MinIO client singleton."""
        if cls._client is None:
            config = cls.config
            endpoint = f"{config.host}:{config.port}"
            cls._client = Minio(
                endpoint=endpoint,
                access_key=config.access_key,
                secret_key=config.secret_key,
                secure=config.secure,
            )
        return cls._client

    @classmethod
    def ensure_bucket_exists(cls, bucket_name: str | None = None) -> bool:
        """
        Ensure bucket exists, create if it doesn't.

        Args:
            bucket_name: Bucket name (uses default from config if None)

        Returns:
            True if bucket exists or was created
        """
        client = cls.get()
        config = MinIOConfig.from_env()
        bucket = bucket_name or config.default_bucket

        try:
            if not client.bucket_exists(bucket):
                client.make_bucket(bucket)

            sse_config = SSEConfig(Rule.new_sse_s3_rule())
            client.set_bucket_encryption(bucket, sse_config)
            return True
        except S3Error as e:
            print(f"Error ensuring bucket exists: {e}")
            return False

    @classmethod
    def put_object(
        cls,
        object_name: str,
        data: bytes,
        bucket_name: str | None = None,
        content_type: str = "application/octet-stream",
    ) -> bool:
        """
        Upload an object to MinIO.

        Args:
            object_name: Name/path of the object
            data: Object data as bytes
            bucket_name: Bucket name (uses default if None)
            content_type: MIME type of the object

        Returns:
            True if successful
        """
        client = cls.get()
        config = MinIOConfig.from_env()
        bucket = bucket_name or config.default_bucket

        try:
            from io import BytesIO
            client.put_object(
                bucket,
                object_name,
                BytesIO(data),
                length=len(data),
                content_type=content_type,
            )
            return True
        except S3Error as e:
            print(f"Error uploading object: {e}")
            return False

    @classmethod
    def get_object(cls, object_name: str, bucket_name: str | None = None) -> bytes | None:
        """
        Download an object from MinIO.

        Args:
            object_name: Name/path of the object
            bucket_name: Bucket name (uses default if None)

        Returns:
            Object data as bytes, or None if failed
        """
        client = cls.get()
        bucket = bucket_name or cls.config.default_bucket

        try:
            response = client.get_object(bucket, object_name)
            return response.read()
        except S3Error as e:
            print(f"Error downloading object: {e}")
            return None

    @classmethod
    def delete_object(cls, object_name: str, bucket_name: str | None = None) -> bool:
        """
        Delete an object from MinIO.

        Args:
            object_name: Name/path of the object
            bucket_name: Bucket name (uses default if None)

        Returns:
            True if successful
        """
        client = cls.get()
        bucket = bucket_name or cls.config.default_bucket

        try:
            client.remove_object(bucket, object_name)
            return True
        except S3Error as e:
            print(f"Error deleting object: {e}")
            return False

    @classmethod
    def list_objects(
        cls, prefix: str = "", bucket_name: str | None = None
    ) -> list[str]:
        """
        List objects in a bucket.

        Args:
            prefix: Object name prefix to filter
            bucket_name: Bucket name (uses default if None)

        Returns:
            List of object names
        """
        client = cls.get()
        bucket = bucket_name or cls.config.default_bucket

        try:
            objects = client.list_objects(bucket, prefix=prefix, recursive=True)
            return [obj.object_name for obj in objects]
        except S3Error as e:
            print(f"Error listing objects: {e}")
            return []

    @classmethod
    def object_exists(cls, object_name: str, bucket_name: str | None = None) -> bool:
        """
        Check if an object exists in MinIO.

        Args:
            object_name: Name/path of the object
            bucket_name: Bucket name (uses default if None)

        Returns:
            True if object exists
        """
        client = cls.get()
        bucket = bucket_name or cls.config.default_bucket

        try:
            client.stat_object(bucket, object_name)
            return True
        except S3Error as e:
            print(f"Error checking object existence: {e}")
            return False
