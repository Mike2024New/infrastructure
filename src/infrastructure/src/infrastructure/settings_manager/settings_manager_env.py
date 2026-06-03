from infrastructure.path_utils.path_finder import get_root_dir_path
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Type, TypeVar

_T = TypeVar('_T', bound=BaseSettings)

__all__ = ['SettingsEnvModel', 'load_settings_env']


class SettingsEnvModel(BaseSettings):
    model_config = SettingsConfigDict(
        extra='ignore',  # скипать не нужные поля
    )


@lru_cache(maxsize=1)
def load_settings_env(settings_class: Type[_T], env_prefix: str) -> _T:
    """
    Загрузка pydantic-settings конфигурации из .env
    :param settings_class: Pydantic-settings класс с описанными полями
    :param env_prefix: префикс полей, например POSTGRES_
    :return: настройки прочиннанные из settings_class

    Пример:
    # эта модель может быть любой (здесь для примера такая)
    class MySettings(Settings):
        username : str = ...

    settings = load_settings(settings_class=MySettings, env_prefix='POSTGRES_')
    print(settings.username)

    # Тогда .env должен выглядеть так:
    --------------------------------------------------------
    POSTGRES_USER_NAME='YourName'
    --------------------------------------------------------
    """
    env_file = get_root_dir_path() / '.env'
    return settings_class(_env_file=env_file, _env_prefix=env_prefix)


if __name__ == '__main__':
    class MySettings(SettingsEnvModel):
        user_name: str = ...


    env_settings = load_settings_env(settings_class=MySettings, env_prefix='POSTGRES_')
    print(env_settings.user_name)
