import sys
import subprocess
import platform
from pathlib import Path
from infrastructure.path_utils.path_finder import get_root_dir_path
from infrastructure.path_utils.symlinks import create_symlink
import shutil
import os

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
        create_resources_symlink: bool = False,
        clear_old_distributive: bool = True,
) -> None:
    """
    Сборщик исполнительных файлов .exe для windows, и .bin для linux.
    Путь к .venv определяется автоматически
    :param entry_point_path:
    :param name: имя выходного приложения
    :param add_data:  устанавливаемые дополнительные ассеты
    :param add_binary: устанавливаемые .dll
    :param exclude_modules: исключаемые модули и файлы (поможет облегчить сборку)
    :param one_file:  собрать .exe одним файлом? (дольше по времени загрузка приложения)
    :param console: приложение консольное?
    :param create_resources_symlink: создавать симлинк на папку с ресурсами?
    :param icon_path: путь к иконке
    :param venv_dir_name: название папки с виртуальным окружением (как правило обычно всегда .venv)
    :param clear_old_distributive: удалить следы предыдущих дистрибутивов?
    :return: None
    Пример использования:

    build(
        entry_point_path=get_root_dir_path() / 'main.py', # путь к файлу с которого начинается приложение
        name='STT', # имя приложения будет отображаться например STT.exe
        add_data=[Path('faster_whisper') / 'assets'], # дополнительные материалы
        add_binary=[], # .dll и прочие библиотеки
        exclude_modules=[], # исключаемые библиотеки (поможет облегчить сборку)
        icon_path=Path('icon.ico'), # путь к иконке (как правило лежит в root_dir)
        one_file=True, # сжать всё в один файл? (дольше по времени загрузка приложения)
        create_resources_symlink=True, # создать симлинк на папку с ресурсами? Если она есть в проекте.
    )
    """
    print('[green]Сборка приложения[/green]')

    # проверка входного пути
    if entry_point_path.parts[-1] != '.py':
        RuntimeError(f'Входной путь должен быть .py файлом, а на вход подан `{entry_point_path}`')
    if not entry_point_path.exists():
        RuntimeError(f'Входной путь `{entry_point_path}` не существует.')

    # определение системных путей
    root_dir = get_root_dir_path(venv_dir_name=venv_dir_name)
    is_windows = platform.system().lower() == 'windows'
    separator = ";" if is_windows else ":"
    ext = ".dll" if is_windows else ".so"
    python_lib = f"Lib\\site-packages" if is_windows else f"lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages"
    python_lib = root_dir / '.venv' / python_lib

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

    distributive_path = root_dir / 'dist'
    build_folder_path = root_dir / 'build'
    file_spec_path = root_dir / f'{name}.spec'

    # очистка следов предыдущего проекта
    if clear_old_distributive:
        if distributive_path.exists():
            shutil.rmtree(distributive_path)
        if build_folder_path.exists():
            shutil.rmtree(build_folder_path)
        if file_spec_path.exists():
            os.remove(file_spec_path)

    result = subprocess.run(cmd, shell=is_windows)
    if result.returncode != 0:
        raise RuntimeError(
            f'Ошибка сборки приложения:\n'
            f'returncode: {result.returncode}\n'
            f'stdout: {result.stdout}\n'
            f'stderr: {result.stderr}\n'
        )

    resources_dir = root_dir / 'resources'
    if create_resources_symlink:
        if not resources_dir.exists():
            print(f'Симлинк не создан так как в корне отсутствует папка resources.')
        # создание симлинка на папку с ресурсами
        create_symlink(
            source_directory=root_dir / 'resources',
            # если не один файл то симлинк вложенный
            target_directory=distributive_path / name if not one_file else distributive_path,

        )
    print(f'[green]Приложение собрано. {distributive_path.parent}[/green]')
