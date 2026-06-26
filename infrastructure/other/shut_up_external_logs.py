import os

__all__ = ['shut_up_external_logs', 'ShutUpLogs']


class ShutUpLogs:
    """
    Подавление логов C++ библиотек.
    Пример использования:
    shut_up = ShutUpLogs(off=False) # если поставить галочку, то можно отключить игнорирование логов
    shut_up.enable() # включение подавления логов
    ... # проблемный код (который кидает непрошенные логи)
    shut_up.disable() # выключение подавления логов
    """

    def __init__(self, off: bool = False):
        self._old_stdout = None
        self._old_stderr = None
        self._devnull = None
        self.off = off

    def enable(self):
        """
        Подавление терминала (подмена дескрипторов)
        """
        if self.off:
            return
        # сохранение оригинальных дескрипторов
        self._old_stdout = os.dup(1)
        self._old_stderr = os.dup(2)

        # Открыть /dev/null
        self._devnull = os.open(os.devnull, os.O_WRONLY)

        # Подмена дескрипторов
        os.dup2(self._devnull, 1)
        os.dup2(self._devnull, 2)

    def disable(self):
        """
        Восстановление дескрипторов (связи с терминалом обратно)
        """
        if self.off:
            return
        # Восстановить оригинальные дескрипторы
        os.dup2(self._old_stdout, 1)
        os.dup2(self._old_stderr, 2)
        os.close(self._devnull)
        os.close(self._old_stdout)
        os.close(self._old_stderr)


def shut_up_external_logs(func=None, *, enable: bool = True):
    """
    Универсальный декоратор для подавления логов сторонних C/C++ библиотек.
    ВАЖНО! Декоратор подавляет полностью все логи, на протяжении всей работы функции. Если это не подходит, то
    использовать класс ShutUpLogs, который позволяет управлять подавлением в ручную через shut_up.disable, shut_up.enable

    Можно использовать с параметром или без:
        @shut_up_external_logs           # enable=True по умолчанию
        @shut_up_external_logs()         # то же самое
        @shut_up_external_logs(enable=False)  # отключить подавление

    Иногда оказывается 🤷‍♂️, что некоторые библиотеки пишут свои логи и засоряют консоль.
    Например Kaldi от vosk, этот декоратор делает 🧙‍♂️ и убирает лишние логи.
    """

    # Если вызвали без скобок, func будет передан напрямую
    if func is not None:
        return _decorator(func, enable)

    # Если вызвали с параметрами, возвращаем декоратор
    return lambda f: _decorator(f, enable)


def _decorator(func, enable: bool):
    def wrapper(*args, **kwargs):
        shut_up = ShutUpLogs()
        if not enable:
            return func(*args, **kwargs)
        # успокоить консоль логи (подавляет абсолютно все логи и даже принты)
        shut_up.enable()
        try:
            res = func(*args, **kwargs)
        finally:
            # вернуть логи обратно
            shut_up.enable()
        return res

    return wrapper
