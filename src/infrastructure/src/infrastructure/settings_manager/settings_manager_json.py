from pathlib import Path
from typing import TypeVar, Generic, Type
from pydantic import BaseModel
import atexit

T = TypeVar('T', bound=BaseModel)

__all__ = ['get_settings_manager']


class SettingsManager(Generic[T]):
    def __init__(
            self,
            json_file_path: Path,
            settings_model: T,
    ):
        # инициализация объектов
        self.json_file_path = json_file_path
        self.settings: T | None = None  # настройки которые будут выгружены из файла
        self._default_settings = settings_model  # настройки по умолчанию из модели
        self._model_class: Type[T] = type(settings_model)  # для типизации
        atexit.register(self.save)  # сохранение настроек при выходе
        # чтение настроек
        self.read()

    def read(self) -> None:
        """Чтение настроек из файла json"""

        # если файл с настройками не существует, то создать его
        if not self.json_file_path.exists():
            self.reset()
            return

        try:
            with open(file=self.json_file_path, mode='r', encoding='utf-8') as f:
                settings = f.read()
                self.settings = self._model_class.model_validate_json(settings)
        except Exception:  # noqa
            self.reset()

    def save(self) -> None:
        """Сохранение настроек в json"""
        settings = self.settings if self.settings is not None else self._default_settings

        with open(file=self.json_file_path, mode='w', encoding='utf-8') as f:
            f.write(settings.model_dump_json(ensure_ascii=True, indent=2))

    def apply_new_settings(self, settings: T) -> None:
        """
        Применить новые настройки соответствующие переданной схеме настроек. (Например для эндпоинта fastapi)
        """
        try:
            # обновление настроек с проверкой
            new_settings = self._model_class.model_validate(settings)
            self.settings = new_settings
        except Exception as err:
            raise f"Ошибка изменения настроек: {err}"
        self.save()

    def reset(self) -> None:
        """сброс и сохранение настроек"""
        self.settings = None
        self.save()  # сохранить настройки (даже если файл ещё не был создан, то сделать это сейчас)
        self.read()  # прочитать записанные настройки


def get_settings_manager(
        json_file_path: Path,
        settings_model: T,
) -> SettingsManager[T]:
    """
    :param json_file_path: путь и имя файла сохранения настроек, например settings.json
    :param settings_model: класс с настройками на базе pydantic схемы
    :return: класс управленец настройками. Настройки в приложениях можно снимать через ключ settings
    """
    return SettingsManager[T](
        json_file_path=json_file_path,
        settings_model=settings_model,
    )


if __name__ == '__main__':
    # Пример использования класса
    # вложенная модель с настройками
    class AudioInputSettings(BaseModel):
        samplerate: int = 16000
        blocksize: int = 1024
        channels: int = 2


    # главная модель с настройками
    class SttSettings(BaseModel):
        stt_model: str = 'whisper'
        audio_settings: AudioInputSettings


    # в schemas модуля (файле где объявлены схемы) создать экземпляр настроек с всеми вложенными моделями
    demo_settings = SttSettings(audio_settings=AudioInputSettings())

    # получение менеджера с настройками
    settings_manager = get_settings_manager(
        json_file_path=Path('settings.json'),
        settings_model=demo_settings,
    )
    print(settings_manager.settings)
    settings_manager.settings.audio_settings.blocksize = 320
    settings_manager.save()
    input(f'enter чтобы выйти')
    print(settings_manager.settings)
    input(f'enter чтобы выйти')
    settings_manager.reset()
