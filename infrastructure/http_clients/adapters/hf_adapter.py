from pathlib import Path
from time import perf_counter
from infrastructure.http_clients import Downloader

SUBCOMPONENT = 'hugging_face_downloader'


def adpater_download_from_hf(
        models_list: dict, download_dir: Path, model_name: str, branch: str = 'main', replace_file: bool = False,
        message_bus_add=None, wait_for: bool = True, print_progress: bool = True,
) -> None:
    """
    HuggingFace загрузчик
    --------------------------------------------------------------------------------------
    Загрузка моделей и ресурсов с huggingfase.
    Работает по прцнципу, генерации url формата:
    f"https://huggingface.co/{parameters['repository']}/{model_name}/resolve/{branch}/"
    Принимает словарь с описанием репозитория, вида:
    models_list = {
    'lmstudio-community': {
        'gemma-3-4b-it-GGUF': ["gemma-3-4b-it-Q4_K_M.gguf"],
        'gemma-3-12b-it-GGUF': ["gemma-3-12b-it-Q4_K_M.gguf"],
        },
    }
    В текущем примере `lmstudio-community` репозиторий, 'gemma-3-4b-it-GGUF' модель, и в списке
    к этой модели указаны файлы которые нужно загрузить.
    --------------------------------------------------------------------------------------
    :return:
    :param models_list: описание репозитория (см п.1 models_list)
    :param download_dir: папка в которую будут загружены модели (во вложенной папке)
    :param model_name: наименование модели например 'gemma-3-4b-it-GGUF'
    :param branch: ветка репозитория например main
    :param replace_file: заменять ли файл если уже был скачан? (для недокачанных файлов ставится True)
    :param message_bus_add: шина сообщений вызывающего компонента
    :param wait_for: заблокировать поток до окончания загрузки?
    :param print_progress: показывать прогресс в терминал?
    :return: None

    --------------------------------------------------------------------------------------
    пример использования:

    adpater_download_from_hf(
        models_list=available_models_list,
        download_dir=config.MODELS_DIR,
        model_name='gemma-3-12b-it-GGUF',
        replace_file=True,
        message_bus_add=config.message_bus_add,
        wait_for=True,
        print_progress=True,
    )
    """
    start_time = perf_counter()
    parameters = None
    for repository in models_list.keys():
        for model in models_list[repository]:
            if model_name == model:
                parameters = {'repository': repository, 'files': models_list[repository][model]}

    if parameters is None:
        message_error = f'Модель {model_name} не найдена.'
        if message_bus_add is not None:
            message_bus_add(
                subcomponent=SUBCOMPONENT,
                level='error',
                event='model not found',
                message=message_error,
            )
        raise RuntimeError(message_error)

    if message_bus_add is not None:
        message_bus_add(
            subcomponent=SUBCOMPONENT,
            level='start',
            event='start download model',
            message=f'Начало загрузки модели {model_name}',
        )
    downloader = Downloader(directory=download_dir / model_name, replace_416=replace_file)
    downloader.download_many_files(
        base_url=f"https://huggingface.co/{parameters['repository']}/{model_name}/resolve/{branch}/",
        filenames=parameters['files'],
        print_progress=print_progress,
        wait_for=wait_for,
        downloaded_name=model_name,
    )
    end_time = f'{perf_counter() - start_time:.2f} сек.'
    if message_bus_add is not None:
        message_bus_add(
            subcomponent=SUBCOMPONENT,
            level='stop',
            event='end download model',
            message=f'Загрузка модели {model_name}, завершена, времени прошло {end_time}',
            data={'metric': end_time},
        )


if __name__ == '__main__':
    # пример описания репозитория (для моделей whisper)
    available_models_list = {
        'Systran': {
            'faster-whisper-tiny': ["model.bin", "config.json", "tokenizer.json", "vocabulary.txt"],
        },

    }

    # загрузка модели
    adpater_download_from_hf(
        models_list=available_models_list,
        download_dir=Path('./models'),
        model_name='faster-whisper-tiny',
        replace_file=True,
        message_bus_add=None,
        wait_for=True,
        print_progress=True,
    )
