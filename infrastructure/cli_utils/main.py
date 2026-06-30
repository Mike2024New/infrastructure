import typer, subprocess
from rich import print
from pathlib import Path
from typing import Callable, Any
from infrastructure.builder import BuildParameters
from infrastructure.builder.main import build as builder_func
from infrastructure.git_client import adapter_git_push_update
from infrastructure.path_utils.open_folder import open_folder

_exe_mode: bool = False
_message_bus: Any | None = None

__all__ = [
    'get_cli_app',
    'cli_command_execute',
]


def cli_command_execute(callback: Callable, command_name: str) -> Any | None:
    """
    Обработка команды, с отловом ошибки
    :param callback: исполняемая функция с аргументами
    :param command_name: Название команды app.info.name
    :return: результат выполнения функции либо None
    """
    try:
        return callback()
    except Exception as err:
        if _message_bus is not None:  # логирование ошибки
            _message_bus(
                level='error',
                subcomponent='cli',
                message=f'Ошибка в процессе выполнения команды {command_name}',
                event='cli run command error',
                error=err,
            )

        if _exe_mode:  # для exe режима
            print(f'[red]Ошибка в процессе выполнения команды: {err}[/red]')
        else:  # для разработчиков
            raise
    return None


def create_cli_app(name: str) -> typer.Typer:
    app = typer.Typer(
        name=name,
        no_args_is_help=True,
        # если пользователь дал команду без аргументов то не падать с ошибкой а показать справку
        rich_markup_mode='rich',
        # добавить rich панели (группировка комманд по заголовкам)
        add_completion=False,  # убрать блок option в всплывающем меню
        invoke_without_command=True,  # разрешить запуск без команд
    )

    @app.callback()
    def main():
        """CLI интерфейс"""

    return app


def register_folder_command(app: typer.Typer, root_dir: Path) -> None:
    @app.command()
    def folder():
        """Открыть домашнюю папку приложения"""
        cli_command_execute(
            callback=lambda: open_folder(root_dir),
            command_name=app.info.name,
        )


def register_build_command(app: typer.Typer, build_settings: BuildParameters) -> None:
    @app.command()
    def build(
            name: str | None = typer.Option(None, '-n', '-name'),
            one_file: bool = typer.Option(False, '-oe', '--onefile', flag_value=True),
            entry_path: Path | None = typer.Option(None, '-ep', '--entry_path'),
            create_resources_symlink: bool = typer.Option(False, '-sl', '--sym-link', flag_value=True),
    ):
        """
        [red]~dev [/red]Создание сборки, приложения .exe или .bin [yellow]build[/yellow]
        система определяется автоматически windows/linux
        Опции:
            -n (--name) - название приложения (если не переопределить то взьмется по умолчанию из settings)
            -oe (--onefile) - сборка одним файлом (по умолчанию выключена)
            -sl (--sym-link) - создать симлинк на папку с ресурсами
            -ep (--entry_path) - стартовый скрипт (по умолчанию этот же скрипт cli_utils.py)
        Примеры команд:
            [yellow]build[/yellow]
            [yellow]build -n my-app[/yellow] - указать название приложения
            [yellow]build -oe[/yellow] - сборка одним файлом
            [yellow]build -ep ./main.py[/yellow] - входная точка приложения указанный файл
            [yellow]build -sl[/yellow] - создать симлинк на папку с ресурсами (для разработки)
            [yellow]build -n my-app -oe -ep -s ./main.py[/yellow] - все вместе с указанием точки сборки
        """

        # переопределение опций
        # build_settings = build_settings or BuildParameters()
        build_settings.name = name if name is not None else build_settings.name
        build_settings.one_file = one_file
        build_settings.create_resources_symlink = create_resources_symlink
        build_settings.entry_point_path = entry_path if entry_path is not None else build_settings.entry_point_path

        cli_command_execute(
            callback=lambda: builder_func(build_settings),
            command_name=app.info.name,
        )


def register_git_push(app: typer.Typer, root_dir: Path):
    @app.command()
    def git_push(
            notests: bool = typer.Option(False, '-nt', '--notests', flag_value=True),
    ):
        """
        [red]~dev [/red]Отправка git, с редактированием минорной версии в pyproject.toml, и редактировании блока
        истории в .md (при условии что там есть заголовок [yellow]`## История развития модуля`[/yellow] и в нем написана новость
        вида [yellow]`@new`[/yellow]. В корне проекта должен быть файл .env с переменными GIT_URL=<ваш url>, GIT_BRANCH=<ветка>.
        Перед коммитом запускаются тесты, если тесты не пройдены, коммит отменяется.
        Опции:
            -nt (--notests) - не делать тесты перед коммитом

        Примеры команд:
            [yellow]git-push[/yellow]
            [yellow]git-push -nt[/yellow] - коммит без тестов
        """

        # выполнить тесты перед коммитом
        if not notests:
            result: subprocess.CompletedProcess = cli_command_execute(
                callback=lambda: subprocess.run(['pytest', '-v', '-s'], cwd=root_dir),
                command_name=app.info.name,
            )
            if result and result.returncode != 0:
                print('[red]Коммит отменён — тесты не пройдены[/red]')
                return

        adapter_git_push_update(
            root_dir=root_dir,
            history_header='## История развития модуля',
            history_new_marker='@new',
        )


def register_run_test(app: typer.Typer, root_dir: Path):
    @app.command()
    def run_tests(
            v: bool = typer.Option(False, '-v', flag_value=True),
            s: bool = typer.Option(False, '-s', flag_value=True),
    ):
        """
        [red]~dev [/red]Запуск тестов.
        Опции:
            -v - подробный режим с путем к каждому модулю
            -s - показывать принты внутри тестов
        Примеры команд:
            [yellow]run-tests -v -s[/yellow] - запуск тестов
        """
        cmd = ['pytest']

        # # добавление опций / add options
        cmd.extend(['-v']) if v else cmd.extend([])
        cmd.extend(['-s']) if s else cmd.extend([])

        result: subprocess.CompletedProcess = cli_command_execute(
            callback=lambda: subprocess.run(cmd, cwd=root_dir),
            command_name=app.info.name,
        )
        if result and result.returncode != 0:
            print('[red]Тесты не пройдены.[/red]')


def get_cli_app(
        name: str,
        root_dir: Path,
        build_settings: BuildParameters | None = None,
        exe_mode: bool = False,
        message_bus=None,
) -> typer.Typer:
    """
    Получение экземпляра typer для консоли приложения, с предопределенными базовыми методами.
    :param name: название приложения
    :param root_dir: корневая папка проекта
    :param build_settings: настройки для сборщика (передавать не обязательно, возьмутся опциональные параметры)
    :param exe_mode: режим exe (приложение) или разработка?
    :param message_bus: Опционально: шина сообщений (см. подробнее `message_bus_factory_v2` в модуле infrastructure.message_bus)
    :return: экземпляр приложения. Который запускается app()
    Пример использования:

    # =========== cli_utils.py =============================================================
    import config
    from cli_base.cli_base import get_cli_app

    # получение базовых повторяющихся команд
    app = get_cli_app(
        name='llm',
        root_dir=config.ROOT_DIR, # корневая папка проекта (в которой лежат pyproject.toml, *.md файлы)
        exe_mode=config.EXE_MODE, # режим работы (код/сборка)
    )

    # запуск:
    if __name__ == '__main__':
        app()
    # =================================================================================
    """
    global _exe_mode, _message_bus

    app = create_cli_app(name=name)
    _exe_mode = exe_mode
    _message_bus = message_bus
    # общие команды
    register_folder_command(app=app, root_dir=root_dir)
    if not exe_mode:  # команды которые будут доступны только в режиме разработчик
        build_settings = build_settings or BuildParameters()  # проброс настроек
        register_run_test(app=app, root_dir=root_dir)
        register_git_push(app=app, root_dir=root_dir)
        register_build_command(app=app, build_settings=build_settings)
    return app
