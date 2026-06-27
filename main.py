from pathlib import Path
from infrastructure.git_client import adapter_git_push_update

# отправка коммита на git с редактированием версии и истории в .md (если есть новые блоки истории)
adapter_git_push_update(
    root_dir=Path.cwd(),  # корневая папка каталога
    history_header='## История развития модуля',
    history_new_marker='@new',
)
