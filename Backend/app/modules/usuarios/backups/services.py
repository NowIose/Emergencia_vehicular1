import os
import subprocess
import boto3
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from dotenv import load_dotenv
from botocore.config import Config
from .models import BackupCloud

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
R2_ENDPOINT_URL = os.getenv("R2_ENDPOINT_URL")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME")

# Definir comandos. Usa la ruta local si existe, sino usa el comando por defecto de Linux (Render)
PG_DUMP_CMD = os.getenv("PG_DUMP_PATH", "pg_dump")
PSQL_CMD = os.getenv("PSQL_PATH", "psql")

TEMP_BACKUP_DIR = "TempBackups"
os.makedirs(TEMP_BACKUP_DIR, exist_ok=True)

def get_r2_client():
    return boto3.client(
        's3',
        endpoint_url=R2_ENDPOINT_URL,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        config=Config(signature_version='s3v4')
    )

def generar_backup_en_nube(db: Session):
    fecha = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"backup_emergencia_{fecha}.sql"
    file_path = os.path.join(TEMP_BACKUP_DIR, filename)

    # Postgres permite pasar la URL completa como argumento --dbname
    comando = [PG_DUMP_CMD, f'--dbname={DATABASE_URL}', '-f', file_path, '--clean']

    try:
        print(f"Ejecutando backup: {filename}...")
        
        # 1. Generar backup (capture_output captura el error de consola si falla)
        resultado = subprocess.run(comando, check=True, capture_output=True, text=True)

        # 2. Subir a R2
        s3 = get_r2_client()
        s3.upload_file(file_path, R2_BUCKET_NAME, filename)

        # 3. Calcular tamaño y URL
        tamano_mb = round(os.path.getsize(file_path) / (1024 * 1024), 2)
        url_referencia = f"{R2_ENDPOINT_URL}/{R2_BUCKET_NAME}/{filename}"

        # 4. Guardar en BD
        nuevo_backup = BackupCloud(
            nombre=filename,
            url=url_referencia,
            key_r2=filename,
            tamano=tamano_mb
        )
        db.add(nuevo_backup)
        db.commit()
        db.refresh(nuevo_backup)

        # 5. Borrar temporal
        os.remove(file_path)
        print("Backup completado y subido con éxito.")
        
        return nuevo_backup

    except FileNotFoundError:
        # Esto salta si Windows no encuentra pg_dump
        print("ERROR CRÍTICO: No se encontró pg_dump.")
        raise HTTPException(status_code=500, detail="No se encontró pg_dump. Verifica PG_DUMP_PATH en tu .env")
    
    except subprocess.CalledProcessError as e:
        # Esto salta si la contraseña está mal o Postgres rechaza la conexión
        print(f"ERROR DE POSTGRESQL: {e.stderr}")
        raise HTTPException(status_code=500, detail=f"Fallo en la base de datos: {e.stderr}")
    
    except Exception as e:
        print(f"ERROR GENERAL: {str(e)}")
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")

def restaurar_backup_desde_nube(filename: str, db: Session):
    backup = db.query(BackupCloud).filter(BackupCloud.nombre == filename).first()
    if not backup:
        raise HTTPException(status_code=404, detail="El registro del backup no existe en la BD")

    file_path = os.path.join(TEMP_BACKUP_DIR, filename)

    try:
        # 1. Descargar de R2
        s3 = get_r2_client()
        s3.download_file(R2_BUCKET_NAME, backup.key_r2, file_path)

        comando = [PSQL_CMD, f'--dbname={DATABASE_URL}', '-f', file_path]

        # 2. Desconectar usuarios activos para poder restaurar
        db.execute(text(f"""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = current_database()
            AND pid <> pg_backend_pid();
        """))
        db.commit()
        db.close() # Cierra sesión para liberar la BD

        # 3. Restaurar usando psql
        subprocess.run(comando, check=True, capture_output=True, text=True)

        # 4. Limpiar
        os.remove(file_path)
        return True

    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="No se encontró psql. Verifica PSQL_PATH en tu .env")
    except subprocess.CalledProcessError as e:
        print(f"ERROR AL RESTAURAR: {e.stderr}")
        raise HTTPException(status_code=500, detail=f"Fallo al restaurar la BD: {e.stderr}")
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Error al restaurar: {str(e)}")