import traceback
from typing import Literal, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

_FMT = '%H:%M:%S.%f %d.%m.%Y'

__all__ = ['Message']


class Message(BaseModel):
    date: str = Field(default_factory=lambda: datetime.now().strftime(_FMT), description='Время происшествия.')
    component_id: str = Field(description='Уникальный id компонента, полезно для нескольких экземпляров приложения')
    component: str = Field(description='Публичное название компонента, так его видят другие API, например STT.')
    subcomponent: str = Field(description='Внутреннее название подкомпонетра, например STT.audio_input')
    level: Literal[
        'start', 'stop', 'process',  # уровни компонента, start - запуск, stop - остановка, process - работа компонента
        'debug', 'info', 'warning', 'error', 'critical'  # универсальные логи
    ]
    message: str | None = Field(default=None, description='Человекочитаемое понятное сообщение.')
    event: str | None = Field(default=None, description='Опциональное машиночитаемое событие (для парсеров логов).')
    error: Any | dict = Field(default_factory=dict,
                              description='Объект err, поствалидатор разберет на ошибку и трассировку.')
    result: dict[str, Any] = Field(default_factory=dict, description=f'если через сообщение передаются результаты.')
    data: dict[str, Any] = Field(default_factory=dict, description=f'Дополнительные даннные, например метрики.')
    request_id: str | None = Field(default=None, description='Уникальный id текущей цепочки операций')

    @field_validator('error', mode='before')  # noqa
    @classmethod
    def error_extract(cls, err):
        if err is None:
            return {}
        if isinstance(err, dict):
            return err
        if isinstance(err, Exception):
            return {
                'err': str(err),
                'traceback': ''.join(traceback.format_exception(type(err), err, err.__traceback__))
            }
        return {'err': str(err)}
