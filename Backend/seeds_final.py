import sys
import os
import traceback
from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import date

# Configurar el path para importar app
sys.path.append(os.path.join(os.getcwd(), "Backend"))

try:
    from app.core.database import SessionLocal, engine
    from app.modules.usuarios.models import Taller, Cliente, PersonalTaller, Usuario, Administrador, Especialidad
    from app.core.security import get_password_hash
    from app.modules.vehiculos.models import Vehiculo
    from app.modules.emergencias.models import Emergencia, DetalleEmergencia, Mensajeria, PrioridadEmergencia, EstadoEmergencia
    from app.modules.bitacora.models import Bitacora
    print("✅ Importaciones de módulos completadas.")
except ImportError as e:
    print(f"❌ Error crítico de importación: {e}")
    print("Asegúrate de ejecutar este script desde la raíz de la carpeta 'Backend' o configurar bien el PYTHONPATH.")
    sys.exit(1)

def fix_enum():
    """Asegura que el valor 'ADMIN_SISTEMA' exista en el ENUM de Postgres."""
    print("\n🔍 Verificando ENUM 'userrole'...")
    try:
        with engine.connect() as conn:
            conn.execute(text("ALTER TYPE userrole ADD VALUE 'ADMIN_SISTEMA'"))
            conn.commit()
            print("  -> ✅ Valor 'ADMIN_SISTEMA' verificado/agregado.")
    except Exception as e:
        if "already exists" in str(e):
            print("  -> ℹ️ El valor 'ADMIN_SISTEMA' ya existe en el ENUM (Normal).")
        else:
            print(f"  -> ⚠️ Nota sobre ENUM: {e}")

def get_or_create_specialty(db: Session, nombre: str, descripcion: str):
    try:
        obj = db.query(Especialidad).filter(Especialidad.nombre == nombre).first()
        if obj:
            obj.descripcion = descripcion
            print(f"  [Especialidad] '{nombre}' actualizada correctamente.")
        else:
            obj = Especialidad(nombre=nombre, descripcion=descripcion)
            db.add(obj)
            print(f"  [Especialidad] '{nombre}' creada satisfactoriamente.")
        return obj
    except Exception as e:
        print(f"  ❌ Error procesando especialidad '{nombre}': {e}")
        return None

def upsert_user(db: Session, model, email: str, **kwargs):
    try:
        obj = db.query(model).filter(model.email == email).first()
        if obj:
            for key, value in kwargs.items():
                setattr(obj, key, value)
            print(f"  [{model.__name__}] '{email}' actualizado.")
        else:
            obj = model(email=email, **kwargs)
            db.add(obj)
            print(f"  [{model.__name__}] '{email}' creado.")
        return obj
    except Exception as e:
        print(f"  ❌ Error procesando {model.__name__} '{email}': {e}")
        db.rollback()
        return None

def seed_final():
    db: Session = SessionLocal()
    print("\n" + "="*50)
    print("🚀 INICIANDO SEED FINAL DETALLADO")
    print("="*50)
    
    try:
        h_pass = get_password_hash("password123")

        # 0. ESPECIALIDADES
        print("\n--- 0. PROCESANDO ESPECIALIDADES ---")
        especialidades_data = [
            ("Mecánica General", "Servicios generales de motor y mantenimiento."),
            ("Electricidad", "Sistema eléctrico, luces y baterías."),
            ("Gomería", "Reparación de neumáticos y alineación."),
            ("Chapa y Pintura", "Restauración de carrocería y pintura."),
            ("Aire Acondicionado", "Carga de gas y reparación de climatización.")
        ]
        for nombre, desc in especialidades_data:
            get_or_create_specialty(db, nombre, desc)
        db.flush()
        print("✅ Fase de especialidades completada.")

        # 1. ADMIN DEL SISTEMA
        print("\n--- 1. PROCESANDO ADMINISTRADOR ---")
        admin = upsert_user(db, Administrador, "admin@emergencia.com", 
            password_hash=get_password_hash("admin123"),
            rol="ADMIN_SISTEMA", nombre_completo="Administrador General", tipo_perfil="admin"
        )
        if not admin: print("⚠️ Fallo al procesar Administrador Principal.")

        # 2. TALLERES
        print("\n--- 2. PROCESANDO TALLERES ---")
        esp_mecanica = db.query(Especialidad).filter(Especialidad.nombre == "Mecánica General").first()
        esp_electrico = db.query(Especialidad).filter(Especialidad.nombre == "Electricidad").first()
        esp_gomeria = db.query(Especialidad).filter(Especialidad.nombre == "Gomería").first()

        t_central = upsert_user(db, Taller, "taller_central@example.com",
            password_hash=h_pass, rol="ADMIN_TALLER",
            nombre_taller="Taller Mecánico Central", telefono="71234567", nit="987654321",
            ciudad="Santa Cruz", direccion="Calle Falsa 123", latitud=-17.7833, longitud=-63.1821,
            foto_perfil="https://res.cloudinary.com/dh8zaedgv/image/upload/v1777239418/1064c26b-8665-40dc-912e-0d722168e398.png",
            tipo_perfil="taller"
        )
        if t_central and esp_mecanica and esp_electrico:
            t_central.especialidades = [esp_mecanica, esp_electrico]

        t_norte = upsert_user(db, Taller, "taller_norte@example.com",
            password_hash=h_pass, rol="ADMIN_TALLER",
            nombre_taller="Taller Mecánico El Norte", telefono="70000001", nit="11111111",
            ciudad="Santa Cruz", direccion="Zona Norte, Av. Banzer", latitud=-17.780987, longitud=-63.193755,
            foto_perfil="https://res.cloudinary.com/dh8zaedgv/image/upload/v1777234606/83a5d61f-4f3d-4fde-94e9-b3a0ff222c45.png",
            tipo_perfil="taller"
        )
        if t_norte and esp_gomeria:
            t_norte.especialidades = [esp_gomeria]

        t_sur = upsert_user(db, Taller, "taller_sur@example.com",
            password_hash=h_pass, rol="ADMIN_TALLER",
            nombre_taller="Taller Mecánico El Sur", telefono="70000002", nit="22222222",
            ciudad="Santa Cruz", direccion="Zona Sur, Av. Santos Dumont", latitud=-17.772393, longitud=-63.198007,
            foto_perfil="https://res.cloudinary.com/dh8zaedgv/image/upload/v1777234795/1dbc6eda-58cd-4d02-9316-3545ee82fb44.png",
            tipo_perfil="taller"
        )
        if t_sur and esp_mecanica:
            t_sur.especialidades = [esp_mecanica]
        db.flush()

        # 3. CLIENTES
        print("\n--- 3. PROCESANDO CLIENTES ---")
        c_juan = upsert_user(db, Cliente, "cliente_juan@example.com",
            password_hash=h_pass, rol="CLIENTE",
            nombre="Juan Pérez", telefono="70012345", ci="1234567 LP", fecha_nacimiento=date(1990, 5, 15),
            foto_perfil="https://res.cloudinary.com/demo/image/upload/v1234567/juan_cliente.jpg", tipo_perfil="cliente"
        )
        upsert_user(db, Cliente, "maria_cliente@example.com", password_hash=h_pass, rol="CLIENTE", nombre="Maria Garcia", telefono="78888881", tipo_perfil="cliente")
        upsert_user(db, Cliente, "carlos_cliente@example.com", password_hash=h_pass, rol="CLIENTE", nombre="Carlos Rodriguez", telefono="78888882", tipo_perfil="cliente")
        db.flush()

        # 4. PERSONAL
        print("\n--- 4. PROCESANDO PERSONAL ---")
        if t_central:
            p_pedro = upsert_user(db, PersonalTaller, "mecanico_pedro@example.com",
                password_hash=h_pass, rol="PERSONAL_TALLER",
                nombre_completo="Pedro El Mecánico", taller_id=t_central.id, cargo="Jefe de Mecánicos",
                especialidad="Transmisiones Automáticas", foto_perfil="https://res.cloudinary.com/demo/image/upload/v1234567/pedro_mecanico.jpg",
                tipo_perfil="personal_taller"
            )
        else:
            p_pedro = None
            print("⚠️ Omitiendo Pedro El Mecánico porque el Taller Central falló.")

        if t_norte: upsert_user(db, PersonalTaller, "mecanico_norte1@example.com", password_hash=h_pass, rol="PERSONAL_TALLER", nombre_completo="Juan Mecanico Norte", taller_id=t_norte.id, cargo="Mecánico", tipo_perfil="personal_taller")
        if t_sur: upsert_user(db, PersonalTaller, "mecanico_sur1@example.com", password_hash=h_pass, rol="PERSONAL_TALLER", nombre_completo="Luis Mecanico Sur", taller_id=t_sur.id, cargo="Mecánico", tipo_perfil="personal_taller")
        db.flush()

        # 5. VEHICULO
        print("\n--- 5. PROCESANDO VEHÍCULO ---")
        try:
            v_juan = db.query(Vehiculo).filter(Vehiculo.placa == "2024-ABC").first()
            if v_juan:
                v_juan.marca, v_juan.modelo, v_juan.color, v_juan.anio = "Toyota", "Hilux", "Blanco", 2022
                print("  [Vehículo] '2024-ABC' actualizado.")
            elif c_juan:
                v_juan = Vehiculo(placa="2024-ABC", marca="Toyota", modelo="Hilux", color="Blanco", anio=2022, cliente_id=c_juan.id)
                db.add(v_juan)
                print("  [Vehículo] '2024-ABC' creado satisfactoriamente.")
            else:
                v_juan = None
                print("⚠️ No se pudo crear el vehículo porque el cliente Juan Pérez falló.")
        except Exception as e:
            print(f"❌ Error procesando vehículo: {e}")
            v_juan = None
        db.flush()

        # 6. FLUJO DE EMERGENCIA
        print("\n--- 6. PROCESANDO EMERGENCIA DE PRUEBA ---")
        try:
            if v_juan and p_pedro:
                em_existente = db.query(Emergencia).filter(Emergencia.id_vehiculo == v_juan.id, Emergencia.estado == EstadoEmergencia.atendiendo).first()
                if not em_existente:
                    em = Emergencia(
                        ubicacion_real="-17.78629,-63.18170", descripcion="El motor se sobrecalentó y sale humo.",
                        prioridad=PrioridadEmergencia.alta, estado=EstadoEmergencia.atendiendo,
                        id_vehiculo=v_juan.id, id_personal=p_pedro.id
                    )
                    db.add(em)
                    db.flush()
                    db.add(DetalleEmergencia(nro_emergencia=em.nro, tiempo_llegada_estimado="12 minutos", ubicacion_personal_real="-17.78400,-63.18000"))
                    db.add(Mensajeria(nro_emergencia=em.nro, id_remitente=t_central.id, mensaje="Ya enviamos a Pedro para ayudarte, Juan.", leido=False))
                    print("  -> Nueva Emergencia de prueba generada con éxito.")
                else:
                    print(f"  -> Se detectó una emergencia activa (Nro {em_existente.nro}), no se creará otra.")
            else:
                print("  ⚠️ No se cumplen los requisitos (Vehículo/Personal) para crear la emergencia de prueba.")
        except Exception as e:
            print(f"  ❌ Error en flujo de emergencia: {e}")

        # 7. BITACORA
        print("\n--- 7. PROCESANDO BITÁCORA ---")
        try:
            conteo_bitacora = db.query(Bitacora).count()
            if conteo_bitacora == 0:
                print("  -> Bitácora vacía. Insertando registros iniciales...")
                registros = []
                if admin: registros.append(Bitacora(accion="LOGIN_EXITOSO", detalle="Admin entró al sistema", ip="192.168.1.1", agente="Chrome/Windows", id_usuario=admin.id, fecha=date.today(), hora="08:00:00"))
                if admin and t_norte: registros.append(Bitacora(accion="REGISTRO_TALLER", detalle="Se creó Taller El Norte", ip="192.168.1.1", id_usuario=admin.id, id_taller=t_norte.id, fecha=date.today(), hora="08:30:00"))
                if c_juan and t_central: registros.append(Bitacora(accion="EMERGENCIA_CREADA", detalle="Emergencia Nro 1 reportada", ip="10.0.0.1", id_usuario=c_juan.id, id_taller=t_central.id, fecha=date.today(), hora="09:15:00"))
                
                if registros:
                    db.add_all(registros)
                    print(f"  -> {len(registros)} registros de bitácora añadidos.")
            else:
                print(f"  -> La bitácora ya contiene {conteo_bitacora} registros. Saltando inserción inicial.")
        except Exception as e:
            print(f"  ❌ Error procesando bitácora: {e}")

        db.commit()
        print("\n" + "="*50)
        print("🚀 SEED FINAL (IDEMPOTENTE) COMPLETADO CON ÉXITO.")
        print("="*50)

    except Exception as e:
        db.rollback()
        print("\n" + "!"*50)
        print(f"🔥 ERROR FATAL DURANTE EL SEED: {e}")
        print("Detalle técnico:")
        traceback.print_exc()
        print("!"*50)
    finally:
        db.close()
        print("\n🔌 Conexión a la base de datos cerrada.")

if __name__ == "__main__":
    fix_enum()
    seed_final()
