import uuid
from pathlib import Path

from infrastructure.path_utils import get_root_dir_path
from infrastructure.git_client import GitClient
from infrastructure.settings_manager.settings_manager_toml import TomlManager
from update_history import update_module_history

"""
Быстрый скрипт, выгрузки изменений пакета infrastructure на git.
"""

commit_hash = str(uuid.uuid4())[:6]

toml_manager = TomlManager(
    project_path=get_root_dir_path()
)
# # инкремент версии.
toml_manager.inc_version(minor_in=True)
version = toml_manager.get_version()

# обновление истории в .md если требуется
update_module_history(
    md_files_dir=Path('./docs'),
    version=version,
    commit_hash=commit_hash,
    history_header='## История развития модуля',
)

# отправка на гит.
git_client = GitClient(
    git_url='git@github.com:Mike2024New/infrastructure.git',
    branch='main',
)
git_client.commit(commit_message=f'commit {commit_hash}')
