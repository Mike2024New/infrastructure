from infrastructure.message_bus.main import MessageBus
from infrastructure.message_bus.schemas import Message
from typing import Literal, Any
from uuid import uuid4


def message_bus_factory(component_name: str, component_id: str | None = None, print_message: bool = True):
    """
    # Пример использования
    # 1. Создать шину сообщений передав название компонента и указав, печатать ли сообщения в консоль
    message_buss = message_bus_factory(
        component_id='001',  # идентификатор компонента (если не передать то сформируется uuid4)
        component_name='app',  # название главного компонента
        print_message=True,  # печатать ли сообщения в консоль
    )
    # 2. Печатать
    message_buss(
        subcomponent='audio_input',  # название подмодуля
        level='start',  # уровни события
        event='app is running',  # event
        message='Приложение запущено',  # человекочитаемое сообщение
        request_id=str(uuid4())[:8],  # id для цепочки операций
    )
    """
    message_bus = MessageBus(print_message=print_message)

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
                component_id=component_id or str(uuid4())[:8],
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
        component_id='001',  # идентификатор компонента (если не передать то сформируется uuid4)
        component_name='app',  # название главного компонента
        print_message=True,  # печатать ли сообщения в консоль
    )
    # 2. Печатать
    message_buss(
        subcomponent='audio_input',  # название подмодуля
        level='start',  # уровни события
        event='app is running',  # event
        message='Приложение запущено',  # человекочитаемое сообщение
        request_id=str(uuid4())[:8],  # id для цепочки операций
    )
