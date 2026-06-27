import uuid
from pathlib import Path
from infrastructure.git_client import GitClient
from infrastructure.settings_manager.settings_manager_toml import TomlManager
from infrastructure.settings_manager.settings_manager_env import load_settings_env, SettingsEnvModel
from infrastructure.git_client.adapters.git_publisher.history_updater import update_module_history

__all__ = ['adapter_git_push_update']


def _get_git_env(env_path: Path) -> tuple[str, str]:
    class GitEnvSettings(SettingsEnvModel):
        git_url: str = ...
        branch: str = 'main'

    env_settings = load_settings_env(
        settings_class=GitEnvSettings,
        env_path=env_path,
        env_prefix='',
    )
    if env_settings.git_url == 'null' or env_settings.branch == 'null':
        raise RuntimeError(
            f'Ошибка отправки коммита на git, в корневом .env, должны быть переменные:\n'
            f'GIT_URL=<ваш репозиторий>\n'
            f'GIT_URL=<ваша ветка>\n'
            f'Сейчас значения этих переменных null\n'
            f'Корневой .env <{env_path}>'
        )
    return env_settings.git_url, env_settings.branch


def adapter_git_push_update(
        root_dir: Path,
        history_header: str = '## История развития модуля',
        history_new_marker: str = '@new',
) -> None:
    """
    Отправка коммита на гит с изменением минорной версии в pyproject.toml и редактированием
    блока истории изменений -> в README.md нужно создать блок вида `# История изменений проекта`
    :param root_dir: корневая папка каталога, для поиска pyproject.toml, .env, .md (в том числе и вложенных)
    :param history_header:  заголовок блока изменений, например '## История развития модуля'
    :param history_new_marker: маркер новой истории, например '@new'
    :return: None
    """
    env_path = root_dir / '.env'

    if not env_path.exists():
        env_path.write_text('GIT_URL=null\nGIT_BRANCH=null', encoding='utf-8')

    git_url, git_branch = _get_git_env(env_path=env_path)

    commit_hash = str(uuid.uuid4())[:6]

    toml_manager = TomlManager(
        project_path=root_dir
    )
    # инкремент версии.
    version = toml_manager.get_version()

    # обновление истории в .md если требуется
    update_module_history(
        md_files_dir=Path(root_dir),
        version=version,
        commit_hash=commit_hash,
        history_header=history_header,
        history_new_marker=history_new_marker,
    )

    # отправка на гит.
    git_client = GitClient(
        git_url=git_url,
        branch=git_branch,
    )
    git_client.commit(commit_message=commit_hash)
    toml_manager.inc_version(minor_in=True)
