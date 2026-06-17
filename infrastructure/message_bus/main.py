from collections import deque
from typing import Generator
import threading
from infrastructure.message_bus.schemas import Message
from rich import print

__all__ = ['MessageBus', 'MessagePrintSettings']

colors = {
    'debug': 'bright_black',  # серый — техническое, неважное
    'info': 'white',  # белый — нейтральная информация
    'warning': 'bright_yellow',  # жёлтый — внимание, но не страшно
    'error': 'bright_red',  # красный — ошибка
    'critical': 'red on white',  # красный на белом — максимальный контраст, беда
    'process': 'bright_cyan',  # голубой — процесс идёт, что-то происходит
    'start': 'bright_green',  # зелёный — запуск, всё хорошо
    'stop': 'yellow',  # тёмно-жёлтый — завершение, спокойное
}

from dataclasses import dataclass


@dataclass
class MessagePrintSettings:
    print_date: bool = True  # дополнительные настройки
    raw_message: bool = False  # сообщение в виде сырой json строки


class MessageBus:
    def __init__(
            self,
            max_size: int = 1000,
            print_message: bool = False, print_settings: MessagePrintSettings | None = None,
    ):
        """

        :param max_size: максимальное количество сообщений которое может пребывать в шине
        :param print_message: печатать ли в консоль сообщения в реал-тайме? (не потребляет сообщения из шины сообщений)
        :param print_settings: настройки печати в реальном времени (сырая строка на печать?, печатать ли дату?)
        """
        self._messages = deque(maxlen=max_size)
        self._lock = threading.Lock()  # защита от гонки состояний
        self._message_new_event = threading.Event()  # наблюдатель за появлением сообщений
        self.print_message = print_message  # для совместимости со старыми приложениями остается такой режим
        self.print_settings = print_settings

    def add(self, message: Message) -> None:
        """
        Добавить сообщениеe
        :param message: основная информация о сообщении см класс Message
        :return:
        """
        with self._lock:
            self._messages.append(message)
            self._message_new_event.set()  # сигнал о том что сообщение получено
            if self.print_message:
                self.render_message(msg=message)

    def get_all(self) -> list[Message]:
        """
        Отдать все накопленные сообщения по прямому запросу
        :return: список Messages
        """
        with self._lock:
            messages = list(self._messages)
            self._messages.clear()
            self._message_new_event.clear()
        return messages

    def stream(self, timeout: float = 0.1) -> Generator[Message, None, None]:
        """
        Для webSocket/CLI - бесконечный поток сообщений с авточисткой. Отдал удалил
        :return: получил сообещние сразу его отдал
        """
        while True:
            self._message_new_event.wait(timeout=timeout)  # возбуждаться на каждый сигнал полученного сообщения
            with self._lock:
                while self._messages:
                    yield self._messages.popleft()
                self._message_new_event.clear()

    def render_message(self, msg: Message) -> None:
        """
        Цветной вывод сообщения из шины сообщений в реальном времени (не потребляет шину, просто показывает пришедшее сообещние)
        :param msg: Message
        :return: None
        """
        color = colors.get(msg.level, 'white')
        # просто показывать сырую строку
        if self.print_settings is None or self.print_settings.raw_message:
            raw = msg.model_dump_json(indent=2)
            print(f'[{color}]{raw}[/{color}]')
            return

        level_text = f'[{color}]{msg.level.ljust(8)}[/{color}]'
        text = f'{level_text} '
        if self.print_settings.print_date:
            text += f'  [bright_black]{msg.date}[/bright_black] '
        text += f'  [{color}]{msg.message}[/{color}]'
        print(text)

    def reset(self):
        with self._lock:
            self._messages.clear()
            self._message_new_event.clear()


if __name__ == '__main__':
    message_bus = MessageBus(
        print_message=True,
        # подключение настроек рендера сообщения
        print_settings=MessagePrintSettings(
            print_date=True,
            raw_message=False,
        ),
    )

    # добавление сообщения в шину сообщений
    message_bus.add(
        message=Message(
            component_id='Любой идентификатор (но в компоненте он генерится из UUID)',
            component='STT',
            subcomponent='STT.audio_input',
            level='error',
            message='Компонент запущен',
            error='Случилась ситуация',
        )
    )
