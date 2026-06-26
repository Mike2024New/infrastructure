import uvicorn
from fastapi import FastAPI
from typing import Literal
from config import message_bus_add
import uuid

SUBCOMPONENT = 'server'


class Server:
    """
    Управление сервером, запуск остановка
    на вход при создании подать приложение fastapi
    start(port) по умолчанию 8000
    stop() остановка из внешних приложений
    ---------------------------------------------
    В реализации backend (или в cli) нужно вызывать метод server.stop()
    """

    def __init__(self, application: FastAPI):
        self._application = application
        self._server = None

    def start(self, port: int = 8000, log_level: Literal['debug', 'info', 'warning', 'error'] = 'warning'):
        request_id = str(uuid.uuid4())[:8]
        try:
            host = 'localhost'
            config = uvicorn.Config(app=self._application, host=host, port=port, log_level=log_level)
            self._server = uvicorn.Server(config)
            message_bus_add(
                subcomponent=SUBCOMPONENT,
                level='start',
                request_id=request_id,
                data={'host': host, 'port': port, 'log_level': log_level}
            )
            self._server.run()  # работает до тех пор пока self.server.shoud_exit=False
            message_bus_add(
                subcomponent=SUBCOMPONENT,
                level='stop',
                request_id=request_id,
            )

        except Exception as err:
            message_bus_add(
                subcomponent=SUBCOMPONENT,
                level='error',
                message='Ошибка запуска сервера',
                event='server is not running',
                request_id=request_id,
                error=err,
            )

    def stop(self):
        self._server.should_exit = True
