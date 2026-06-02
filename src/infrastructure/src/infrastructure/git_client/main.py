import subprocess
import uuid
from infrastructure.path_utils.path_finder import get_root_dir_path

__all__ = ['GitClient']

"""
Простейший гит клиент, для заброса пакетов на репозиторий. И принятия пакетов через uv в других проектах.
"""


class GitClient:

    def __init__(self, git_url: str, branch: str = 'main', venv_dir_name: str = '.venv'):
        """

        :param git_url:
        :param branch:
        :param venv_dir_name:
        """
        self._root_dir = get_root_dir_path(venv_dir_name=venv_dir_name)
        self._git_url = git_url
        self._branch = branch
        self._git_http_url = 'https://github.com/' + self._git_url.split(':')[-1].replace('.git', '')
        if not (self._root_dir / '.venv').exists():
            raise RuntimeError(
                f'Данная реализация клиента, работает только с venv, который должен быть в корневом каталоге и называться .venv\n'
                f'Например root_dir = "home/porjects/project" -> home/porjects/project/.venv'
            )
        self._change_branch_to_main()
        self._check_git()

    def _change_branch_to_main(self):
        cmd = ['git', 'config', '--global', 'init.defaultBranch', 'main']
        res = subprocess.run(cmd, cwd=self._root_dir, capture_output=True)
        if res.returncode != 0:
            raise RuntimeError(f'Не удалось изменить ветку на main. stdout: {res.stdout}, stderr: {res.stderr}')

    def _check_git(self):
        # проверка что гит инициализирован
        print(f'Порверка что git инициализирован')
        cmd = ['git', 'status']
        res = subprocess.run(cmd, cwd=self._root_dir, capture_output=True)
        if res.returncode != 0:
            raise RuntimeError(f'Ошибка, возможно git не инициализирован. stdout: {res.stdout}, stderr: {res.stderr}')

        # проверка что репозиторий существует
        print(f'Порверка наличия репозитория...')
        cmd = ['git', 'ls-remote', self._git_url]
        res = subprocess.run(cmd, cwd=self._root_dir, capture_output=True)
        if res.returncode != 0:
            raise RuntimeError(f'Ошибка, репозитория `{self._git_url}` не существует.')

        # проверка что указанная ветка существует
        cmd = ['git', 'branch']
        res = subprocess.run(cmd, cwd=self._root_dir, text=True, capture_output=True)
        branches = res.stdout.replace('*', '').strip().split()
        print(branches)
        if not branches:
            # ветки ещё не существует, так как это 1 коммит
            return
        if not self._branch in branches:
            raise RuntimeError(f'Ветка `{self._branch}` не найдена в репозитории `{self._git_url}`')

    def uv_install_package(self) -> None:
        """
        uv потребитель репозитория, установка пакета как библиотеки python (для повторяющихся в проектах скриптов)
        :return: None
        """
        # проверка что есть uv и работает корректно
        print(f'Порверка uv...')
        cmd = ['uv', '--version']
        res = subprocess.run(cmd, cwd=self._root_dir, capture_output=True)
        if res.returncode != 0:
            raise RuntimeError(
                f'Проблемы с uv, скорее всего не установлен.\n'
                f'stdout: {res.stdout}, stderr: {res.stderr}'
            )

        # проверка что toml есть
        print(f'Порверка pyproject.toml...')
        if not (self._root_dir / 'pyproject.toml').exists():
            raise RuntimeError(f'Нет файла `pyproject.toml` в корневом каталоге. uv не инициализирован.')

        # добавление репозитория в uv
        print(f'Установка репозитория и зависимостей...')
        uv_url = self._git_url.replace('git@github.com:', 'git+https://github.com/')
        cmd = ['uv', 'add', uv_url]
        res = subprocess.run(cmd, cwd=self._root_dir, capture_output=False)
        if res.returncode != 0:
            raise RuntimeError(
                f'Не удалось получить репозиторий `{self._git_url}`.\n'
                f'stdout: {res.stdout}, stderr: {res.stderr}')

    def commit(self, commit_message_auto: bool = False) -> None:
        """
        отправить изменения на репозиторий
        :param commit_message_auto: генерировать автоматическое сообщение для коммита (uuid)
        :return:
        """
        # проверка что есть что обновлять
        print(f'Проверка того что есть что обновлять.')
        cmd = ['git', 'status', '--porcelain']
        res = subprocess.run(cmd, cwd=self._root_dir, capture_output=True)
        if res.returncode != 0:
            raise RuntimeError(
                f'Проблемы с гитом внутри пакета, вероятно git не инициализирован.\n'
                f'stdout: {res.stdout}, stderr: {res.stderr}'
            )
        if not res.stdout.strip():
            print('Нет изменений, git не отправлен.')
            return

        print(f'Стыковка с репозиторием.')
        cmd = ['git', 'remote', 'get-url', 'origin']  # получение ссылки текущего репозитория
        res = subprocess.run(cmd, cwd=self._root_dir, capture_output=True)
        if not res.stdout.strip():
            cmd = ['git', 'remote', 'add', 'origin', self._git_url]  # если нет стыковки то прилинковаться
            res = subprocess.run(cmd, cwd=self._root_dir, capture_output=True)
            if res.returncode != 0:
                raise RuntimeError(
                    f'Не удалось подключить git к url {self._git_url}'
                    f'stdout: {res.stdout}, stderr: {res.stderr}'
                )

        # сообщение в комите
        commit_msg = f'commit {str(uuid.uuid4())[:6]}' if commit_message_auto \
            else input('Введите сообщение с описанием коммита:_')

        # обновление
        cmd_list = [
            ['git', 'add', '.'],
            ['git', 'commit', '-m', commit_msg],
            ['git', 'push', '-u', 'origin', self._branch]
        ]

        for cmd in cmd_list:
            res = subprocess.run(cmd, cwd=self._root_dir)
            if res.returncode != 0:
                raise RuntimeError(
                    f'Ошибка в команде {cmd}'
                    f'stdout: {res.stdout}, stderr: {res.stderr}'
                )

        print(
            f'Готово! Проект отправлен на GitHub.\n'
            f'  url: {self._git_http_url}\n'
            f'  clone: `git clone --depth 1 {self._git_url}`'
        )

    def pull(self):
        """Получение обновления репозитория"""
        cmd = ['git', 'pull', 'origin', self._branch]
        res = subprocess.run(cmd, cwd=self._root_dir, capture_output=True)
        if res.returncode != 0:
            raise RuntimeError(
                f'Ошибка обновления репозитория.\n'
                f'stdout: {res.stdout}, stderr: {res.stderr}',
            )
        print(f'Репозиторий обновлен.')

    def info(self):
        return {
            'url': self._git_url,
            'url_http': self._git_http_url,
            'url_uv': self._git_url.replace('git@github.com:', 'git+https://github.com/'),
            'branch': self._branch,
        }
