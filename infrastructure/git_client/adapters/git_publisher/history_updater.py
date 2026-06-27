import re
from pathlib import Path
from datetime import datetime

__all__ = ['update_module_history']


def process_history_block(
        content: str, version: str, commit_hash: str,
        history_header: str = '## История развития модуля', history_new_marker='@new',
) -> str | None:
    start_history = False
    start_new_block = False
    blocks = []
    for line in content.splitlines():
        if history_header in line:
            start_history = True
        elif '---' in line:
            start_history = False
        elif '<details>' in line:
            start_history = False
            start_new_block = False

        if re.match(pattern=fr'^{history_new_marker}', string=line):
            start_new_block = True
        if start_history and start_new_block:
            blocks.append(line)

    if not blocks:
        return None

    # подстановка текущей даты
    today = datetime.now().strftime("%d.%m.%Y")

    new_block = [
        '<details>',
        f"  <summary>{today} - v{version} - {commit_hash}</summary>",
        '\n'.join(blocks[1:]),
        '</details>\n'
    ]

    block = '\n'.join(blocks)
    new_block = '\n'.join(new_block)
    content = content.replace(block, new_block)
    return content


def update_module_history(
        md_files_dir: Path, version: str, commit_hash: str,
        history_header: str = '## История развития модуля', history_new_marker='@new',
) -> None:
    """
    Обновление истории в readme.md, привязанное к каждому коммиту и версии.
    Оборачивает блок в тег details, чтобы не раздувать файл длинным текстом, а скрывать блоки.
    ------------------------------------------------------------
    # Как использовать:
    В файле reamde.md, должен быть создан блок вида:
    26.06.2026
    - Изменение такое то...

    На выходе будет преобразован в :

    <details>
      <summary>26.06.2026 - vx.x.x - <commit></summary>

    - Изменение такое то...

    </details>

    Пример:
    update_module_history(
        md_files_dir=Path('./docs'),
        version='0.1.0',
        commit_hash='baa557',
        history_header='## История развития модуля',
    )
    ------------------------------------------------------------
    :param md_files_dir: директория с файлами с .md документами, например .docs
    :param version: версия приложения (например из pyproject.toml)
    :param commit_hash: id коммита (или сообщение комита)
    :param history_header: заголовок блока с историей изменений в .md файле
    :param history_new_marker: начало строки нового поста
    :return: None
    """
    for file in md_files_dir.rglob('*md'):
        with open(file, mode='r', encoding='utf-8') as fr:
            content = fr.read()
            update_content = process_history_block(
                content=content,
                version=version,
                commit_hash=commit_hash,
                history_header=history_header,
                history_new_marker=history_new_marker,
            )

            if update_content is not None and update_content:
                with open(file, mode='w', encoding='utf-8') as fw:
                    fw.write(update_content)
