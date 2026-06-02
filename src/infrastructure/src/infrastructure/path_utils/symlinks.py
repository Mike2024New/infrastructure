import platform
from pathlib import Path
import subprocess


def create_symlink(source_directory: Path, target_directory: Path) -> None:
    """
    Cоздание ссылки (симлинка) на папку с ресурсами (экономия дискового пространства)
    :param source_directory: исходная директория (большая папка с ресурсами)
    :param target_directory: папка в которой нужно создать ссылку на большую папку с ресурсами
    :return: None

    Пример использования:
        root_dir = get_root_dir_path() # целевая директория
        create_symlink(
            source_directory=root_dir / 'resources', # большая папка с ресурсами
            target_directory=root_dir / 'dist', # папка в которой нужно создать ссылку на большую папку с ресурсами
        )
    """
    if not source_directory.exists():
        raise RuntimeError(f'Исходной директории `{source_directory}` не существует.')

    if not source_directory.is_dir():
        raise RuntimeError(f'Путь исходной директории должен быть папкой. А сейчас `{source_directory}`.')

    if not target_directory.exists():
        raise RuntimeError(f'Целевой директории `{target_directory}` не существует.')

    if not target_directory.is_dir():
        raise RuntimeError(f'Путь целевой директории должен быть папкой. А сейчас `{source_directory}`.')

    target_full_path = target_directory / source_directory.parts[-1]
    if target_full_path.exists():
        raise RuntimeError(f'Целевая директория `{target_full_path}` уже существует.')

    if platform.system().lower() == 'windows':
        cmd = ['cmd', '/c', 'mklink', '/J', str(target_full_path), str(source_directory)]
    else:
        cmd = ['ln', '-s', str(source_directory), str(target_full_path)]

    res = subprocess.run(cmd, capture_output=True)
    if res.returncode != 0:
        raise RuntimeError(
            f'Ошибка при создании симлинка\n'
            f'return code : {res.returncode}\n'
            f'stdout: {res.stdout}\n'
            f'stderr: {res.stderr}\n'
        )
    print(
        f'Ссылка создана `{target_directory}`\n'
        f'Исходный путь: {source_directory}\n'
        f'Целевая директория: {target_full_path}\n'
    )
