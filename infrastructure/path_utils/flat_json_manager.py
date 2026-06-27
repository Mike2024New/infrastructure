from pathlib import Path
import json
from threading import Lock
from typing import Any


class FlatJsonManager:
    """
    Простой json менеджер для плоской структуры словарей (Ключ значение), например:
    { 'key1' : 'val1', 'key2' : 'val2', }
    """

    def __init__(self, prompt_file_path: Path):
        self._prompt_file_path = prompt_file_path
        self._lock = Lock()
        self._init()  # для создания файла сразу

    def get(self, key: str, default=None) -> Any:
        """Получение значения по конкретонму ключу"""
        with self._lock:
            data = self._read()
            return data.get(key, default)

    def data(self) -> dict[str, Any]:
        """Полностью выгрузить весь словарь с данными"""
        data = self._read()
        return data

    def add(self, key: str, value: Any) -> None:
        """
        Добавить ключ значение в словарь
        """
        with self._lock:
            data = self._read()
            data[key] = value
            self._save(data)

    def remove(self, key: str) -> None:
        """
        Удалить значение по ключу
        """
        with self._lock:
            data = self._read()
            if key in data.keys():
                del data[key]
                self._save(data)

    def _save(self, data: dict) -> None:
        """Запись файла json"""
        with open(self._prompt_file_path, mode='w', encoding='utf-16') as f:
            f.write(json.dumps(data, ensure_ascii=False, indent=2))

    def _init(self) -> None:
        """Создание пустого файла (если ещё нет)"""
        if not self._prompt_file_path.exists():
            self._save(data={})

    def _read(self) -> dict[str, Any]:
        """Чтение файла json, если файла нет то создание нового"""
        with open(self._prompt_file_path, mode='r', encoding='utf-16') as f:
            data = json.loads(f.read())
        return data


if __name__ == '__main__':
    pm = FlatJsonManager(prompt_file_path=Path('prompts.json'))
    pm.add(key='prompt1', value='Привет! Давай просто пообщаемся.')
    pm.add(key='prompt2', value='Привет! Давай просто пообщаемся.')
    pm.add(key='prompt3', value='Привет! Давай просто пообщаемся.')
    pm.remove(key='prompt1')
    print(pm.data())
    print(pm.get(key='prompt2'))
