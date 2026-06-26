from fastapi import FastAPI, APIRouter, status
from server._server import Server
from config.settings import routers_list
from datetime import datetime

app = FastAPI()
# подключение роутеров
[app.include_router(router) for router in routers_list]
# создание экземпляра сервера для внешних приложений
server = Server(application=app)

__all__ = ['server']  # объект для управления сервером

info_routers = APIRouter(tags=['info'])
settings_routers = APIRouter(tags=['settings'])
manager_routers = APIRouter(tags=['manager'])


@info_routers.get('/')
@info_routers.get('/health/')
@info_routers.get('/status/')
def component_status():
    """
    Проверка состояния сервера. Проверка запущен ли компонент сервера (component_is_run).
    """
    return {
        'msg': 'Основная информация о сервере.',
        'timestamp': datetime.now().isoformat(),
    }


@manager_routers.get(
    '/shutdown/',
    response_model=dict[str, str],
    status_code=status.HTTP_200_OK,
    summary='Остановка сервера'
)
def shutdown():
    """Остановка сервера"""
    server.stop()
    return {
        'msg': 'сервер остановлен.'
    }


# добавление роутеров (разделено для удобного отображения в swagger ui)
app.include_router(info_routers)
app.include_router(manager_routers)
