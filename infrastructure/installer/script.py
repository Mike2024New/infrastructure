import subprocess
import platform
from pathlib import Path

IS_WINDOWS = 'windows' in platform.system().lower()
ROOT_DIR = Path.cwd()
START_FILE = ROOT_DIR / 'start'
START_FILE_NAME = 'start'
PYTHON_EMBED_DIR = ROOT_DIR / 'python_embed'
APP_NAME = 'installer' if IS_WINDOWS else 'installer'

header_print = lambda msg: print(f'{"=" * 50}\n{msg}\n{"=" * 50}\n')

header_print(f'I.СБОРКА/ПЕРЕСБОРКА ПРОЕКТА')
header_print(f'1.Определение наличия python.')
if IS_WINDOWS:
    exe_file = PYTHON_EMBED_DIR / 'python.exe'
else:
    exe_file = PYTHON_EMBED_DIR / 'bin' / 'python'
    if not exe_file.exists():
        exe_file = PYTHON_EMBED_DIR / 'bin' / 'python3'

if not exe_file.exists():
    raise RuntimeError(
        f'Не найден встроенный python, в целевом проекте обязательно должна быть папка python_embed, с портативным Python'
    )

# 2. Проверка python
header_print(f'2.Проверка python')
cmd = [exe_file, '--version']
res = subprocess.run(cmd, capture_output=True)
if res.returncode != 0:
    raise RuntimeError(f'В embed_python находится python не совместимый с текущей системой')

# 3. Создание виртуального окружения для проекта
header_print(f'3.Создание виртуального окружения')
if not (ROOT_DIR / '.venv').exists():
    cmd = [exe_file, '-m', 'venv', '.venv']
    subprocess.run(cmd, cwd=ROOT_DIR)

if IS_WINDOWS:
    venv_python_exe = ROOT_DIR / '.venv' / 'Scripts' / 'python.exe'
else:
    venv_python_exe = ROOT_DIR / '.venv' / 'bin' / 'python'

# интеграция uv
header_print(f'4.1.Установка uv')
cmd = [venv_python_exe, '-m', 'pip', 'install', 'uv']
subprocess.run(cmd, cwd=ROOT_DIR)
header_print(f'4.2.Инициализация uv')
cmd = [venv_python_exe, '-m', 'uv', 'init']
subprocess.run(cmd, cwd=ROOT_DIR)
header_print(f'4.3.Установка зависимостей uv (pyproject.toml)')
cmd = [venv_python_exe, '-m', 'uv', 'sync']
subprocess.run(cmd, cwd=ROOT_DIR)

header_print(f'II.Запуск стартового скрипта проекта (start.py)')
cmd = [venv_python_exe, '-m', START_FILE_NAME]
subprocess.run(cmd, cwd=ROOT_DIR)
