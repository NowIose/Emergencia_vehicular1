# Estructura del Backend - Sistema de Emergencia Vehicular

## Árbol del Proyecto (Backend)

```text
Backend/
├── .env                  # Variables de entorno (Configuración, BD, Secretos)
├── alembic.ini           # Configuración de migraciones de base de datos
├── requirements.txt      # Dependencias del proyecto
├── seeds.py              # Script para población inicial de datos
├── app/                  # Núcleo de la aplicación
│   ├── main.py           # Punto de entrada (Configuración de FastAPI)
│   ├── api/              # Endpoints (rutas) de la API
│   │   └── auth.py       # Rutas para autenticación y login
│   ├── core/             # Lógica base y configuración compartida
│   │   ├── config.py     # Carga de variables de entorno
│   │   ├── database.py   # Gestión de conexión a BD y sesión de SQLAlchemy
│   │   └── security.py   # Utilidades de cifrado y JWT
│   └── modules/          # Funcionalidad por dominios
│       ├── bitacora/     # Registro de eventos/historiales
│       ├── emergencias/  # Lógica principal de gestión de emergencias
│       ├── reportes/     # Generación de informes
│       ├── usuarios/     # Gestión de usuarios y perfiles
│       └── vehiculos/    # Gestión de inventario/vehículos
└── alembic/              # Control de versiones de BD
    ├── env.py            # Configuración del entorno de migración
    └── versions/         # Archivos de migración (.py)
```

## Detalle de Módulos Principales

### 1. Módulo `usuarios`
Gestiona la identidad, roles y perfiles.

*   **Modelos (`models.py`)**: 
    *   `Usuario`: (id, email, password_hash, nombre, telefono, is_active, rol_id)
    *   `Rol`: (id, nombre_rol)
*   **Schemas (`schemas.py`)**: `UsuarioBase`, `UsuarioCreate`, `UsuarioUpdate`, `UsuarioInDB`.
*   **Endpoints (`routes.py`)**:
    *   `POST /usuarios/`: Crear usuario.
    *   `GET /usuarios/`: Listar usuarios.
    *   `GET /usuarios/{id}`: Detalle de usuario.
    *   `PUT /usuarios/{id}`: Actualizar perfil.
    *   `DELETE /usuarios/{id}`: Desactivar/Eliminar.

### 2. Módulo `emergencias`
Gestión de reportes y estado de eventos.

*   **Modelos (`models.py`)**: `Emergencia` (id, estado, descripcion, ubicacion, usuario_id, vehiculo_id, taller_id, fecha_creacion).
*   **Schemas (`schemas.py`)**: `EmergenciaCreate`, `EmergenciaUpdate`, `EmergenciaOut`.
*   **Endpoints (`routes.py`)**:
    *   `POST /emergencias/`: Reportar emergencia.
    *   `GET /emergencias/`: Listado filtrado.
    *   `PATCH /emergencias/{id}/estado`: Cambio de flujo.
    *   `GET /emergencias/{id}/detalles`: Información completa.
*   **Tiempo Real**: `websockets.py` (actualizaciones en vivo).

### 3. Módulo `vehiculos`
Gestión de inventario de vehículos.

*   **Modelos (`models.py`)**: `Vehiculo` (id, placa, marca, modelo, año, propietario_id).
*   **Schemas (`schemas.py`)**: `VehiculoBase`, `VehiculoCreate`.
*   **Endpoints (`routes.py`)**:
    *   `GET /vehiculos/`: Listar inventario.
    *   `POST /vehiculos/`: Registrar vehículo.
    *   `GET /vehiculos/{placa}`: Búsqueda por placa.

### 4. Módulo `bitacora`
Auditoría del sistema.

*   **Modelos (`models.py`)**: `Bitacora` (id, usuario_id, accion, entidad_afectada, timestamp).
*   **Schemas (`schemas.py`)**: `BitacoraBase`.
*   **Endpoints (`routes.py`)**:
    *   `GET /bitacora/`: Listar registros de auditoría.
*   **Utilidades (`utils.py`)**: Funciones para inserción automática en auditoría.

gogogo
