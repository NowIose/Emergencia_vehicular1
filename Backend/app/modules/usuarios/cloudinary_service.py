# Backend\app\modules\usuarios\cloudinary_service.py
import cloudinary.uploader
from fastapi import UploadFile
from starlette.concurrency import run_in_threadpool
from app.core.config import settings

class CloudinaryService:

    @staticmethod
    async def upload_image(file: UploadFile, folder: str = "emergencia_vehicular/profiles"):
        """
        Versión asíncrona del servicio de Cloudinary.
        folder: Carpeta dentro de Cloudinary para organizar las imágenes.
        """
        if not file:
            raise ValueError("No se proporcionó archivo")

        try:
            # Leemos el contenido del archivo que viene de FastAPI
            file_content = await file.read()
            
            # Ejecutamos la subida en un threadpool para no bloquear el Event Loop
            result = await run_in_threadpool(
                cloudinary.uploader.upload,
                file_content,
                folder=folder
            )
        except Exception as exc:
            # Capturamos errores del SDK de Cloudinary
            raise ValueError(f"Error de Cloudinary: {str(exc)}")
        finally:
            # Siempre cerramos el archivo para liberar memoria
            await file.close()

        return {
            "url": result.get("secure_url"),
            "public_id": result.get("public_id")
        }

    @staticmethod
    async def delete_image(public_id: str):
        """
        Elimina una imagen de Cloudinary dado su public_id.
        """
        if not public_id:
            return None
        return await run_in_threadpool(cloudinary.uploader.destroy, public_id)