# UniNav

UniNav permite explorar el campus universitario en 3D, buscar lugares y calcular rutas con A* o Dijkstra.
Incluye registro e inicio de sesión, selección de pisos, avatar, indicaciones, historial, recorridos guiados,
colas y administración. La información de usuarios e historial se conserva en SQLite.

Este repositorio contiene el servidor FastAPI y los datos del campus. La interfaz y los modelos finales están
en [UniNav-Frontend](https://github.com/1dxvn/UniNav-Frontend). La instalación automática descarga ese repositorio.

## Requisitos

- Python 3.11 o posterior, con `pip` y `venv`.
- Node.js 22.12 o posterior, con npm.
- Git y conexión a Internet durante la primera instalación.
- Navegador actualizado con WebGL 2.

En Windows, instala Python y Node.js con sus opciones de añadirlos al PATH y vuelve a abrir la terminal.
En distribuciones Linux que separan `venv`, instala también el paquete `python3-venv`.

## Ejecutar desde un clon nuevo

```bash
git clone --depth 1 https://github.com/1dxvn/UniNav.git
cd UniNav
```

En Windows:

```powershell
py -3 start.py
```

En Linux o macOS:

```bash
python3 start.py
```

El comando descarga el frontend dentro de `UniNav-Frontend/`, crea `.venv`, instala las dependencias,
comprueba los modelos, compila la interfaz y arranca el campus con 235 lugares y 218 conexiones.
También crea una clave de sesión local en `.env` y la base `uninav-campus.db`.
No necesitas Blender, planos, una base de datos previa ni archivos de otro equipo.

Abre **http://127.0.0.1:8001/app/** y deja la terminal abierta. Detén el servidor con `Ctrl+C`.
Para volver a ejecutarlo, utiliza el mismo comando; conserva los datos existentes.

| Usuario de demostración | Contraseña | Función |
| --- | --- | --- |
| `student` | `demo1234` | Explorar y usar las funciones de usuario |
| `admin` | `demo1234` | Administrar lugares, recorridos y colas |

Son credenciales de demostración local. Puedes cambiar la contraseña desde la aplicación.
Para elegir la contraseña inicial de administrador, define `UNINAV_ADMIN_PASSWORD` en `.env` antes del primer arranque.

## Configuración y comandos

```bash
python start.py --port 8002
python start.py --setup-only
```

En los ejemplos de esta sección, utiliza `py -3` en Windows o `python3` donde corresponda.
Si ya instalaste y compilaste, puedes iniciar directamente:

```powershell
# Windows
.venv\Scripts\python.exe -m scripts.run_campus --port 8001
```

```bash
# Linux / macOS
.venv/bin/python -m scripts.run_campus --port 8001
```

El servidor sirve la interfaz y la API en el mismo puerto. La documentación de la API está en
http://127.0.0.1:8001/docs y su estado en http://127.0.0.1:8001/health.
Si el puerto está ocupado, cambia `--port`. Ejecuta un solo proceso del servidor para esta base SQLite.

Variables opcionales de `.env`:

| Variable | Uso |
| --- | --- |
| `UNINAV_SECRET_KEY` | Clave de firma de sesiones; el instalador genera una automáticamente |
| `UNINAV_ADMIN_PASSWORD` | Contraseña inicial del administrador |
| `UNINAV_DATABASE_URL` | Ruta SQLite alternativa |
| `UNINAV_FRONTEND_DIST` | Carpeta de interfaz compilada alternativa |

La clave, las bases, los entornos y las dependencias instaladas se generan en cada equipo y no se versionan.
Si se mueve el proyecto, vuelve a crear su entorno de Python ejecutando `start.py` en la nueva ubicación.

## Modelos y navegación

La aplicación incluye los modelos C20 de los pisos 0–5, la vista general y la terraza como piso 6.
La terraza tiene vista previa, sin rutas propias. Los modelos actualizados conservan algunos bloqueos de
navegación conocidos: calcular una ruta no garantiza poder atravesar todos sus segmentos en 3D.

El repositorio incluye únicamente el código, los datos y los archivos de instalación necesarios para la app.
