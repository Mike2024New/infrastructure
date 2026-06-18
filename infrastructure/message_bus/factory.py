from infrastructure.message_bus.main import MessageBus, MessagePrintSettings, FileLogSettings
from infrastructure.message_bus.schemas import Message
from typing import Literal, Any
from uuid import uuid4
from pathlib import Path


def message_bus_factory(
        component_name: str,
        component_id: str | None = None,
        print_message: bool = True,
        message_print_settings: MessagePrintSettings | None = None,
        file_log_json_path: Path | None = None,
        file_log_settings: FileLogSettings | None = None,
):
    """
        # Пример использования
    # 1. Создать шину сообщений передав название компонента и указав, печатать ли сообщения в консоль
    message_buss = message_bus_factory(
        component_id=str(uuid4())[:8],  # уникальный идентификатор компонента (закреплен за ним всё время)
        component_name='app',  # название главного компонента
        print_message=True,  # печатать ли сообщения в консоль
        # настройки печати (с игнорированием полей если нужно)
        print_message_settings=MessagePrintSettings(
            print_date=True,
            raw_message=False,
            ignore_levels=['start', 'stop'],
            ignore_levels_invers=False,
        ),
        # активация логирования сообщений в файлы (нужно просто передать путь, если путь не передан файлов логов не будет)
        file_log_json_path=Path(logs_dir / 'log.jsonl'),
        # подключение настроек ротации файлов (если не подключены но передан путь, возьмутся по умолчанию)
        file_log_settings=FileLogSettings(
            max_size_mb=0.5, # максимальный размер одного файла
            max_files=5, # максимально файлов
            rotation_disable=False, # можно отключить ротацию
        ),
    )
    # 2. Печатать
    message_buss(
        subcomponent='audio_input',  # название подмодуля
        level='start',  # уровни события
        event='app is running',  # event
        message='Приложение запущено',  # человекочитаемое сообщение
        request_id=str(uuid4())[:8],  # id для цепочки операций
    )

    :param component_name: название компонента
    :param component_id:  уникальный идентификатор компонента (для удобства отслеживания микросервисов, это id всего приложения)
    :param print_message: печатать сообщения в консоль? (Не потребляет сообщения из шины сообещиний не делая их просмотренными)
    :param message_print_settings: опциональные настройки печати ( сырая строка или человекочитаемый вывод, игнорирование ключей и так далее )
    :param file_log_json_path: логировать сообщения в файл? если передать сюда путь, то логирование будет, иначе нет
    :param file_log_settings: опциональные настройки логирования (размер файла, и кол-во файлов)
    """
    message_bus = MessageBus(
        print_message=print_message,
        print_settings=message_print_settings,
        file_log_json_path=file_log_json_path,
        file_log_settings=file_log_settings,
    )

    def message_bus_add(
            subcomponent: str,
            level: Literal['start', 'stop', 'process', 'debug', 'info', 'warning', 'error', 'critical'],
            message: str | None = None,
            event: str | None = None,
            error: Exception | RuntimeError | None = None,
            result: dict[str, Any] | None = None,
            data: dict[str, Any] | None = None,
            request_id: str | None = None,
    ):
        """
        предзаполненная шина сообщений (component, component_id) уже заполнены
        :param subcomponent: Внутреннее название подкомпонетра, например STT.audio_input
        :param level:  уровни компонента:
        1. Специальные:    start - запуск, stop - остановка, process - работа компонента
        2. Универсальные: 'debug', 'info', 'warning', 'error', 'critical'

        :param message: Человекочитаемое понятное сообщение
        :param event: Опциональное машиночитаемое событие (для парсеров логов)
        :param error: Объект err, поствалидатор разберет на ошибку и трассировку
        :param result: если через сообщение передаются результаты
        :param data: Дополнительные даннные, например метрики
        :param request_id: Идентификатор для цепочки операций (определяется уже в самом коде)
        :return: None
        """
        message_bus.add(
            Message(
                component_id=component_id,
                component=component_name,
                # обязательные для переопределения поля (subcomponent, level)
                subcomponent=subcomponent,
                level=level,
                message=message,
                event=event,
                error=error or {},
                result=result or {},
                data=data or {},
                request_id=request_id or None,
            )
        )

    return message_bus_add


if __name__ == '__main__':
    # Пример использования
    # 1. Создать шину сообщений передав название компонента и указав, печатать ли сообщения в консоль
    message_buss = message_bus_factory(
        component_id=str(uuid4())[:8],  # уникальный идентификатор компонента (закреплен за ним всё время)
        component_name='app',  # название главного компонента
        print_message=True,  # печатать ли сообщения в консоль
        message_print_settings=MessagePrintSettings(
            print_date=True,
            raw_message=False,
            ignore_levels=['start'],
            ignore_levels_invers=False,
        ),
        # подключение настроек логирования
        # file_log_json_path=Path('logs/log.jsonl'),
        # file_log_settings=FileLogSettings(
        #     max_size_mb=10,
        #     max_files=5,
        #     rotation_disable=False,
        # )
    )
    # 2. Печатать
    message_buss(
        subcomponent='audio_input',  # название подмодуля
        level='start',  # уровни события
        event='app is running',  # event
        message='Приложение запущено',  # человекочитаемое сообщение
        # request_id=str(uuid4())[:8],  # id для цепочки операций
    )
