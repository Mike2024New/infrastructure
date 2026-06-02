from collections import deque
from typing import Generator
import threading
from message_bus.schemas import Message


class MessageBus:
    def __init__(self, max_size: int = 1000, print_message: bool = False):
        self._messages = deque(maxlen=max_size)
        self._lock = threading.Lock()  # защита от гонки состояний
        self._message_new_event = threading.Event()  # наблюдатель за появлением сообщений
        self._print_message = print_message

    def add(self, message: Message) -> None:
        """
        Добавить сообщениеe
        :param message: основная информация о сообщении см класс Message
        :return:
        """
        with self._lock:
            self._messages.append(message)
            self._message_new_event.set()  # сигнал о том что сообщение получено
            if self._print_message:
                print(message)

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

    def reset(self):
        with self._lock:
            self._messages.clear()
            self._message_new_event.clear()


if __name__ == '__main__':
    msg = Message(
        component_id='Любой идентификатор (но в компоненте он генерится из UUID)',
        component='STT',
        subcomponent='STT.audio_input',
        level='debug',
        message='Компонент запущен'
    )
    print(msg)
