import tomllib
import tomli_w
from pathlib import Path
import sys

__all__ = ['TomlManager', 'TomlSettings']

from dataclasses import dataclass


@dataclass
class TomlSettings:
    project_name: str = 'MyProject'
    version: int = '0.1.0'
    requires_python: str = f">={sys.version_info.major}.{sys.version_info.minor}"
    description: str = 'Project description...'


class TomlManager:
    def __init__(self, project_path: Path, toml_settings: TomlSettings | None = None):
        self.data: dict | None = None
        self.toml_path = project_path / "pyproject.toml"
        self._init(toml_settings or TomlSettings())

    # Создание нового toml
    def _init(self, toml_settings: TomlSettings) -> None:
        if self.toml_path.exists():
            return
        # если разрастётся то можно перенести в jinja2 шаблоны
        template = {
            "project": {
                "name": toml_settings.project_name,
                "version": toml_settings.version,
                "description": toml_settings.description,
                "requires-python": toml_settings.requires_python,
                "dependencies": [],
            }
        }
        self.data = template
        self._save()

    # Сохраняет pyproject.toml
    def _save(self) -> None:
        """Сохраняет pyproject.toml"""
        self.toml_path.parent.mkdir(exist_ok=True, parents=True)
        with open(self.toml_path, "wb") as f:
            tomli_w.dump(self.data, f)

    def _load(self):
        with open(self.toml_path, "rb") as f:
            self.data = tomllib.load(f)

    def inc_version(self, major_in: bool = False, minor_in: bool = False, micro_in: bool = False) -> None:
        """
        Инкрементальный счётчик увеличения версии пакета (для простых случаев с числовыми версиями без букв)
        (Может быть полезно для автокоммитов)
        :param major_in: мажнорая версия - когда полностью меняется api и не совместим со старыми весиями
        :param minor_in: минорная версия - добавление новых фич, изменение старых функций но api обратносовместим
        :param micro_in: микроверсия - когда внесены исправления в функции ни как не задевая внешние api
        :return: None
        """
        self._load()
        try:
            version = self.data.get('project', {}).get('version', None)
            if isinstance(version, str):
                major, minor, micro = map(int, version.split('.'))
                major = major + 1 if major_in else major
                minor = minor + 1 if minor_in else minor
                micro = micro + 1 if micro_in else micro
                self.data['project']['version'] = f"{major}.{minor}.{micro}"
                self._save()
        except Exception as err:
            raise RuntimeError(f'Не удалось увеличить версию toml, причина: {err}')


if __name__ == '__main__':
    toml_manager = TomlManager(
        project_path=Path.cwd() / 'demo',
        toml_settings=TomlSettings(project_name='Demo')
    )
    toml_manager.inc_version(minor_in=True)
