# services/image_service.py
import os
import io
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image
import aiofiles
from loguru import logger
from config import settings

class ImageService:
    SUPPORTED_FORMATS = (".jpg", ".jpeg", ".png", ".webp")
    MAX_SIZE_MB = 20
    MAX_DIMENSION = 4096
    
    @staticmethod
    async def validate_image(file_path: Path) -> Tuple[bool, str]:
        """Validate image file"""
        if not file_path.exists():
            return False, "File not found"
        
        size_mb = file_path.stat().st_size / (1024 * 1024)
        if size_mb > ImageService.MAX_SIZE_MB:
            return False, f"File too large ({size_mb:.1f}MB). Max {ImageService.MAX_SIZE_MB}MB"
        
        if file_path.suffix.lower() not in ImageService.SUPPORTED_FORMATS:
            return False, f"Unsupported format {file_path.suffix}. Use JPG, PNG, or WebP"
        
        try:
            async with aiofiles.open(file_path, "rb") as f:
                data = await f.read()
            img = Image.open(io.BytesIO(data))
            width, height = img.size
            if width > ImageService.MAX_DIMENSION or height > ImageService.MAX_DIMENSION:
                return False, f"Image too large ({width}x{height}). Max {ImageService.MAX_DIMENSION}px"
            img.close()
        except Exception as e:
            return False, f"Invalid image: {e}"
        
        return True, "OK"
    
    @staticmethod
    async def compress_image(file_path: Path, quality: int = 85) -> Optional[Path]:
        """Compress image to reduce size"""
        try:
            async with aiofiles.open(file_path, "rb") as f:
                data = await f.read()
            img = Image.open(io.BytesIO(data))
            
            # Convert to RGB if necessary
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            # Resize if too large
            max_dim = 2048
            if img.width > max_dim or img.height > max_dim:
                ratio = min(max_dim / img.width, max_dim / img.height)
                new_size = (int(img.width * ratio), int(img.height * ratio))
                img = img.resize(new_size, Image.LANCZOS)
            
            compressed_path = file_path.parent / f"compressed_{file_path.name}"
            img.save(compressed_path, "JPEG", quality=quality, optimize=True)
            img.close()
            
            original_size = file_path.stat().st_size
            compressed_size = compressed_path.stat().st_size
            ratio = (1 - compressed_size / original_size) * 100
            
            logger.info("Image compressed: {} -> {} ({:.1f}% reduction)", 
                       file_path.name, compressed_path.name, ratio)
            
            return compressed_path
        
        except Exception as e:
            logger.error("Image compression failed: {}", e)
            return None
    
    @staticmethod
    async def save_photo(bot, file_id: str, user_id: int) -> Optional[Path]:
        """Download and save a Telegram photo"""
        try:
            file = await bot.get_file(file_id)
            photo_dir = settings.DATA_DIR / "photos" / str(user_id)
            photo_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = __import__("datetime").datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            file_path = photo_dir / f"{timestamp}.jpg"
            
            await bot.download_file(file.file_path, destination=str(file_path))
            logger.info("Photo saved: {}", file_path)
            
            return file_path
        
        except Exception as e:
            logger.error("Failed to save photo: {}", e)
            return None
