from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db 
from .services import generar_backup_en_nube, restaurar_backup_desde_nube
from .models import BackupCloud

router = APIRouter(prefix="/backups", tags=["Backups"])

@router.get("/")
def listar_backups(db: Session = Depends(get_db)):
    # Monitoreo en la consola de Uvicorn
    total = db.query(BackupCloud).count()
    print(f"DEBUG: Se encontraron {total} registros en la base de datos")
    
    backups = db.query(BackupCloud).order_by(BackupCloud.fecha_creacion.desc()).all()
    
    lista_limpia = [
        {
            "id": b.id,
            "nombre": b.nombre,
            "tamano": b.tamano,
            "fecha_creacion": b.fecha_creacion.strftime("%Y-%m-%d %H:%M:%S") if b.fecha_creacion else "",
            "url": b.url
        } for b in backups
    ]
    
    return {"backups": lista_limpia}

@router.post("/crear")
def crear_backup(db: Session = Depends(get_db)):
    nuevo_backup = generar_backup_en_nube(db)
    return {
        "mensaje": "Backup creado y subido a R2 exitosamente", 
        "archivo": nuevo_backup.nombre
    }

@router.post("/restaurar/{filename}")
def restaurar_backup(filename: str, db: Session = Depends(get_db)):
    backup = db.query(BackupCloud).filter(BackupCloud.nombre == filename).first()
    if not backup:
        raise HTTPException(status_code=404, detail="Backup no encontrado en la base de datos")
    
    # 1. Guardamos el nombre en un String de Python de forma segura
    nombre_archivo = backup.nombre
    
    # 2. Ejecutamos la restauración (esto romperá la sesión de BD actual, ¡pero no importa!)
    restaurar_backup_desde_nube(nombre_archivo, db)
    
    # 3. Usamos nuestra variable segura para el mensaje
    return {"mensaje": f"Base de datos restaurada correctamente desde {nombre_archivo}"}