from pydantic_settings import BaseSettings,SettingsConfigDict
import cloudinary
import os
from typing import Optional

class Settings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    DEBUG: bool = False

    # Agregamos estas para que Pydantic las valide automáticamente
    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str

    # Stripe (modo test para el proyecto academico)
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    STRIPE_MONTHLY_PRICE_ID: Optional[str] = None
    STRIPE_YEARLY_PRICE_ID: Optional[str] = None
    FRONTEND_URL: str = "http://localhost:4200"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")   

settings = Settings()

# Ahora usamos settings.VARIABLES en lugar de os.getenv
cloudinary.config(
    cloud_name = settings.CLOUDINARY_CLOUD_NAME,
    api_key    = settings.CLOUDINARY_API_KEY,
    api_secret = settings.CLOUDINARY_API_SECRET,
    secure = True
)

print(f"--- CONFIGURACIÓN CARGADA ---")
print(f"DEBUG MODE: {settings.DEBUG}")
print(f"CLOUDINARY: {settings.CLOUDINARY_CLOUD_NAME}")
