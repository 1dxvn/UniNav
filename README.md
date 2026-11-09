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

## Clonar ambos repositorios y ejecutar la aplicación

Son dos repositorios independientes. Primero clona el backend y después clona el frontend **dentro de la
carpeta del backend**. Mantén el nombre `UniNav-Frontend`: el servidor busca allí la interfaz compilada.
Sigue los pasos en la misma terminal. No hace falta abrir dos servidores para utilizar la aplicación completa.

### 1. Comprobar los requisitos

En Windows, abre PowerShell y ejecuta:

```powershell
git --version
py -3 --version
node --version
npm --version
```

En Linux o macOS, abre una terminal y ejecuta:

```bash
git --version
python3 --version
node --version
npm --version
```

Cada comando debe mostrar una versión. Python debe ser 3.11 o posterior y Node.js 22.12 o posterior.
Si un comando no se reconoce, instala ese requisito y vuelve a abrir la terminal antes de continuar.

### 2. Clonar el backend

Abre la terminal en la carpeta donde quieras guardar el proyecto, por ejemplo Documentos. Debe ser una
ubicación donde todavía no exista una carpeta llamada `UniNav`. Ejecuta:

```bash
git clone --depth 1 https://github.com/1dxvn/UniNav.git UniNav
cd UniNav
```

El primer comando descarga el servidor y crea la carpeta `UniNav`. El segundo entra en ella.
`--depth 1` descarga la versión actual sin el historial anterior; es suficiente para ejecutar la aplicación.

### 3. Clonar el frontend dentro del backend

Sin salir de `UniNav`, ejecuta:

```bash
git clone --depth 1 https://github.com/1dxvn/UniNav-Frontend.git UniNav-Frontend
```

Este comando crea `UniNav/UniNav-Frontend`. **No ejecutes `cd UniNav-Frontend` para el siguiente paso**:
el comando de arranque se ejecuta desde `UniNav`, donde está `start.py`.

La estructura debe quedar así:

```text
UniNav/                      # repositorio del backend; terminal situada aquí
  README.md
  start.py
  main.py
  requirements.txt
  data/
  UniNav-Frontend/            # repositorio del frontend
    README.md
    package.json
    package-lock.json
    src/
    public/models/
```

No deben quedar como carpetas hermanas `UniNav/` y `UniNav-Frontend/`, ni debe aparecer una carpeta adicional
`UniNav/UniNav/`. Cada repositorio conserva su propio historial Git; no tienes que combinarlos.

Puedes comprobar la ubicación en PowerShell:

```powershell
Test-Path .\start.py
Test-Path .\UniNav-Frontend\package.json
```

Ambos resultados deben ser `True`. En Linux o macOS, comprueba ambos archivos con:

```bash
ls start.py UniNav-Frontend/package.json
```

### 4. Instalar e iniciar

Desde `UniNav`, ejecuta el comando de tu sistema operativo.

Windows:

```powershell
py -3 start.py
```

Linux o macOS:

```bash
python3 start.py
```

El instalador detecta el frontend que acabas de clonar y lo utiliza. Después crea `.venv`, instala las
dependencias de Python y npm, comprueba los modelos, compila la interfaz y arranca el campus con
235 lugares y 218 conexiones. También crea una clave de sesión local en `.env` y la base `uninav-campus.db`.
No necesitas ejecutar `npm ci` o `npm run build` por separado para esta instalación.

La primera ejecución tarda más porque descarga las dependencias y prepara los modelos. Deja que termine
hasta que la terminal indique que el servidor inició. No necesitas Blender, planos, una base de datos previa
ni archivos de otro equipo.

### 5. Abrir la aplicación y volver a ejecutarla

Abre **http://127.0.0.1:8001/app/** en el navegador y deja la terminal abierta mientras utilizas la aplicación.
La API y la interfaz se sirven juntas en ese puerto. Detén el servidor con `Ctrl+C`.

Para abrirla otro día, entra en la carpeta `UniNav` y vuelve a ejecutar `py -3 start.py` en Windows o
`python3 start.py` en Linux/macOS. No vuelvas a clonar los repositorios: se conservan los datos existentes.

### Alternativa: descargar automáticamente el frontend

También puedes hacer solo el paso 2 y ejecutar `start.py`: si `UniNav-Frontend/` no existe, el instalador
clona automáticamente ese segundo repositorio en la ubicación correcta. El resultado es el mismo que
clonar ambos manualmente. Si ya seguiste el paso 3, no crea otra copia del frontend.

## Acceso de demostración

| Usuario de demostración | Contraseña | Función |
| --- | --- | --- |
| `student` | `demo1234` | Explorar y usar las funciones de usuario |
| `admin` | `demo1234` | Administrar lugares, recorridos y colas |

Son credenciales de demostración local. Puedes cambiar la contraseña desde la aplicación.
Para elegir la contraseña inicial de administrador, define `UNINAV_ADMIN_PASSWORD` en `.env` antes del primer arranque.

## Problemas habituales al clonar o iniciar

- **`destination path 'UniNav' already exists`:** ya hay una carpeta con ese nombre. Si es tu clon del proyecto,
  entra en ella y continúa desde el paso que falte. Si pertenece a otro proyecto, elige otra ubicación para clonar.
- **El frontend quedó fuera del backend:** la ubicación esperada es `UniNav/UniNav-Frontend/`. Revisa el árbol
  del paso 3 antes de iniciar; el repositorio del frontend por sí solo no incluye la API.
- **`start.py` no se encuentra:** la terminal está en otra carpeta. Vuelve a `UniNav`, donde están `main.py`
  y `requirements.txt`.
- **GitHub pide autenticación o responde `Repository not found`:** comprueba la URL y que tu cuenta tenga
  acceso a ambos repositorios.
- **La interfaz responde que falta el build:** ejecuta `start.py` desde el backend y espera a que termine la
  compilación. No abras `index.html` directamente desde el explorador de archivos.

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
