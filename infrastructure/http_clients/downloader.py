import os
import threading
import requests
import atexit
from pathlib import Path


class Downloader:
    """
    Класс загрузчика файлов http. После доводки перейдет в пакет infrastructure, как переиспользуемый компонент.
    """

    def __init__(self, directory: Path, replace_416: bool = False, timeout: float = 10):
        """
        Параметры для загрузчика
        :param directory: директория куда всё загружается
        :param replace_416: если файл уже есть, или на сервере изменился, то размеры не совпадут и вылезет 416 ошибка
        """
        self.progress = 0
        self._replace_416 = replace_416
        self._directory = directory
        self._timeout = timeout
        self._stop_it = threading.Event()
        atexit.register(self.stop)

    def _download_file(self, url, filename, print_progress=True) -> Path:
        """
        Загрузка файла
        :param url: url для загрузки файла
        :param filename: название файла после скачивания
        :param print_progress: показывать процесс загрузки?
        :return: путь к файлу
        """
        self._stop_it.clear()
        dest = self._directory / filename
        local_size = dest.stat().st_size if dest.exists() else 0
        # если файл уже есть (недоскачанный) то продолжить загрузку с его последнего байта
        headers = {'Range': f'bytes={local_size}-'} if local_size else {}

        try:
            response: requests.Response = requests.get(url, headers=headers, stream=True, timeout=self._timeout)
        except requests.exceptions.ConnectionError:
            raise RuntimeError(f"❌ Нет интернета. Невозможно скачать {filename}")
        except requests.exceptions.Timeout:
            raise RuntimeError(f"❌ Таймаут соединения. Сервер {url} не отвечает")

        if response.status_code == 416:
            if not self._replace_416:
                raise RuntimeError(
                    f'Ошибка 416, вероятно файл `{filename}` уже есть. Если нужна замена, поставить флаг replace_416'
                )
            response: requests.Response = requests.get(url, headers={}, stream=True)
        response.raise_for_status()

        total = int(
            response.headers.get('content-range', '/').split('/')[-1] or response.headers.get('content-length', 0)
        )
        mode = 'ab' if response.status_code == 206 else 'wb'
        if mode == 'wb':
            local_size = 0
            total = int(response.headers.get('content-length', 0))

        os.makedirs(self._directory, exist_ok=True)

        with open(dest, mode) as f:
            downloaded = local_size
            for chunk in response.iter_content(8192):
                if self._stop_it.is_set():
                    print("\n⏹ Загрузка прервана")
                    break
                f.write(chunk)
                downloaded += len(chunk)
                self.progress = {
                    'percent': (downloaded / total) * 100 if total > 0 else 0,
                    'downloaded': round(downloaded / (1024 ** 3), 2),
                    'total': round(total / (1024 ** 3), 2),
                }
                if print_progress and total:
                    print(
                        f"\r📥 Загрузка `{filename}` - {self.progress['percent']:.1f}% - "
                        f"{self.progress['downloaded']}/{self.progress['total']} GB",
                        end='', flush=True
                    )
        return dest

    def download_many_file(
            self, base_url, filenames: list[str], print_progress=True, wait_for: bool = False,
            callback_result_complete=None
    ) -> None:
        """
        Загрузка пакета файлов, для тех случаев когда по базовому url можно скачать несколько файлов.
        Например: base_url = `https://example.com/audio`
        а файлы: ['sound1.mp3','sound2.mp3']
        :param base_url: базовый url на котором размещены ресурсы
        :param filenames: названия скачиваемых файлов
        :param print_progress: показывать ли прогресс бар скачивания в терминале?
        :param wait_for: дожидаться окончания загрузки?
        :param callback_result_complete: действие с выполненным файлом
        :return: None
        """
        for filename in filenames:
            url = base_url + filename
            self.download_file(
                url=url,
                filename=filename,
                wait_for=wait_for,
                print_progress=print_progress,
                callback_result_complete=callback_result_complete,
            )

    def download_file(
            self, url, filename, print_progress=True, wait_for: bool = False,
            callback_result_complete=None
    ) -> None:
        """
        Скачивание файла (с возможностью докачки если был ранее не докачанный файл), в отдельном потоке, не блокируя
        основной код.
        :param url: url для загрузки файла
        :param filename: название файла после скачивания
        :param print_progress: показывать процесс загрузки?
        :param wait_for: заблокировать поток до окночания загрузки файла?
        :param callback_result_complete: callback функция применяемая к результату (пути к файлу после загрузки)
        :return: None
        """

        def wrapper():
            result = self._download_file(url, filename, print_progress)
            if callback_result_complete:
                callback_result_complete(result)

        thread = threading.Thread(target=wrapper, daemon=True)
        thread.start()
        if wait_for:
            thread.join()

    def stop(self):
        self._stop_it.set()


if __name__ == '__main__':
    # пример использования на скачивании модели с huggingface
    downloader = Downloader(
        replace_416=True,  # замена в случае если произойдет статус код 416
        directory=Path('./models')  # директория куда будут сохраняться файлы
    )

    downloader.download_file(
        # ссылка откуда скачивается файл
        url="https://huggingface.co/lmstudio-community/gemma-3-4b-it-GGUF/resolve/main/gemma-3-4b-it-Q4_K_M.gguf",
        # название сохраняемого файла (этот файл сохранится в папку directory)
        filename='gemma-3-4b-it-Q4_K_M.gguf',
        # заблокировать поток и дождаться загрузки?
        wait_for=True,
        # Действие с путем к файлу
        callback_result_complete=lambda file: print(f"Загрузка завершена, путь: {file} ")
    )
