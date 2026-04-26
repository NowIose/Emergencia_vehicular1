from sqlalchemy.orm import Session
from sqlalchemy import func
from app.modules.usuarios import models as user_models

def obtener_reporte_usuarios(db: Session, rol_filtro: str = None, orden: str = None):
    query = db.query(user_models.Usuario)
    
    # Filtro de Rol con manejo de Enum para evitar Error 500
    if rol_filtro and rol_filtro.strip():
        try:
            rol_enum = user_models.UserRole[rol_filtro.upper()]
            query = query.filter(user_models.Usuario.rol == rol_enum)
        except KeyError:
            pass
        
    usuarios = query.all()
    resultado = []
    
    for u in usuarios:
        data = {
            "id": u.id,
            "email": u.email,
            "rol": u.rol.value if u.rol else "sin_rol",
            "nombre": "Sin nombre",
            "extra": "",
            "puntuacion_num": 0.0  # Los clientes se quedan en 0.0
        }
        
        # Lógica para TALLERES (Con calificación)
        if u.tipo_perfil == "taller":
            taller = db.query(user_models.Taller).filter(user_models.Taller.id == u.id).first()
            if taller:
                data["nombre"] = taller.nombre_taller
                promedio = db.query(func.avg(user_models.CalificacionTaller.puntuacion))\
                             .filter(user_models.CalificacionTaller.taller_id == u.id).scalar()
                
                if promedio:
                    data["puntuacion_num"] = float(promedio)
                    data["extra"] = f"⭐ {round(promedio, 1)}/5.0"
                else:
                    data["extra"] = "⭐ Sin calificar"
        
        # Lógica para CLIENTES (Sin calificación, solo teléfono)
        elif u.tipo_perfil == "cliente":
            cliente = db.query(user_models.Cliente).filter(user_models.Cliente.id == u.id).first()
            if cliente:
                data["nombre"] = cliente.nombre
                data["extra"] = f"📱 {cliente.telefono}"
        
        resultado.append(data)

    # 3. Aplicar Ordenamiento
    if orden == "mejor_calificados":
        # Los talleres con más estrellas arriba. Los clientes y talleres sin estrellas abajo.
        resultado.sort(key=lambda x: x["puntuacion_num"], reverse=True)
    elif orden == "peor_calificados":
        # Solo tiene sentido si filtramos por talleres primero
        # Filtramos los que tienen 0 para no poner a los clientes arriba
        resultado.sort(key=lambda x: x["puntuacion_num"] if x["puntuacion_num"] > 0 else 9.9)

    return resultado