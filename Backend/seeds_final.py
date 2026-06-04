import sys
import os
from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import date

# Configurar el path para importar app
sys.path.append(os.path.join(os.getcwd(), "Backend"))

from app.core.database import SessionLocal, engine
from app.modules.usuarios.models import Taller, Cliente, PersonalTaller, UserRole, Usuario, Administrador, Especialidad
from app.core.security import get_password_hash
from app.modules.vehiculos.models import Vehiculo
from app.modules.emergencias.models import Emergencia, DetalleEmergencia, Mensajeria, PrioridadEmergencia, EstadoEmergencia
from app.modules.bitacora.models import Bitacora

def fix_enum():
    """Asegura que el valor 'ADMIN_SISTEMA' exista en el ENUM de Postgres."""
    try:
        with engine.connect() as conn:
            conn.execute(text("ALTER TYPE userrole ADD VALUE 'ADMIN_SISTEMA'"))
            conn.commit()
            print("✅ Valor 'ADMIN_SISTEMA' verificado.")
    except Exception as e:
        if "already exists" in str(e):
            pass
        else:
            print(f"ℹ️ Nota sobre ENUM: {e}")

def seed_final():
    db: Session = SessionLocal()
    try:
        # --- LIMPIEZA INICIAL ---
        # Borramos por emails para permitir re-ejecución limpia
        emails_a_limpiar = [
            "admin@emergencia.com", "taller_central@example.com", "taller_norte@example.com", 
            "taller_sur@example.com", "mecanico_pedro@example.com", "mecanico_norte1@example.com",
            "mecanico_norte2@example.com", "mecanico_sur1@example.com", "mecanico_sur2@example.com",
            "cliente_juan@example.com", "maria_cliente@example.com", "carlos_cliente@example.com"
        ]
        
        usuarios_viejos = db.query(Usuario).filter(Usuario.email.in_(emails_a_limpiar)).all()
        ids_viejos = [u.id for u in usuarios_viejos]
        
        if ids_viejos:
            # Borrar en orden de dependencia
            db.query(Bitacora).filter(Bitacora.id_usuario.in_(ids_viejos)).delete(synchronize_session=False)
            db.query(Mensajeria).filter(Mensajeria.id_remitente.in_(ids_viejos)).delete(synchronize_session=False)
            db.query(DetalleEmergencia).delete(synchronize_session=False)
            db.query(Emergencia).delete(synchronize_session=False)
            db.query(Vehiculo).filter(Vehiculo.cliente_id.in_(ids_viejos)).delete(synchronize_session=False)
            db.query(PersonalTaller).filter(PersonalTaller.id.in_(ids_viejos)).delete(synchronize_session=False)
            db.query(Administrador).filter(Administrador.id.in_(ids_viejos)).delete(synchronize_session=False)
            db.query(Taller).filter(Taller.id.in_(ids_viejos)).delete(synchronize_session=False)
            db.query(Cliente).filter(Cliente.id.in_(ids_viejos)).delete(synchronize_session=False)
            db.query(Usuario).filter(Usuario.id.in_(ids_viejos)).delete(synchronize_session=False)
            db.commit()
            print("🧹 Limpieza profunda completada.")

        h_pass = get_password_hash("password123")

        # 1. ADMIN DEL SISTEMA
        admin = Administrador(
            email="admin@emergencia.com", password_hash=get_password_hash("admin123"),
            rol="ADMIN_SISTEMA", nombre_completo="Administrador General", tipo_perfil="admin"
        )
        db.add(admin)

        # 2. TALLERES (Con todos los campos de ambos seeds)
        t_central = Taller(
            email="taller_central@example.com", password_hash=h_pass, rol="ADMIN_TALLER",
            nombre_taller="Taller Mecánico Central", telefono="71234567", nit="987654321",
            ciudad="Santa Cruz", direccion="Calle Falsa 123", latitud=-17.7833, longitud=-63.1821,
            foto_perfil="https://res.cloudinary.com/dh8zaedgv/image/upload/v1777239418/1064c26b-8665-40dc-912e-0d722168e398.png",
            tipo_perfil="taller"
        )
        t_norte = Taller(
            email="taller_norte@example.com", password_hash=h_pass, rol="ADMIN_TALLER",
            nombre_taller="Taller Mecánico El Norte", telefono="70000001", nit="11111111",
            ciudad="Santa Cruz", direccion="Zona Norte, Av. Banzer", latitud=-17.780987, longitud=-63.193755,
            foto_perfil="https://res.cloudinary.com/dh8zaedgv/image/upload/v1777234606/83a5d61f-4f3d-4fde-94e9-b3a0ff222c45.png",
            tipo_perfil="taller"
        )
        t_sur = Taller(
            email="taller_sur@example.com", password_hash=h_pass, rol="ADMIN_TALLER",
            nombre_taller="Taller Mecánico El Sur", telefono="70000002", nit="22222222",
            ciudad="Santa Cruz", direccion="Zona Sur, Av. Santos Dumont", latitud=-17.772393, longitud=-63.198007,
            foto_perfil="https://res.cloudinary.com/dh8zaedgv/image/upload/v1777234795/1dbc6eda-58cd-4d02-9316-3545ee82fb44.png",
            tipo_perfil="taller"
        )
        db.add_all([t_central, t_norte, t_sur])
        db.flush()

        # 3. CLIENTES
        c_juan = Cliente(
            email="cliente_juan@example.com", password_hash=h_pass, rol="CLIENTE",
            nombre="Juan Pérez", telefono="70012345", ci="1234567 LP", fecha_nacimiento=date(1990, 5, 15),
            foto_perfil="https://res.cloudinary.com/demo/image/upload/v1234567/juan_cliente.jpg", tipo_perfil="cliente"
        )
        c_maria = Cliente(email="maria_cliente@example.com", password_hash=h_pass, rol="CLIENTE", nombre="Maria Garcia", telefono="78888881", tipo_perfil="cliente")
        c_carlos = Cliente(email="carlos_cliente@example.com", password_hash=h_pass, rol="CLIENTE", nombre="Carlos Rodriguez", telefono="78888882", tipo_perfil="cliente")
        db.add_all([c_juan, c_maria, c_carlos])
        db.flush()

        # 4. PERSONAL
        p_pedro = PersonalTaller(
            email="mecanico_pedro@example.com", password_hash=h_pass, rol="PERSONAL_TALLER",
            nombre_completo="Pedro El Mecánico", taller_id=t_central.id, cargo="Jefe de Mecánicos",
            especialidad="Transmisiones Automáticas", foto_perfil="https://res.cloudinary.com/demo/image/upload/v1234567/pedro_mecanico.jpg",
            tipo_perfil="personal_taller"
        )
        p_n1 = PersonalTaller(email="mecanico_norte1@example.com", password_hash=h_pass, rol="PERSONAL_TALLER", nombre_completo="Juan Mecanico Norte", taller_id=t_norte.id, cargo="Mecánico", tipo_perfil="personal_taller")
        p_s1 = PersonalTaller(email="mecanico_sur1@example.com", password_hash=h_pass, rol="PERSONAL_TALLER", nombre_completo="Luis Mecanico Sur", taller_id=t_sur.id, cargo="Mecánico", tipo_perfil="personal_taller")
        db.add_all([p_pedro, p_n1, p_s1])
        db.flush()

        # 5. VEHICULO
        v_juan = Vehiculo(placa="2024-ABC", marca="Toyota", modelo="Hilux", color="Blanco", anio=2022, cliente_id=c_juan.id)
        db.add(v_juan)
        db.flush()

        # 6. FLUJO DE EMERGENCIA (De seeds.py)
        em = Emergencia(
            ubicacion_real="-17.78629,-63.18170", descripcion="El motor se sobrecalentó y sale humo.",
            prioridad=PrioridadEmergencia.alta, estado=EstadoEmergencia.atendiendo,
            id_vehiculo=v_juan.id, id_personal=p_pedro.id
        )
        db.add(em)
        db.flush()

        db.add(DetalleEmergencia(nro_emergencia=em.nro, tiempo_llegada_estimado="12 minutos", ubicacion_personal_real="-17.78400,-63.18000"))
        db.add(Mensajeria(nro_emergencia=em.nro, id_remitente=t_central.id, mensaje="Ya enviamos a Pedro para ayudarte, Juan.", leido=False))

        # 7. BITACORA (Datos variados para probar filtros del Admin)
        db.add_all([
            Bitacora(accion="LOGIN_EXITOSO", detalle="Admin entró al sistema", ip="192.168.1.1", agente="Chrome/Windows", id_usuario=admin.id, fecha=date.today(), hora="08:00:00"),
            Bitacora(accion="REGISTRO_TALLER", detalle="Se creó Taller El Norte", ip="192.168.1.1", id_usuario=admin.id, id_taller=t_norte.id, fecha=date.today(), hora="08:30:00"),
            Bitacora(accion="EMERGENCIA_CREADA", detalle="Emergencia Nro 1 reportada", ip="10.0.0.1", id_usuario=c_juan.id, id_taller=t_central.id, fecha=date.today(), hora="09:15:00"),
            Bitacora(accion="LOGIN_FALLIDO", detalle="Intento de acceso erróneo", ip="201.10.50.4", agente="Firefox/Linux", fecha=date.today(), hora="10:00:00")
        ])

        db.commit()
        print("\n🚀 SEED FINAL COMPLETADO CON ÉXITO.")
        print("Incluye: Admin, 3 Talleres (fotos/GPS), 3 Clientes, 3 Mecánicos, 1 Vehículo, 1 Emergencia activa y Bitácora.")

    except Exception as e:
        db.rollback()
        print(f"❌ Error durante el seed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    fix_enum()
    seed_final()
