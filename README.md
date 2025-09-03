# Guía de Desarrollador - App Task

## 1. Descripción General

Esta es una aplicación de backend construida con **FastAPI** que sirve como un sistema de gestión de tareas. La aplicación está completamente dockerizada para un fácil despliegue y desarrollo.

**Pila Tecnológica:**
- **Framework:** FastAPI
- **Base de Datos:** PostgreSQL (asíncrona con `asyncpg`)
- **ORM:** SQLAlchemy (con soporte `asyncio`)
- **Validación de Datos:** Pydantic
- **Autenticación:** JWT (JSON Web Tokens)
- **Migraciones de BD:** Alembic
- **Contenerización:** Docker & Docker Compose

---

## 2. Configuración y Puesta en Marcha

### Prerrequisitos
- Docker
- Docker Compose

### Pasos para Ejecutar la Aplicación

1.  **Clonar el Repositorio:**
    ```bash
    git clone <url-del-repositorio>
    cd app_task
    ```

2.  **Configurar Variables de Entorno:**
    Crea un archivo `.env` en el directorio `app/` copiando el ejemplo `env_example` que se encuentra en la raíz.
    ```bash
    cp env_example app/.env
    ```
    El archivo `env_example` ya contiene los valores por defecto que funcionan con `docker-compose.yml`. No necesitas modificarlo para levantar el entorno local.

3.  **Levantar los Contenedores:**
    Desde el directorio raíz del proyecto, ejecuta:
    ```bash
    docker-compose up --build
    ```
    Este comando construirá la imagen de la aplicación de FastAPI y levantará dos servicios: `db` (PostgreSQL) y `app` (FastAPI).

4.  **Acceder a la Aplicación:**
    - La API estará disponible en `http://localhost:8000`.
    - La documentación interactiva de la API (Swagger UI) está en `http://localhost:8000/docs`.
    - La base de datos PostgreSQL es accesible en el puerto `5433` del host.

5.  **Usuario Administrador por Defecto:**
    Al iniciar, la aplicación crea automáticamente un usuario administrador si no existe:
    - **Email:** `admin@task.com`
    - **Password:** `admin`

---

## 3. Estructura del Proyecto

El proyecto sigue una estructura modular para separar responsabilidades.

```
/
├── app/
│   ├── alembic.ini         # Configuración de Alembic para migraciones.
│   ├── config.py           # Carga y gestiona las variables de entorno.
│   ├── Dockerfile            # Instrucciones para construir la imagen de la app.
│   ├── entrypoint.sh       # Script que se ejecuta al iniciar el contenedor.
│   ├── main.py             # Punto de entrada de FastAPI, define la app y routers.
│   ├── requirements.txt      # Dependencias de Python.
│   │
│   ├── api/                # Módulos de la API (endpoints).
│   │   ├── auth.py         # Endpoints para autenticación (login, register, logout).
│   │   ├── tasks.py        # Endpoints para el CRUD de Tareas.
│   │   └── user.py         # Endpoints para el CRUD de Usuarios (protegido por rol Admin).
│   │
│   ├── core/               # Componentes base de la aplicación.
│   │   ├── base.py         # Base declarativa de SQLAlchemy para los modelos.
│   │   ├── dependencies.py # Dependencias de FastAPI (ej. obtener usuario actual).
│   │   ├── security.py     # Lógica para crear y decodificar JWT.
│   │   ├── session.py      # Gestión de la sesión de la base de datos asíncrona.
│   │   └── token_blacklist.py # Lógica para invalidar tokens (logout).
│   │
│   ├── migrations/         # Scripts de migración de Alembic.
│   │
│   ├── models/             # Modelos de datos de SQLAlchemy (tablas de la BD).
│   │   ├── task.py         # Modelo Task.
│   │   └── user.py         # Modelos User y Log.
│   │
│   ├── schemas/            # Esquemas de Pydantic para validación y serialización.
│   │   ├── task_schema.py  # Esquemas para la data de Tareas.
│   │   └── user_schema.py  # Esquemas para la data de Usuarios y Auth.
│   │
│   ├── services/           # Lógica de negocio.
│   │   ├── task_service.py # Funciones que interactúan con el modelo Task.
│   │   └── user_service.py # Funciones que interactúan con el modelo User.
│   │
│   └── utils/              # Utilidades y Mixins.
│       └── mixins.py       # Mixins para modelos (SoftDelete, Timestamps).
│
├── docker-compose.yml      # Orquesta los servicios de la app y la BD.
├── env_example             # Plantilla para las variables de entorno.
└── ...
```

---

## 4. Módulos y Funcionalidades

### Configuración (`app/config.py`)
Carga las variables de entorno desde el archivo `app/.env` utilizando `python-dotenv`. Provee un objeto `settings` global para acceder a la configuración.

### API Endpoints (`app/api/`)
- **Autenticación (`/auth`):**
    - `POST /register`: Crea un nuevo usuario y retorna un token.
    - `POST /login`: Autentica un usuario y retorna un token en una cookie `httpOnly`.
    - `GET /logout`: Invalida el token del usuario y lo elimina de las cookies.
    - `GET /me`: Devuelve los datos del usuario autenticado.
- **Usuarios (`/users`):** (Requiere rol de Administrador)
    - `GET /`: Lista todos los usuarios.
    - `GET /filter`: Filtra y busca usuarios.
    - `GET /{user_id}`: Obtiene un usuario específico.
    - `PUT /{user_id}`: Actualiza un usuario.
    - `DELETE /{user_id}`: Desactiva un usuario (soft delete).
    - `POST /activate/{user_id}`: Reactiva un usuario.
- **Tareas (`/tasks`):**
    - `GET /`: Lista las tareas del usuario autenticado.
    - `POST /`: Crea una nueva tarea para el usuario autenticado.
    - `GET /filter`: Filtra y busca tareas.
    - `GET /{task_id}`: Obtiene una tarea específica (solo si es el propietario).
    - `PUT /{task_id}`: Actualiza una tarea (solo si es el propietario).
    - `DELETE /{task_id}`: Elimina una tarea (soft delete, solo si es el propietario).

### Modelos de Datos (`app/models/`)
- **User:** Almacena la información del usuario. Campos como `email` y `password` son encriptados en la base de datos usando `sqlalchemy_utils.StringEncryptedType`.
- **Task:** Almacena las tareas. También utiliza encriptación para `task_name` y `description`.
- **Log:** Guarda un registro de acciones importantes (creación de usuarios, tareas, etc.).

### Lógica de Negocio (`app/services/`)
Abstrae las operaciones de la base de datos de los endpoints. Contiene toda la lógica para crear, leer, actualizar y eliminar registros, asegurando que los endpoints en `api/` se mantengan simples y centrados en manejar la solicitud/respuesta HTTP.

### Seguridad
- **Autenticación:** Se maneja con JWT. El token se genera en el login/registro y se valida en cada petición a endpoints protegidos a través de la dependencia `get_current_user`.
- **Encriptación en BD:** Datos sensibles como el email del usuario, contraseña y nombre de la tarea se encriptan directamente en la base de datos gracias a la `DB_SECRET_KEY`.

---

## 5. Base de Datos y Migraciones

El proyecto utiliza **Alembic** para gestionar las migraciones del esquema de la base de datos.

- **Configuración:** `alembic.ini` y `app/migrations/env.py`.
- **Crear una nueva migración:** Si realizas cambios en los modelos de `app/models/`, debes generar un nuevo script de migración:
  ```bash
  # Dentro del contenedor de la app
  docker exec -it todos_app bash

  # Luego, dentro del contenedor
  alembic revision --autogenerate -m "Descripción breve de los cambios"
  ```
- **Aplicar migraciones:** Para aplicar las migraciones a la base de datos:
  ```bash
  # Dentro del contenedor de la app
  alembic upgrade head
  ```
  El `entrypoint.sh` ya ejecuta `alembic upgrade head` cada vez que el contenedor se inicia para asegurar que la base de datos esté siempre actualizada.