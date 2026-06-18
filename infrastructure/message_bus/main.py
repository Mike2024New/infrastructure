import uuid
from collections import deque
from pathlib import Path
from typing import Generator
import threading
from infrastructure.message_bus.schemas import Message
from infrastructure.path_utils.rotate_file import rotate_file_by_size
from dataclasses import dataclass
from rich import print
import atexit

__all__ = ['MessageBus', 'MessagePrintSettings', 'FileLogSettings']

colors = {
    'debug': 'bright_black',  # серый — техническое, неважное
    'info': 'white',  # белый — нейтральная информация
    'warning': 'bright_yellow',  # жёлтый — внимание, но не страшно
    'error': 'bright_red',  # красный — ошибка
    'critical': 'red on white',  # красный на белом — максимальный контраст, беда
    'process': 'bright_cyan',  # голубой — процесс идёт, что-то происходит
    'start': 'bright_green',  # зелёный — запуск, всё хорошо
    'stop': 'bright_green',  # зелёный — завершено, всё хорошо
}

from dataclasses import field
from typing import Literal


@dataclass
class MessagePrintSettings:
    """
    :param print_date: показывать дату события?
    :param raw_message: показывыть в консоли сырую строку?
    :param ignore_levels: игнорировать уровни чтобы не засорять консоль ( 'debug', 'info', 'warning', 'error', 'critical', 'start', 'stop', 'process')
    :param ignore_levels_invers:  перевернуть условие, показывать только содержащиеся в ignore_levels ключи
    """
    print_date: bool = True  # дополнительные настройки
    raw_message: bool = False  # сообщение в виде сырой json строки
    ignore_levels: list[Literal['debug', 'info', 'warning', 'error', 'critical', 'start', 'stop', 'process',]] | None = field(
        default_factory=list),  # игнорировать уровни
    ignore_levels_invers: bool = False,  # перевернуть условие, показывать только содержащиеся в ignore_levels ключи


@dataclass
class FileLogSettings:
    """
    Настройка файлов логирования. Здесь указывается максимальный размер, и количество файлов
    :param max_size_mb: максимальный размер файла в mb
    :param max_files:  максимальное количество файлов в размерах
    :param rotation_disable:  отключить ротацию? (просто тогда пишет монолитный файл)
    """
    max_size_mb: int | float = 10
    max_files: int = 10
    rotation_disable: bool = False


class MessageBus:
    def __init__(
            self,
            max_size: int = 1000,
            print_message: bool = False,
            print_settings: MessagePrintSettings | None = None,
            file_log_json_path: Path | None = None,
            file_log_settings: FileLogSettings | None = None,
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
        self._json_bufer_msg = []
        self._json_bufer_msg_limit = 5
        # настройки логирования
        self._file_log_settings = file_log_settings or FileLogSettings()  # берутся по умолчанию если не указаны
        self._json_log_path = file_log_json_path
        self._json_file_lock = threading.Lock()  # защита файла json от состояния гонки
        atexit.register(self._write_log)  # при выходе обязательно записать оставшиеся в буфере сообщения

    def add(self, message: Message) -> None:
        """
        Добавить сообщениеe
        :param message: основная информация о сообщении см класс Message
        :return:
        """
        with self._lock:
            self._messages.append(message)
            self._message_new_event.set()  # сигнал о том что сообщение получено
            self._json_bufer_msg.append(message)

            # сообщения добавляются через лимитированный буфер, чтобы не делать операцию ввода/вывода на каждый message
            if len(self._json_bufer_msg) >= self._json_bufer_msg_limit:
                self._write_log()

            if self.print_message:
                self.render_message(msg=message)

    def _write_log(self) -> None:
        """
        Добавление json логов
        """
        if self._json_log_path is None:
            return

        with self._json_file_lock:
            if not self._json_bufer_msg:
                return

            buffer = self._json_bufer_msg
            self._json_bufer_msg = []

        # подключение ротатора файлов
        @rotate_file_by_size(
            max_size_mb=self._file_log_settings.max_size_mb,
            max_files=self._file_log_settings.max_files,
            path_key_name='file_path',  # определение ключа который отвечает за путь в операции записи
            disable=self._file_log_settings.rotation_disable,
        )
        def write_log_file(file_path):
            with open(file=file_path, mode='a', encoding='utf-8') as f:
                for msg in buffer:
                    f.write(msg.model_dump_json() + '\n')

        write_log_file(file_path=self._json_log_path)

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
        # Ранний выход: нет настроек или сырой режим
        if self.print_settings is None or self.print_settings.raw_message:
            color = colors.get(msg.level, 'white')
            raw = msg.model_dump_json(indent=2)
            print(f'[{color}]{raw}[/{color}]')
            return

        # Фильтр по уровням
        if not self.print_settings.ignore_levels:
            pass  # список пуст — показываем всё
        elif not self.print_settings.ignore_levels_invers:
            if msg.level in self.print_settings.ignore_levels:
                return  # игнорируем
        else:
            if msg.level not in self.print_settings.ignore_levels:
                return  # показываем только из списка

        # Обычный вывод
        color = colors.get(msg.level, 'white')
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

    logs_dir = Path.cwd() / 'logs'
    logs_dir.mkdir(parents=True, exist_ok=True)

    message_bus = MessageBus(
        print_message=True,  # активация печати принтов
        # активация логирования сообщений в файлы (нужно просто передать путь, если путь не передан файлов логов не будет)
        file_log_json_path=Path(logs_dir / 'log.jsonl'),
        # подключение настроек рендера сообщения
        print_settings=MessagePrintSettings(
            print_date=True,
            raw_message=False,
            ignore_levels=['start', 'stop'],
            ignore_levels_invers=False,
        ),
        # подключение настроек ротации файлов (если не подключены но передан путь, возьмутся по умолчанию)
        file_log_settings=FileLogSettings(
            max_size_mb=0.5,
            max_files=5,
            rotation_disable=False,
        ),
    )

    for i in range(10000):
        message_bus.add(
            message=Message(
                component_id=str(uuid.uuid4())[:4],
                component='demo',
                subcomponent='sub',
                level='start',
                message=f'Msg for example {i}',
                event='event example',
                data={'status': 'ok'},
            )
        )
