from app.core.database import SessionLocal
from app.modules.usuarios.models import Taller, Cliente, PersonalTaller, UserRole, Usuario
from sqlalchemy.orm import Session
from app.core.security import get_password_hash # Importamos la función de hashing

from app.modules.vehiculos.models import Vehiculo
from app.modules.emergencias.models import Emergencia, DetalleEmergencia, Mensajeria, PrioridadEmergencia, EstadoEmergencia

def seed_database():
    db: Session = SessionLocal()
    try:
        # 1. Limpieza de correos de prueba
        emails_test = [
            "taller_central@example.com", 
            "cliente_juan@example.com", 
            "mecanico_pedro@example.com"
        ]
        
        # Primero buscamos los IDs
        usuarios_viejos = db.query(Usuario).filter(Usuario.email.in_(emails_test)).all()
        ids_viejos = [u.id for u in usuarios_viejos]
        
        if ids_viejos:
            # --- ORDEN DE BORRADO CORRECTO ---
            # 1. Borramos el personal (depende de talleres)
            db.query(PersonalTaller).filter(PersonalTaller.taller_id.in_(ids_viejos)).delete(synchronize_session=False)
            
            # 2. Borramos los talleres y clientes
            db.query(Taller).filter(Taller.id.in_(ids_viejos)).delete(synchronize_session=False)
            db.query(Cliente).filter(Cliente.id.in_(ids_viejos)).delete(synchronize_session=False)
            
            # 3. Finalmente borramos el usuario base (id)
            db.query(Usuario).filter(Usuario.id.in_(ids_viejos)).delete(synchronize_session=False)
            
            db.commit()
            print("🧹 Datos de prueba antiguos limpiados correctamente.")

        # Generamos una contraseña segura para todos (password123)
        hashed_password = get_password_hash("password123")

        # 2. Crear un Taller (Admin)
        taller = Taller(
            email="taller_central@example.com",
            password_hash=hashed_password, 
            rol=UserRole.ADMIN_TALLER,
            nombre_taller="Taller Mecánico Central",
            telefono="71234567",
            nit="987654321",
            ciudad="Santa Cruz",
            direccion="Calle Falsa 123",
            foto_perfil="https://res.cloudinary.com/demo/image/upload/v1234567/taller_test.jpg",
            latitud=-17.7833,
            longitud=-63.1821
        )
        db.add(taller)
        db.commit()
        db.refresh(taller)
        print(f"✅ Taller Seeded: {taller.nombre_taller} (ID: {taller.id})")

        # 3. Crear un Cliente
        cliente = Cliente(
            email="cliente_juan@example.com",
            password_hash=hashed_password,
            rol=UserRole.CLIENTE,
            nombre="Juan Pérez",
            telefono="70012345",
            ci="1234567 LP",
            fecha_nacimiento="1990-05-15",
            foto_perfil="https://res.cloudinary.com/demo/image/upload/v1234567/juan_cliente.jpg"
        )
        db.add(cliente)
        db.commit()
        db.refresh(cliente)
        print(f"✅ Cliente Seeded: {cliente.nombre} (ID: {cliente.id})")

        # 4. Crear un Personal para el Taller
        personal = PersonalTaller(
            email="mecanico_pedro@example.com",
            password_hash=hashed_password,
            rol=UserRole.PERSONAL_TALLER,
            nombre_completo="Pedro El Mecánico",
            cargo="Jefe de Mecánicos",
            especialidad="Transmisiones Automáticas",
            foto_perfil="https://res.cloudinary.com/demo/image/upload/v1234567/pedro_mecanico.jpg",
            taller_id=taller.id
        )
        db.add(personal)
        db.commit()
        db.refresh(personal)
        print(f"✅ Personal Seeded: {personal.nombre_completo} (ID: {personal.id})")

        print("\n🚀 ¡Base de datos poblada usuarios con éxito para pruebas locales!")

        
        # 5. Crear un Vehículo para el Cliente
        vehiculo = Vehiculo(
            placa="2024-ABC",
            marca="Toyota",
            modelo="Hilux",
            color="Blanco",
            anio=2022,
            cliente_id=cliente.id # Relación con el cliente creado arriba
        )
        db.add(vehiculo)
        db.commit()
        db.refresh(vehiculo)
        print(f"✅ Vehículo Seeded: {vehiculo.placa} (Dueño: {cliente.nombre})")

        # 6. Crear una Emergencia
        emergencia = Emergencia(
            ubicacion_real="-17.78629,-63.18170",
            descripcion="El motor se sobrecalentó y sale humo.",
            prioridad=PrioridadEmergencia.alta,
            estado=EstadoEmergencia.atendiendo,
            id_vehiculo=vehiculo.id,
            id_personal=personal.id # Asignamos al mecánico Pedro
        )
        db.add(emergencia)
        db.commit()
        db.refresh(emergencia)
        print(f"✅ Emergencia Seeded: Nro {emergencia.nro} (Asignada a: {personal.nombre_completo})")

        # 7. Crear el Detalle de la Emergencia (Seguimiento GPS)
        detalle = DetalleEmergencia(
            nro_emergencia=emergencia.nro,
            tiempo_llegada_estimado="12 minutos",
            ubicacion_personal_real="-17.78400,-63.18000"
        )
        db.add(detalle)
        
        # 8. Crear un mensaje de prueba (Chat)
        mensaje = Mensajeria(
            nro_emergencia=emergencia.nro,
            id_remitente=taller.id, # El taller envía el mensaje
            mensaje="Ya enviamos a Pedro para ayudarte, Juan.",
            leido=False
        )
        db.add(mensaje)

        db.commit()
        print("✅ Flujo de Emergencia y Mensajería Seeded correctamente.")

    except Exception as e:
        db.rollback()
        print(f"❌ Error durante el seeding: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
