"""Prepare and run UniNav from a fresh clone using only Python's standard library."""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import venv

ROOT = Path(__file__).resolve().parent
FRONTEND = ROOT / 'UniNav-Frontend'


def run(command: list[str], cwd: Path = ROOT) -> None:
    subprocess.run(command, cwd=cwd, check=True)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description='Instala las dependencias y ejecuta UniNav.')
    parser.add_argument('--port', type=int, default=8001)
    parser.add_argument('--setup-only', action='store_true', help='Prepara la aplicación sin iniciar el servidor.')
    args = parser.parse_args()
    if sys.version_info < (3, 11):
        parser.error('Se necesita Python 3.11 o posterior.')
    if not 0 <= args.port <= 65535:
        parser.error('El puerto debe estar entre 0 y 65535.')
    npm = shutil.which('npm.cmd' if os.name == 'nt' else 'npm')
    node = shutil.which('node')
    if not npm or not node:
        parser.error('Instala Node.js 22.12 o posterior y vuelve a abrir la terminal.')
    version = subprocess.check_output([node, '--version'], text=True).strip().lstrip('v')
    if tuple(map(int, version.split('.')[:2])) < (22, 12):
        parser.error('Se necesita Node.js 22.12 o posterior.')
    if not FRONTEND.exists():
        git = shutil.which('git')
        if not git:
            parser.error('Instala Git para descargar UniNav-Frontend.')
        print('Descargando UniNav-Frontend...', flush=True)
        run([git, 'clone', '--depth', '1', 'https://github.com/1dxvn/UniNav-Frontend.git', str(FRONTEND)])
    if not (FRONTEND / 'package.json').is_file():
        parser.error(f'{FRONTEND} existe pero no contiene el frontend. Revisa esa carpeta.')
    environment = ROOT / '.venv'
    python = environment / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    if not python.is_file():
        print('Creando el entorno de Python...', flush=True)
        venv.EnvBuilder(with_pip=True).create(environment)
    requirements_stamp = environment / 'requirements.sha256'
    expected = digest(ROOT / 'requirements.txt')
    if not requirements_stamp.exists() or requirements_stamp.read_text() != expected:
        print('Instalando dependencias del servidor...', flush=True)
        run([str(python), '-m', 'pip', 'install', '--disable-pip-version-check', '-r', 'requirements.txt'])
        requirements_stamp.write_text(expected)
    dependency_stamp = FRONTEND / 'node_modules/.uninav-lock.sha256'
    expected = digest(FRONTEND / 'package-lock.json')
    if not dependency_stamp.exists() or dependency_stamp.read_text() != expected:
        print('Instalando dependencias del frontend...', flush=True)
        run([npm, 'ci'], FRONTEND)
        dependency_stamp.write_text(expected)
    print('Compilando la aplicación...', flush=True)
    run([npm, 'run', 'build'], FRONTEND)
    env_file = ROOT / '.env'
    if not env_file.exists():
        with env_file.open('x', encoding='utf-8') as output:
            output.write('UNINAV_SECRET_KEY=' + secrets.token_urlsafe(48) + '\n')
    if args.setup_only:
        print('UniNav está preparado. Ejecuta este mismo comando sin --setup-only para iniciar.')
        return 0
    print(f'Abre http://127.0.0.1:{args.port}/app/ al iniciar el servidor. Ctrl+C para detener.', flush=True)
    run([str(python), '-m', 'scripts.run_campus', '--profile', 'ucc-six-floors-c18', '--port', str(args.port)])
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print('\nServidor detenido.')
    except (OSError, subprocess.CalledProcessError) as error:
        print(f'No se pudo iniciar UniNav: {error}', file=sys.stderr)
        raise SystemExit(1)
