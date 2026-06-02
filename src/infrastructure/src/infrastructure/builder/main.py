import sys
import subprocess
import platform
from pathlib import Path
from infrastructure.path_utils.path_finder import get_root_dir_path

"""
Сборщик исполнительных файлов .exe для windows, и .bin для linux
"""


def build(
        entry_point_path: Path,
        name: str,
        add_data: list[Path] | None = None,
        add_binary: list[Path] | None = None,
        exclude_modules: list[Path] | None = None,
        one_file: bool = False,
        console: bool = True,
        icon_path: Path = Path('icon.ico'),
        venv_dir_name: str = '.venv',
)->None:
    """
    Сборщик исполнительных файлов .exe для windows, и .bin для linux.
    Путь к .venv определяется автоматически
    :param entry_point_path:
    :param name: имя выходного приложения
    :param add_data:  устанавливаемые дополнительные ассеты
    :param add_binary: устанавливаемые .dll
    :param exclude_modules: исключаемые модули и файлы
    :param one_file:  собрать .exe одним файлом?
    :param console: приложение консольное?
    :param icon_path: путь к иконке
    :param venv_dir_name: название папки с виртуальным окружением (как правило обычно всегда .venv)
    :return: None
    Пример использования:

    build(
        entry_point_path=Path(r'S:\_projects\python\SERVICES\STT\main.py'),
        name='STT',
        add_data=[Path('faster_whisper') / 'assets'],
        add_binary=[],
        exclude_modules=[],
        icon_path=Path('icon.ico'),
        one_file=False,
    )
    """
    print('[green]Сборка приложения[/green]')

    # проверка входного пути
    if entry_point_path.parts[-1] != '.py':
        RuntimeError(f'Входной путь должен быть .py файлом, а на вход подан `{entry_point_path}`')
    if not entry_point_path.exists():
        RuntimeError(f'Входной путь `{entry_point_path}` не существует.')

    # определение системных путей
    is_windows = platform.system().lower() == 'windows'
    separator = ";" if is_windows else ":"
    ext = ".dll" if is_windows else ".so"
    python_lib = f"Lib\\site-packages" if is_windows else f"lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages"
    python_lib = get_root_dir_path(venv_dir_name=venv_dir_name) / '.venv' / python_lib

    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--name', name,
        '--exclude-module', Path(__file__).stem,
    ]

    # исключаемые модули
    if exclude_modules is not None:
        for e in exclude_modules:
            cmd.extend(['--exclude-module', e])

    # сборка бинарных файлов (.dll, библиотек)
    if add_binary is not None:
        for binary in add_binary:
            binary_path = python_lib / binary
            # сборка .dll или .so файлов
            for f in binary_path.iterdir():
                if str(f).endswith(ext):
                    cmd.extend(['--add-binary', f'{f}{separator}{binary}'])

    # сборка data
    if add_data is not None:
        for d in add_data:
            data_path = python_lib / d
            cmd.extend(['--add-data', f'{str(data_path)}{separator}{d}'])

    # собирать приложение 1 файлом
    if one_file:
        cmd.append('--onefile')

    # приложение консольное или нет
    cmd.append('--console') if console else cmd.append('--noconsole')

    # добавление иконки
    if icon_path.exists():
        cmd.append(f'--icon={str(icon_path)}')

    cmd.append(str(entry_point_path))
    print(cmd)

    distributive_path = Path(__file__).parent / 'dist'
    result = subprocess.run(cmd, shell=is_windows)
    if result.returncode != 0:
        raise RuntimeError(
            f'Ошибка сборки приложения:\n'
            f'returncode: {result.returncode}\n'
            f'stdout: {result.stdout}\n'
            f'stderr: {result.stderr}\n'
        )
    print(f'[green]Приложение собрано. {distributive_path.parent}[/green]')
