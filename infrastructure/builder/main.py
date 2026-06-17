import sys
import subprocess
import platform
from pathlib import Path
from infrastructure.path_utils.path_finder import get_root_dir_path
from infrastructure.path_utils.symlinks import create_symlink
from infrastructure.path_utils.open_folder import open_folder
import shutil
import os
from dataclasses import dataclass, field

"""
Сборщик исполнительных файлов .exe для windows, и .bin для linux
"""

ROOT_DIR = get_root_dir_path()


@dataclass
class BuildParameters:
    """
    :param entry_point_path:
    :param name: имя выходного приложения
    :param add_data:  устанавливаемые дополнительные ассеты
    :param add_binary: устанавливаемые .dll
    :param excluded: исключаемые модули и файлы (поможет облегчить сборку)
    :param one_file:  собрать .exe одним файлом? (дольше по времени загрузка приложения)
    :param console: приложение консольное?
    :param create_resources_symlink: создавать симлинк на папку с ресурсами?
    :param icon_path: путь к иконке
    :param venv_dir_name: название папки с виртуальным окружением (как правило обычно всегда .venv)
    :param clear_old_distributive: удалить следы предыдущих дистрибутивов?
    :param open_folder: открыть папку с дистрибутивом после создания дистрибутива
    :param copy_dirs: копируемые директории, список заполненный кортежами вида (<копируемая папка>, <её название в папке дистрибутива>)
    :return: None
    Пример заполнения:
    BuildParameters(
        entry_point_path=get_root_dir_path() / 'main.py', # путь к файлу с которого начинается приложение
        name='STT', # имя приложения будет отображаться например STT.exe
        add_data=[Path('faster_whisper') / 'assets'], # дополнительные материалы
        add_binary=[], # .dll и прочие библиотеки
        excluded=[], # исключаемые библиотеки (поможет облегчить сборку)
        icon_path=Path('icon.ico'), # путь к иконке (как правило лежит в root_dir)
        one_file=True, # сжать всё в один файл? (дольше по времени загрузка приложения)
        create_resources_symlink=True, # создать симлинк на папку с ресурсами? Если она есть в проекте.
        open_folder=True # открыть папку с дистрибутивом после создания дистрибутива
        copy_dirs=[(./add_dir, 'dir_name'), (./add_dir2, 'dir_name2'),] # копируемые директории
    )
    """
    name: str = 'APP'
    entry_point_path: Path = ROOT_DIR / 'main.py'
    icon_path: Path = ROOT_DIR / 'resources' / 'images' / 'icon.ico'
    one_file: bool = True
    console: bool = True
    create_resources_symlink: bool = True
    clear_old_distributive: bool = True
    # не трогать, поля ниже. Заполнятся автоматически (то что в них попадет определяется в app/_engine/registry.py
    add_data: list[Path] = field(default_factory=list)
    add_binary: list[Path] = field(default_factory=list)
    excluded: list[Path] = field(default_factory=list)
    venv_dir_name: str = '.venv'
    open_folder: bool = False  # открыть папку после создания дистрибутива
    copy_dirs: list[tuple[Path, str]] = field(default_factory=list)  # список файлов для копирования


def build(parameters: BuildParameters) -> None | Path:
    """
    Сборщик исполнительных файлов .exe для windows, и .bin для linux.
    Путь к .venv определяется автоматически
    :param parameters:  Класс BuildParameters с настройками
    :return: None
    Пример использования:

    build(
        parameters = BuildParameters( ... настройки приложения ... )
    )
    """
    print('[green]Сборка приложения[/green]')

    # проверка входного пути
    if parameters.entry_point_path.parts[-1] != '.py':
        RuntimeError(f'Входной путь должен быть .py файлом, а на вход подан `{parameters.entry_point_path}`')
    if not parameters.entry_point_path.exists():
        RuntimeError(f'Входной путь `{parameters.entry_point_path}` не существует.')

    # определение системных путей
    root_dir = get_root_dir_path(venv_dir_name=parameters.venv_dir_name)
    is_windows = platform.system().lower() == 'windows'
    separator = ";" if is_windows else ":"
    ext = ".dll" if is_windows else ".so"
    python_lib = f"Lib\\site-packages" if is_windows else f"lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages"
    python_lib = root_dir / '.venv' / python_lib

    # выходные файлы
    releases_folder_path = root_dir / 'releases' / 'win' if is_windows else root_dir / 'releases' / 'linux'
    distributive_path = releases_folder_path / 'dist'
    build_folder_path = releases_folder_path / 'build'
    file_spec_path = releases_folder_path / f'{parameters.name}.spec'

    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--name', parameters.name,
        f'--distpath', distributive_path,
        '--exclude-module', Path(__file__).stem,
        '--workpath', build_folder_path,
        '--specpath', file_spec_path.parent,
    ]

    # исключаемые модули
    if parameters.excluded is not None:
        for e in parameters.excluded:
            cmd.extend(['--exclude-module', e])

    # сборка бинарных файлов (.dll, библиотек)
    if parameters.add_binary is not None:
        for binary in parameters.add_binary:
            binary_path = python_lib / binary
            # сборка .dll или .so файлов
            for f in binary_path.iterdir():
                if str(f).endswith(ext):
                    cmd.extend(['--add-binary', f'{f}{separator}{binary}'])

    # сборка data
    if parameters.add_data is not None:
        for d in parameters.add_data:
            data_path = python_lib / d
            cmd.extend(['--add-data', f'{str(data_path)}{separator}{d}'])

    # собирать приложение 1 файлом
    if parameters.one_file:
        cmd.append('--onefile')

    # приложение консольное или нет
    cmd.append('--console') if parameters.console else cmd.append('--noconsole')

    # добавление иконки
    if parameters.icon_path.exists():
        cmd.append(f'--icon={str(parameters.icon_path)}')

    cmd.append(str(parameters.entry_point_path))

    # очистка следов предыдущего проекта
    if parameters.clear_old_distributive:
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
    if parameters.create_resources_symlink:
        if not resources_dir.exists():
            print(f'Симлинк не создан так как в корне отсутствует папка resources.')
        # создание симлинка на папку с ресурсами
        create_symlink(
            source_directory=root_dir / 'resources',
            # если не один файл то симлинк вложенный
            target_directory=distributive_path / parameters.name if not parameters.one_file else distributive_path,

        )

    # копирование заданных файлов
    if parameters.copy_dirs:
        for target_dir, name in parameters.copy_dirs:
            shutil.copytree(str(target_dir), distributive_path / name)

    # открытие папки в конце файла
    if parameters.open_folder:
        open_folder(path=distributive_path)

    print(f'[green]Приложение собрано. {distributive_path.parent}[/green]')
    return distributive_path
