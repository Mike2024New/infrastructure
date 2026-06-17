import os
import sys
import subprocess
from pathlib import Path


def open_folder(path: Path | str) -> None:
    """
    Кросплатформенное открытие папки
    :param path: путь к папке
    :return: None
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Путь не существует: {path}")

    if not path.is_dir():
        raise NotADirectoryError(f"Указан файл, а не папка: {path}")

    try:
        if sys.platform == 'win32':
            # Windows
            os.startfile(str(path))
            return None

        elif sys.platform == 'darwin':
            # macOS
            subprocess.run(['open', str(path)], check=True)
            return None

        else:
            # обход команд открытия linux и других unix подобных систем
            commands = [
                ['xdg-open', str(path)],  # Стандартный для Linux
                ['nautilus', str(path)],  # GNOME
                ['dolphin', str(path)],  # KDE
                ['thunar', str(path)],  # XFCE
                ['pcmanfm', str(path)],  # LXDE
                ['caja', str(path)],  # MATE
                ['nemo', str(path)],  # Cinnamon
            ]

            for cmd in commands:
                try:
                    subprocess.run(cmd, check=True, capture_output=True)
                    return None
                except (subprocess.SubprocessError, FileNotFoundError):
                    continue
            else:
                raise RuntimeError("Не найдено ни одного файлового менеджера")


    except Exception:
        raise


if __name__ == '__main__':
    # пример использования
    from pathlib import Path

    open_folder(path=Path.cwd())
