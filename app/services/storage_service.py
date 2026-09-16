import os
import aiofiles
from typing import Optional
from app.core.config import settings


class StorageService:
    def __init__(self):
        self.storage_type = settings.STORAGE_TYPE
        self.local_dir = settings.LOCAL_STORAGE_DIR
        if self.storage_type == "local":
            os.makedirs(self.local_dir, exist_ok=True)

    async def save_file(self, file_bytes: bytes, storage_key: str) -> str:
        """Saves file bytes to local disk or S3 bucket."""
        if self.storage_type == "local":
            full_path = os.path.join(self.local_dir, storage_key)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            async with aiofiles.open(full_path, "wb") as f:
                await f.write(file_bytes)
            return full_path
        else:
            # S3 storage implementation
            import aioboto3
            session = aioboto3.Session()
            async with session.client(
                "s3",
                endpoint_url=settings.S3_ENDPOINT_URL,
                aws_access_key_id=settings.S3_ACCESS_KEY,
                aws_secret_access_key=settings.S3_SECRET_KEY,
                region_name=settings.S3_REGION,
            ) as s3:
                await s3.put_object(
                    Bucket=settings.S3_BUCKET_NAME,
                    Key=storage_key,
                    Body=file_bytes
                )
            return storage_key

    async def get_file_bytes(self, storage_key: str) -> Optional[bytes]:
        """Retrieves raw file bytes from storage."""
        if self.storage_type == "local":
            full_path = os.path.join(self.local_dir, storage_key)
            if not os.path.exists(full_path):
                # Check if absolute path was provided
                if os.path.exists(storage_key):
                    full_path = storage_key
                else:
                    return None
            async with aiofiles.open(full_path, "rb") as f:
                return await f.read()
        else:
            import aioboto3
            session = aioboto3.Session()
            async with session.client(
                "s3",
                endpoint_url=settings.S3_ENDPOINT_URL,
                aws_access_key_id=settings.S3_ACCESS_KEY,
                aws_secret_access_key=settings.S3_SECRET_KEY,
                region_name=settings.S3_REGION,
            ) as s3:
                response = await s3.get_object(Bucket=settings.S3_BUCKET_NAME, Key=storage_key)
                return await response["Body"].read()

    async def delete_file(self, storage_key: str) -> bool:
        """Deletes file from storage."""
        try:
            if self.storage_type == "local":
                full_path = os.path.join(self.local_dir, storage_key)
                if os.path.exists(full_path):
                    os.remove(full_path)
                    return True
                elif os.path.exists(storage_key):
                    os.remove(storage_key)
                    return True
            else:
                import aioboto3
                session = aioboto3.Session()
                async with session.client(
                    "s3",
                    endpoint_url=settings.S3_ENDPOINT_URL,
                    aws_access_key_id=settings.S3_ACCESS_KEY,
                    aws_secret_access_key=settings.S3_SECRET_KEY,
                    region_name=settings.S3_REGION,
                ) as s3:
                    await s3.delete_object(Bucket=settings.S3_BUCKET_NAME, Key=storage_key)
                    return True
        except Exception:
            return False
        return False


storage_service = StorageService()
