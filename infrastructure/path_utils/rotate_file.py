import os
from pathlib import Path
from functools import wraps

__all__ = ['rotate_file_by_size']


def rotate_file_by_size(
        max_size_mb: int | float = 10, max_files: int = 5, index_separator: str = '~',
        path_key_name: str = 'file_path', disable: bool = False,
):
    """
    Универсальный ротатор файлов по размеру и количеству файлов.
    Навешивается на операции записи файлов. Пример использования:

    @rotate_file_by_size(max_size_mb=10, max_files=5) # декоратор с настройками
    def write_log(file_path: Path, content: dict): # функция обёртка для операции записи
        with open(file=file_path, mode='a', encoding='utf-8') as f: # операция записи, в неё передается оригинальное имя файла
            f.write(json.dumps(content) + '\n')

    :param disable: отключить декоратор (режим байпас)
    :param max_size_mb: ограничение файла по размеру
    :param max_files: максимальное кол-во файлов
    :param index_separator: служебный разделитель между оригинальным названием файла и индексом например ~ , тогда до 'file.txt' после 'file~0.txt'
    :param path_key_name: название ключа из функции операции записи в котором передается путь
    :return: результат выполнения функции если она что-то возвращает
    """
    max_size_bytes = max_size_mb * 1024 * 1024

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if disable:  # пропуск действий декоратора в случае отключенного режима
                return func(*args, **kwargs)

            if path_key_name not in kwargs:
                raise RuntimeError(
                    f'Ошибка rotate_file декораторе: в декоратор необходимо передать путь с ключом `{path_key_name}`'
                )
            if '~' in str(kwargs[path_key_name].name):
                raise RuntimeError(
                    f'Ошибка rotate_file декораторе: в названии файла указан символ `{index_separator}`, он является служебным разделителем для логов.'
                )

            file_path = Path(kwargs[path_key_name])
            file_dir = file_path.parent
            file_stem = file_path.stem
            file_suffix = file_path.suffix

            # Всегда писать файл с индексом ~0
            current_file = file_dir / f'{file_stem}{index_separator}0{file_suffix}'

            # Если текущий файл существует и превысил лимит — ротировать
            if current_file.exists() and current_file.stat().st_size > max_size_bytes:
                # Удаление старого
                oldest = file_dir / f'{file_stem}{index_separator}{max_files}{file_suffix}'
                if oldest.exists():
                    os.remove(oldest)

                # Сдвиг: ~4 → ~5, ~3 → ~4, ..., ~0 → ~1
                for i in range(max_files, 0, -1):
                    old = file_dir / f'{file_stem}{index_separator}{i - 1}{file_suffix}'
                    new = file_dir / f'{file_stem}{index_separator}{i}{file_suffix}'
                    if old.exists():
                        os.replace(old, new)

            kwargs[path_key_name] = str(current_file)
            return func(*args, **kwargs)

        return wrapper

    return decorator


def test():
    # пример использования и тест:
    import json
    from datetime import datetime

    # Использование:
    @rotate_file_by_size(max_size_mb=0.1, max_files=5, index_separator='~', path_key_name='file_path', disable=False)
    def write_log(file_path: Path, content: dict):
        with open(file=file_path, mode='a', encoding='utf-8') as f:
            f.write(json.dumps(content) + '\n')

    path = Path('logs/log.jsonl')
    for j in range(10000):
        # При создании нового файла:
        timestamp = datetime.now().strftime('%H:%M:%S.%f %d.%m.%Y')
        write_log(file_path=path, content={"message": f"Msg for example {j}", "timestamp": timestamp})

    for p in path.parent.iterdir():
        print(p.name)


if __name__ == '__main__':
    test()
